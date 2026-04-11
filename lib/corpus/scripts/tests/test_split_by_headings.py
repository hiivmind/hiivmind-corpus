"""Tests for split_by_headings.py — heading-based file splitting."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from split_by_headings import split_by_headings


class TestSplitByHeadings:
    def test_basic_split(self):
        text = (
            "# Title\n\nIntro paragraph.\n\n"
            "## Section One\n\nContent for section one.\nMore content here.\n\n"
            "## Section Two\n\nContent for section two.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert len(result) == 2
        assert result[0]["title"] == "Section One"
        assert result[1]["title"] == "Section Two"

    def test_line_ranges(self):
        text = "## First\nLine 2\nLine 3\n\n## Second\nLine 6\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result[0]["line_start"] == 1
        assert result[0]["line_end"] == 4
        assert result[1]["line_start"] == 5
        assert result[1]["line_end"] == 6

    def test_anchor_generation(self):
        text = "## Getting Started Guide\nContent.\n\n## API (v2) Reference!\nContent.\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result[0]["anchor"] == "getting-started-guide"
        assert result[1]["anchor"] == "api-v2-reference"

    def test_skips_code_block_headings(self):
        text = (
            "## Real Heading\nContent.\n\n"
            "```markdown\n## Fake Heading Inside Code\n```\n\n"
            "## Another Real Heading\nContent.\n"
        )
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert len(result) == 2
        titles = [r["title"] for r in result]
        assert "Fake Heading Inside Code" not in titles

    def test_respects_level_range(self):
        text = "# H1\nContent.\n## H2\nContent.\n### H3\nContent.\n#### H4\nContent.\n##### H5\nContent.\n"
        result = split_by_headings(text, min_level=2, max_level=3, min_tokens=0)
        levels = [r["level"] for r in result]
        assert all(2 <= l <= 3 for l in levels)

    def test_merges_small_sections(self):
        text = "## Big Section\n" + "Word " * 200 + "\n\n## Tiny\nOne line.\n\n## Another Big\n" + "Word " * 200 + "\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=100)
        titles = [r["title"] for r in result]
        assert "Tiny" not in titles

    def test_no_headings_returns_empty(self):
        text = "Just a plain text file.\nWith no headings at all.\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert result == []

    def test_text_preview_included(self):
        text = "## Section\nFirst line of content.\nSecond line.\n"
        result = split_by_headings(text, min_level=2, max_level=4, min_tokens=0)
        assert "text_preview" in result[0]
        assert "First line" in result[0]["text_preview"]


class TestSplitByHeadingsCLI:
    def test_cli_json_output(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("## Section\nContent.\n")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "split_by_headings.py"),
             "--file", str(md), "--json", "--min-tokens", "0"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) == 1

    def test_cli_missing_file(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "split_by_headings.py"),
             "--file", "/nonexistent.md", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2

    def test_cli_tab_output(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("## First\nContent.\n\n## Second\nMore.\n")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "split_by_headings.py"),
             "--file", str(md), "--min-tokens", "0"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "first" in result.stdout  # anchor
        assert "second" in result.stdout
