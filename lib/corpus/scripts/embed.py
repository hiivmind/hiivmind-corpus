#!/usr/bin/env python3
"""Generate embeddings from index.yaml into a Lance dataset.

Usage:
  python3 embed.py [--force] <index.yaml> <output.lance>

Reads entries from index.yaml including their concepts[] field.
Embedding text: "passage: {title} | {summary} | {tags} | {concepts}"

The output path (e.g., index-embeddings.lance/) is the LanceDB database directory.
A fixed table name "embeddings" is used inside it. Model metadata is stored in a
"_meta" table within the same Lance database.

Exit codes:
  0 - success
  1 - fastembed/lancedb not installed
  2 - input file not found or invalid
  3 - other error
  4 - model mismatch (existing dataset built with different model)
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
TABLE_NAME = "embeddings"
META_TABLE = "_meta"
PASSAGE_PREFIX = "passage: "  # bge-small asymmetric retrieval prefix for documents
QUERY_PREFIX = "query: "  # bge-small asymmetric retrieval prefix for queries
VECTOR_INDEX_THRESHOLD = 500  # Create IVF_PQ index above this entry count


def parse_args():
    parser = argparse.ArgumentParser(description="Generate embeddings")
    parser.add_argument("input", help="Path to index.yaml")
    parser.add_argument("output", help="Path to output Lance dataset directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-embedding all entries",
    )
    return parser.parse_args()


def load_entries(input_path):
    """Load entries from index.yaml, return list of dicts."""
    import yaml

    with open(input_path) as f:
        data = yaml.safe_load(f)

    items = []
    for entry in data.get("entries", []):
        entry_id = entry.get("id", "")
        source = entry.get("source", "")
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        tags = entry.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        concepts = entry.get("concepts", [])
        if not isinstance(concepts, list):
            concepts = []
        metadata_text = (
            f"{title} | {summary} | {', '.join(tags)} | {', '.join(concepts)}"
        )
        items.append(
            {
                "id": entry_id,
                "source": source,
                "title": title,
                "tags": tags,
                "concepts": concepts,
                "metadata_text": metadata_text.strip(),
            }
        )
    return items


def read_meta(db):
    """Read metadata from _meta table. Returns dict or None."""
    try:
        if META_TABLE not in db.list_tables():
            return None
        meta_table = db.open_table(META_TABLE)
        meta_arrow = meta_table.to_arrow()
        keys = meta_arrow.column("key").to_pylist()
        values = meta_arrow.column("value").to_pylist()
        return dict(zip(keys, values))
    except Exception:
        return None


def write_meta(db, metadata, pa):
    """Write metadata to _meta table."""
    meta_records = [{"key": k, "value": str(v)} for k, v in metadata.items()]
    meta_schema = pa.schema(
        [
            pa.field("key", pa.string()),
            pa.field("value", pa.string()),
        ]
    )
    meta_table = pa.Table.from_pylist(meta_records, schema=meta_schema)
    db.create_table(META_TABLE, data=meta_table, mode="overwrite")


def migrate_meta_json(output_path, db, pa):
    """Migrate _meta.json sidecar to _meta table if needed."""
    meta_json_path = output_path / "_meta.json"
    if meta_json_path.exists() and META_TABLE not in db.list_tables():
        try:
            meta = json.loads(meta_json_path.read_text())
            write_meta(db, meta, pa)
            meta_json_path.unlink()
            print("Migrated _meta.json to _meta table", file=sys.stderr)
        except Exception as e:
            print(f"Warning: failed to migrate _meta.json: {e}", file=sys.stderr)


def main():
    args = parse_args()

    if not Path(args.input).exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    try:
        from fastembed import TextEmbedding
    except ImportError:
        print(
            "Error: fastembed not installed. "
            "Run: pip install fastembed lancedb pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import lancedb
        import pyarrow as pa
    except ImportError:
        print(
            "Error: lancedb not installed. "
            "Run: pip install fastembed lancedb pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load items
    try:
        items = load_entries(args.input)
    except Exception as e:
        print(f"Error: failed to parse input file: {e}", file=sys.stderr)
        sys.exit(2)

    if not items:
        print("Warning: no items found in input file", file=sys.stderr)
        sys.exit(2)

    # Check for existing dataset and model mismatch
    output_path = Path(args.output)
    if output_path.exists():
        db = lancedb.connect(str(output_path))
        # Migrate _meta.json -> _meta table if needed
        migrate_meta_json(output_path, db, pa)

        if not args.force:
            meta = read_meta(db)
            if meta:
                existing_model = meta.get("model", "")
                if existing_model and existing_model != MODEL_NAME:
                    print(
                        f"Error: dataset was built with {existing_model}, "
                        f"current model is {MODEL_NAME}. "
                        f"Re-embed with: python3 embed.py --force "
                        f"{args.input} {args.output}",
                        file=sys.stderr,
                    )
                    sys.exit(4)

    # Generate embeddings
    print(f"Embedding {len(items)} items with {MODEL_NAME}...", file=sys.stderr)
    model = TextEmbedding(model_name=MODEL_NAME)
    texts = [f"{PASSAGE_PREFIX}{item['metadata_text']}" for item in items]
    embeddings = list(model.embed(texts))

    # Build PyArrow table with explicit schema
    now = datetime.now(timezone.utc).isoformat()

    schema = pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("source", pa.string()),
            pa.field("title", pa.string()),
            pa.field("tags", pa.list_(pa.string())),
            pa.field("concepts", pa.list_(pa.string())),
            pa.field("metadata_text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), DIMENSIONS)),
            pa.field("updated_at", pa.string()),
        ]
    )

    records = []
    for item, embedding in zip(items, embeddings):
        records.append(
            {
                "id": item["id"],
                "source": item["source"],
                "title": item["title"],
                "tags": item["tags"],
                "concepts": item["concepts"],
                "metadata_text": item["metadata_text"],
                "vector": embedding.tolist(),
                "updated_at": now,
            }
        )

    arrow_table = pa.Table.from_pylist(records, schema=schema)

    # Write Lance dataset
    is_new = not output_path.exists()
    if is_new:
        db = lancedb.connect(str(output_path))

    if args.force or is_new or TABLE_NAME not in db.list_tables():
        tbl = db.create_table(TABLE_NAME, data=arrow_table, mode="overwrite")
    else:
        tbl = db.open_table(TABLE_NAME)
        (
            tbl.merge_insert("id")
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(arrow_table)
        )

    # Create FTS index on metadata_text for hybrid search
    try:
        tbl.create_fts_index("metadata_text", replace=True)
    except Exception as e:
        print(f"Warning: FTS index creation failed: {e}", file=sys.stderr)

    # Create vector index for large corpora
    if len(records) > VECTOR_INDEX_THRESHOLD:
        try:
            tbl.create_index(metric="cosine")
            print(
                f"Created vector index ({len(records)} entries "
                f"> {VECTOR_INDEX_THRESHOLD})",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Warning: vector index creation failed: {e}", file=sys.stderr)

    # Write metadata to _meta table
    metadata = {
        "model": MODEL_NAME,
        "dimensions": DIMENSIONS,
        "generated_at": now,
        "entry_count": len(records),
    }
    write_meta(db, metadata, pa)

    total = len(records)
    print(json.dumps({"total": total, "embedded": total, "dataset": str(output_path)}))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
