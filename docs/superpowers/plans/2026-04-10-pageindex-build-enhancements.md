# PageIndex-Inspired Build Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five deterministic Python scripts (nav detection, entry verification, tree thinning, large-file splitting, heading-aware chunking) and integrate them into the source-scanner agent and build/refresh skills with proper guard/skip/post-check blocks.

**Architecture:** Six new scripts in `lib/corpus/scripts/` following existing conventions (shebang, docstring, argparse, JSON stdout, exit codes). A shared token-counting utility extracted for DRY. Skill/agent prompt updates add GUARD blocks and post-step summaries matching the existing pseudocode patterns. No index.yaml schema changes. No new required dependencies.

**Tech Stack:** Python 3 stdlib, PyYAML (optional), fastembed (optional for token counting), pytest for tests.

**Spec:** `docs/superpowers/specs/2026-04-10-pageindex-build-enhancements-design.md`

---

## File Structure

### New files

| File | Responsibility |
|---|---|
| `lib/corpus/scripts/token_utils.py` | Shared token counting: fastembed tokenizer with word-count fallback |
| `lib/corpus/scripts/detect_nav.py` | Parse mkdocs.yml / _sidebar.md / SUMMARY.md into hierarchy JSON |
| `lib/corpus/scripts/verify_entries.py` | Extract content previews for index entries (data prep for LLM verification) |
| `lib/corpus/scripts/thin_sections.py` | Bottom-up merge of small section entries in index.yaml |
| `lib/corpus/scripts/detect_large_files.py` | Find markdown files exceeding a token threshold |
| `lib/corpus/scripts/split_by_headings.py` | Split a markdown file into sections by heading structure |
| `lib/corpus/scripts/tests/test_detect_nav.py` | Tests for detect_nav.py |
| `lib/corpus/scripts/tests/test_verify_entries.py` | Tests for verify_entries.py |
| `lib/corpus/scripts/tests/test_thin_sections.py` | Tests for thin_sections.py |
| `lib/corpus/scripts/tests/test_detect_large_files.py` | Tests for detect_large_files.py |
| `lib/corpus/scripts/tests/test_split_by_headings.py` | Tests for split_by_headings.py |
| `lib/corpus/scripts/tests/test_chunk_headings.py` | Tests for chunk.py headings strategy |
| `lib/corpus/scripts/tests/test_token_utils.py` | Tests for token_utils.py |

### Modified files

| File | Change |
|---|---|
| `lib/corpus/scripts/chunk.py` | Add `headings` strategy option |
| `agents/source-scanner.md` | Add Step 0 (nav detection), Step 1b (large file splitting), chunking strategy selection |
| `skills/hiivmind-corpus-build/SKILL.md` | Add tree thinning guard, verification guard (Phase 7c) |
| `skills/hiivmind-corpus-refresh/SKILL.md` | Add optional post-refresh verification |
| `lib/corpus/scripts/embed.py` | Prepend `heading_context` to chunk embedding text when present |
| `CLAUDE.md` | Add cross-cutting concerns rows for five new features |

---

## Task 1: Shared Token Counting Utility

**Files:**
- Create: `lib/corpus/scripts/token_utils.py`
- Create: `lib/corpus/scripts/tests/test_token_utils.py`

All five algorithms need token counting. Currently `chunk.py` uses `TOKENS_PER_WORD = 1.3` inline. Extract this into a shared module that tries fastembed's tokenizer first, falls back to word count.

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_token_utils.py
"""Tests for token_utils.py — shared token counting."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from token_utils import estimate_tokens


class TestEstimateTokens:
    """Token estimation with graceful fallback."""

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_single_word(self):
        result = estimate_tokens("hello")
        assert result >= 1

    def test_approximation_scales_with_length(self):
        short = estimate_tokens("one two three")
        long = estimate_tokens("one two three four five six seven eight nine ten")
        assert long > short

    def test_none_returns_zero(self):
        assert estimate_tokens(None) == 0

    def test_whitespace_only_returns_zero(self):
        assert estimate_tokens("   \n\t  ") == 0

    def test_returns_integer(self):
        result = estimate_tokens("some words here for testing purposes")
        assert isinstance(result, int)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_token_utils.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'token_utils'`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/token_utils.py
#!/usr/bin/env python3
"""Shared token counting with graceful fallback.

Tries fastembed's tokenizer first (accurate), falls back to
word-count approximation (len(text.split()) * 1.3).

Usage as module:
  from token_utils import estimate_tokens
  count = estimate_tokens("some text here")
"""

TOKENS_PER_WORD = 1.3

_tokenizer = None
_tokenizer_checked = False


def _get_tokenizer():
    """Try to load fastembed tokenizer once, cache result."""
    global _tokenizer, _tokenizer_checked
    if _tokenizer_checked:
        return _tokenizer
    _tokenizer_checked = True
    try:
        from fastembed import TextEmbedding

        model = TextEmbedding("BAAI/bge-small-en-v1.5")
        _tokenizer = model.model.tokenizer
    except Exception:
        _tokenizer = None
    return _tokenizer


def estimate_tokens(text: str | None) -> int:
    """Estimate token count for text.

    Returns 0 for None, empty, or whitespace-only strings.
    Uses fastembed tokenizer if available, else word-count * 1.3.
    """
    if not text or not text.strip():
        return 0

    tokenizer = _get_tokenizer()
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text).ids)
        except Exception:
            pass

    return int(len(text.split()) * TOKENS_PER_WORD)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_token_utils.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/token_utils.py lib/corpus/scripts/tests/test_token_utils.py
git commit -m "feat: add shared token counting utility (token_utils.py)"
```

---

## Task 2: detect_nav.py — Navigation Structure Detection

**Files:**
- Create: `lib/corpus/scripts/detect_nav.py`
- Create: `lib/corpus/scripts/tests/test_detect_nav.py`

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_detect_nav.py
"""Tests for detect_nav.py — navigation structure detection.

Unit tests (no external deps):
  - MkDocs YAML nav parsing
  - Docsify _sidebar.md parsing
  - mdBook SUMMARY.md parsing
  - Coverage calculation
  - Missing files handling
  - No nav file found
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from detect_nav import detect_nav, parse_mkdocs_nav, parse_sidebar_md


