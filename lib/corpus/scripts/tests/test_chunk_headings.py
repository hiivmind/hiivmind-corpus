"""Tests for chunk.py headings strategy."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeadingsStrategy:
    def test_sections_within_target_are_single_chunks(self):
        from chunk import chunk_text
        text = "## Section One\n\nShort content.\n\n## Section Two\n\nAnother short section.\n"
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
        for c in chunks:
            assert c["heading_context"] == "## Big Section"

    def test_no_overlap_at_heading_boundaries(self):
        from chunk import chunk_text
        text = "## First\n\nContent one.\n\n## Second\n\nContent two.\n"
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

    def test_no_headings_falls_back(self):
        from chunk import chunk_text
        text = "Just plain text.\n" * 50
        chunks = chunk_text(text, strategy="headings", target_tokens=20, overlap_tokens=5)
        assert len(chunks) >= 1
        for c in chunks:
            assert "heading_context" in c
