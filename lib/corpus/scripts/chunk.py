#!/usr/bin/env python3
"""Deterministic document chunking with strategy-based boundary detection.

Usage:
  python3 chunk.py <file> --strategy <markdown|transcript|code|paragraph> [--target-tokens 900] [--overlap-tokens 100] [--json]

Splits a document into chunks using boundary scoring. Each strategy assigns
scores to potential break points (headings, blank lines, speaker turns, etc.)
and picks the highest-scoring boundary within a window of the target size.

Output: JSON array of chunks with text, line_range, chunk_index, overlap_prev.

Exit codes:
  0 - success
  1 - invalid strategy
  2 - file not found
  3 - other error
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

TOKENS_PER_WORD = 1.3

BOUNDARY_SCORES = {
    "markdown": {
        "heading": 100,
        "blank_line": 20,
        "list_item": 10,
    },
    "transcript": {
        "speaker_turn": 80,
        "timestamp": 50,
        "blank_line": 20,
    },
    "code": {
        "function_boundary": 100,
        "blank_line": 20,
    },
    "paragraph": {
        "double_newline": 50,
        "single_newline": 10,
    },
}

STRATEGY_DEFAULTS = {
    "markdown": {"target_tokens": 900, "overlap_tokens": 100},
    "transcript": {"target_tokens": 900, "overlap_tokens": 100},
    "code": {"target_tokens": 600, "overlap_tokens": 50},
    "paragraph": {"target_tokens": 900, "overlap_tokens": 100},
}

HEADING_RE = re.compile(r"^#{1,6}\s+")
SPEAKER_RE = re.compile(r"^[A-Z][a-zA-Z\s]*:\s")
TIMESTAMP_RE = re.compile(r"^\[?\d{1,2}:\d{2}(:\d{2})?\]?\s")
LIST_ITEM_RE = re.compile(r"^[\s]*[-*+]\s|^[\s]*\d+\.\s")
CODE_BOUNDARY_RE = re.compile(
    r"^(def |class |function |fn |func |pub fn |async fn |export |const \w+ = |let \w+ = )"
)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    return max(1, math.ceil(len(text.split()) * TOKENS_PER_WORD))


def score_line(line: str, strategy: str) -> int:
    """Score a line as a potential chunk boundary."""
    scores = BOUNDARY_SCORES[strategy]

    if strategy == "markdown":
        if HEADING_RE.match(line):
            return scores["heading"]
        if line.strip() == "":
            return scores["blank_line"]
        if LIST_ITEM_RE.match(line):
            return scores["list_item"]

    elif strategy == "transcript":
        if SPEAKER_RE.match(line):
            return scores["speaker_turn"]
        if TIMESTAMP_RE.match(line):
            return scores["timestamp"]
        if line.strip() == "":
            return scores["blank_line"]

    elif strategy == "code":
        if CODE_BOUNDARY_RE.match(line):
            return scores["function_boundary"]
        if line.strip() == "":
            return scores["blank_line"]

    elif strategy == "paragraph":
        if line.strip() == "":
            return scores["double_newline"]
        return scores["single_newline"]

    return 0


def chunk_text(
    text: str,
    strategy: str = "markdown",
    target_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> list[dict]:
    """Split text into chunks using boundary scoring.

    Returns list of dicts with: text, line_range, chunk_index, overlap_prev.
    Line ranges are 1-indexed.
    """
    if not text or not text.strip():
        return []

    if strategy not in BOUNDARY_SCORES:
        raise ValueError(f"Unknown strategy: {strategy}")

    defaults = STRATEGY_DEFAULTS[strategy]
    if target_tokens is None:
        target_tokens = defaults["target_tokens"]
    if overlap_tokens is None:
        overlap_tokens = defaults["overlap_tokens"]

    lines = text.split("\n")
    total_lines = len(lines)

    total_tokens = estimate_tokens(text)
    if total_tokens <= target_tokens * 1.5:
        return [
            {
                "text": text,
                "line_range": [1, total_lines],
                "chunk_index": 0,
                "overlap_prev": False,
            }
        ]

    line_scores = [score_line(line, strategy) for line in lines]

    chunks = []
    chunk_start = 0

    while chunk_start < total_lines:
        token_count = 0
        target_end = chunk_start
        for i in range(chunk_start, total_lines):
            line_tokens = estimate_tokens(lines[i]) if lines[i].strip() else 1
            token_count += line_tokens
            target_end = i
            if token_count >= target_tokens:
                break

        if target_end >= total_lines - 1:
            chunk_text_str = "\n".join(lines[chunk_start:])
            chunks.append(
                {
                    "text": chunk_text_str,
                    "line_range": [chunk_start + 1, total_lines],
                    "chunk_index": len(chunks),
                    "overlap_prev": chunk_start > 0 and overlap_tokens > 0 and len(chunks) > 0,
                }
            )
            break

        window_size = max(5, (target_end - chunk_start) // 5)
        window_start = max(chunk_start + 1, target_end - window_size)
        window_end = min(total_lines - 1, target_end + window_size)

        best_boundary = target_end
        best_score = -1
        for i in range(window_start, window_end + 1):
            if line_scores[i] > best_score:
                best_score = line_scores[i]
                best_boundary = i

        if best_score <= 0:
            best_boundary = target_end

        if best_score >= 50 and HEADING_RE.match(lines[best_boundary]):
            split_at = best_boundary
        elif best_score >= 50 and (
            SPEAKER_RE.match(lines[best_boundary])
            or TIMESTAMP_RE.match(lines[best_boundary])
            or CODE_BOUNDARY_RE.match(lines[best_boundary])
        ):
            split_at = best_boundary
        else:
            split_at = best_boundary + 1

        chunk_text_str = "\n".join(lines[chunk_start:split_at])
        if chunk_text_str.strip():
            chunks.append(
                {
                    "text": chunk_text_str,
                    "line_range": [chunk_start + 1, split_at],
                    "chunk_index": len(chunks),
                    "overlap_prev": chunk_start > 0 and overlap_tokens > 0 and len(chunks) > 0,
                }
            )

        if overlap_tokens > 0 and split_at < total_lines:
            overlap_lines = 0
            overlap_token_count = 0
            for i in range(split_at - 1, chunk_start, -1):
                overlap_token_count += estimate_tokens(lines[i]) if lines[i].strip() else 1
                overlap_lines += 1
                if overlap_token_count >= overlap_tokens:
                    break
            chunk_start = max(chunk_start + 1, split_at - overlap_lines)
        else:
            chunk_start = split_at

    return chunks


def parse_args():
    parser = argparse.ArgumentParser(description="Chunk a document by strategy")
    parser.add_argument("file", help="Path to document file")
    parser.add_argument(
        "--strategy",
        choices=["markdown", "transcript", "code", "paragraph"],
        default="markdown",
        help="Chunking strategy (default: markdown)",
    )
    parser.add_argument(
        "--target-tokens",
        type=int,
        default=None,
        help="Target chunk size in tokens",
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=None,
        help="Overlap between chunks in tokens",
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

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    text = file_path.read_text()
    chunks = chunk_text(
        text,
        strategy=args.strategy,
        target_tokens=args.target_tokens,
        overlap_tokens=args.overlap_tokens,
    )

    if args.json_output:
        print(json.dumps(chunks))
    else:
        for c in chunks:
            lr = c["line_range"]
            print(f"chunk-{c['chunk_index']}\tL{lr[0]}-{lr[1]}\t{len(c['text'])} chars")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
