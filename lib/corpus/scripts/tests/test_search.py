"""Tests for search.py — querying Lance embedding datasets.

Unit tests: error handling, argument parsing
Integration tests: end-to-end search with real embeddings
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = "lib/corpus/scripts/search.py"
EMBED_SCRIPT = "lib/corpus/scripts/embed.py"


# --- Fixtures ---


@pytest.fixture
def sample_index_yaml(tmp_path):
    """Create index.yaml with semantically distinct entries for search testing."""
    content = """
entries:
  - id: "test:cooking.md"
    source: "test"
    title: "Italian Cooking"
    summary: "Recipes for pasta, pizza, and risotto"
    tags: [cooking, italian, recipes]
  - id: "test:performance.md"
    source: "test"
    title: "Query Optimization"
    summary: "Speed up database queries with indexing and caching"
    tags: [performance, database, optimization]
  - id: "test:deploy.md"
    source: "test"
    title: "Cloud Deployment"
    summary: "Deploy applications to AWS, GCP, and Azure"
    tags: [deployment, cloud, infrastructure]
  - id: "test:testing.md"
    source: "test"
    title: "Unit Testing"
    summary: "Write reliable tests with pytest and mocking"
    tags: [testing, pytest, quality]

meta:
  generated_at: "2026-03-27T10:00:00Z"
  entry_count: 4