class TestParseMkdocsNav:
    """Parse mkdocs.yml nav: key into hierarchy."""

    def test_simple_flat_nav(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Home: index.md\n"
            "  - Getting Started: getting-started.md\n"
            "  - API Reference: api.md\n"
        )
        # Create the referenced files
        for name in ["index.md", "getting-started.md", "api.md"]:
            (tmp_path / name).write_text(f"# {name}")

        result = parse_mkdocs_nav(mkdocs, tmp_path)
        assert len(result) == 3
        assert result[0]["title"] == "Home"
        assert result[0]["path"] == "index.md"
        assert result[0]["level"] == 1

    def test_nested_nav(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Home: index.md\n"
            "  - Guide:\n"
            "    - Install: guide/install.md\n"
            "    - Usage: guide/usage.md\n"
        )
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "guide").mkdir()
        (tmp_path / "guide" / "install.md").write_text("# Install")
        (tmp_path / "guide" / "usage.md").write_text("# Usage")

        result = parse_mkdocs_nav(mkdocs, tmp_path)
        assert len(result) == 2  # Home + Guide (with children)
        guide = result[1]
        assert guide["title"] == "Guide"
        assert len(guide["children"]) == 2
        assert guide["children"][0]["level"] == 2

    def test_missing_files_still_parsed(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Exists: exists.md\n"
            "  - Missing: missing.md\n"
        )
        (tmp_path / "exists.md").write_text("# Exists")
        # missing.md intentionally not created

        result = parse_mkdocs_nav(mkdocs, tmp_path)
        assert len(result) == 2  # both parsed


class TestParseSidebarMd:
    """Parse _sidebar.md / SUMMARY.md link-list format."""

    def test_flat_sidebar(self, tmp_path):
        sidebar = tmp_path / "_sidebar.md"
        sidebar.write_text(
            "- [Home](index.md)\n"
            "- [Guide](guide.md)\n"
            "- [API](api.md)\n"
        )
        for name in ["index.md", "guide.md", "api.md"]:
            (tmp_path / name).write_text(f"# {name}")

        result = parse_sidebar_md(sidebar, tmp_path)
        assert len(result) == 3
        assert result[0]["title"] == "Home"
        assert result[0]["path"] == "index.md"

    def test_nested_sidebar(self, tmp_path):
        sidebar = tmp_path / "SUMMARY.md"
        sidebar.write_text(
            "- [Introduction](intro.md)\n"
            "  - [Install](install.md)\n"
            "  - [Config](config.md)\n"
            "- [Advanced](advanced.md)\n"
        )
        for name in ["intro.md", "install.md", "config.md", "advanced.md"]:
            (tmp_path / name).write_text(f"# {name}")

        result = parse_sidebar_md(sidebar, tmp_path)
        assert len(result) == 2  # Introduction (with children) + Advanced
        assert len(result[0]["children"]) == 2
        assert result[0]["children"][0]["level"] == 2


