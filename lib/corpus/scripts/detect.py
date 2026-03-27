#!/usr/bin/env python3
"""Check fastembed availability and model status.

Usage: python3 detect.py

Output (stdout, one line):
  "ready"         - fastembed installed, model downloaded
  "no-model"      - fastembed installed, model not yet downloaded
  "not-installed" - fastembed not importable

Exit codes:
  0 - fastembed importable (ready or no-model)
  1 - fastembed not installed
  2 - python error
"""
import sys

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    try:
        import fastembed  # noqa: F401
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
        model_dirs = list(cache_path.glob("*MiniLM*")) if cache_path.exists() else []
        if model_dirs:
            print("ready")
        else:
            print("no-model")
    except Exception:
        # fastembed is importable but we can't determine model status
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
