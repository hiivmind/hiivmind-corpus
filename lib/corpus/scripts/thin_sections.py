#!/usr/bin/env python3
"""Bottom-up merge of small section entries in index.yaml.

Usage:
  python3 thin_sections.py --index <path> [--min-tokens 300] [--dry-run]

Merges section entries below min-tokens into nearest sibling or parent.
Modifies index.yaml in-place unless --dry-run.

Output: JSON summary to stdout with sections_before, sections_after, merged[].

Exit codes:
  0 - success
  1 - invalid arguments or missing index
  2 - python error
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from token_utils import estimate_tokens


def _has_children(entry_id: str, entries: list[dict]) -> bool:
    return any(e.get("parent") == entry_id for e in entries)


def _source_prefix(entry_id: str) -> str:
    if ":" in entry_id:
        return entry_id.split(":")[0]
    return ""


def thin_sections(
    index: dict,
    min_tokens: int = 300,
    dry_run: bool = False,
) -> dict:
    if dry_run:
        work = copy.deepcopy(index)
    else:
        work = index

    entries = work.get("entries", [])
    sections = [e for e in entries if e.get("tier") == "section"]
    sections_before = len(sections)
    merged_log = []

    sections_by_depth = sorted(sections, key=lambda e: e.get("heading_level", 0), reverse=True)
    ids_to_remove = set()

    for section in sections_by_depth:
        sid = section["id"]
        if sid in ids_to_remove:
            continue
        if _has_children(sid, entries):
            continue

        text = (section.get("summary", "") + " " + " ".join(section.get("keywords", []))).strip()
        tokens = estimate_tokens(text)
        if tokens >= min_tokens:
            continue

        parent_id = section.get("parent")
        source_pfx = _source_prefix(sid)

        siblings = [
            e for e in entries
            if e.get("parent") == parent_id
            and e.get("tier") == "section"
            and _source_prefix(e["id"]) == source_pfx
            and e["id"] != sid
            and e["id"] not in ids_to_remove
        ]

        prev_sibling = None
        section_start = (section.get("line_range") or [0])[0]
        for sib in siblings:
            sib_start = (sib.get("line_range") or [0])[0]
            if sib_start < section_start:
                if prev_sibling is None or sib_start > (prev_sibling.get("line_range") or [0])[0]:
                    prev_sibling = sib

        if prev_sibling:
            target = prev_sibling
            target_id = target["id"]
        elif parent_id:
            target = next((e for e in entries if e["id"] == parent_id), None)
            if target is None:
                continue
            target_id = target["id"]
        else:
            continue

        if _source_prefix(target_id) != source_pfx:
            continue

        target_kw = target.get("keywords", [])
        section_kw = section.get("keywords", [])
        target["keywords"] = list(dict.fromkeys(target_kw + section_kw))

        if target.get("line_range") and section.get("line_range"):
            target["line_range"][1] = max(target["line_range"][1], section["line_range"][1])

        if section.get("summary"):
            target["summary"] = (target.get("summary", "") + " " + section["summary"]).strip()

        ids_to_remove.add(sid)
        merged_log.append({
            "removed_id": sid,
            "merged_into": target_id,
            "reason": f"{tokens} tokens (below {min_tokens} threshold)",
        })

    work["entries"] = [e for e in entries if e["id"] not in ids_to_remove]
    work["meta"]["entry_count"] = len(work["entries"])

    sections_after = len([e for e in work["entries"] if e.get("tier") == "section"])

    if dry_run:
        return {
            "sections_before": sections_before,
            "sections_after": sections_after,
            "merged": merged_log,
        }
    return work


def parse_args():
    parser = argparse.ArgumentParser(description="Thin section entries in index.yaml")
    parser.add_argument("--index", required=True, help="Path to index.yaml")
    parser.add_argument("--min-tokens", type=int, default=300, help="Min tokens per section (default: 300)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without modifying")
    return parser.parse_args()


def main():
    args = parse_args()
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"error: index not found: {args.index}", file=sys.stderr)
        sys.exit(1)
    try:
        import yaml
    except ImportError:
        print("error: PyYAML required for thin_sections.py", file=sys.stderr)
        sys.exit(1)

    with open(index_path) as f:
        index = yaml.safe_load(f)

    if args.dry_run:
        result = thin_sections(index, args.min_tokens, dry_run=True)
        print(json.dumps(result, indent=2))
    else:
        result = thin_sections(index, args.min_tokens, dry_run=False)
        with open(index_path, "w") as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        summary = {
            "sections_before": len([e for e in index.get("entries", []) if e.get("tier") == "section"]),
            "sections_after": len([e for e in result["entries"] if e.get("tier") == "section"]),
            "merged": [],
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
