#!/usr/bin/env python3
"""Detect markdown files exceeding a token threshold.

Usage:
  python3 detect_large_files.py --source-root <path> [--max-tokens 15000] [--paths <file>]

Output: JSON array of {path, token_count, line_count, has_headings, heading_count, deepest_heading_level}.

Exit codes:
  0 - success
  1 - invalid arguments
  2 - python error
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from token_utils import estimate_tokens

HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)


def detect_large_files(
    source_root: str,
    max_tokens: int = 15000,
    paths: list[str] | None = None,
) -> list[dict]:
    root = Path(source_root)
    result = []

    if paths:
        files = [root / p for p in paths]
    else:
        files = sorted(root.rglob("*.md")) + sorted(root.rglob("*.mdx"))

    for file_path in files:
        if not file_path.exists():
            continue
        text = file_path.read_text(errors="replace")
        token_count = estimate_tokens(text)
        if token_count <= max_tokens:
            continue

        headings = HEADING_RE.findall(text)
        heading_count = len(headings)
        deepest = max((len(h) for h in headings), default=0) if headings else 0

        rel_path = str(file_path.relative_to(root))
        result.append({
            "path": rel_path, "token_count": token_count,
            "line_count": text.count("\n") + 1,
            "has_headings": heading_count > 0,
            "heading_count": heading_count,
            "deepest_heading_level": deepest,
        })
    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Detect large markdown files")
    parser.add_argument("--source-root", required=True, help="Path to source root")
    parser.add_argument("--max-tokens", type=int, default=15000, help="Token threshold (default: 15000)")
    parser.add_argument("--paths", default=None, help="File with paths to check (one per line)")
    return parser.parse_args()


def main():
    args = parse_args()
    paths = None
    if args.paths:
        paths = Path(args.paths).read_text().strip().splitlines()
    result = detect_large_files(args.source_root, args.max_tokens, paths)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
