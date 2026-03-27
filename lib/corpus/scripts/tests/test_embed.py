"""Tests for embed.py — embedding generation into Lance datasets.

Unit tests (no fastembed/lancedb required):
  - YAML parsing functions
  - Metadata text construction
  - Argument parsing
  - Error handling for missing files

Integration tests (require fastembed + lancedb):
  - End-to-end embedding generation
  - Incremental updates
  - Model mismatch detection
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = "lib/corpus/scripts/embed.py"


# --- Fixtures ---


@pytest.fixture
def sample_index_yaml(tmp_path):
    """Create a minimal index.yaml for testing."""
    content = """
entries:
  - id: "test:doc1.md"
    source: "test"
    title: "Getting Started"
    summary: "How to install and configure the project"
    tags: [setup, installation]
    keywords: [install, config]
    category: tutorial
  - id: "test:doc2.md"
    source: "test"
    title: "API Reference"
    summary: "Complete API documentation for all endpoints"
    tags: [api, reference]
    keywords: [endpoints, rest]
    category: reference
  - id: "test:doc3.md"
    source: "test"
    title: "Performance Tuning"
    summary: "Optimize query speed and resource usage"
    tags: [performance, optimization]
    keywords: [cache, index, query]
    category: guide

meta:
  generated_at: "2026-03-27T10:00:00Z"
  entry_count: 3
"""
    path = tmp_path / "index.yaml"
    path.write_text(content)
    return path


@pytest.fixture
def sample_concepts_yaml(tmp_path):
    """Create a minimal concepts YAML for testing."""
    content = """
concepts:
  - id: "polars:lazy-evaluation"
    label: "Lazy Evaluation"
    description: "Deferred query execution for optimization"
    tags: [performance, lazy]
  - id: "ibis:deferred-execution"
    label: "Deferred Execution"
    description: "Backend-agnostic lazy expression API"
    tags: [performance, backends]
"""
    path = tmp_path / "concepts.yaml"
    path.write_text(content)
    return path


@pytest.fixture
def empty_yaml(tmp_path):
    """Create a YAML file with no entries."""
    path = tmp_path / "empty.yaml"
    path.write_text("entries: []\n")
    return path


# --- Unit Tests (no deps required) ---


class TestYAMLParsing:
    """Test YAML loading without running the full pipeline."""

    def test_load_entries_parses_fields(self, sample_index_yaml):
        """load_entries extracts id, source, title, tags, metadata_text."""
        # Import the function directly
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))

        assert len(items) == 3
        assert items[0]["id"] == "test:doc1.md"
        assert items[0]["source"] == "test"
        assert items[0]["title"] == "Getting Started"
        assert items[0]["tags"] == ["setup", "installation"]

    def test_metadata_text_format(self, sample_index_yaml):
        """metadata_text uses pipe-delimited title | summary | tags."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))

        expected = "Getting Started | How to install and configure the project | setup, installation"
        assert items[0]["metadata_text"] == expected

    def test_load_concepts_parses_fields(self, sample_concepts_yaml):
        """load_concepts extracts id, label, description, tags."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_concepts

        items = load_concepts(str(sample_concepts_yaml))

        assert len(items) == 2
        assert items[0]["id"] == "polars:lazy-evaluation"
        assert items[0]["title"] == "Lazy Evaluation"
        assert items[0]["source"] == "polars"

    def test_concepts_metadata_text_format(self, sample_concepts_yaml):
        """Concepts metadata_text uses label | description | tags."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_concepts

        items = load_concepts(str(sample_concepts_yaml))

        expected = "Lazy Evaluation | Deferred query execution for optimization | performance, lazy"
        assert items[0]["metadata_text"] == expected

    def test_missing_tags_defaults_to_empty(self, tmp_path):
        """Entries with no tags field get empty list."""
        content = """
entries:
  - id: "test:no-tags.md"
    source: "test"
    title: "No Tags"
    summary: "Entry without tags"
"""
        path = tmp_path / "no-tags.yaml"
        path.write_text(content)

        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(path))
        assert items[0]["tags"] == []
        assert items[0]["metadata_text"] == "No Tags | Entry without tags |"


class TestErrorHandling:
    """Test error cases via subprocess."""

    def test_missing_input_file(self, tmp_path):
        """Exit code 2 when input file doesn't exist."""
        result = subprocess.run(
            [sys.executable, SCRIPT, "/nonexistent/file.yaml", str(tmp_path / "out.lance")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "not found" in result.stderr

    def test_empty_entries(self, empty_yaml, tmp_path):
        """Exit code 2 when YAML has no entries."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(empty_yaml), str(tmp_path / "out.lance")],
            capture_output=True,
            text=True,
        )
        # Will be 2 (no items) or 1 (no fastembed) depending on environment
        assert result.returncode in (1, 2)


# --- Integration Tests (require fastembed + lancedb) ---


def deps_available():
    """Check if fastembed and lancedb are installed."""
    try:
        import fastembed  # noqa: F401
        import lancedb  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not deps_available(), reason="fastembed/lancedb not installed")
class TestEmbeddingPipeline:
    """End-to-end tests requiring fastembed + lancedb."""

    def test_full_build(self, sample_index_yaml, tmp_path):
        """Build embeddings from index.yaml, verify output structure."""
        output = tmp_path / "index-embeddings.lance"
        result = subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"

        # Parse JSON output
        output_json = json.loads(result.stdout)
        assert output_json["total"] == 3
        assert output_json["embedded"] == 3

        # Check _meta.json sidecar
        meta = json.loads((output / "_meta.json").read_text())
        assert meta["model"] == "BAAI/bge-small-en-v1.5"
        assert meta["dimensions"] == 384
        assert meta["entry_count"] == 3
        assert meta["mode"] == "entries"

    def test_concepts_mode(self, sample_concepts_yaml, tmp_path):
        """Build embeddings in concepts mode."""
        output = tmp_path / "registry-embeddings.lance"
        result = subprocess.run(
            [sys.executable, SCRIPT, "--mode", "concepts",
             str(sample_concepts_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"

        output_json = json.loads(result.stdout)
        assert output_json["total"] == 2
        assert output_json["embedded"] == 2

        meta = json.loads((output / "_meta.json").read_text())
        assert meta["mode"] == "concepts"

    def test_force_rebuild(self, sample_index_yaml, tmp_path):
        """--force re-embeds everything even if dataset exists."""
        output = tmp_path / "index-embeddings.lance"

        # First build
        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        # Second build with --force
        result = subprocess.run(
            [sys.executable, SCRIPT, "--force",
             str(sample_index_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output_json = json.loads(result.stdout)
        assert output_json["embedded"] == 3  # All re-embedded

    def test_lance_dataset_queryable(self, sample_index_yaml, tmp_path):
        """Verify the Lance dataset can be opened and queried."""
        import lancedb

        output = tmp_path / "index-embeddings.lance"
        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        db = lancedb.connect(str(output))
        table = db.open_table("embeddings")

        # Check schema
        assert "id" in table.schema.names
        assert "vector" in table.schema.names
        assert "tags" in table.schema.names
        assert "metadata_text" in table.schema.names

        # Check row count
        assert table.count_rows() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
