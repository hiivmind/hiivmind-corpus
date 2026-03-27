#!/usr/bin/env python3
"""Generate embeddings from index.yaml or concepts YAML into a Lance dataset.

Usage:
  python3 embed.py [--mode entries|concepts] [--force] <input.yaml> <output.lance>

Modes:
  entries (default): Reads index.yaml, embeds title + summary + tags per entry
  concepts: Reads concepts YAML, embeds label + description + tags per concept

The output path (e.g., index-embeddings.lance/) is the LanceDB database directory.
A fixed table name "embeddings" is used inside it. Model metadata is stored in a
_meta.json sidecar file alongside the Lance data.

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


def parse_args():
    parser = argparse.ArgumentParser(description="Generate embeddings")
    parser.add_argument("input", help="Path to index.yaml or concepts YAML")
    parser.add_argument("output", help="Path to output Lance dataset directory")
    parser.add_argument(
        "--mode",
        choices=["entries", "concepts"],
        default="entries",
        help="Embedding mode (default: entries)",
    )
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
        metadata_text = f"{title} | {summary} | {', '.join(tags)}"
        items.append(
            {
                "id": entry_id,
                "source": source,
                "title": title,
                "tags": tags,
                "metadata_text": metadata_text.strip(),
            }
        )
    return items


def load_concepts(input_path):
    """Load concepts from concepts YAML, return list of dicts."""
    import yaml

    with open(input_path) as f:
        data = yaml.safe_load(f)

    items = []
    for concept in data.get("concepts", []):
        concept_id = concept.get("id", "")
        label = concept.get("label", "")
        description = concept.get("description", "")
        tags = concept.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        metadata_text = f"{label} | {description} | {', '.join(tags)}"
        items.append(
            {
                "id": concept_id,
                "source": concept_id.split(":")[0] if ":" in concept_id else "",
                "title": label,
                "tags": tags,
                "metadata_text": metadata_text.strip(),
            }
        )
    return items


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

    # Check for existing dataset and model mismatch
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        meta_path = output_path / "_meta.json"
        if meta_path.exists():
            existing_meta = json.loads(meta_path.read_text())
            existing_model = existing_meta.get("model", "")
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
    texts = [f"passage: {item['metadata_text']}" for item in items]
    embeddings = list(model.embed(texts))

    # Build PyArrow table with explicit schema to avoid type inference issues
    now = datetime.now(timezone.utc).isoformat()

    schema = pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("source", pa.string()),
            pa.field("title", pa.string()),
            pa.field("tags", pa.list_(pa.string())),
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
                "metadata_text": item["metadata_text"],
                "vector": embedding.tolist(),
                "updated_at": now,
            }
        )

    arrow_table = pa.Table.from_pylist(records, schema=schema)

    # Write Lance dataset
    db = lancedb.connect(str(output_path))

    if args.force or not output_path.exists():
        db.create_table(TABLE_NAME, data=arrow_table, mode="overwrite")
    else:
        table = db.open_table(TABLE_NAME)
        (
            table.merge_insert("id")
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(arrow_table)
        )

    # Write model metadata as JSON sidecar
    meta_path = output_path / "_meta.json"
    metadata = {
        "model": MODEL_NAME,
        "dimensions": DIMENSIONS,
        "generated_at": now,
        "entry_count": len(records),
        "mode": args.mode,
    }
    meta_path.write_text(json.dumps(metadata, indent=2))

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
