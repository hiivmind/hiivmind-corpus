#!/usr/bin/env python3
"""Split a markdown file into sections by heading structure.

Usage:
  python3 split_by_headings.py --file <path> [--min-level 2] [--max-level 4] [--min-tokens 200] [--json]

Output: JSON array of sections with title, level, line_start, line_end, token_count, anchor, text_preview.

Exit codes:
  0 - success
  1 - invalid arguments
  2 - file not found
  3 - python error
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from token_utils import estimate_tokens

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
CODE_FENCE_RE = re.compile(r"^```")
ANCHOR_STRIP_RE = re.compile(r"[^\w\s-]")


def _make_anchor(title: str) -> str:
    anchor = title.lower().strip()
    anchor = ANCHOR_STRIP_RE.sub("", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = anchor.strip("-")
    return anchor


def split_by_headings(
    text: str,
    min_level: int = 2,
    max_level: int = 4,
    min_tokens: int = 200,
) -> list[dict]:
    lines = text.split("\n")
    in_code_block = False
    raw_sections = []

    for i, line in enumerate(lines):
        if CODE_FENCE_RE.match(line.strip()):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            if min_level <= level <= max_level:
                raw_sections.append({"title": match.group(2).strip(), "level": level, "line_start": i + 1})

    if not raw_sections:
        return []

    # Find the last non-empty line
    last_content_line = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_content_line = i + 1
            break

    for idx, section in enumerate(raw_sections):
        if idx + 1 < len(raw_sections):
            section["line_end"] = raw_sections[idx + 1]["line_start"] - 1
        else:
            section["line_end"] = last_content_line

        section_text = "\n".join(lines[section["line_start"] - 1 : section["line_end"]])
        section["token_count"] = estimate_tokens(section_text)
        section["anchor"] = _make_anchor(section["title"])
        section["text_preview"] = section_text[:200]

    if min_tokens > 0:
        merged = []
        for section in raw_sections:
            if section["token_count"] < min_tokens and merged:
                prev = merged[-1]
                prev["line_end"] = section["line_end"]
                prev_text = "\n".join(lines[prev["line_start"] - 1 : prev["line_end"]])
                prev["token_count"] = estimate_tokens(prev_text)
                prev["text_preview"] = prev_text[:200]
            else:
                merged.append(section)
        raw_sections = merged

    return raw_sections


def parse_args():
    parser = argparse.ArgumentParser(description="Split markdown file by headings")
    parser.add_argument("--file", required=True, help="Path to markdown file")
    parser.add_argument("--min-level", type=int, default=2, help="Min heading level (default: 2)")
    parser.add_argument("--max-level", type=int, default=4, help="Max heading level (default: 4)")
    parser.add_argument("--min-tokens", type=int, default=200, help="Min tokens per section (default: 200)")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)
    text = file_path.read_text(errors="replace")
    sections = split_by_headings(text, args.min_level, args.max_level, args.min_tokens)
    if args.json_output:
        print(json.dumps(sections, indent=2))
    else:
        for s in sections:
            print(f"{s['anchor']}\tL{s['line_start']}-{s['line_end']}\t{s['token_count']} tokens\t{s['title']}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(3)
