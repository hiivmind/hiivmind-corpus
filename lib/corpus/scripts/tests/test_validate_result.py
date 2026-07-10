"""Essential tests for validate_result.py — headless result contract validation."""
import subprocess
import sys

SCRIPT = "lib/corpus/scripts/validate_result.py"

VALID_REFRESH = """\
contract_version: 1
kind: refresh
corpus: lancedb
run_at: "2026-07-09T00:00:00Z"
sources:
  - id: lancedb-docs
    type: git
    status: updated
    old_sha: abc1234
    new_sha: def5678
    files_changed: 12
index_changes:
  added: 3
  modified: 8
  removed: 1
  stale_entries: ["lancedb-docs:guides/new.md"]
embeddings: deferred
errors: []
"""

VALID_ENRICH = """\
contract_version: 1
kind: enrich
corpus: lancedb
run_at: "2026-07-09T01:00:00Z"
enriched: 11
skipped: 0
concepts_assigned: 9
new_concept_candidates: []
verification:
  sampled: 10
  failed: 0
  drift_entries: []
embeddings: updated
errors: []
"""


VALID_MIGRATE = """\
contract_version: 1
kind: migrate
corpus: flyio
run_at: "2026-07-09T02:00:00Z"
entries_migrated: 142
entries_skipped:
  - id: "flyio:old/moved.md"
    reason: file-missing
sections: ["getting-started", "machines"]
strategy: tiered
id_parity: true
embeddings: skipped
errors: []
"""


VALID_STATUS = """\
contract_version: 1
kind: status
corpus: lancedb
run_at: "2026-07-09T03:00:00Z"
index_format: v2
sources:
  - id: lancedb-docs
    type: git
    freshness: behind
stale_entries: 4
embeddings_lag: 12
refresh_needed: true
errors: []
"""


VALID_GRAPH_VALIDATE = """\
contract_version: 1
kind: graph-validate
corpus: lancedb
run_at: "2026-07-09T04:00:00Z"
concepts: 30
relationships: 42
issues:
  - severity: warning
    rule: orphan-concept
    detail: "concept 'io' has no entries"
valid: true
errors: []
"""


def run_validate(tmp_path, content, kind):
    f = tmp_path / "result.yaml"
    f.write_text(content)
    return subprocess.run(
        [sys.executable, SCRIPT, str(f), "--kind", kind],
        capture_output=True, text=True,
    )


def test_valid_refresh_passes(tmp_path):
    r = run_validate(tmp_path, VALID_REFRESH, "refresh")
    assert r.returncode == 0, r.stderr


def test_valid_enrich_passes(tmp_path):
    r = run_validate(tmp_path, VALID_ENRICH, "enrich")
    assert r.returncode == 0, r.stderr


def test_valid_migrate_passes(tmp_path):
    r = run_validate(tmp_path, VALID_MIGRATE, "migrate")
    assert r.returncode == 0, r.stderr


def test_valid_status_result(tmp_path):
    r = run_validate(tmp_path, VALID_STATUS, "status")
    assert r.returncode == 0, r.stderr


def test_status_null_embeddings_lag_ok(tmp_path):
    content = VALID_STATUS.replace("embeddings_lag: 12", "embeddings_lag: null")
    r = run_validate(tmp_path, content, "status")
    assert r.returncode == 0, r.stderr


def test_valid_graph_validate_result(tmp_path):
    r = run_validate(tmp_path, VALID_GRAPH_VALIDATE, "graph-validate")
    assert r.returncode == 0, r.stderr


def test_refresh_optional_embeddings_lag_ok(tmp_path):
    content = VALID_REFRESH.replace("embeddings: deferred", "embeddings: deferred\nembeddings_lag: 5")
    r = run_validate(tmp_path, content, "refresh")
    assert r.returncode == 0, r.stderr


def test_invalid_result_fails(tmp_path):
    broken = VALID_REFRESH.replace("status: updated", "status: banana")
    r = run_validate(tmp_path, broken, "refresh")
    assert r.returncode == 1
    assert "status" in r.stderr
