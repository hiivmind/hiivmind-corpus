#!/usr/bin/env python3
"""Query embeddings.db by cosine similarity.

Usage:
  python3 search.py <embeddings.db> <query> [--top-k 10] [--json]

Exit codes:
  0 - success (even if no results)
  1 - fastembed not installed
  2 - embeddings.db not found
  3 - other error
  4 - model mismatch (db built with different model)
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384


def parse_args():
    parser = argparse.ArgumentParser(description="Search embeddings")
    parser.add_argument("db", help="Path to embeddings.db")
    parser.add_argument("query", help="Query string to search for")
    parser.add_argument(
        "--top-k", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    return parser.parse_args()


def check_model_match(conn):
    """Check if db was built with the current model."""
    cursor = conn.execute("SELECT value FROM meta WHERE key = 'model'")
    row = cursor.fetchone()
    if row is None:
        return True
    return row[0] == MODEL_NAME


def main():
    args = parse_args()

    # Check db exists
    if not Path(args.db).exists():
        print(f"Error: embeddings.db not found: {args.db}", file=sys.stderr)
        sys.exit(2)

    # Import fastembed and numpy (numpy is a transitive dependency of fastembed)
    try:
        from fastembed import TextEmbedding
    except ImportError:
        print(
            "Error: fastembed not installed. Run: pip install fastembed pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    import numpy as np

    # Open db and check model
    conn = sqlite3.connect(args.db)
    if not check_model_match(conn):
        existing = conn.execute(
            "SELECT value FROM meta WHERE key = 'model'"
        ).fetchone()[0]
        print(
            f"Error: embeddings.db was built with {existing}, "
            f"current model is {MODEL_NAME}.",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(4)

    # Load vectors
    cursor = conn.execute("SELECT id, vector FROM embeddings")
    ids = []
    vectors = []
    for row_id, vector_blob in cursor:
        ids.append(row_id)
        vec = np.frombuffer(vector_blob, dtype=np.float32)
        vectors.append(vec)
    conn.close()

    if not ids:
        if args.json_output:
            print("[]")
        sys.exit(0)

    db_vectors = np.stack(vectors)

    # Embed query
    model = TextEmbedding(model_name=MODEL_NAME)
    query_embedding = list(model.embed([args.query]))[0].astype("float32")

    # Compute cosine similarity
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
    db_norms = db_vectors / (
        np.linalg.norm(db_vectors, axis=1, keepdims=True) + 1e-10
    )
    scores = db_norms @ query_norm

    # Rank and return top-k
    top_indices = np.argsort(scores)[::-1][: args.top_k]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score > 0:
            results.append({"id": ids[idx], "score": round(score, 4)})

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
