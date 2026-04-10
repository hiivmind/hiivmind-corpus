"""Tests for detect_large_files.py — large file detection."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from detect_large_files import detect_large_files


@pytest.fixture
def docs_dir(tmp_path):
    (tmp_path / "small.md").write_text("# Small\n\nJust a small file.\n")
    large_content = "# Large File\n\n"
    for i in range(20):
        large_content += f"## Section {i}\n\n" + f"Content for section {i}. " * 10 + "\n\n"
    (tmp_path / "large_with_headings.md").write_text(large_content)
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
