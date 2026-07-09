#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Extract content previews for index entries (data prep for LLM verification).

Usage:
  python3 verify_entries.py --index <path> --source-root <path> [--config config.yaml] [--token-limit 500] [--sample N] [--entries ID,ID,...]

Entry files resolve via the v2 schema: entry.source is a source ID and
entry.path is relative to that source's docs_root (from --config).

Output: JSON array to stdout. Each entry: {entry_id, title, summary, source_path, content_preview, token_count}.

Exit codes:
  0 - success
  1 - invalid arguments or missing index
  2 - python error
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from token_utils import estimate_tokens


def _load_index(index_path: str) -> list[dict]:
    try:
        import yaml
    except ImportError:
        return _load_index_regex(index_path)
    with open(index_path) as f:
        data = yaml.safe_load(f)
    return data.get("entries", []) if isinstance(data, dict) else []


def _load_index_regex(index_path: str) -> list[dict]:
    text = Path(index_path).read_text()
    entries = []
    current = None
    for line in text.splitlines():
        if line.strip().startswith("- id:"):
            if current:
                entries.append(current)
            current = {"id": line.split(":", 1)[1].strip().strip("'\"")}
        elif current and ":" in line and line.startswith("    "):
            key, _, val = line.strip().partition(":")
            current[key.strip()] = val.strip().strip("'\"")
    if current:
        entries.append(current)
    return entries


def _load_docs_roots(config_path: str | None) -> dict[str, str]:
    """Map source id -> normalized docs_root ('' when '.', missing, or root)."""
    if not config_path or not Path(config_path).exists():
        return {}
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return {}
    roots = {}
    for source in config.get("sources", []) or []:
        sid = source.get("id")
        if not sid:
            continue
        docs_root = (source.get("docs_root") or "").strip()
        roots[sid] = "" if docs_root in (".", "") else docs_root
    return roots


def _resolve_entry_file(source_root: Path, entry: dict, docs_roots: dict[str, str]) -> Path | None:
    """Resolve the on-disk file for an index entry.

    v2 schema: entry has source (id) + path (relative). Candidates in order:
      source_root/<id>/<docs_root>/<path>   (when docs_root known)
      source_root/<id>/<path>
    Legacy shape (no 'path' key): source_root/<source> as a file.
    """
    source_id = entry.get("source", "")
    rel_path = entry.get("path")
    if rel_path:
        candidates = []
        docs_root = docs_roots.get(source_id)
        if docs_root:
            candidates.append(source_root / source_id / docs_root / rel_path)
        candidates.append(source_root / source_id / rel_path)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None
    legacy = source_root / source_id
    return legacy if legacy.is_file() else None


def _truncate_to_tokens(text: str, token_limit: int) -> str:
    words = text.split()
    word_limit = int(token_limit / 1.3) + 1
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit])


def extract_previews(
    index_path: str,
    source_root: str,
    token_limit: int = 500,
    sample: int | None = None,
    entry_ids: list[str] | None = None,
    config_path: str | None = None,
) -> list[dict]:
    entries = _load_index(index_path)
    source = Path(source_root)
    docs_roots = _load_docs_roots(config_path)

    # Section entries share their parent file; verify file entries only.
    entries = [e for e in entries if e.get("tier") != "section"]

    if entry_ids:
        id_set = set(entry_ids)
        entries = [e for e in entries if e.get("id") in id_set]

    if sample is not None and sample < len(entries):
        entries = random.sample(entries, sample)

    result = []
    for entry in entries:
        entry_id = entry.get("id", "")
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        source_path = entry.get("path") or entry.get("source", "")
        file_path = _resolve_entry_file(source, entry, docs_roots)

        if file_path is not None:
            content = file_path.read_text(errors="replace")
            preview = _truncate_to_tokens(content, token_limit)
            token_count = estimate_tokens(preview)
        else:
            preview = None
            token_count = 0

        result.append({
            "entry_id": entry_id, "title": title, "summary": summary,
            "source_path": source_path, "content_preview": preview, "token_count": token_count,
        })
    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Extract content previews for entry verification")
    parser.add_argument("--index", required=True, help="Path to index.yaml")
    parser.add_argument("--source-root", required=True, help="Path to source root directory")
    parser.add_argument("--config", default=None, help="Path to config.yaml (for per-source docs_root)")
    parser.add_argument("--token-limit", type=int, default=500, help="Max tokens per preview (default: 500)")
    parser.add_argument("--sample", type=int, default=None, help="Random sample N entries (default: all)")
    parser.add_argument("--entries", default=None, help="Comma-separated entry IDs to verify")
    return parser.parse_args()


def main():
    args = parse_args()
    entry_ids = args.entries.split(",") if args.entries else None
    result = extract_previews(args.index, args.source_root, token_limit=args.token_limit, sample=args.sample, entry_ids=entry_ids, config_path=args.config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
