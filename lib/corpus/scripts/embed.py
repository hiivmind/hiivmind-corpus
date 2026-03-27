#!/usr/bin/env python3
"""Generate embeddings from index.yaml or concepts YAML into SQLite.

Usage:
  python3 embed.py [--mode entries|concepts] [--force] <input.yaml> <output.db>

Modes:
  entries (default): Reads index.yaml, embeds title + summary + keywords per entry
  concepts: Reads concepts YAML, embeds label + description + tags per concept

Exit codes:
  0 - success
  1 - fastembed not installed
  2 - input file not found or invalid
  3 - other error
  4 - model mismatch (existing db built with different model)
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384


def parse_args():
    parser = argparse.ArgumentParser(description="Generate embeddings")
    parser.add_argument("input", help="Path to index.yaml or concepts YAML")
    parser.add_argument("output", help="Path to output SQLite database")
    parser.add_argument(
        "--mode",
        choices=["entries", "concepts"],
        default="entries",
        help="Embedding mode (default: entries)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-embedding all entries (ignore hashes)",
    )
    return parser.parse_args()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_entries(input_path):
    """Load entries from index.yaml, return list of (id, text) tuples."""
    import yaml

    with open(input_path) as f:
        data = yaml.safe_load(f)

    entries = []
    for entry in data.get("entries", []):
        entry_id = entry.get("id", "")
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        keywords = entry.get("keywords", [])
        if isinstance(keywords, list):
            keywords = ", ".join(keywords)
        text = f"{title} - {summary} {keywords}"
        entries.append((entry_id, text.strip()))
    return entries


def load_concepts(input_path):
    """Load concepts from concepts YAML, return list of (id, text) tuples."""
    import yaml

    with open(input_path) as f:
        data = yaml.safe_load(f)

    concepts = []
    for concept in data.get("concepts", []):
        concept_id = concept.get("id", "")
        label = concept.get("label", "")
        description = concept.get("description", "")
        tags = concept.get("tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        text = f"{label} - {description} {tags}"
        concepts.append((concept_id, text.strip()))
    return concepts


def init_db(db_path):
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            vector BLOB NOT NULL,
            text_hash TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


def check_model_match(conn):
    """Check if existing db was built with the same model. Returns True if ok."""
    cursor = conn.execute("SELECT value FROM meta WHERE key = 'model'")
    row = cursor.fetchone()
    if row is None:
        return True  # New db, no model set yet
    return row[0] == MODEL_NAME


def get_existing_hashes(conn):
    """Get dict of id -> text_hash from existing db."""
    cursor = conn.execute("SELECT id, text_hash FROM embeddings")
    return dict(cursor.fetchall())


def main():
    args = parse_args()

    # Check input file exists
    if not Path(args.input).exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    # Import fastembed
    try:
        from fastembed import TextEmbedding
    except ImportError:
        print(
            "Error: fastembed not installed. Run: pip install fastembed pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load entries/concepts
    try:
        if args.mode == "entries":
            items = load_entries(args.input)
        else:
            items = load_concepts(args.input)
    except Exception as e:
        print(f"Error: failed to parse input file: {e}", file=sys.stderr)
        sys.exit(2)

    if not items:
        print("Warning: no items found in input file", file=sys.stderr)
        sys.exit(2)

    # Initialize db
    db_path = Path(args.output)
    is_new = not db_path.exists()
    conn = init_db(str(db_path))

    # Check model match for existing db
    if not is_new and not args.force:
        if not check_model_match(conn):
            existing = conn.execute(
                "SELECT value FROM meta WHERE key = 'model'"
            ).fetchone()[0]
            print(
                f"Error: embeddings.db was built with {existing}, "
                f"current model is {MODEL_NAME}. "
                f"Re-embed with: python3 embed.py --force {args.input} {args.output}",
                file=sys.stderr,
            )
            conn.close()
            sys.exit(4)

    # Determine which items need embedding
    existing_hashes = {} if is_new or args.force else get_existing_hashes(conn)
    items_to_embed = []
    current_ids = set()

    for item_id, item_text in items:
        current_ids.add(item_id)
        h = text_hash(item_text)
        if args.force or existing_hashes.get(item_id) != h:
            items_to_embed.append((item_id, item_text, h))

    # Remove deleted entries
    if not is_new:
        existing_ids = set(existing_hashes.keys())
        deleted_ids = existing_ids - current_ids
        if deleted_ids:
            conn.executemany(
                "DELETE FROM embeddings WHERE id = ?",
                [(did,) for did in deleted_ids],
            )
            print(f"Removed {len(deleted_ids)} deleted entries", file=sys.stderr)

    # Embed new/changed items
    if items_to_embed:
        print(f"Embedding {len(items_to_embed)} items...", file=sys.stderr)
        model = TextEmbedding(model_name=MODEL_NAME)
        texts = [t for _, t, _ in items_to_embed]
        embeddings = list(model.embed(texts))

        for (item_id, _, h), embedding in zip(items_to_embed, embeddings):
            vector_blob = embedding.astype("float32").tobytes()
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (id, vector, text_hash) "
                "VALUES (?, ?, ?)",
                (item_id, vector_blob, h),
            )
    else:
        print("All embeddings up to date", file=sys.stderr)

    # Update metadata
    now = datetime.now(timezone.utc).isoformat()
    meta = {
        "model": MODEL_NAME,
        "dimensions": str(DIMENSIONS),
        "generated_at": now,
        "entry_count": str(len(items)),
        "mode": args.mode,
    }
    for key, value in meta.items():
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value)
        )

    conn.commit()
    conn.close()

    changed = len(items_to_embed)
    total = len(items)
    print(json.dumps({"total": total, "embedded": changed, "db": str(db_path)}))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
