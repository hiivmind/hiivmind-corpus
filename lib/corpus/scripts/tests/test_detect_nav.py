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
        assert len(result) == 2
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

        result = parse_mkdocs_nav(mkdocs, tmp_path)
        assert len(result) == 2


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
        assert len(result) == 2
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

        result = detect_nav(str(tmp_path))
        assert result["coverage"]["nav_entries"] == 2
        assert result["coverage"]["files_resolved"] == 1
        assert result["coverage"]["files_missing"] == 1
        assert result["coverage"]["total_md_files"] == 2
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
