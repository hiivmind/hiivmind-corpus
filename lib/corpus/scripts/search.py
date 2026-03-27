#!/usr/bin/env python3
"""Query a Lance embedding dataset by cosine similarity with optional SQL filtering.

Usage:
  python3 search.py <dataset.lance> <query> [--top-k 10] [--where "SQL"] [--json]

The dataset path (e.g., index-embeddings.lance/) is the LanceDB database directory.
A fixed table name "embeddings" is expected inside it. Model metadata is read from
a _meta.json sidecar file.

Exit codes:
  0 - success (even if no results)
  1 - fastembed/lancedb not installed
  2 - dataset not found
  3 - other error
  4 - model mismatch
"""
import argparse
import json
import sys
from pathlib import Path

MODEL_NAME = "BAAI/bge-small-en-v1.5"
TABLE_NAME = "embeddings"


def parse_args():
    parser = argparse.ArgumentParser(description="Search embeddings")
    parser.add_argument("dataset", help="Path to Lance dataset directory")
    parser.add_argument("query", help="Query string to search for")
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results (default: 10)",
    )
    parser.add_argument(
        "--where",
        default=None,
        help="SQL predicate for hybrid filtering",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: dataset not found: {args.dataset}", file=sys.stderr)
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
    except ImportError:
        print(
            "Error: lancedb not installed. "
            "Run: pip install fastembed lancedb pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    # Open dataset
    db = lancedb.connect(str(dataset_path))

    try:
        table = db.open_table(TABLE_NAME)
    except Exception as e:
        print(f"Error: could not open dataset: {e}", file=sys.stderr)
        sys.exit(2)

    # Check model match via JSON sidecar
    meta_path = dataset_path / "_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        existing_model = meta.get("model", "")
        if existing_model and existing_model != MODEL_NAME:
            print(
                f"Error: dataset was built with {existing_model}, "
                f"current model is {MODEL_NAME}.",
                file=sys.stderr,
            )
            sys.exit(4)

    # Embed query with query: prefix
    model = TextEmbedding(model_name=MODEL_NAME)
    query_embedding = list(model.embed([f"query: {args.query}"]))[0]

    # Build search query with cosine metric
    search = (
        table.search(query_embedding.tolist(), vector_column_name="vector")
        .metric("cosine")
        .limit(args.top_k)
    )

    # Add SQL predicate if provided
    if args.where:
        search = search.where(args.where)

    # Execute
    results_df = search.to_pandas()

    if results_df.empty:
        if args.json_output:
            print("[]")
        sys.exit(0)

    # Format results
    # Cosine distance is in [0, 2], similarity = 1 - distance
    results = []
    for _, row in results_df.iterrows():
        score = 1.0 - float(row.get("_distance", 0))
        if score > 0:
            results.append({"id": row["id"], "score": round(score, 4)})

    if args.json_output:
        print(json.dumps(results))
    else:
        for r in results:
            print(f"{r['score']:.4f}\t{r['id']}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