"""
    path = tmp_path / "index.yaml"
    path.write_text(content)
    return path


def deps_available():
    try:
        import fastembed  # noqa: F401
        import lancedb  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.fixture
def embedded_dataset(sample_index_yaml, tmp_path):
    """Build a Lance dataset from sample data. Requires fastembed + lancedb."""
    output = tmp_path / "index-embeddings.lance"
    result = subprocess.run(
        [sys.executable, EMBED_SCRIPT, str(sample_index_yaml), str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Failed to build: {result.stderr}"
    return output


# --- Unit Tests (no deps required) ---


class TestErrorHandling:

    def test_missing_dataset(self):
        """Exit code 2 when dataset doesn't exist."""
        result = subprocess.run(
            [sys.executable, SCRIPT, "/nonexistent/dataset.lance", "test query"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "not found" in result.stderr

    def test_help_flag(self):
        """--help prints usage and exits 0."""
        result = subprocess.run(
            [sys.executable, SCRIPT, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Search embeddings" in result.stdout


# --- Integration Tests (require fastembed + lancedb) ---


@pytest.mark.skipif(not deps_available(), reason="fastembed/lancedb not installed")
class TestSearchPipeline:

    def test_basic_search_returns_results(self, embedded_dataset):
        """Search returns ranked results in tab-separated format."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset), "how to optimize queries"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0

        # Each line: score<tab>id
        score, entry_id = lines[0].split("\t")
        assert 0 < float(score) <= 1.0
        assert ":" in entry_id  # IDs have source:path format

    def test_json_output(self, embedded_dataset):
        """--json returns valid JSON array."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "database performance", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert isinstance(results, list)
        assert len(results) > 0
        assert "id" in results[0]
        assert "score" in results[0]

    def test_semantic_relevance(self, embedded_dataset):
        """Top result for a performance query should be the performance entry."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "speed up slow queries", "--json"],
            capture_output=True,
            text=True,
        )
        results = json.loads(result.stdout)
        top_id = results[0]["id"]
        assert top_id == "test:performance.md", (
            f"Expected performance entry as top result, got {top_id}"
        )

    def test_top_k_limits_results(self, embedded_dataset):
        """--top-k limits number of results."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "anything", "--top-k", "2", "--json"],
            capture_output=True,
            text=True,
        )
        results = json.loads(result.stdout)
        assert len(results) <= 2

    def test_where_filter_on_tags(self, embedded_dataset):
        """--where with tag filter narrows results."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "how to do things",
             "--where", "array_has_any(tags, ['cooking'])",
             "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        # Should only return the cooking entry
        for r in results:
            assert r["id"] == "test:cooking.md", (
                f"Filter should restrict to cooking, got {r['id']}"
            )

    def test_where_filter_on_title(self, embedded_dataset):
        """--where with title LIKE filter works."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "general question",
             "--where", "title LIKE '%Deploy%'",
             "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) > 0
        assert results[0]["id"] == "test:deploy.md"

    def test_scores_are_sorted_descending(self, embedded_dataset):
        """Results should be sorted by score, highest first."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "testing code quality", "--json"],
            capture_output=True,
            text=True,
        )
        results = json.loads(result.stdout)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Scores not sorted descending: {scores}"
        )

    def test_scores_never_negative(self, embedded_dataset):
        """Scores are capped at 0.0, never negative."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "completely unrelated gibberish xyzzy", "--json"],
            capture_output=True,
            text=True,
        )
        results = json.loads(result.stdout)
        for r in results:
            assert r["score"] >= 0.0, f"Negative score: {r['score']}"

    def test_select_returns_extra_columns(self, embedded_dataset):
        """--select with --json returns requested columns."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "database performance",
             "--select", "concepts,title", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) > 0
        assert "title" in results[0]
        assert "concepts" in results[0]

    def test_select_ignored_without_json(self, embedded_dataset):
        """--select without --json produces normal tab output."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "anything", "--select", "title"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert "\t" in lines[0]
        parts = lines[0].split("\t")
        assert len(parts) == 2  # score + id only

    def test_table_parameter_uses_named_table(self, embedded_dataset):
        """--table selects a specific table within the Lance database."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "database performance", "--table", "embeddings", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) > 0

    def test_table_parameter_missing_table_exits_2(self, embedded_dataset):
        """--table with nonexistent table name exits 2."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(embedded_dataset),
             "query", "--table", "nonexistent"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2
        assert "could not open" in result.stderr.lower()


class TestHybridSearch:
    """Tests for --hybrid mode (FTS + vector + RRF)."""

    @pytest.fixture
    def chunk_dataset(self, tmp_path):
        """Build a Lance dataset with chunk_text column for hybrid search testing."""
        import lancedb
        import pyarrow as pa
        from fastembed import TextEmbedding

        db = lancedb.connect(str(tmp_path / "chunks.lance"))
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        records = [
            {"id": "src:file.md#chunk-0", "parent": "src:file.md", "source": "src",
             "chunk_text": "Python is a great programming language for data science and machine learning.",
             "chunk_index": 0},
            {"id": "src:file.md#chunk-1", "parent": "src:file.md", "source": "src",
             "chunk_text": "Italian cooking involves pasta, pizza, olive oil and fresh tomatoes.",
             "chunk_index": 1},
            {"id": "src:other.md#chunk-0", "parent": "src:other.md", "source": "src",
             "chunk_text": "Cloud deployment on AWS requires configuring EC2 instances and load balancers.",
             "chunk_index": 0},
        ]

        texts = [r["chunk_text"] for r in records]
        embeddings = list(model.embed(texts))

        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("parent", pa.string()),
            pa.field("source", pa.string()),
            pa.field("chunk_text", pa.string()),
            pa.field("chunk_index", pa.int64()),
            pa.field("vector", pa.list_(pa.float32(), 384)),
        ])

        for rec, emb in zip(records, embeddings):
            rec["vector"] = emb.tolist()

        tbl = db.create_table("chunks", data=pa.Table.from_pylist(records, schema=schema))
        tbl.create_fts_index("chunk_text", replace=True)

        meta_schema = pa.schema([pa.field("key", pa.string()), pa.field("value", pa.string())])
        meta_records = [
            {"key": "model", "value": "BAAI/bge-small-en-v1.5"},
            {"key": "dimensions", "value": "384"},
        ]
        db.create_table("_meta", data=pa.Table.from_pylist(meta_records, schema=meta_schema))

        return tmp_path / "chunks.lance"

    @pytest.mark.skipif(not deps_available(), reason="fastembed/lancedb not installed")
    def test_hybrid_search_returns_results(self, chunk_dataset):
        """--hybrid with --table chunks returns results using FTS+vector."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(chunk_dataset),
             "python data science", "--table", "chunks",
             "--hybrid", "--text-column", "chunk_text", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert len(results) > 0
        assert results[0]["id"] == "src:file.md#chunk-0"

    @pytest.mark.skipif(not deps_available(), reason="fastembed/lancedb not installed")
    def test_hybrid_returns_extra_columns(self, chunk_dataset):
        """--hybrid with --select returns requested columns."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(chunk_dataset),
             "deploy cloud AWS", "--table", "chunks",
             "--hybrid", "--text-column", "chunk_text",
             "--select", "parent,chunk_text", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert "parent" in results[0]
        assert "chunk_text" in results[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
