"""Tests for verify_entries.py — entry content verification data prep."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from verify_entries import extract_previews


@pytest.fixture
def sample_index(tmp_path):
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
                assert word_count <= 30

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
