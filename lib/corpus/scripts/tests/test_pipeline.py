"""Integration tests for cross-script pipelines.

Tests that scripts compose correctly when used in sequence,
as the source-scanner agent would use them.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parent.parent


class TestLargeFileSplittingPipeline:
    """detect_large_files → split_by_headings pipeline."""

    @pytest.fixture
    def source_with_large_file(self, tmp_path):
        """Create a source directory with one large file and one small file."""
        # Large file with headings (~500 words)
        large = "# API Reference\n\n"
        for i in range(15):
            large += f"## Method {i}\n\n"
            large += f"Description of method {i}. " * 20 + "\n\n"
            large += f"### Parameters\n\nParam details for method {i}. " * 10 + "\n\n"
        (tmp_path / "api.md").write_text(large)

        # Small file
        (tmp_path / "readme.md").write_text("# README\n\nShort file.\n")
        return tmp_path

    def test_detect_then_split(self, source_with_large_file):
        """detect_large_files finds the file, split_by_headings splits it."""
        # Step 1: detect large files
        r1 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "detect_large_files.py"),
             "--source-root", str(source_with_large_file), "--max-tokens", "100"],
            capture_output=True, text=True,
        )
        assert r1.returncode == 0
        large_files = json.loads(r1.stdout)
        assert len(large_files) >= 1

        # Find the api.md entry
        api_entry = [f for f in large_files if "api.md" in f["path"]]
        assert len(api_entry) == 1
        assert api_entry[0]["has_headings"] is True

        # Step 2: split the large file by headings
        api_path = source_with_large_file / api_entry[0]["path"]
        r2 = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "split_by_headings.py"),
             "--file", str(api_path), "--min-tokens", "0", "--json"],
            capture_output=True, text=True,
        )
        assert r2.returncode == 0
        sections = json.loads(r2.stdout)
        assert len(sections) >= 10  # should have many sections

        # Verify section structure
        for section in sections:
            assert "title" in section
            assert "line_start" in section
            assert "line_end" in section
            assert "anchor" in section
            assert section["line_start"] <= section["line_end"]

    def test_small_files_not_split(self, source_with_large_file):
        """Small files should not appear in detect_large_files output."""
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "detect_large_files.py"),
             "--source-root", str(source_with_large_file), "--max-tokens", "100"],
            capture_output=True, text=True,
        )
        large_files = json.loads(r.stdout)
        paths = [f["path"] for f in large_files]
        assert not any("readme" in p.lower() for p in paths)

    def test_section_line_ranges_cover_file(self, source_with_large_file):
        """Sections from split_by_headings should not have gaps."""
        api_path = source_with_large_file / "api.md"
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "split_by_headings.py"),
             "--file", str(api_path), "--min-level", "2", "--min-tokens", "0", "--json"],
            capture_output=True, text=True,
        )
        sections = json.loads(r.stdout)
        if len(sections) >= 2:
            for i in range(len(sections) - 1):
                # Next section starts at or after current section ends
                assert sections[i + 1]["line_start"] == sections[i]["line_end"] + 1


class TestNavDetectToScanPipeline:
    """detect_nav → file scanning (simulated)."""

    def test_nav_hierarchy_paths_are_resolvable(self, tmp_path):
        """Paths in nav hierarchy should point to real files."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            "nav:\n"
            "  - Home: index.md\n"
            "  - Guide: guide/start.md\n"
        )
        (tmp_path / "index.md").write_text("# Home")
        guide = tmp_path / "guide"
        guide.mkdir()
        (guide / "start.md").write_text("# Guide")

        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "detect_nav.py"),
             "--source-root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        result = json.loads(r.stdout)
        assert result["found"] is True

        # All resolved paths should exist
        for entry in result["hierarchy"]:
            if entry.get("path"):
                assert (tmp_path / entry["path"]).exists()
