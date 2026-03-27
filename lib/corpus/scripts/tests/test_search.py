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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
