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


def test_invalid_result_fails(tmp_path):
    broken = VALID_REFRESH.replace("status: updated", "status: banana")
    r = run_validate(tmp_path, broken, "refresh")
    assert r.returncode == 1
    assert "status" in r.stderr
