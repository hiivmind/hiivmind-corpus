#!/usr/bin/env python3
"""Detect and parse documentation navigation structure.

Usage:
  python3 detect_nav.py --source-root <path>

Scans for mkdocs.yml, _sidebar.md, SUMMARY.md, _toc.yml in priority order.
Parses the first found into a hierarchy with coverage stats.

Output: JSON to stdout with {found, nav_file, framework, hierarchy, coverage}.

Exit codes:
  0 - success (found or not found)
  1 - invalid arguments
  2 - python error
"""
import argparse
import json
import re
import sys
from pathlib import Path

NAV_CANDIDATES = [
    ("mkdocs.yml", "mkdocs", "yaml_nav"),
    ("mkdocs.yaml", "mkdocs", "yaml_nav"),
    ("_sidebar.md", "docsify", "sidebar_md"),
    ("SUMMARY.md", "mdbook", "sidebar_md"),
    ("src/SUMMARY.md", "mdbook", "sidebar_md"),
    ("_toc.yml", "custom", "yaml_toc"),
]

LINK_RE = re.compile(r"^(\s*)-\s*\[([^\]]+)\]\(([^)]+)\)")


def parse_mkdocs_nav(nav_file: Path, source_root: Path) -> list[dict]:
    """Parse mkdocs.yml nav: key into hierarchy list."""
    try:
        import yaml
    except ImportError:
        return _parse_mkdocs_nav_regex(nav_file, source_root)

    with open(nav_file) as f:
        data = yaml.safe_load(f)

    nav = data.get("nav") if isinstance(data, dict) else None
    if not nav:
        return []

    return _walk_mkdocs_nav(nav, source_root, level=1)


def _walk_mkdocs_nav(nav_items: list, source_root: Path, level: int) -> list[dict]:
    result = []
    for item in nav_items:
        if isinstance(item, dict):
            for title, value in item.items():
                if isinstance(value, str):
                    result.append({"title": title, "path": value, "level": level, "children": []})
                elif isinstance(value, list):
                    children = _walk_mkdocs_nav(value, source_root, level + 1)
                    result.append({"title": title, "path": None, "level": level, "children": children})
        elif isinstance(item, str):
            result.append({"title": item, "path": item, "level": level, "children": []})
    return result


def _parse_mkdocs_nav_regex(nav_file: Path, source_root: Path) -> list[dict]:
    text = nav_file.read_text()
    in_nav = False
    flat = []
    min_indent = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("nav:"):
            in_nav = True
            continue
        if in_nav:
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                break
            # Match lines with format: "  - Title: path.md" or "  - Title:"
            match = re.match(r"^(\s*)-\s+(.+?):\s*(.*?)$", line)
            if match:
                indent = len(match.group(1))
                if min_indent is None:
                    min_indent = indent
                level = ((indent - min_indent) // 2) + 1
                title = match.group(2).strip()
                path = match.group(3).strip() if match.group(3).strip() else None
                flat.append({"title": title, "path": path, "level": level, "children": []})
    return _nest_by_level(flat)


def parse_sidebar_md(sidebar_file: Path, source_root: Path) -> list[dict]:
    text = sidebar_file.read_text()
    flat = []
    for line in text.splitlines():
        match = LINK_RE.match(line)
        if match:
            indent = len(match.group(1))
            level = (indent // 2) + 1
            flat.append({"title": match.group(2).strip(), "path": match.group(3).strip(), "level": level, "children": []})
    return _nest_by_level(flat)


def _nest_by_level(flat: list[dict]) -> list[dict]:
    if not flat:
        return []
    root = []
    stack: list[dict] = []
    for item in flat:
        while stack and stack[-1]["level"] >= item["level"]:
            stack.pop()
        if stack:
            stack[-1]["children"].append(item)
        else:
            root.append(item)
        stack.append(item)
    return root


def _collect_paths(hierarchy: list[dict]) -> list[str]:
    paths = []
    for item in hierarchy:
        if item.get("path"):
            paths.append(item["path"])
        paths.extend(_collect_paths(item.get("children", [])))
    return paths


def _count_md_files(source_root: Path) -> int:
    count = 0
    for ext in ("*.md", "*.mdx"):
        count += len(list(source_root.rglob(ext)))
    return count


def detect_nav(source_root_str: str) -> dict:
    source_root = Path(source_root_str)
    empty_result = {
        "found": False, "nav_file": None, "framework": None, "hierarchy": [],
        "coverage": {"nav_entries": 0, "files_resolved": 0, "files_missing": 0, "total_md_files": _count_md_files(source_root) if source_root.is_dir() else 0, "coverage_pct": 0.0},
    }
    if not source_root.is_dir():
        return empty_result

    for filename, framework, parser_type in NAV_CANDIDATES:
        nav_path = source_root / filename
        if not nav_path.exists():
            continue
        if parser_type == "yaml_nav":
            hierarchy = parse_mkdocs_nav(nav_path, source_root)
        elif parser_type == "sidebar_md":
            hierarchy = parse_sidebar_md(nav_path, source_root)
        elif parser_type == "yaml_toc":
            hierarchy = parse_mkdocs_nav(nav_path, source_root)
        else:
            continue
        if not hierarchy:
            continue

        all_paths = _collect_paths(hierarchy)
        resolved = sum(1 for p in all_paths if (source_root / p).exists())
        missing = len(all_paths) - resolved
        total_md = _count_md_files(source_root)
        coverage_pct = round((resolved / total_md * 100) if total_md > 0 else 0.0, 1)

        return {
            "found": True, "nav_file": filename, "framework": framework, "hierarchy": hierarchy,
            "coverage": {"nav_entries": len(all_paths), "files_resolved": resolved, "files_missing": missing, "total_md_files": total_md, "coverage_pct": coverage_pct},
        }
    return empty_result


def parse_args():
    parser = argparse.ArgumentParser(description="Detect documentation nav structure")
    parser.add_argument("--source-root", required=True, help="Path to source root directory")
    return parser.parse_args()


def main():
    args = parse_args()
    result = detect_nav(args.source_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
