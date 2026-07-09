#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check fastembed and lancedb availability and model status.

Usage: python3 detect.py

Output (stdout, one line):
  "ready"         - embedding deps available, model downloaded
  "no-model"      - embedding deps available, model not yet downloaded
  "not-installed" - no uv on PATH and fastembed/lancedb not importable

Exit codes:
  0 - dependencies available (ready or no-model)
  1 - dependencies not installed
  2 - python error

When uv is on PATH, dependency availability is guaranteed at run time
(embed.py/search.py carry PEP 723 metadata and run via `uv run`), so the
import probe is skipped and only the model-cache state is reported.
"""

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import MODEL_NAME  # noqa: E402, F401


def _install_hint() -> str:
    """Return the install command, preferring uv if available."""
    pkg = "fastembed lancedb pyyaml"
    if shutil.which("uv"):
        return f"uv pip install {pkg}"
    return f"pip install {pkg}"


def _model_cache_status() -> str:
    """Return 'ready' if the bge-small model is in the fastembed cache, else 'no-model'.

    Honors FASTEMBED_CACHE_PATH (used by scheduler runtimes) before the
    default ~/.cache/fastembed location. If cache layout changes across
    versions, "no-model" is the safe fallback — worst case is an
    unnecessary "downloading model" message.
    """
    try:
        env_path = os.environ.get("FASTEMBED_CACHE_PATH")
        cache_path = Path(env_path) if env_path else Path.home() / ".cache" / "fastembed"
        model_dirs = list(cache_path.glob("*bge-small*")) if cache_path.exists() else []
        return "ready" if model_dirs else "no-model"
    except Exception:
        return "no-model"


def main():
    # With uv available, dependency availability is guaranteed at run time:
    # embed.py/search.py carry PEP 723 metadata and run via `uv run`.
    # Only the model-cache state matters.
    if shutil.which("uv"):
        print(_model_cache_status())
        sys.exit(0)

    # Legacy path (no uv): probe the ambient interpreter.
    try:
        import fastembed  # noqa: F401
    except ImportError:
        print("not-installed")
        print(f"Install with: {_install_hint()}", file=sys.stderr)
        sys.exit(1)

    try:
        import lancedb  # noqa: F401
    except ImportError:
        print("not-installed")
        print(f"Install with: {_install_hint()}", file=sys.stderr)
        sys.exit(1)

    print(_model_cache_status())
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