class TestDetectNav:
    """End-to-end nav detection."""

    def test_no_nav_file(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Hello")
        result = detect_nav(str(tmp_path))
        assert result["found"] is False
        assert result["hierarchy"] == []

    def test_mkdocs_detected(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "site_name: Test\n"
            "nav:\n"
            "  - Home: index.md\n"
            "  - About: about.md\n"
        )
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "about.md").write_text("# About")

        result = detect_nav(str(tmp_path))
        assert result["found"] is True
        assert result["nav_file"] == "mkdocs.yml"
        assert result["framework"] == "mkdocs"
        assert len(result["hierarchy"]) == 2

    def test_coverage_calculation(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Home: index.md\n"
            "  - Missing: missing.md\n"
        )
        (tmp_path / "index.md").write_text("# Home")
        (tmp_path / "extra.md").write_text("# Extra")
        # missing.md not created, extra.md not in nav

        result = detect_nav(str(tmp_path))
        assert result["coverage"]["nav_entries"] == 2
        assert result["coverage"]["files_resolved"] == 1
        assert result["coverage"]["files_missing"] == 1
        assert result["coverage"]["total_md_files"] == 2  # index.md + extra.md
        assert result["coverage"]["coverage_pct"] == 50.0

    def test_sidebar_fallback(self, tmp_path):
        sidebar = tmp_path / "_sidebar.md"
        sidebar.write_text("- [Home](index.md)\n")
        (tmp_path / "index.md").write_text("# Home")

        result = detect_nav(str(tmp_path))
        assert result["found"] is True
        assert result["framework"] == "docsify"

    def test_summary_md_detected(self, tmp_path):
        summary = tmp_path / "SUMMARY.md"
        summary.write_text("- [Intro](intro.md)\n")
        (tmp_path / "intro.md").write_text("# Intro")

        result = detect_nav(str(tmp_path))
        assert result["found"] is True
        assert result["framework"] in ("mdbook", "gitbook")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_detect_nav.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'detect_nav'`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/detect_nav.py
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

# Priority-ordered nav file candidates: (filename, framework, parser)
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
    """Recursively walk mkdocs nav structure."""
    result = []
    for item in nav_items:
        if isinstance(item, dict):
            for title, value in item.items():
                if isinstance(value, str):
                    # Leaf: "Title: path.md"
                    result.append({
                        "title": title,
                        "path": value,
                        "level": level,
                        "children": [],
                    })
                elif isinstance(value, list):
                    # Group: "Title: [children]"
                    children = _walk_mkdocs_nav(value, source_root, level + 1)
                    result.append({
                        "title": title,
                        "path": None,
                        "level": level,
                        "children": children,
                    })
        elif isinstance(item, str):
            result.append({
                "title": item,
                "path": item,
                "level": level,
                "children": [],
            })
    return result


def _parse_mkdocs_nav_regex(nav_file: Path, source_root: Path) -> list[dict]:
    """Fallback: extract nav entries from mkdocs.yml via regex (no PyYAML)."""
    text = nav_file.read_text()
    # Simple pattern: "  - Title: path.md" lines under nav:
    in_nav = False
    result = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("nav:"):
            in_nav = True
            continue
        if in_nav:
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                break  # left nav block
            match = re.match(r"\s*-\s+(.+?):\s+(\S+\.md\S*)", line)
            if match:
                result.append({
                    "title": match.group(1).strip(),
                    "path": match.group(2).strip(),
                    "level": 1,
                    "children": [],
                })
    return result


def parse_sidebar_md(sidebar_file: Path, source_root: Path) -> list[dict]:
    """Parse _sidebar.md or SUMMARY.md link-list format into hierarchy."""
    text = sidebar_file.read_text()
    flat = []
    for line in text.splitlines():
        match = LINK_RE.match(line)
        if match:
            indent = len(match.group(1))
            level = (indent // 2) + 1
            flat.append({
                "title": match.group(2).strip(),
                "path": match.group(3).strip(),
                "level": level,
                "children": [],
            })

    # Build nested structure from flat list using level
    return _nest_by_level(flat)


def _nest_by_level(flat: list[dict]) -> list[dict]:
    """Convert flat list with levels into nested children."""
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
    """Collect all paths from hierarchy (recursive)."""
    paths = []
    for item in hierarchy:
        if item.get("path"):
            paths.append(item["path"])
        paths.extend(_collect_paths(item.get("children", [])))
    return paths


def _count_md_files(source_root: Path) -> int:
    """Count all .md/.mdx files in source root."""
    count = 0
    for ext in ("*.md", "*.mdx"):
        count += len(list(source_root.rglob(ext)))
    return count


def detect_nav(source_root_str: str) -> dict:
    """Detect navigation structure in a source root directory.

    Returns dict with found, nav_file, framework, hierarchy, coverage.
    """
    source_root = Path(source_root_str)
    empty_result = {
        "found": False,
        "nav_file": None,
        "framework": None,
        "hierarchy": [],
        "coverage": {
            "nav_entries": 0,
            "files_resolved": 0,
            "files_missing": 0,
            "total_md_files": _count_md_files(source_root),
            "coverage_pct": 0.0,
        },
    }

    if not source_root.is_dir():
        return empty_result

    # Try each nav file candidate in priority order
    for filename, framework, parser_type in NAV_CANDIDATES:
        nav_path = source_root / filename
        if not nav_path.exists():
            continue

        if parser_type == "yaml_nav":
            hierarchy = parse_mkdocs_nav(nav_path, source_root)
        elif parser_type == "sidebar_md":
            hierarchy = parse_sidebar_md(nav_path, source_root)
        elif parser_type == "yaml_toc":
            hierarchy = parse_mkdocs_nav(nav_path, source_root)  # similar structure
        else:
            continue

        if not hierarchy:
            continue

        # Calculate coverage
        all_paths = _collect_paths(hierarchy)
        resolved = sum(1 for p in all_paths if (source_root / p).exists())
        missing = len(all_paths) - resolved
        total_md = _count_md_files(source_root)
        coverage_pct = round((resolved / total_md * 100) if total_md > 0 else 0.0, 1)

        return {
            "found": True,
            "nav_file": filename,
            "framework": framework,
            "hierarchy": hierarchy,
            "coverage": {
                "nav_entries": len(all_paths),
                "files_resolved": resolved,
                "files_missing": missing,
                "total_md_files": total_md,
                "coverage_pct": coverage_pct,
            },
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_detect_nav.py -v`
Expected: All 10 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/detect_nav.py lib/corpus/scripts/tests/test_detect_nav.py
git commit -m "feat: add navigation structure detection (detect_nav.py)"
```

---

## Task 3: verify_entries.py — Entry Content Verification

**Files:**
- Create: `lib/corpus/scripts/verify_entries.py`
- Create: `lib/corpus/scripts/tests/test_verify_entries.py`

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_verify_entries.py
"""Tests for verify_entries.py — entry content verification data prep.

Unit tests (no external deps):
  - Extracts content preview from existing files
  - Handles missing files gracefully
  - Respects token limit
  - Samples entries when --sample is set
  - Filters by --entries when set
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from verify_entries import extract_previews


@pytest.fixture
def sample_index(tmp_path):
    """Create a minimal index.yaml and source files."""
    index_yaml = tmp_path / "index.yaml"
    index_yaml.write_text(
        "meta:\n"
        "  entry_count: 3\n"
        "entries:\n"
        "  - id: 'src:docs/intro.md'\n"
        "    title: Introduction\n"
        "    summary: Overview of the project\n"
        "    source: docs/intro.md\n"
        "  - id: 'src:docs/guide.md'\n"
        "    title: Guide\n"
        "    summary: How to use the tool\n"
        "    source: docs/guide.md\n"
        "  - id: 'src:docs/missing.md'\n"
        "    title: Missing\n"
        "    summary: This file does not exist\n"
        "    source: docs/missing.md\n"
    )
    source_root = tmp_path / "source"
    docs = source_root / "docs"
    docs.mkdir(parents=True)
    (docs / "intro.md").write_text("# Introduction\n\nThis is the overview of the project.\n" * 10)
    (docs / "guide.md").write_text("# Guide\n\nStep by step instructions.\n" * 5)
    # missing.md intentionally not created
    return index_yaml, source_root


class TestExtractPreviews:
    def test_extracts_existing_files(self, sample_index):
        index_yaml, source_root = sample_index
        result = extract_previews(str(index_yaml), str(source_root), token_limit=500)
        existing = [r for r in result if r["content_preview"] is not None]
        assert len(existing) == 2
        assert existing[0]["entry_id"] == "src:docs/intro.md"
        assert "Introduction" in existing[0]["content_preview"]

    def test_handles_missing_files(self, sample_index):
        index_yaml, source_root = sample_index
        result = extract_previews(str(index_yaml), str(source_root), token_limit=500)
        missing = [r for r in result if r["content_preview"] is None]
        assert len(missing) == 1
        assert missing[0]["entry_id"] == "src:docs/missing.md"

    def test_respects_token_limit(self, sample_index):
        index_yaml, source_root = sample_index
        result = extract_previews(str(index_yaml), str(source_root), token_limit=10)
        for r in result:
            if r["content_preview"] is not None:
                word_count = len(r["content_preview"].split())
                assert word_count <= 30  # ~10 tokens * 1.3 safety margin

    def test_sample_limits_count(self, sample_index):
        index_yaml, source_root = sample_index
        result = extract_previews(str(index_yaml), str(source_root), token_limit=500, sample=1)
        assert len(result) == 1

    def test_filter_by_entry_ids(self, sample_index):
        index_yaml, source_root = sample_index
        result = extract_previews(
            str(index_yaml), str(source_root), token_limit=500,
            entry_ids=["src:docs/guide.md"]
        )
        assert len(result) == 1
        assert result[0]["entry_id"] == "src:docs/guide.md"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_verify_entries.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/verify_entries.py
#!/usr/bin/env python3
"""Extract content previews for index entries (data prep for LLM verification).

Usage:
  python3 verify_entries.py --index <path> --source-root <path> [--token-limit 500] [--sample N] [--entries ID,ID,...]

Output: JSON array to stdout. Each entry has {entry_id, title, summary, source_path, content_preview, token_count}.
content_preview is null if the source file is missing.

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
    """Load entries from index.yaml."""
    try:
        import yaml
    except ImportError:
        # Fallback: basic regex extraction
        return _load_index_regex(index_path)

    with open(index_path) as f:
        data = yaml.safe_load(f)

    return data.get("entries", []) if isinstance(data, dict) else []


def _load_index_regex(index_path: str) -> list[dict]:
    """Fallback index loader using regex (no PyYAML)."""
    text = Path(index_path).read_text()
    entries = []
    current: dict | None = None
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


def _truncate_to_tokens(text: str, token_limit: int) -> str:
    """Truncate text to approximately token_limit tokens."""
    words = text.split()
    # Approximate: 1 token ≈ 1 word / 1.3
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
) -> list[dict]:
    """Extract content previews for index entries.

    Args:
        index_path: Path to index.yaml
        source_root: Path to source root directory
        token_limit: Max tokens per preview
        sample: If set, randomly sample this many entries
        entry_ids: If set, only process these entry IDs

    Returns:
        List of dicts with entry_id, title, summary, source_path, content_preview, token_count.
    """
    entries = _load_index(index_path)
    source = Path(source_root)

    # Filter by entry IDs if specified
    if entry_ids:
        id_set = set(entry_ids)
        entries = [e for e in entries if e.get("id") in id_set]

    # Sample if specified
    if sample is not None and sample < len(entries):
        entries = random.sample(entries, sample)

    result = []
    for entry in entries:
        entry_id = entry.get("id", "")
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        source_path = entry.get("source", "")

        # Resolve source path — strip source_id prefix if present
        # Entry IDs look like "src:docs/intro.md", source field is "docs/intro.md"
        file_path = source / source_path

        if file_path.exists():
            content = file_path.read_text(errors="replace")
            preview = _truncate_to_tokens(content, token_limit)
            token_count = estimate_tokens(preview)
        else:
            preview = None
            token_count = 0

        result.append({
            "entry_id": entry_id,
            "title": title,
            "summary": summary,
            "source_path": source_path,
            "content_preview": preview,
            "token_count": token_count,
        })

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Extract content previews for entry verification")
    parser.add_argument("--index", required=True, help="Path to index.yaml")
    parser.add_argument("--source-root", required=True, help="Path to source root directory")
    parser.add_argument("--token-limit", type=int, default=500, help="Max tokens per preview (default: 500)")
    parser.add_argument("--sample", type=int, default=None, help="Random sample N entries (default: all)")
    parser.add_argument("--entries", default=None, help="Comma-separated entry IDs to verify")
    return parser.parse_args()


def main():
    args = parse_args()
    entry_ids = args.entries.split(",") if args.entries else None
    result = extract_previews(
        args.index, args.source_root,
        token_limit=args.token_limit,
        sample=args.sample,
        entry_ids=entry_ids,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_verify_entries.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/verify_entries.py lib/corpus/scripts/tests/test_verify_entries.py
git commit -m "feat: add entry content verification (verify_entries.py)"
```

