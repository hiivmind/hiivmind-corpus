#!/usr/bin/env python3
"""Check fastembed and lancedb availability and model status.

Usage: python3 detect.py

Output (stdout, one line):
  "ready"         - fastembed + lancedb installed, model downloaded
  "no-model"      - fastembed + lancedb installed, model not yet downloaded
  "not-installed" - fastembed or lancedb not importable

Exit codes:
  0 - dependencies importable (ready or no-model)
  1 - dependencies not installed
  2 - python error
"""
import sys

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def main():
    try:
        import fastembed  # noqa: F401
    except ImportError:
        print("not-installed")
        sys.exit(1)

    try:
        import lancedb  # noqa: F401
    except ImportError:
        print("not-installed")
        sys.exit(1)

    # Check if model is already downloaded.
    # Best-effort heuristic: check default fastembed cache directory.
    # If cache location changes across versions, "no-model" is the safe
    # fallback - worst case is an unnecessary "downloading model" message.
    try:
        from pathlib import Path

        cache_path = Path.home() / ".cache" / "fastembed"
        model_dirs = (
            list(cache_path.glob("*bge-small*")) if cache_path.exists() else []
        )
        if model_dirs:
            print("ready")
        else:
            print("no-model")
    except Exception:
        print("no-model")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
