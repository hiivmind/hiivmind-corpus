"""Tests for PyYAML regex fallback parsers.

Tests the regex-based parsers directly to ensure they work when PyYAML
is unavailable. These parse the same formats as the YAML parsers but
using regex.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from detect_nav import _parse_mkdocs_nav_regex
from verify_entries import _load_index_regex


class TestMkdocsNavRegexFallback:
    """Test _parse_mkdocs_nav_regex directly."""

    def test_flat_nav(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "site_name: Test\n"
            "nav:\n"
            "  - Home: index.md\n"
            "  - Guide: guide.md\n"
            "  - API: api/reference.md\n"
        )
        result = _parse_mkdocs_nav_regex(mkdocs, tmp_path)
        assert len(result) == 3
        assert result[0]["title"] == "Home"
        assert result[0]["path"] == "index.md"
        assert result[1]["title"] == "Guide"
        assert result[2]["path"] == "api/reference.md"

    def test_stops_at_next_top_level_key(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Home: index.md\n"
            "  - About: about.md\n"
            "theme:\n"
            "  name: material\n"
        )
        result = _parse_mkdocs_nav_regex(mkdocs, tmp_path)
        assert len(result) == 2  # should not parse theme section

    def test_empty_nav(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("nav:\ntheme:\n  name: material\n")
        result = _parse_mkdocs_nav_regex(mkdocs, tmp_path)
        assert result == []

    def test_no_nav_key(self, tmp_path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("site_name: Test\ntheme:\n  name: material\n")
        result = _parse_mkdocs_nav_regex(mkdocs, tmp_path)
        assert result == []


class TestIndexRegexFallback:
    """Test _load_index_regex directly."""

    def test_parses_entries(self, tmp_path):
        index = tmp_path / "index.yaml"
        index.write_text(
            "meta:\n"
            "  entry_count: 2\n"
            "entries:\n"
            "  - id: 'src:docs/intro.md'\n"
            "    title: Introduction\n"
            "    summary: Overview of the project\n"
            "    source: docs/intro.md\n"
            "  - id: 'src:docs/guide.md'\n"
            "    title: Guide\n"
            "    summary: How to use the tool\n"
            "    source: docs/guide.md\n"
        )
        result = _load_index_regex(str(index))
        assert len(result) == 2
        assert result[0]["id"] == "src:docs/intro.md"
        assert result[0]["title"] == "Introduction"
        assert result[0]["source"] == "docs/intro.md"
        assert result[1]["id"] == "src:docs/guide.md"

    def test_strips_quotes(self, tmp_path):
        index = tmp_path / "index.yaml"
        index.write_text(
            "entries:\n"
            "  - id: \"src:file.md\"\n"
            "    title: 'Quoted Title'\n"
        )
        result = _load_index_regex(str(index))
        assert result[0]["id"] == "src:file.md"
        assert result[0]["title"] == "Quoted Title"

    def test_empty_file(self, tmp_path):
        index = tmp_path / "index.yaml"
        index.write_text("")
        result = _load_index_regex(str(index))
        assert result == []

    def test_no_entries(self, tmp_path):
        index = tmp_path / "index.yaml"
        index.write_text("meta:\n  entry_count: 0\n")
        result = _load_index_regex(str(index))
        assert result == []
