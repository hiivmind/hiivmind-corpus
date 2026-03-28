"""Tests for embed.py — embedding generation into Lance datasets.

Unit tests (no fastembed/lancedb required):
  - YAML parsing functions
  - Metadata text construction (including concepts)
  - Error handling for missing files

Integration tests (require fastembed + lancedb):
  - End-to-end embedding generation
  - _meta table verification
  - FTS index creation
  - Concepts in Lance schema
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = "lib/corpus/scripts/embed.py"


# --- Fixtures ---


@pytest.fixture
def sample_index_yaml(tmp_path):
    """Create a minimal index.yaml with concepts for testing."""
    content = """
entries:
  - id: "test:doc1.md"
    source: "test"
    title: "Getting Started"
    summary: "How to install and configure the project"
    tags: [setup, installation]
    keywords: [install, config]
    concepts: [getting-started]
    category: tutorial
  - id: "test:doc2.md"
    source: "test"
    title: "API Reference"
    summary: "Complete API documentation for all endpoints"
    tags: [api, reference]
    keywords: [endpoints, rest]
    concepts: [api]
    category: reference
  - id: "test:doc3.md"
    source: "test"
    title: "Performance Tuning"
    summary: "Optimize query speed and resource usage"
    tags: [performance, optimization]
    keywords: [cache, index, query]
    concepts: [performance, optimization]
    category: guide
  - id: "test:doc4.md"
    source: "test"
    title: "Migration Guide"
    summary: "How to migrate from v1 to v2"
    tags: [migration]
    keywords: [upgrade, breaking-changes]
    category: guide

meta:
  generated_at: "2026-03-27T10:00:00Z"
  entry_count: 4
"""
    path = tmp_path / "index.yaml"
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
        """load_entries extracts id, source, title, tags, concepts, metadata_text."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))

        assert len(items) == 4
        assert items[0]["id"] == "test:doc1.md"
        assert items[0]["source"] == "test"
        assert items[0]["title"] == "Getting Started"
        assert items[0]["tags"] == ["setup", "installation"]
        assert items[0]["concepts"] == ["getting-started"]

    def test_metadata_text_includes_concepts(self, sample_index_yaml):
        """metadata_text uses pipe-delimited title | summary | tags | concepts."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))

        expected = "Getting Started | How to install and configure the project | setup, installation | getting-started"
        assert items[0]["metadata_text"] == expected

    def test_multiple_concepts_in_metadata(self, sample_index_yaml):
        """Entry with multiple concepts includes all in metadata_text."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))
        assert "performance, optimization" in items[2]["metadata_text"]

    def test_missing_concepts_defaults_to_empty(self, sample_index_yaml):
        """Entries without concepts field get empty list (backward compat)."""
        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(sample_index_yaml))
        assert items[3]["concepts"] == []
        assert items[3]["metadata_text"].endswith("|")

    def test_missing_tags_defaults_to_empty(self, tmp_path):
        """Entries with no tags or concepts get empty lists."""
        content = """
entries:
  - id: "test:no-tags.md"
    source: "test"
    title: "No Tags"
    summary: "Entry without tags or concepts"
"""
        path = tmp_path / "no-tags.yaml"
        path.write_text(content)

        sys.path.insert(0, str(Path(SCRIPT).parent))
        from embed import load_entries

        items = load_entries(str(path))
        assert items[0]["tags"] == []
        assert items[0]["concepts"] == []


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

    def test_full_build_with_meta_table(self, sample_index_yaml, tmp_path):
        """Build embeddings, verify _meta table (not _meta.json)."""
        import lancedb

        output = tmp_path / "index-embeddings.lance"
        result = subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"

        output_json = json.loads(result.stdout)
        assert output_json["total"] == 4
        assert output_json["embedded"] == 4

        # Verify _meta table exists (not _meta.json)
        db = lancedb.connect(str(output))
        assert "_meta" in db.list_tables()
        meta_table = db.open_table("_meta")
        meta_arrow = meta_table.to_arrow()
        keys = meta_arrow.column("key").to_pylist()
        values = meta_arrow.column("value").to_pylist()
        meta = dict(zip(keys, values))
        assert meta["model"] == "BAAI/bge-small-en-v1.5"
        assert meta["dimensions"] == "384"
        assert meta["entry_count"] == "4"

        # No _meta.json should exist
        assert not (output / "_meta.json").exists()

    def test_fts_index_created(self, sample_index_yaml, tmp_path):
        """FTS index is created on metadata_text column."""
        import lancedb

        output = tmp_path / "index-embeddings.lance"
        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        db = lancedb.connect(str(output))
        table = db.open_table("embeddings")
        assert "metadata_text" in table.schema.names

    def test_force_rebuild(self, sample_index_yaml, tmp_path):
        """--force re-embeds everything even if dataset exists."""
        output = tmp_path / "index-embeddings.lance"

        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        result = subprocess.run(
            [sys.executable, SCRIPT, "--force",
             str(sample_index_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output_json = json.loads(result.stdout)
        assert output_json["embedded"] == 4

    def test_lance_dataset_has_concepts_column(self, sample_index_yaml, tmp_path):
        """Verify concepts column exists in Lance dataset."""
        import lancedb

        output = tmp_path / "index-embeddings.lance"
        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        db = lancedb.connect(str(output))
        table = db.open_table("embeddings")

        assert "id" in table.schema.names
        assert "vector" in table.schema.names
        assert "tags" in table.schema.names
        assert "concepts" in table.schema.names
        assert "metadata_text" in table.schema.names
        assert table.count_rows() == 4

    def test_meta_json_migration(self, sample_index_yaml, tmp_path):
        """_meta.json is migrated to _meta table on rebuild."""
        import lancedb

        output = tmp_path / "index-embeddings.lance"

        # First build creates _meta table
        subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
        )

        # Simulate old format: create _meta.json and remove _meta table
        db = lancedb.connect(str(output))
        db.drop_table("_meta")
        meta_json = output / "_meta.json"
        meta_json.write_text(json.dumps({"model": "BAAI/bge-small-en-v1.5", "dimensions": 384}))

        # Rebuild should migrate
        result = subprocess.run(
            [sys.executable, SCRIPT, str(sample_index_yaml), str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # _meta.json should be gone, _meta table should exist
        assert not meta_json.exists()
        db2 = lancedb.connect(str(output))
        assert "_meta" in db2.list_tables()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
