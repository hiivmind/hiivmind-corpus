#!/usr/bin/env python3
"""Query a Lance embedding dataset by cosine similarity with optional filtering and reranking.

Usage:
  python3 search.py <dataset.lance> <query> [--top-k 10] [--where "SQL"] [--rerank] [--select "cols"] [--json]

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
META_TABLE = "_meta"
QUERY_PREFIX = "query: "


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
        "--rerank",
        action="store_true",
        help="Rerank results with CrossEncoder for better precision",
    )
    parser.add_argument(
        "--select",
        default=None,
        help="Comma-separated extra columns to include in JSON output "
        "(e.g., 'concepts,title')",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--table",
        default=TABLE_NAME,
        help="Table name to search within the Lance database (default: embeddings)",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Use hybrid search (FTS + vector + RRF) instead of vector-only",
    )
    parser.add_argument(
        "--text-column",
        default="metadata_text",
        help="Text column for hybrid FTS search (default: metadata_text)",
    )
    return parser.parse_args()


def read_model_from_meta(db, dataset_path):
    """Read model name from _meta table or _meta.json fallback."""
    # Try _meta table first
    try:
        if META_TABLE in db.table_names():
            meta_table = db.open_table(META_TABLE)
            meta_arrow = meta_table.to_arrow()
            keys = meta_arrow.column("key").to_pylist()
            values = meta_arrow.column("value").to_pylist()
            meta = dict(zip(keys, values))
            return meta.get("model", "")
    except Exception:
        pass

    # Fallback to _meta.json for backward compat
    meta_path = dataset_path / "_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            return meta.get("model", "")
        except Exception:
            pass

    return ""


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
        table = db.open_table(args.table)
    except Exception as e:
        print(f"Error: could not open table '{args.table}': {e}", file=sys.stderr)
        sys.exit(2)

    # Check model match
    existing_model = read_model_from_meta(db, dataset_path)
    if existing_model and existing_model != MODEL_NAME:
        print(
            f"Error: dataset was built with {existing_model}, "
            f"current model is {MODEL_NAME}.",
            file=sys.stderr,
        )
        sys.exit(4)

    # Embed query
    model = TextEmbedding(model_name=MODEL_NAME)
    query_embedding = list(model.embed([f"{QUERY_PREFIX}{args.query}"]))[0]

    if args.hybrid:
        try:
            from lancedb.rerank import RRFReranker
            search = (
                table.search(args.query, query_type="hybrid")
                .rerank(reranker=RRFReranker())
                .limit(args.top_k)
            )
        except ImportError:
            print("Warning: RRFReranker not available, falling back to vector search", file=sys.stderr)
            search = (
                table.search(query_embedding.tolist(), vector_column_name="vector")
                .metric("cosine")
                .limit(args.top_k)
            )
    else:
        search = (
            table.search(query_embedding.tolist(), vector_column_name="vector")
            .metric("cosine")
            .limit(args.top_k)
        )

    if args.where:
        search = search.where(args.where)

    if args.rerank:
        try:
            from lancedb.rerank import CrossEncoderReranker
            search = search.rerank(reranker=CrossEncoderReranker())
        except ImportError:
            print("Warning: reranking not available", file=sys.stderr)
        except Exception as e:
            print(f"Warning: reranking failed: {e}", file=sys.stderr)

    # Execute
    arrow_result = search.to_arrow()

    if arrow_result.num_rows == 0:
        if args.json_output:
            print("[]")
        sys.exit(0)

    # Format results
    ids = arrow_result.column("id").to_pylist()

    # Hybrid search returns _relevance_score, vector search returns _distance
    if "_relevance_score" in arrow_result.schema.names:
        raw_scores = arrow_result.column("_relevance_score").to_pylist()
        scores = [max(0.0, float(s)) for s in raw_scores]
    else:
        distances = arrow_result.column("_distance").to_pylist()
        scores = [max(0.0, 1.0 - float(d)) for d in distances]

    # Determine extra columns to include (--select requires --json)
    select_cols = []
    if args.select and args.json_output:
        select_cols = [c.strip() for c in args.select.split(",")]

    results = []
    for i, (entry_id, score) in enumerate(zip(ids, scores)):
        result = {"id": entry_id, "score": round(score, 4)}

        # Add selected columns
        for col in select_cols:
            if col in arrow_result.schema.names:
                result[col] = arrow_result.column(col)[i].as_py()

        results.append(result)

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
