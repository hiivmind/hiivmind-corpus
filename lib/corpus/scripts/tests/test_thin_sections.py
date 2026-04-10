"""Tests for thin_sections.py — bottom-up section merging."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from thin_sections import thin_sections


def _make_index(entries):
    return {"meta": {"entry_count": len(entries)}, "entries": entries}


class TestThinSections:
    def test_merges_small_into_sibling(self):
        index = _make_index([
            {"id": "src:api.md", "title": "API", "summary": "API docs", "tier": "file"},
            {"id": "src:api.md#methods", "title": "Methods", "summary": "Method documentation content here " * 80,
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [10, 50], "keywords": ["methods"]},
            {"id": "src:api.md#params", "title": "Parameters", "summary": "Short",
             "tier": "section", "parent": "src:api.md", "heading_level": 2,
             "line_range": [51, 55], "keywords": ["params"]},
        ])
        result = thin_sections(index, min_tokens=100)
        section_ids = [e["id"] for e in result["entries"] if e.get("tier") == "section"]
        assert "src:api.md#params" not in section_ids
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
        assert index == original
        assert result["sections_before"] >= 1