---

## Task 4: split_by_headings.py — Heading-Based File Splitting

**Files:**
- Create: `lib/corpus/scripts/split_by_headings.py`
- Create: `lib/corpus/scripts/tests/test_split_by_headings.py`

This is needed by both Algorithm 4 (large-node splitting) and Algorithm 5 (heading-aware chunking), so it comes before both.

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_split_by_headings.py
"""Tests for split_by_headings.py — heading-based file splitting.

Unit tests (no external deps):
  - Splits on headings at configured levels
  - Skips headings inside code blocks
  - Generates correct anchors
  - Calculates line ranges
  - Merges small sections (tree thinning)
  - Handles files with no headings
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from split_by_headings import split_by_headings


class TestSplitByHeadings:
    def test_basic_split(self):
        text = (
            "# Title\n"
            "\n"
            "Intro paragraph.\n"
            "\n"
            "## Section One\n"
            "\n"
            "Content for section one.\n"
            "More content here.\n"
            "\n"
            "## Section Two\n"
            "\n"
            "Content for section two.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert len(result) == 2
        assert result[0]["title"] == "Section One"
        assert result[1]["title"] == "Section Two"

    def test_line_ranges(self):
        text = (
            "## First\n"
            "Line 2\n"
            "Line 3\n"
            "\n"
            "## Second\n"
            "Line 6\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result[0]["line_start"] == 1
        assert result[0]["line_end"] == 4
        assert result[1]["line_start"] == 5
        assert result[1]["line_end"] == 6

    def test_anchor_generation(self):
        text = (
            "## Getting Started Guide\n"
            "Content.\n"
            "\n"
            "## API (v2) Reference!\n"
            "Content.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result[0]["anchor"] == "getting-started-guide"
        assert result[1]["anchor"] == "api-v2-reference"

    def test_skips_code_block_headings(self):
        text = (
            "## Real Heading\n"
            "Content.\n"
            "\n"
            "```markdown\n"
            "## Fake Heading Inside Code\n"
            "```\n"
            "\n"
            "## Another Real Heading\n"
            "Content.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert len(result) == 2
        titles = [r["title"] for r in result]
        assert "Fake Heading Inside Code" not in titles

    def test_respects_level_range(self):
        text = (
            "# H1\n"
            "Content.\n"
            "## H2\n"
            "Content.\n"
            "### H3\n"
            "Content.\n"
            "#### H4\n"
            "Content.\n"
            "##### H5\n"
            "Content.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=3, min_tokens=0)
        levels = [r["level"] for r in result]
        assert all(2 <= l <= 3 for l in levels)

    def test_merges_small_sections(self):
        text = (
            "## Big Section\n"
            + "Word " * 200
            + "\n\n## Tiny\nOne line.\n\n## Another Big\n"
            + "Word " * 200
            + "\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=100)
        # "Tiny" section should be merged into previous section
        titles = [r["title"] for r in result]
        assert "Tiny" not in titles

    def test_no_headings_returns_empty(self):
        text = "Just a plain text file.\nWith no headings at all.\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result == []

    def test_text_preview_included(self):
        text = (
            "## Section\n"
            "First line of content.\n"
            "Second line.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert "text_preview" in result[0]
        assert "First line" in result[0]["text_preview"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_split_by_headings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/split_by_headings.py
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
    """Generate URL anchor from heading title."""
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
    """Split markdown text into sections by heading structure.

    Args:
        text: Markdown content
        min_level: Minimum heading level to split at (2 = ##)
        max_level: Maximum heading level to split at (4 = ####)
        min_tokens: Sections below this token count are merged into previous

    Returns:
        List of section dicts with title, level, line_start, line_end,
        token_count, anchor, text_preview.
    """
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
                title = match.group(2).strip()
                raw_sections.append({
                    "title": title,
                    "level": level,
                    "line_start": i + 1,  # 1-indexed
                })

    if not raw_sections:
        return []

    # Calculate line ranges and token counts
    for idx, section in enumerate(raw_sections):
        if idx + 1 < len(raw_sections):
            section["line_end"] = raw_sections[idx + 1]["line_start"] - 1
        else:
            section["line_end"] = len(lines)

        section_text = "\n".join(lines[section["line_start"] - 1 : section["line_end"]])
        section["token_count"] = estimate_tokens(section_text)
        section["anchor"] = _make_anchor(section["title"])
        section["text_preview"] = section_text[:200]

    # Tree thinning: merge small sections into previous
    if min_tokens > 0:
        merged = []
        for section in raw_sections:
            if section["token_count"] < min_tokens and merged:
                # Merge into previous section
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_split_by_headings.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/split_by_headings.py lib/corpus/scripts/tests/test_split_by_headings.py
git commit -m "feat: add heading-based file splitting (split_by_headings.py)"
```

---

## Task 5: detect_large_files.py — Large File Detection

**Files:**
- Create: `lib/corpus/scripts/detect_large_files.py`
- Create: `lib/corpus/scripts/tests/test_detect_large_files.py`

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_detect_large_files.py
"""Tests for detect_large_files.py — large file detection.

Unit tests (no external deps):
  - Detects files above token threshold
  - Ignores files below threshold
  - Reports heading presence and count
  - Handles empty directories
  - Respects --paths filter
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from detect_large_files import detect_large_files


@pytest.fixture
def docs_dir(tmp_path):
    """Create a directory with files of varying sizes."""
    # Small file (~10 words)
    (tmp_path / "small.md").write_text("# Small\n\nJust a small file.\n")
    # Large file with headings (~200 words)
    large_content = "# Large File\n\n"
    for i in range(20):
        large_content += f"## Section {i}\n\n"
        large_content += f"Content for section {i}. " * 10 + "\n\n"
    (tmp_path / "large_with_headings.md").write_text(large_content)
    # Large file without headings (~200 words)
    plain_content = "Just a very long file.\n" * 100
    (tmp_path / "large_plain.md").write_text(plain_content)
    return tmp_path


class TestDetectLargeFiles:
    def test_detects_large_files(self, docs_dir):
        result = detect_large_files(str(docs_dir), max_tokens=50)
        paths = [r["path"] for r in result]
        assert any("large_with_headings" in p for p in paths)
        assert any("large_plain" in p for p in paths)

    def test_ignores_small_files(self, docs_dir):
        result = detect_large_files(str(docs_dir), max_tokens=50)
        paths = [r["path"] for r in result]
        assert not any("small" in p for p in paths)

    def test_reports_heading_info(self, docs_dir):
        result = detect_large_files(str(docs_dir), max_tokens=50)
        with_headings = [r for r in result if "large_with_headings" in r["path"]]
        assert len(with_headings) == 1
        assert with_headings[0]["has_headings"] is True
        assert with_headings[0]["heading_count"] >= 20

    def test_no_headings_detected(self, docs_dir):
        result = detect_large_files(str(docs_dir), max_tokens=50)
        plain = [r for r in result if "large_plain" in r["path"]]
        assert len(plain) == 1
        assert plain[0]["has_headings"] is False

    def test_empty_dir(self, tmp_path):
        result = detect_large_files(str(tmp_path), max_tokens=50)
        assert result == []

    def test_high_threshold_finds_nothing(self, docs_dir):
        result = detect_large_files(str(docs_dir), max_tokens=999999)
        assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_detect_large_files.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/detect_large_files.py
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
    """Find markdown files exceeding max_tokens.

    Args:
        source_root: Path to source root directory
        max_tokens: Token threshold for "large"
        paths: If set, only check these relative paths

    Returns:
        List of dicts with path, token_count, line_count, has_headings,
        heading_count, deepest_heading_level.
    """
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
            "path": rel_path,
            "token_count": token_count,
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_detect_large_files.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/detect_large_files.py lib/corpus/scripts/tests/test_detect_large_files.py
git commit -m "feat: add large file detection (detect_large_files.py)"
```

---

## Task 6: thin_sections.py — Section Tree Thinning

**Files:**
- Create: `lib/corpus/scripts/thin_sections.py`
- Create: `lib/corpus/scripts/tests/test_thin_sections.py`

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_thin_sections.py
"""Tests for thin_sections.py — bottom-up section merging.

Unit tests (no external deps):
  - Merges small sections into siblings
  - Merges into parent when no sibling
  - Never merges across source files
  - Never merges sections with children
  - Preserves keywords from merged sections
  - Dry-run mode does not modify
  - Updates entry count
"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from thin_sections import thin_sections


def _make_index(entries):
    """Helper: wrap entries in index.yaml structure."""
    return {"meta": {"entry_count": len(entries)}, "entries": entries}


class TestThinSections:
    def test_merges_small_into_sibling(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs", "tier": "file"},
            {"id": "src:api.md#methods", "title": "Methods", "summary": "Method docs " * 30,
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [10, 50], "keywords": ["methods"]},
            {"id": "src:api.md#params", "title": "Parameters", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [51, 55], "keywords": ["params"]},
        ])
        result = thin_sections(index, min_tokens=100)
        section_ids = [e["id"] for e in result["entries"] if e.get("tier") == "section"]
        assert "src:api.md#params" not in section_ids
        # Keywords preserved on the surviving sibling
        methods = [e for e in result["entries"] if e["id"] == "src:api.md#methods"][0]
        assert "params" in methods["keywords"]

    def test_merges_into_parent_when_no_sibling(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs",
             "tier": "file", "keywords": ["api"]},
            {"id": "src:api.md#tiny", "title": "Tiny", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [10, 12], "keywords": ["tiny"]},
        ])
        result = thin_sections(index, min_tokens=100)
        section_ids = [e["id"] for e in result["entries"] if e.get("tier") == "section"]
        assert "src:api.md#tiny" not in section_ids
        parent = [e for e in result["entries"] if e["id"] == "src:api.md"][0]
        assert "tiny" in parent["keywords"]

    def test_never_merges_across_sources(self):
        index = _make_index([
            {"id": "src1:a.md", "title": "A", "summary": "A docs", "tier": "file"},
            {"id": "src1:a.md#small", "title": "Small A", "summary": "Short",
             "tier": "section", "parent": "src1:a.md", "heading_level": 2,
             "line_range": [1, 3], "keywords": []},
            {"id": "src2:b.md", "title": "B", "summary": "B docs " * 30, "tier": "file"},
            {"id": "src2:b.md#big", "title": "Big B", "summary": "Big section " * 30,
             "tier": "section", "parent": "src2:b.md", "heading_level": 2,
             "line_range": [1, 50], "keywords": []},
        ])
        result = thin_sections(index, min_tokens=100)
        # src1 small section can only merge into src1 parent, not into src2
        section_ids = [e["id"] for e in result["entries"] if e.get("tier") == "section"]
        assert "src1:a.md#small" not in section_ids

    def test_never_merges_section_with_children(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs", "tier": "file"},
            {"id": "src:api.md#parent", "title": "Parent", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [10, 50], "keywords": []},
            {"id": "src:api.md#child", "title": "Child", "summary": "Child section " * 30,
             "tier": "section", "parent": "src:api.md#parent", "heading_level": 3,
             "line_range": [20, 50], "keywords": []},
        ])
        result = thin_sections(index, min_tokens=100)
        # Parent has children, so it must not be merged even if small
        section_ids = [e["id"] for e in result["entries"] if e.get("tier") == "section"]
        assert "src:api.md#parent" in section_ids

    def test_updates_entry_count(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs", "tier": "file"},
            {"id": "src:api.md#big", "title": "Big", "summary": "Big section " * 30,
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [10, 50], "keywords": []},
            {"id": "src:api.md#tiny", "title": "Tiny", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [51, 53], "keywords": []},
        ])
        result = thin_sections(index, min_tokens=100)
        assert result["meta"]["entry_count"] == len(result["entries"])

    def test_dry_run_returns_plan(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs", "tier": "file"},
            {"id": "src:api.md#tiny", "title": "Tiny", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [1, 3], "keywords": []},
        ])
        original = copy.deepcopy(index)
        result = thin_sections(index, min_tokens=100, dry_run=True)
        # In dry_run, the input should not be modified
        assert index == original
        # But the result should report what would be merged
        assert result["sections_before"] >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_thin_sections.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# lib/corpus/scripts/thin_sections.py
#!/usr/bin/env python3
"""Bottom-up merge of small section entries in index.yaml.

Usage:
  python3 thin_sections.py --index <path> [--min-tokens 300] [--dry-run]

Merges section entries below min-tokens into their nearest sibling or parent.
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
    """Check if any entry has this entry_id as parent."""
    return any(e.get("parent") == entry_id for e in entries)


def _source_prefix(entry_id: str) -> str:
    """Extract source prefix from entry ID (everything before the first colon+path)."""
    if ":" in entry_id:
        return entry_id.split(":")[0]
    return ""


def thin_sections(
    index: dict,
    min_tokens: int = 300,
    dry_run: bool = False,
) -> dict:
    """Merge small section entries bottom-up.

    Args:
        index: Parsed index.yaml dict with meta and entries keys
        min_tokens: Sections below this token count are merged
        dry_run: If True, return merge plan without modifying index

    Returns:
        If dry_run: dict with sections_before, sections_after, merged[]
        If not dry_run: modified index dict
    """
    if dry_run:
        work = copy.deepcopy(index)
    else:
        work = index

    entries = work.get("entries", [])
    sections = [e for e in entries if e.get("tier") == "section"]
    sections_before = len(sections)
    merged_log = []

    # Sort sections by heading_level descending (deepest first = bottom-up)
    sections_by_depth = sorted(sections, key=lambda e: e.get("heading_level", 0), reverse=True)

    ids_to_remove = set()

    for section in sections_by_depth:
        sid = section["id"]
        if sid in ids_to_remove:
            continue

        # Skip sections that have children
        if _has_children(sid, entries):
            continue

        # Estimate tokens from summary + keywords
        text = (section.get("summary", "") + " " + " ".join(section.get("keywords", []))).strip()
        tokens = estimate_tokens(text)

        if tokens >= min_tokens:
            continue

        # Find merge target: previous sibling (same parent, same source) or parent
        parent_id = section.get("parent")
        source_pfx = _source_prefix(sid)

        # Find siblings: same parent, same source prefix, section tier, not marked for removal
        siblings = [
            e for e in entries
            if e.get("parent") == parent_id
            and e.get("tier") == "section"
            and _source_prefix(e["id"]) == source_pfx
            and e["id"] != sid
            and e["id"] not in ids_to_remove
        ]

        # Find the previous sibling by line_range
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
            # Merge into parent
            target = next((e for e in entries if e["id"] == parent_id), None)
            if target is None:
                continue
            target_id = target["id"]
        else:
            continue

        # Verify same source
        if _source_prefix(target_id) != source_pfx:
            continue

        # Perform merge
        target_kw = target.get("keywords", [])
        section_kw = section.get("keywords", [])
        target["keywords"] = list(dict.fromkeys(target_kw + section_kw))  # deduplicated, order-preserving

        # Extend line_range if target is a section
        if target.get("line_range") and section.get("line_range"):
            target["line_range"][1] = max(target["line_range"][1], section["line_range"][1])

        # Append summary snippet
        if section.get("summary"):
            target["summary"] = (target.get("summary", "") + " " + section["summary"]).strip()

        ids_to_remove.add(sid)
        merged_log.append({
            "removed_id": sid,
            "merged_into": target_id,
            "reason": f"{tokens} tokens (below {min_tokens} threshold)",
        })

    # Remove merged entries
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
            "merged": [],  # not tracked in non-dry-run for simplicity
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_thin_sections.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/thin_sections.py lib/corpus/scripts/tests/test_thin_sections.py
git commit -m "feat: add section tree thinning (thin_sections.py)"
```

---

## Task 7: chunk.py Headings Strategy

**Files:**
- Modify: `lib/corpus/scripts/chunk.py`
- Create: `lib/corpus/scripts/tests/test_chunk_headings.py`

Add a `headings` strategy to the existing `chunk.py` that uses `split_by_headings` for primary boundaries and falls back to paragraph splitting within large sections. Each chunk carries a `heading_context` field.

- [ ] **Step 1: Write the failing tests**

```python
# lib/corpus/scripts/tests/test_chunk_headings.py
"""Tests for chunk.py headings strategy.

Unit tests (no external deps):
  - Sections within target are single chunks
  - Large sections split at paragraphs
  - heading_context is populated
  - Overlap only on paragraph splits, not heading boundaries
  - Falls back to markdown strategy for files without headings
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeadingsStrategy:
    def test_sections_within_target_are_single_chunks(self):
        from chunk import chunk_text

        text = (
            "## Section One\n\nShort content.\n\n"
            "## Section Two\n\nAnother short section.\n"
        )
        chunks = chunk_text(text, strategy="headings", target_tokens=100, overlap_tokens=10)
        assert len(chunks) == 2
        assert "heading_context" in chunks[0]
        assert chunks[0]["heading_context"] == "## Section One"
        assert chunks[1]["heading_context"] == "## Section Two"

    def test_large_sections_split_at_paragraphs(self):
        from chunk import chunk_text

        text = "## Big Section\n\n"
        for i in range(20):
            text += f"Paragraph {i}. " * 20 + "\n\n"
        chunks = chunk_text(text, strategy="headings", target_tokens=50, overlap_tokens=10)
        assert len(chunks) > 1
        # All chunks should have the same heading context
        for c in chunks:
            assert c["heading_context"] == "## Big Section"

    def test_no_overlap_at_heading_boundaries(self):
        from chunk import chunk_text

        text = (
            "## First\n\nContent one.\n\n"
            "## Second\n\nContent two.\n"
        )
        chunks = chunk_text(text, strategy="headings", target_tokens=100, overlap_tokens=10)
        if len(chunks) >= 2:
            assert chunks[1].get("overlap_prev") is False

    def test_overlap_on_paragraph_splits(self):
        from chunk import chunk_text

        text = "## Section\n\n"
        for i in range(20):
            text += f"Paragraph {i}. " * 20 + "\n\n"
        chunks = chunk_text(text, strategy="headings", target_tokens=50, overlap_tokens=10)
        if len(chunks) >= 2:
            assert chunks[1].get("overlap_prev") is True

    def test_nested_heading_context(self):
        from chunk import chunk_text

        text = (
            "## Parent\n\nIntro.\n\n"
            "### Child\n\nChild content.\n"
        )
        chunks = chunk_text(text, strategy="headings", target_tokens=100, overlap_tokens=0)
        child_chunks = [c for c in chunks if "Child" in c.get("text", "")]
        if child_chunks:
            assert "Parent" in child_chunks[0]["heading_context"]
            assert "Child" in child_chunks[0]["heading_context"]

    def test_no_headings_falls_back(self):
        from chunk import chunk_text

        text = "Just plain text.\n" * 50
        chunks = chunk_text(text, strategy="headings", target_tokens=20, overlap_tokens=5)
        assert len(chunks) >= 1
        # Should still work, falling back to paragraph splitting
        for c in chunks:
            assert "heading_context" in c
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_chunk_headings.py -v`
Expected: FAIL — `ValueError` or `KeyError` because `headings` strategy doesn't exist yet

- [ ] **Step 3: Read current chunk.py to find insertion points**

Read: `lib/corpus/scripts/chunk.py` — full file. Note:
- `BOUNDARY_SCORES` dict at top (add `"headings"` key)
- `STRATEGY_DEFAULTS` dict (add `"headings"` defaults)
- `chunk_text()` function — the main function that dispatches on strategy
- `parse_args()` — add `"headings"` to choices

- [ ] **Step 4: Add headings strategy to chunk.py**

The changes to `chunk.py`:

1. Add `"headings"` to `BOUNDARY_SCORES` and `STRATEGY_DEFAULTS`:

```python
BOUNDARY_SCORES = {
    ...existing strategies...
    "headings": {"heading": 100, "blank_line": 20},
}

STRATEGY_DEFAULTS = {
    ...existing strategies...
    "headings": {"target_tokens": 900, "overlap_tokens": 100},
}
```

2. Add `"headings"` to `parse_args()` choices:

```python
parser.add_argument("--strategy",
    choices=["markdown", "transcript", "code", "paragraph", "headings"],
    default="markdown", help="Chunking strategy (default: markdown)")
```

3. Add heading-aware chunking logic to `chunk_text()`. Before the existing boundary-scoring code, add a branch for the headings strategy that:
   - Imports and calls `split_by_headings` to get section boundaries
   - For sections that fit in `target_tokens`, emits them as single chunks with `heading_context`
   - For sections that exceed `target_tokens`, splits at paragraph boundaries with overlap
   - Falls back to the existing markdown strategy if no headings found

The exact code depends on the current structure of `chunk_text()`. Read the full function, then add a new branch at the top:

```python
if strategy == "headings":
    from split_by_headings import split_by_headings as _split_headings
    sections = _split_headings(text, min_level=1, max_level=6, min_tokens=0)
    if not sections:
        # No headings found — fall back to paragraph splitting
        return _chunk_paragraphs(lines, target_tokens, overlap_tokens, heading_context="")
    return _chunk_by_sections(lines, sections, target_tokens, overlap_tokens)
```

Add helper functions `_chunk_by_sections()` and `_chunk_paragraphs()`:

```python
def _build_heading_context(sections, current_line):
    """Build ancestor heading chain for a line number."""
    context_parts = []
    for s in sections:
        if s["line_start"] <= current_line <= s["line_end"]:
            context_parts.append(f"{'#' * s['level']} {s['title']}")
    return " > ".join(context_parts) if context_parts else ""


def _chunk_paragraphs(lines, target_tokens, overlap_tokens, heading_context, start_line=1):
    """Split lines into chunks at paragraph boundaries with overlap."""
    chunks = []
    current_lines = []
    current_tokens = 0
    chunk_start = start_line

    for i, line in enumerate(lines):
        line_tokens = int(len(line.split()) * TOKENS_PER_WORD)
        if current_tokens + line_tokens > target_tokens and current_lines:
            chunk_text_str = "\n".join(current_lines)
            chunks.append({
                "text": chunk_text_str,
                "line_range": [chunk_start, start_line + i - 1],
                "chunk_index": len(chunks),
                "overlap_prev": len(chunks) > 0 and overlap_tokens > 0,
                "heading_context": heading_context,
            })
            # Overlap: keep last N tokens worth of lines
            if overlap_tokens > 0:
                overlap_lines = []
                overlap_count = 0
                for prev_line in reversed(current_lines):
                    overlap_count += int(len(prev_line.split()) * TOKENS_PER_WORD)
                    overlap_lines.insert(0, prev_line)
                    if overlap_count >= overlap_tokens:
                        break
                current_lines = overlap_lines
                current_tokens = overlap_count
                chunk_start = start_line + i - len(overlap_lines)
            else:
                current_lines = []
                current_tokens = 0
                chunk_start = start_line + i
        current_lines.append(line)
        current_tokens += line_tokens

    if current_lines:
        chunks.append({
            "text": "\n".join(current_lines),
            "line_range": [chunk_start, start_line + len(lines) - 1],
            "chunk_index": len(chunks),
            "overlap_prev": len(chunks) > 0 and overlap_tokens > 0,
            "heading_context": heading_context,
        })
    return chunks


def _chunk_by_sections(all_lines, sections, target_tokens, overlap_tokens):
    """Chunk by heading sections, splitting large sections at paragraphs."""
    chunks = []
    for section in sections:
        start = section["line_start"] - 1  # 0-indexed
        end = section["line_end"]  # exclusive for slicing
        section_lines = all_lines[start:end]
        section_tokens = int(len(" ".join(section_lines).split()) * TOKENS_PER_WORD)
        heading_context = f"{'#' * section['level']} {section['title']}"

        if section_tokens <= target_tokens:
            chunks.append({
                "text": "\n".join(section_lines),
                "line_range": [section["line_start"], section["line_end"]],
                "chunk_index": len(chunks),
                "overlap_prev": False,
                "heading_context": heading_context,
            })
        else:
            sub_chunks = _chunk_paragraphs(
                section_lines, target_tokens, overlap_tokens,
                heading_context, start_line=section["line_start"]
            )
            for sc in sub_chunks:
                sc["chunk_index"] = len(chunks)
                chunks.append(sc)
    return chunks
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_chunk_headings.py lib/corpus/scripts/tests/test_chunk.py -v`
Expected: All tests pass (both new headings tests and existing tests)

- [ ] **Step 6: Commit**

```bash
git add lib/corpus/scripts/chunk.py lib/corpus/scripts/tests/test_chunk_headings.py
git commit -m "feat: add headings chunking strategy to chunk.py"
```

---

## Task 8: embed.py — heading_context in Chunk Embeddings

**Files:**
- Modify: `lib/corpus/scripts/embed.py`

When embedding chunks that have a `heading_context` field, prepend it to the embedding text.

- [ ] **Step 1: Read embed.py to find the chunk embedding text construction**

Read: `lib/corpus/scripts/embed.py` — find the section where chunk text is constructed for embedding. Look for where `PASSAGE_PREFIX` is used with chunk data.

- [ ] **Step 2: Modify chunk embedding text to include heading_context**

Find the line where chunk embedding text is constructed (something like `text = chunk["text"]` or `text = PASSAGE_PREFIX + chunk["chunk_text"]`) and change it to:

```python
heading_ctx = chunk.get("heading_context", "")
raw_text = chunk.get("chunk_text", chunk.get("text", ""))
if heading_ctx:
    text = f"{PASSAGE_PREFIX}{heading_ctx} | {raw_text}"
else:
    text = f"{PASSAGE_PREFIX}{raw_text}"
```

- [ ] **Step 3: Run existing embed tests to verify no regression**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/test_embed.py -v`
Expected: All existing tests still pass

- [ ] **Step 4: Commit**

```bash
git add lib/corpus/scripts/embed.py
git commit -m "feat: prepend heading_context to chunk embeddings"
```

---

## Task 9: Source-Scanner Agent Prompt Updates

**Files:**
- Modify: `agents/source-scanner.md`

Add three new steps with GUARD blocks matching existing pseudocode patterns: Step 0 (nav detection), Step 1b (large file splitting), and chunking strategy selection.

- [ ] **Step 1: Read the current source-scanner agent prompt**

Read: `agents/source-scanner.md` — full file. Note the existing step numbering, format, and pseudocode style.

- [ ] **Step 2: Add Step 0 (nav detection) before existing Step 1**

Insert before the existing file discovery step. Use the exact pseudocode from the spec's `STEP_0_NAV_DETECTION()` block. Key elements:
- Pre-check: source root accessible
- Run `python3 ${PLUGIN_ROOT}/lib/corpus/scripts/detect_nav.py --source-root {source_root}`
- Graceful fallback on script failure
- Coverage threshold decision (>=80 auto-use, 50-80 ask user, <50 fallback)
- Post-check: DISPLAY coverage info

- [ ] **Step 3: Add Step 1b (large file splitting) after file discovery**

Insert after file discovery. Use the exact pseudocode from the spec's `STEP_1B_LARGE_FILE_SPLITTING()` block. Key elements:
- Pre-check: `computed.file_list` exists
- Skip when `large_file_threshold == 0`
- Run `detect_large_files.py` then `split_by_headings.py` per file
- Post-check: DISPLAY split summary

- [ ] **Step 4: Add chunking strategy selection**

In the existing chunking step, add strategy auto-selection logic from the spec's `STEP_CHUNKING_STRATEGY_SELECTION()` block. If `computed.nav_skeleton` exists or `heading_consistency == "high"`, use `headings` strategy.

- [ ] **Step 5: Update the Reference section**

Add the five new features to the source-scanner's reference section listing related skills and features.

- [ ] **Step 6: Commit**

```bash
git add agents/source-scanner.md
git commit -m "feat: add nav detection, large file splitting, and chunking strategy to source-scanner"
```

---

## Task 10: Build Skill Prompt Updates

**Files:**
- Modify: `skills/hiivmind-corpus-build/SKILL.md`

Add GUARD blocks for tree thinning (after Phase 2c) and verification (Phase 7c).

- [ ] **Step 1: Read the current build skill**

Read: `skills/hiivmind-corpus-build/SKILL.md` — find Phase 2c (section indexing), Phase 7/7b (embeddings), and Phase 8 (save).

- [ ] **Step 2: Add tree thinning GUARD after Phase 2c**

Insert the `GUARD_TREE_THINNING()` pseudocode block from the spec between Phase 2c and Phase 3. Key elements:
- Pre-check: section entries exist in scan results
- Skip when `min_section_tokens` not configured
- Dry-run first, present merge plan
- User confirmation `[Y/n]` before applying

- [ ] **Step 3: Add verification GUARD as Phase 7c**

Insert the `GUARD_PHASE_7C_VERIFICATION()` pseudocode block from the spec after Phase 7b and before Phase 8. Key elements:
- GUARD: `computed.index` exists
- Skip: `verify_on_build` disabled or entry_count >= 200 (default heuristic)
- Run `verify_entries.py --sample N`
- LLM verification in batches
- Present inaccurate entries with `[Y/n]` regeneration prompt

- [ ] **Step 4: Update Phase 8 GUARD to verify Phase 7c was evaluated**

Add `Phase 7c (Verification) evaluated` to the Phase 8 guard check, matching the existing pattern where Phase 8 verifies all prior phases ran.

- [ ] **Step 5: Update the Reference section**

Add the five new features to the build skill's reference section.

- [ ] **Step 6: Commit**

```bash
git add skills/hiivmind-corpus-build/SKILL.md
git commit -m "feat: add tree thinning and verification guards to build skill"
```

---

## Task 11: Refresh Skill Prompt Updates

**Files:**
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md`

Add optional post-refresh verification step.

- [ ] **Step 1: Read the current refresh skill**

Read: `skills/hiivmind-corpus-refresh/SKILL.md` — find Phase 6 (Apply Changes) and the existing embedding update logic.

- [ ] **Step 2: Add verification guard after Phase 6**

Insert the `GUARD_REFRESH_VERIFICATION()` pseudocode block from the spec. Key elements:
- Pre-check: `computed.changes_applied` exists
- Skip: only deletions applied
- Run `verify_entries.py --entries {modified_ids}`
- LLM verification
- Present inaccurate entries with `[Y/n]` prompt

- [ ] **Step 3: Update the Reference section**

Add the five new features to the refresh skill's reference section.

- [ ] **Step 4: Commit**

```bash
git add skills/hiivmind-corpus-refresh/SKILL.md
git commit -m "feat: add post-refresh verification to refresh skill"
```

---

## Task 12: CLAUDE.md Cross-Cutting Concerns Update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read the current cross-cutting concerns table**

Read: `CLAUDE.md` — find the `### Cross-Cutting Concerns` section and the feature table.

- [ ] **Step 2: Add five new rows to the table**

Add these rows to the cross-cutting concerns table:

```markdown
| Nav detection | source-scanner, build, add-source | `detect_nav.py` called before glob scan, coverage threshold logic |
| Verification loop | build, refresh | `verify_entries.py` + LLM verification, config flag |
| Tree thinning | build, enhance, refresh | `thin_sections.py` post-processing, `min_section_tokens` config |
| Large-node splitting | source-scanner, build | `detect_large_files.py` + `split_by_headings.py`, interaction with section indexing |
| Structure-aware chunking | build, source-scanner, navigate | `headings` strategy in `chunk.py`, `heading_context` in embeddings |
```

- [ ] **Step 3: Update the Skill Dependency Chain**

Add the new scripts to the dependency chain diagram:

```
build ──► detect_nav.py, detect_large_files.py, split_by_headings.py (Phase 2)
build ──► thin_sections.py (post Phase 2c)
build ──► verify_entries.py (Phase 7c)
refresh ──► verify_entries.py (post Phase 6)
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add PageIndex build enhancements to cross-cutting concerns"
```

---

## Task 13: Run Full Test Suite

**Files:** None modified. Verification only.

- [ ] **Step 1: Run all script tests**

Run: `cd /home/nathanielramm/git/hiivmind/hiivmind-corpus && python3 -m pytest lib/corpus/scripts/tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Verify no import errors across scripts**

Run each script with `--help` to verify imports work:

```bash
python3 lib/corpus/scripts/detect_nav.py --help
python3 lib/corpus/scripts/verify_entries.py --help
python3 lib/corpus/scripts/thin_sections.py --help
python3 lib/corpus/scripts/detect_large_files.py --help
python3 lib/corpus/scripts/split_by_headings.py --help
python3 lib/corpus/scripts/chunk.py --help
```

Expected: All print usage and exit 0.

- [ ] **Step 3: Check spec acceptance criteria**

Walk each acceptance criterion from `docs/superpowers/specs/2026-04-10-pageindex-build-enhancements-design.md` and confirm it is implemented. Report any gaps.
