"""Tests for chunk.py — deterministic document chunking.

Unit tests (no external deps):
  - Markdown strategy boundary detection
  - Transcript strategy boundary detection
  - Paragraph strategy boundary detection
  - Overlap handling
  - Edge cases (empty file, single line, file smaller than target)
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMarkdownStrategy:
    """Markdown chunking: headings (100), blank lines (20), list items (10)."""

    def test_splits_on_headings(self):
        from chunk import chunk_text

        text = "\n".join([
            "# Introduction",
            "First paragraph of intro.",
            "Second paragraph of intro.",
            "",
            "## Getting Started",
            "Content for getting started section.",
            "More content here with details.",
            "",
            "## Advanced Usage",
            "Advanced content goes here.",
            "Even more advanced content.",
        ])
        chunks = chunk_text(text, strategy="markdown", target_tokens=20, overlap_tokens=0)
        assert len(chunks) >= 2
        assert "text" in chunks[0]
        assert "line_range" in chunks[0]
        assert "chunk_index" in chunks[0]
        assert chunks[0]["chunk_index"] == 0
        assert chunks[1]["chunk_index"] == 1

    def test_respects_target_size(self):
        from chunk import chunk_text

        lines = [f"Line {i} with some content to fill space." for i in range(100)]
        text = "\n".join(lines)
        chunks = chunk_text(text, strategy="markdown", target_tokens=50, overlap_tokens=0)
        for c in chunks:
            word_count = len(c["text"].split())
            assert word_count < 150, f"Chunk too large: {word_count} words"

    def test_overlap_produces_shared_content(self):
        from chunk import chunk_text

        lines = []
        for i in range(5):
            lines.append(f"## Section {i}")
            lines.extend([f"Content line {i}-{j}." for j in range(10)])
            lines.append("")
        text = "\n".join(lines)
        chunks = chunk_text(text, strategy="markdown", target_tokens=30, overlap_tokens=10)
        if len(chunks) >= 2:
            assert chunks[1].get("overlap_prev", False) is True

    def test_small_file_single_chunk(self):
        from chunk import chunk_text

        text = "Just a small file.\nWith two lines."
        chunks = chunk_text(text, strategy="markdown", target_tokens=900, overlap_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["line_range"] == [1, 2]

    def test_empty_file_returns_empty(self):
        from chunk import chunk_text

        chunks = chunk_text("", strategy="markdown", target_tokens=900, overlap_tokens=100)
        assert chunks == []


class TestTranscriptStrategy:
    """Transcript chunking: speaker turns (80), timestamps (50), blank lines (20)."""

    def test_splits_on_speaker_turns(self):
        from chunk import chunk_text

        text = "\n".join([
            "Alice: Hello everyone, let's get started with the meeting.",
            "Alice: First item on the agenda is the Q3 review.",
            "",
            "Bob: Thanks Alice. The numbers look good this quarter.",
            "Bob: Revenue is up 15% compared to last quarter.",
            "",
            "Charlie: I have some concerns about the infrastructure costs.",
            "Charlie: We need to discuss the cloud spending.",
        ])
        chunks = chunk_text(text, strategy="transcript", target_tokens=20, overlap_tokens=0)
        assert len(chunks) >= 2

    def test_splits_on_timestamps(self):
        from chunk import chunk_text

        text = "\n".join([
            "[00:00:00] Meeting started",
            "Discussion about project timeline.",
            "More discussion here.",
            "",
            "[00:15:00] Moving to next topic",
            "Budget review discussion.",
            "More budget details.",
            "",
            "[00:30:00] Action items",
            "List of things to do.",
        ])
        chunks = chunk_text(text, strategy="transcript", target_tokens=20, overlap_tokens=0)
        assert len(chunks) >= 2


class TestParagraphStrategy:
    """Paragraph chunking: double newlines (50), single newlines (10)."""

    def test_splits_on_double_newlines(self):
        from chunk import chunk_text

        paragraphs = []
        for i in range(10):
            paragraphs.append(f"Paragraph {i} with enough content to matter. " * 5)
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, strategy="paragraph", target_tokens=50, overlap_tokens=0)
        assert len(chunks) >= 2


class TestCodeStrategy:
    """Code chunking: function/class boundaries (100), blank lines (20)."""

    def test_splits_on_function_definitions(self):
        from chunk import chunk_text

        text = "\n".join([
            "def hello():",
            "    print('hello')",
            "    print('world')",
            "",
            "def goodbye():",
            "    print('goodbye')",
            "    print('world')",
            "",
            "class MyClass:",
            "    def method(self):",
            "        pass",
        ])
        chunks = chunk_text(text, strategy="code", target_tokens=10, overlap_tokens=0)
        assert len(chunks) >= 2


class TestLineRanges:
    """Verify line_range accuracy across all strategies."""

    def test_line_ranges_are_contiguous(self):
        from chunk import chunk_text

        lines = [f"Line {i}" for i in range(50)]
        text = "\n".join(lines)
        chunks = chunk_text(text, strategy="paragraph", target_tokens=20, overlap_tokens=0)

        for i in range(len(chunks) - 1):
            current_end = chunks[i]["line_range"][1]
            next_start = chunks[i + 1]["line_range"][0]
            assert next_start <= current_end + 1

    def test_line_ranges_cover_entire_file(self):
        from chunk import chunk_text

        lines = [f"Line {i}" for i in range(50)]
        text = "\n".join(lines)
        chunks = chunk_text(text, strategy="paragraph", target_tokens=20, overlap_tokens=0)

        assert chunks[0]["line_range"][0] == 1
        assert chunks[-1]["line_range"][1] == 50


class TestCLI:
    """Test command-line interface."""

    def test_cli_json_output(self, tmp_path):
        import subprocess

        doc = tmp_path / "test.md"
        doc.write_text("# Title\n\nSome content.\n\n## Section\n\nMore content.\n")

        result = subprocess.run(
            [sys.executable, "lib/corpus/scripts/chunk.py",
             str(doc), "--strategy", "markdown",
             "--target-tokens", "10", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "text" in data[0]
        assert "line_range" in data[0]

    def test_cli_missing_file(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "lib/corpus/scripts/chunk.py",
             "/nonexistent/file.md", "--strategy", "markdown"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2
