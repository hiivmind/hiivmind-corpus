# Wave 1 Headless Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement backlog items 04 (Python packaging + detect.py bug + CI), 02 (headless result contract as a file + shared index-update pattern), and 01 (headless enrichment skill that closes the stale-entry loop) from `docs/backlog/`.

**Architecture:** Three phases, each independently shippable, ordered so later phases build on earlier contracts. Phase A makes the Python scripts self-contained (PEP 723 + uv) and adds CI. Phase B replaces prose-parsed `---headless-result` blocks with a written, versioned `refresh-result.yaml` file validated by a new script, and extracts the duplicated refresh index-update algorithm into one pattern doc. Phase C adds `hiivmind-corpus-enrich-headless`, a new skill that re-scans stale entries, assigns concepts from graph.yaml, verifies summaries, and re-embeds — then wires it into the scheduler tasks.

**Tech Stack:** Python ≥3.10 (stdlib + pyyaml/fastembed/lancedb/pyarrow/pymupdf), uv with PEP 723 inline script metadata, pytest, GitHub Actions, Claude Code SKILL.md prose skills.

## Global Constraints

- Python floor: `requires-python = ">=3.10"` everywhere (matches existing scheduler pyprojects; scripts already use `int | None` syntax).
- Embedding model: `BAAI/bge-small-en-v1.5`, 384 dims — after Task 2 this is defined ONCE in `lib/corpus/scripts/constants.py`.
- Result contract: `contract_version: 1`. Result files (`refresh-result.yaml`, `enrich-result.yaml`) are written to the corpus root and MUST be gitignored in corpus repos.
- Source statuses in the contract: `current | updated | failed | skipped-manual`.
- `detect.py` must remain **stdlib-only** (its job is probing the environment; giving it heavy deps under `uv run` would defeat detection).
- Skill/doc conventions (from CLAUDE.md): kebab-case names, `${CLAUDE_PLUGIN_ROOT}` for paths, every skill keeps a Related Skills/Reference section, new cross-cutting features get a row in CLAUDE.md's "Cross-Cutting Concerns" table.
- Tests are invoked from the repo root (`/Users/nathanielramm/git/hiivmind/hiivmind-corpus`); test files call scripts via `subprocess` with repo-root-relative paths or import them after `sys.path.insert`.
- Commit after every task. Conventional-commit subjects. End commit messages with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- The scheduler repo at `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler` is touched only in Task 11 (its own git repo — commit there separately).
- Scope correction vs backlog 04: the scheduler repo has **no** stale root `pyproject.toml` (already removed) — skip that subtask. Per-task pyproject deletion is deferred to backlog item 05.

---

## Phase A — Backlog 04: Packaging, detect.py fix, constants, CI

### Task 1: Fix `detect.py` — honor `FASTEMBED_CACHE_PATH`, uv-aware availability

**Files:**
- Modify: `lib/corpus/scripts/detect.py`
- Test: `lib/corpus/scripts/tests/test_detect.py` (append new test class)

**Interfaces:**
- Produces: `detect.py` stdout contract used by all skills — one of `ready | no-model | not-installed` (unchanged values, revised semantics):
  - Model-cache check now uses `os.environ.get("FASTEMBED_CACHE_PATH")` before falling back to `~/.cache/fastembed`.
  - If `uv` is on PATH, import-probing is skipped entirely (deps are guaranteed at run time by `uv run` + PEP 723): output is `ready`/`no-model` from the cache check alone, exit 0.
  - If `uv` is absent, legacy behavior: import-probe fastembed/lancedb, `not-installed` + exit 1 on failure.

- [ ] **Step 1: Write the failing tests**

Append to `lib/corpus/scripts/tests/test_detect.py`:

```python
class TestCachePathAndUv:
    """FASTEMBED_CACHE_PATH override and uv-aware availability."""

    def _run(self, env_overrides, tmp_path):
        import os
        env = os.environ.copy()
        env.update(env_overrides)
        return subprocess.run(
            [sys.executable, "lib/corpus/scripts/detect.py"],
            capture_output=True, text=True, env=env,
        )

    def test_custom_cache_path_with_model_reports_ready(self, tmp_path):
        """A bge-small model dir under FASTEMBED_CACHE_PATH must be found."""
        cache = tmp_path / "custom-cache"
        (cache / "models--qdrant--bge-small-en-v1.5").mkdir(parents=True)
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "ready"

    def test_custom_cache_path_empty_reports_no_model(self, tmp_path):
        cache = tmp_path / "empty-cache"
        cache.mkdir()
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "no-model"

    def test_uv_present_never_reports_not_installed(self, tmp_path, monkeypatch):
        """With uv on PATH, availability is guaranteed by `uv run`, so the
        import probe must be skipped even in an env without fastembed."""
        import shutil
        if shutil.which("uv") is None:
            pytest.skip("uv not installed on this host")
        cache = tmp_path / "empty-cache"
        cache.mkdir()
        # Run under the system python even if fastembed IS importable here;
        # the assertion is only that exit code is 0 and output is a model status.
        result = self._run({"FASTEMBED_CACHE_PATH": str(cache)}, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() in ("ready", "no-model")
```

Note: the first two tests fail against current code whenever the real `~/.cache/fastembed` disagrees with the custom path (current code ignores the env var entirely). If the dev machine's real cache has the model, `test_custom_cache_path_empty_reports_no_model` is the one that demonstrates the bug.

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_detect.py -v`
Expected: `test_custom_cache_path_empty_reports_no_model` FAILS (stdout is `ready` from the real home cache, or `not-installed`); pre-existing tests PASS.

- [ ] **Step 3: Implement**

Replace the body of `main()` in `lib/corpus/scripts/detect.py`:

```python
import os
import shutil
import sys
from pathlib import Path

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _install_hint() -> str:
    """Return the install command, preferring uv if available."""
    pkg = "fastembed lancedb pyyaml"
    if shutil.which("uv"):
        return f"uv pip install {pkg}"
    return f"pip install {pkg}"


def _model_cache_status() -> str:
    """Return 'ready' if the bge-small model is in the fastembed cache, else 'no-model'.

    Honors FASTEMBED_CACHE_PATH (used by scheduler runtimes) before the
    default ~/.cache/fastembed location.
    """
    try:
        env_path = os.environ.get("FASTEMBED_CACHE_PATH")
        cache_path = Path(env_path) if env_path else Path.home() / ".cache" / "fastembed"
        model_dirs = list(cache_path.glob("*bge-small*")) if cache_path.exists() else []
        return "ready" if model_dirs else "no-model"
    except Exception:
        return "no-model"


def main():
    # With uv available, dependency availability is guaranteed at run time:
    # embed.py/search.py carry PEP 723 metadata and run via `uv run`.
    # Only the model-cache state matters.
    if shutil.which("uv"):
        print(_model_cache_status())
        sys.exit(0)

    # Legacy path (no uv): probe the ambient interpreter.
    try:
        import fastembed  # noqa: F401
    except ImportError:
        print("not-installed")
        print(f"Install with: {_install_hint()}", file=sys.stderr)
        sys.exit(1)

    try:
        import lancedb  # noqa: F401
    except ImportError:
        print("not-installed")
        print(f"Install with: {_install_hint()}", file=sys.stderr)
        sys.exit(1)

    print(_model_cache_status())
    sys.exit(0)
```

Keep the existing `if __name__ == "__main__":` wrapper unchanged. Move `import shutil` and `import os` to module top; delete the now-inlined cache check from the old `main()`.

Check whether existing tests in `test_detect.py` assert `not-installed` behavior in a way the uv-short-circuit breaks (they run on a host where uv exists). If any existing test asserts exit 1 / `not-installed` unconditionally, update it to monkeypatch `PATH` to hide uv (pass `env={"PATH": "/usr/bin:/bin"}` minus uv's dir) — the legacy path must still be testable.

- [ ] **Step 4: Run the full detect test file**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_detect.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/detect.py lib/corpus/scripts/tests/test_detect.py
git commit -m "fix(detect): honor FASTEMBED_CACHE_PATH and skip import-probe when uv present"
```

---

### Task 2: Single source of truth for embedding constants

**Files:**
- Create: `lib/corpus/scripts/constants.py`
- Modify: `lib/corpus/scripts/detect.py`, `lib/corpus/scripts/embed.py`, `lib/corpus/scripts/search.py`
- Test: `lib/corpus/scripts/tests/test_constants.py`

**Interfaces:**
- Produces: `constants.py` module with `MODEL_NAME: str`, `DIMENSIONS: int`, `TABLE_NAME: str`, `CHUNKS_TABLE_NAME: str`, `META_TABLE: str`, `PASSAGE_PREFIX: str`, `QUERY_PREFIX: str`, `VECTOR_INDEX_THRESHOLD: int`. Imported by sibling scripts using the existing script-dir sys.path pattern (same as `token_utils`).

- [ ] **Step 1: Write the failing test**

Create `lib/corpus/scripts/tests/test_constants.py`:

```python
"""Constants must be defined once and re-exported by consumer scripts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_constants_module_values():
    import constants
    assert constants.MODEL_NAME == "BAAI/bge-small-en-v1.5"
    assert constants.DIMENSIONS == 384
    assert constants.TABLE_NAME == "embeddings"
    assert constants.META_TABLE == "_meta"


def test_scripts_reference_shared_constants():
    import constants
    import detect
    import embed
    import search
    assert detect.MODEL_NAME is constants.MODEL_NAME
    assert embed.MODEL_NAME is constants.MODEL_NAME
    assert search.MODEL_NAME is constants.MODEL_NAME
    assert embed.DIMENSIONS == constants.DIMENSIONS
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_constants.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'constants'`.

- [ ] **Step 3: Implement**

Create `lib/corpus/scripts/constants.py`:

```python
"""Shared constants for the embedding pipeline.

Single source of truth for the model identity and Lance table layout.
detect.py, embed.py, and search.py import from here — do not redefine
these values in individual scripts.
"""

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
TABLE_NAME = "embeddings"
CHUNKS_TABLE_NAME = "chunks"
META_TABLE = "_meta"
PASSAGE_PREFIX = "passage: "  # bge-small asymmetric retrieval prefix for documents
QUERY_PREFIX = "query: "  # bge-small asymmetric retrieval prefix for queries
VECTOR_INDEX_THRESHOLD = 500  # Create IVF_PQ index above this entry count
```

In `detect.py`, `embed.py`, and `search.py`, replace each locally defined constant that exists in `constants.py` with an import. Use the explicit sys.path insert (matches `verify_entries.py`) so the scripts work when invoked from any cwd:

```python
sys.path.insert(0, str(Path(__file__).parent))
from constants import (
    MODEL_NAME, DIMENSIONS, TABLE_NAME, CHUNKS_TABLE_NAME,
    META_TABLE, PASSAGE_PREFIX, QUERY_PREFIX, VECTOR_INDEX_THRESHOLD,
)
```

Import only the names each script actually uses (detect.py needs just `MODEL_NAME`; check search.py for which of the table/prefix constants it defines locally today and swap exactly those). Delete the local definitions.

- [ ] **Step 4: Run the embedding-related test files**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_constants.py lib/corpus/scripts/tests/test_detect.py lib/corpus/scripts/tests/test_embed.py lib/corpus/scripts/tests/test_search.py -v`
Expected: ALL PASS (integration tests may skip if fastembed absent — skips are fine).

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/scripts/constants.py lib/corpus/scripts/detect.py lib/corpus/scripts/embed.py lib/corpus/scripts/search.py lib/corpus/scripts/tests/test_constants.py
git commit -m "refactor(scripts): single constants module for model/table identity"
```

---

### Task 3: PEP 723 inline metadata + `uv run` invocation docs

**Files:**
- Modify: `lib/corpus/scripts/embed.py`, `search.py`, `chunk.py`, `detect.py`, `detect_nav.py`, `detect_large_files.py`, `split_by_headings.py`, `thin_sections.py`, `verify_entries.py`, `lib/corpus/tools/split_pdf.py`
- Modify: `lib/corpus/patterns/tool-detection.md`, `lib/corpus/patterns/embeddings.md`, `lib/corpus/patterns/chunking.md`, plus every SKILL.md that invokes `python3 ${CLAUDE_PLUGIN_ROOT}/...` (find with grep in Step 3)
- Test: manual verification commands (Step 4) — no new pytest file

**Interfaces:**
- Produces: every script runnable as `uv run <script.py>` on a clean machine with only uv installed. Canonical invocation in all docs: `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/<script>.py`, with `python3` + manual-install fallback documented once in `tool-detection.md`.

- [ ] **Step 1: Add PEP 723 blocks**

Immediately after the shebang line of each script, insert the block for its dependency set. Local sibling imports (`token_utils`, `constants`) are not dependencies — they resolve via the script directory.

`embed.py`:
```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastembed>=0.4.0", "lancedb>=0.20.0", "pyarrow>=15.0.0", "pyyaml>=6.0"]
# ///
```

`search.py`:
```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastembed>=0.4.0", "lancedb>=0.20.0", "pyarrow>=15.0.0"]
# ///
```

`detect_nav.py`, `thin_sections.py`, `verify_entries.py`:
```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
```

`detect.py`, `chunk.py`, `detect_large_files.py`, `split_by_headings.py` (stdlib-only — the empty list is deliberate and load-bearing for detect.py, see Global Constraints):
```python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
```

`lib/corpus/tools/split_pdf.py`:
```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24.0"]
# ///
```

- [ ] **Step 2: Update `tool-detection.md` with the canonical invocation policy**

Add a section (place it near the existing Python detection material):

```markdown
## Python Script Invocation (uv-first)

All Python scripts under `lib/corpus/scripts/` and `lib/corpus/tools/` carry
PEP 723 inline metadata (`# /// script` blocks) declaring their dependencies.

**Preferred (uv available):**

    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/

uv creates/reuses a cached ephemeral environment with the script's declared
dependencies — no venv setup, no pip install step, works identically on
macOS/Linux/Windows.

**Fallback (no uv):**

    python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py ...

requires the dependencies to be installed in the ambient interpreter:
`pip install fastembed lancedb pyarrow pyyaml` (embedding scripts) /
`pip install pymupdf` (PDF tools). detect.py reports `not-installed` on
this path when imports fail.

Detect once per session: `command -v uv` → use `uv run` for every script
invocation in this session; otherwise use `python3` and respect detect.py.
```

- [ ] **Step 3: Sweep all invocation sites**

Find every call site:

```bash
grep -rn 'python3 \${CLAUDE_PLUGIN_ROOT}\|python3 \${PLUGIN_ROOT}' skills/ lib/ agents/ commands/ templates/
```

For each hit, replace `python3 ${...}/lib/...` with `uv run ${CLAUDE_PLUGIN_ROOT}/lib/...` and, at the FIRST invocation in each SKILL.md only, append the note: `(fallback: python3 — see patterns/tool-detection.md § "Python Script Invocation")`. Fix `${PLUGIN_ROOT}` inconsistencies to `${CLAUDE_PLUGIN_ROOT}` while there (build SKILL.md Phase 2 uses `${PLUGIN_ROOT}`). Update the pip-install prompt in build Phase 7 step 4b to offer `uv` phrasing: `Requires uv (recommended, zero-setup) or pip install fastembed lancedb pyyaml (~260MB)`.

- [ ] **Step 4: Verify scripts run under uv**

```bash
uv run lib/corpus/scripts/detect.py
uv run lib/corpus/scripts/chunk.py --help
uv run lib/corpus/scripts/verify_entries.py --help
uv run lib/corpus/scripts/embed.py --help
uv run lib/corpus/scripts/search.py --help 2>&1 | head -3
uv run lib/corpus/tools/split_pdf.py --help
grep -rn 'python3 \${' skills/ lib/ agents/ commands/ | grep -v 'fallback'
```
Expected: each `--help` prints usage and exits 0 (first embed/search run may take a moment resolving deps); the final grep returns no un-annotated `python3` call sites.

- [ ] **Step 5: Run the full test suite (regression)**

Run: `python3 -m pytest lib/corpus/scripts/tests/ -q`
Expected: PASS/SKIP as before — PEP 723 comments are inert under plain python3.

- [ ] **Step 6: Commit**

```bash
git add lib/corpus/scripts/ lib/corpus/tools/ lib/corpus/patterns/ skills/ agents/ commands/ templates/
git commit -m "feat(scripts): PEP 723 inline deps; uv-first invocation across skills and patterns"
```

---

### Task 4: Dev dependency group + GitHub Actions CI

**Files:**
- Create: `pyproject.toml` (repo root)
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `uv run --group dev pytest` as the single local + CI test entrypoint.

- [ ] **Step 1: Create root `pyproject.toml`**

```toml
[project]
name = "hiivmind-corpus-dev"
version = "0.0.0"
description = "Dev/test environment for hiivmind-corpus plugin scripts (the scripts themselves are PEP 723 self-contained)"
requires-python = ">=3.10"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pyyaml>=6.0",
    "fastembed>=0.4.0",
    "lancedb>=0.20.0",
    "pyarrow>=15.0.0",
    "pymupdf>=1.24.0",
]

[tool.pytest.ini_options]
testpaths = ["lib/corpus/scripts/tests", "lib/corpus/tools"]
```

- [ ] **Step 2: Verify locally**

Run: `uv run --group dev pytest -q`
Expected: full suite passes, including the integration tests that previously skipped (fastembed/lancedb now present; first run downloads the ~45MB model). Note the runtime — if model download makes this slow, that's expected once, then cached.

- [ ] **Step 3: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Cache fastembed model
        uses: actions/cache@v4
        with:
          path: ~/.cache/fastembed
          key: fastembed-bge-small-en-v1.5

      - name: Run tests
        run: uv run --group dev pytest -q

      - name: Smoke-test PEP 723 scripts
        run: |
          uv run lib/corpus/scripts/detect.py
          uv run lib/corpus/scripts/chunk.py --help
          uv run lib/corpus/scripts/verify_entries.py --help
```

- [ ] **Step 4: Add `.venv` and `uv.lock` handling to `.gitignore`**

Check the repo `.gitignore`; ensure it contains `.venv/`. Commit `uv.lock` (reproducible dev env) — do NOT gitignore it.

- [ ] **Step 5: Commit and verify CI**

```bash
git add pyproject.toml .github/workflows/ci.yml .gitignore uv.lock
git commit -m "ci: pytest + uv dev group + PEP 723 smoke tests on GitHub Actions"
```

After the branch is pushed (end of phase), confirm the workflow goes green before merging.

---

## Phase B — Backlog 02: Result contract as a file; shared index-update pattern

### Task 5: `validate_result.py` + `patterns/headless-contract.md`

**Files:**
- Create: `lib/corpus/scripts/validate_result.py`
- Create: `lib/corpus/patterns/headless-contract.md`
- Test: `lib/corpus/scripts/tests/test_validate_result.py`

**Interfaces:**
- Produces: `validate_result.py <file> --kind refresh|enrich` → exit 0 (valid) / 1 (invalid, human-readable errors on stderr) / 2 (unreadable file). Used by CI, tests, and the scheduler orchestrator.
- Produces: the contract schema (below) consumed by Tasks 6, 9, 11.

**The contract (contract_version 1):**

`refresh-result.yaml` (written by refresh-headless):
```yaml
contract_version: 1
kind: refresh
corpus: <name from config>            # str, required
run_at: <ISO 8601 timestamp>          # str, required
sources:                              # list, required (may be empty)
  - id: <source id>                   # str, required
    type: <source type>               # str, required
    status: current | updated | failed | skipped-manual   # required
    old_sha: <str or null>
    new_sha: <str or null>
    files_changed: <int>
index_changes:                        # required
  added: <int>
  modified: <int>
  removed: <int>
  stale_entries: [<entry id>, ...]    # list of str
embeddings: updated | skipped | no-model | not-installed | deferred   # required
errors: [<str>, ...]                  # list, required (may be empty)
```

`enrich-result.yaml` (written by enrich-headless, Task 9):
```yaml
contract_version: 1
kind: enrich
corpus: <name>                        # str, required
run_at: <ISO 8601>                    # str, required
enriched: <int>                       # entries re-scanned and un-staled, required
skipped: <int>                        # stale entries not enrichable (e.g. source file unreadable)
concepts_assigned: <int>              # entries that received concept membership
new_concept_candidates:               # list (may be empty) — needs human review
  - label: <str>
    evidence: [<entry id>, ...]
verification:                         # required
  sampled: <int>
  failed: <int>
  drift_entries: [<entry id>, ...]
embeddings: updated | skipped | no-model | not-installed   # required
errors: [<str>, ...]                  # required
```

- [ ] **Step 1: Write the failing tests**

Create `lib/corpus/scripts/tests/test_validate_result.py`:

```python
"""Tests for validate_result.py — headless result contract validation."""
import subprocess
import sys
from pathlib import Path

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


def test_missing_required_key_fails(tmp_path):
    broken = VALID_REFRESH.replace("index_changes:", "index_changes_oops:")
    r = run_validate(tmp_path, broken, "refresh")
    assert r.returncode == 1
    assert "index_changes" in r.stderr


def test_bad_source_status_fails(tmp_path):
    broken = VALID_REFRESH.replace("status: updated", "status: banana")
    r = run_validate(tmp_path, broken, "refresh")
    assert r.returncode == 1
    assert "status" in r.stderr


def test_wrong_kind_fails(tmp_path):
    r = run_validate(tmp_path, VALID_REFRESH, "enrich")
    assert r.returncode == 1
    assert "kind" in r.stderr


def test_unsupported_contract_version_fails(tmp_path):
    broken = VALID_REFRESH.replace("contract_version: 1", "contract_version: 99")
    r = run_validate(tmp_path, broken, "refresh")
    assert r.returncode == 1
    assert "contract_version" in r.stderr


def test_missing_file_exits_2(tmp_path):
    r = subprocess.run(
        [sys.executable, SCRIPT, str(tmp_path / "nope.yaml"), "--kind", "refresh"],
        capture_output=True, text=True,
    )
    assert r.returncode == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_validate_result.py -v`
Expected: all FAIL (script missing).

- [ ] **Step 3: Implement `validate_result.py`**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate a headless result file against the corpus result contract.

Usage: validate_result.py <result.yaml> --kind refresh|enrich

Exit codes:
  0 - valid
  1 - invalid (errors on stderr, one per line)
  2 - file missing or unparseable
"""
import argparse
import sys
from pathlib import Path

SUPPORTED_VERSIONS = {1}
SOURCE_STATUSES = {"current", "updated", "failed", "skipped-manual"}
REFRESH_EMBEDDINGS = {"updated", "skipped", "no-model", "not-installed", "deferred"}
ENRICH_EMBEDDINGS = {"updated", "skipped", "no-model", "not-installed"}


def _err(errors, msg):
    errors.append(msg)


def _require(data, key, types, errors, ctx=""):
    label = f"{ctx}{key}"
    if key not in data:
        _err(errors, f"missing required key: {label}")
        return None
    if not isinstance(data[key], types):
        _err(errors, f"wrong type for {label}: expected {types}, got {type(data[key]).__name__}")
        return None
    return data[key]


def validate(data: dict, kind: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["result is not a mapping"]

    version = _require(data, "contract_version", int, errors)
    if version is not None and version not in SUPPORTED_VERSIONS:
        _err(errors, f"unsupported contract_version: {version}")

    got_kind = _require(data, "kind", str, errors)
    if got_kind is not None and got_kind != kind:
        _err(errors, f"kind mismatch: expected {kind}, got {got_kind}")

    _require(data, "corpus", str, errors)
    _require(data, "run_at", str, errors)
    _require(data, "errors", list, errors)

    if kind == "refresh":
        sources = _require(data, "sources", list, errors)
        for i, s in enumerate(sources or []):
            if not isinstance(s, dict):
                _err(errors, f"sources[{i}] is not a mapping")
                continue
            _require(s, "id", str, errors, ctx=f"sources[{i}].")
            _require(s, "type", str, errors, ctx=f"sources[{i}].")
            status = _require(s, "status", str, errors, ctx=f"sources[{i}].")
            if status is not None and status not in SOURCE_STATUSES:
                _err(errors, f"sources[{i}].status invalid: {status}")
        ic = _require(data, "index_changes", dict, errors)
        if ic is not None:
            for k in ("added", "modified", "removed"):
                _require(ic, k, int, errors, ctx="index_changes.")
            _require(ic, "stale_entries", list, errors, ctx="index_changes.")
        emb = _require(data, "embeddings", str, errors)
        if emb is not None and emb not in REFRESH_EMBEDDINGS:
            _err(errors, f"embeddings invalid: {emb}")

    elif kind == "enrich":
        for k in ("enriched", "skipped", "concepts_assigned"):
            _require(data, k, int, errors)
        _require(data, "new_concept_candidates", list, errors)
        ver = _require(data, "verification", dict, errors)
        if ver is not None:
            _require(ver, "sampled", int, errors, ctx="verification.")
            _require(ver, "failed", int, errors, ctx="verification.")
            _require(ver, "drift_entries", list, errors, ctx="verification.")
        emb = _require(data, "embeddings", str, errors)
        if emb is not None and emb not in ENRICH_EMBEDDINGS:
            _err(errors, f"embeddings invalid: {emb}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a headless result file")
    parser.add_argument("file", help="Path to result YAML file")
    parser.add_argument("--kind", required=True, choices=["refresh", "enrich"])
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    import yaml
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        print(f"error: unparseable YAML: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate(data, args.kind)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_validate_result.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Write `lib/corpus/patterns/headless-contract.md`**

Content: the two schema blocks from this task's Interfaces section verbatim, plus:

```markdown
# Pattern: Headless Result Contract

Headless skills communicate with orchestrators through **result files written
to disk**, not by prose parsing. The printed `---headless-result` block is
retained for human-readable logs only — orchestrators MUST read the file.

## File locations

| Skill | File | Default path |
|-------|------|--------------|
| hiivmind-corpus-refresh-headless | refresh-result.yaml | `{corpus_root}/refresh-result.yaml` |
| hiivmind-corpus-enrich-headless | enrich-result.yaml | `{corpus_root}/enrich-result.yaml` |

Result files are transient run artifacts: the skill ensures both filenames are
listed in the corpus `.gitignore` (appending if missing) before writing.
Orchestrators should treat the file as consumed after parsing; a subsequent
run overwrites it.

## Versioning

`contract_version` is a required integer. Current version: **1**. Consumers
MUST reject files with versions they don't support (validate_result.py does).
Additive optional fields do not bump the version; renamed/removed/retyped
fields do.

## Validation

    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py refresh-result.yaml --kind refresh

Orchestrators should validate before consuming and treat exit 1/2 as a failed
run (report, do not commit).

## Schemas

[refresh schema block]

[enrich schema block]

## Source status semantics

- `current` — upstream unchanged, nothing done
- `updated` — upstream changes pulled and applied to the index
- `failed` — this source errored; details in `errors[]`; other sources proceed
- `skipped-manual` — source type has no automatic change detection (e.g. `local`);
  requires an interactive refresh. Surfaced so automation cannot silently
  never-refresh a corpus.

## embeddings: deferred

`deferred` means stale/placeholder entries exist and embedding was
intentionally left to the enrichment stage — embedding placeholder summaries
("Pending re-scan") would poison semantic search. Orchestrators seeing
`deferred` MUST run enrich-headless before merging.
```

- [ ] **Step 6: Commit**

```bash
git add lib/corpus/scripts/validate_result.py lib/corpus/scripts/tests/test_validate_result.py lib/corpus/patterns/headless-contract.md
git commit -m "feat(contract): versioned headless result files + validate_result.py"
```

---

### Task 6: refresh-headless writes the result file; `skipped-manual` for local sources

**Files:**
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md`

**Interfaces:**
- Consumes: contract + file location from Task 5.
- Produces: refresh-headless behavior that Task 11's scheduler tasks rely on: writes `{corpus_root}/refresh-result.yaml`, ensures `.gitignore` coverage, sets `embeddings: deferred` when stale entries exist, reports local sources as `skipped-manual`.

- [ ] **Step 1: Update the frontmatter**

Add to `inputs:` in the YAML frontmatter:

```yaml
  - name: result_path
    type: string
    required: false
    description: Where to write refresh-result.yaml (defaults to {corpus_root}/refresh-result.yaml)
```

Change the `outputs:` description to: `Structured result written to result_path and echoed as a log block — see patterns/headless-contract.md`.

- [ ] **Step 2: Update Phase 2's freshness table**

In the Phase 2 table, change the `local` row from `Always "current" (no auto-detection)` to `Always "skipped-manual" (no auto-detection — needs interactive refresh)`. In the State block comment, extend status values to `current | updated | failed | skipped-manual`.

- [ ] **Step 3: Update Phase 5 (Embeddings)**

Replace the phase body with:

```markdown
Skip if `index-embeddings.lance/` doesn't exist, or if no entries were added/modified.

If `computed.index_changes.stale_entries` is non-empty, set
`computed.embedding_status = "deferred"` and skip embedding entirely —
stale entries have placeholder or outdated summaries, and embedding them
would poison semantic search. The enrichment stage
(`hiivmind-corpus-enrich-headless`) re-embeds after regenerating summaries.

Otherwise run `detect.py`: if "ready", run
`uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/`
(incremental upsert). If "no-model", skip — never trigger a download during
automated refresh. If not installed, skip.
```

- [ ] **Step 4: Replace the Output Contract section**

Replace the whole `## Output Contract` section with:

```markdown
## Output Contract

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

1. Resolve `result_path` (input, default `{corpus_root}/refresh-result.yaml`).
2. Ensure the corpus `.gitignore` contains lines `refresh-result.yaml` and
   `enrich-result.yaml` — append them if missing (create `.gitignore` if absent).
3. Write the result file with the Write tool:

```yaml
contract_version: 1
kind: refresh
corpus: {name from config}
run_at: {ISO timestamp}
sources:
  - id: {source id}
    type: {source type}
    status: current | updated | failed | skipped-manual
    old_sha: {short sha or null}
    new_sha: {short sha or null}
    files_changed: {count}
index_changes:
  added: {n}
  modified: {n}
  removed: {n}
  stale_entries:
    - {entry id}
embeddings: updated | skipped | no-model | not-installed | deferred
errors:
  - {description}
```

4. Echo the same YAML between `---headless-result` and `---` markers as the
   final output — this is a human-readable log convenience only; pipelines
   MUST read the file, not parse prose.

Write the file even on partial failure or early exit (all-current, validation
abort): a missing result file is indistinguishable from a crashed run.
```

Also update the Error Handling table's abort row: `Abort: write result file with error, emit log block, exit`.

- [ ] **Step 5: Add pattern reference**

Add to the Pattern Documentation list: `- **Result contract:** ${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

- [ ] **Step 6: Verify and commit**

Verify: `grep -n "contract_version\|skipped-manual\|deferred\|result_path" skills/hiivmind-corpus-refresh-headless/SKILL.md` shows all four concepts present.

```bash
git add skills/hiivmind-corpus-refresh-headless/SKILL.md
git commit -m "feat(refresh-headless): write versioned result file; skipped-manual locals; defer embeddings when stale"
```

---

### Task 7: Extract shared index-update algorithm to `patterns/index-updating.md`

**Files:**
- Create: `lib/corpus/patterns/index-updating.md`
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md` (Phase 6), `skills/hiivmind-corpus-refresh-headless/SKILL.md` (Phase 4)
- Modify: `CLAUDE.md` (pattern table + cross-cutting concerns)

**Interfaces:**
- Produces: one pattern doc owning the v1/v2 index-update rules; both refresh skills reference it. Enrich-headless (Task 9) also references it for config-metadata updates.

- [ ] **Step 1: Create `lib/corpus/patterns/index-updating.md`**

Assemble from the CURRENT text of the two skills (they are verbatim-identical today — copy from `refresh-headless` Phase 4 as the master). Structure:

```markdown
# Pattern: Applying Source Changes to the Index

Single source of truth for how refresh flows (interactive and headless) apply
detected file changes (A/M/D) to the index. Both refresh skills reference
this pattern — do not duplicate these rules into skill files.

## Inputs
[updated_sources with files_changed lists; index format v1|v2; tiered or single]

## v2 format (index.yaml)
[UPDATE_INDEX_V2 pseudocode — verbatim from refresh-headless Phase 4:
 M → stale:true + stale_since, preserve summary/tags/keywords/concepts/links_from;
 A → placeholder entry with stale:true, category unknown, summary "Pending re-scan";
 D → remove entry + remove from graph.yaml if referenced;
 update meta.generated_at/entry_count; re-render via render-index.sh]
[Notes: links_from and concepts preserved — full build / graph skill recompute them.
 Stale entries are resolved by hiivmind-corpus-enrich-headless or the next build.]

## v1 format (index.md, single or tiered)
[Per-change rules verbatim: D removes entry line; M no edit needed; A extracts
 real title/intro from .source/ before writing — full pseudocode block;
 Liquid template-variable stripping BEFORE truncation; placement into existing
 ## sections by path structure; never stage under "New in This Refresh".]
[Tiered: map changes to affected index-*.md sub-indexes, update each, update
 main index.md summary section.]

## Updating config.yaml after index changes (both formats)
[advance last_indexed_at; last_commit_sha for git/self/generated-docs;
 manifest.last_hash for llms-txt; set index.last_updated_at; save]

## Embedding update (v2 with index-embeddings.lance/ present)
[detect.py gate; incremental embed.py run; no-model → skip, never download
 during refresh; headless flows defer entirely when stale entries exist —
 see headless-contract.md § "embeddings: deferred"]
```

Copy the pseudocode blocks EXACTLY as they exist in `refresh-headless/SKILL.md` today (they contain the v1.5.2 fixes — real-title extraction, template-variable stripping, existing-section placement).

- [ ] **Step 2: Slim both skills to references**

In `skills/hiivmind-corpus-refresh-headless/SKILL.md`, replace the bodies of "### v2 format (index.yaml)", "### v1 format (index.md)", and "### Update config.yaml (both formats)" in Phase 4 with:

```markdown
Apply every change per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-updating.md`:
v2 → stale-marking rules (M/A/D); v1 → direct entry edits with real titles
extracted from `.source/` (single or tiered). Then update config metadata per
the same pattern. Track counts into `computed.index_changes`.
```

In `skills/hiivmind-corpus-refresh/SKILL.md`, replace the equivalent Phase 6 subsections ("### v2 format (index.yaml exists)", the v1 per-change rules block, "### Update config metadata (both formats)", "### Embedding Update (if applicable)") with the same reference plus the interactive-only additions that must stay in the skill: the preview-and-confirm steps (`Show preview of changes to user`, `If auto_approve or user confirms → save`).

- [ ] **Step 3: Verify single-sourcing**

```bash
grep -rln "Never stage entries under a temporary heading" skills/ lib/
grep -rln "Pending re-scan" skills/ lib/
```
Expected: first grep → only `lib/corpus/patterns/index-updating.md`. Second grep → `index-updating.md` (and `headless-contract.md`/`enrich` docs if they mention it), but NOT both refresh skills.

- [ ] **Step 4: Update CLAUDE.md**

- Add `index-updating.md` to the pattern library table: `| index-updating.md | Applying A/M/D changes to v1/v2 indexes | Stale marking, entry rules, config metadata |`
- Add cross-cutting row: `| Index updating | refresh, refresh-headless, enrich (headless) | Single algorithm in patterns/index-updating.md — never duplicate into skills |`
- Add cross-cutting row: `| Headless result contract | refresh-headless, enrich-headless, scheduler tasks | contract_version, result files, validate_result.py |`

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/patterns/index-updating.md skills/hiivmind-corpus-refresh/SKILL.md skills/hiivmind-corpus-refresh-headless/SKILL.md CLAUDE.md
git commit -m "refactor(patterns): extract shared index-update algorithm; de-dupe refresh skills"
```

---

## Phase C — Backlog 01: Headless enrichment

### Task 8: Fix `verify_entries.py` path resolution for the real v2 schema

**Files:**
- Modify: `lib/corpus/scripts/verify_entries.py`
- Modify: `lib/corpus/scripts/tests/test_verify_entries.py`

**Interfaces:**
- Produces: `extract_previews(index_path, source_root, token_limit=500, sample=None, entry_ids=None, config_path=None)` and CLI flag `--config <config.yaml>`. File resolution for a v2 entry `{source: <id>, path: <relpath>}` is `source_root/<id>/<docs_root>/<relpath>` (docs_root from config.yaml per source, `"."` normalized to nothing), falling back to `source_root/<id>/<relpath>`. Entries with `tier: section` are skipped. Legacy fixture shape (`source` holding a path, no `path` key) still resolves as `source_root/<source>`.

**Why:** today the script does `file_path = source_root / entry["source"]` — but in real v2 indexes `source` is the source ID (e.g. `lancedb-docs`) and the relative path lives in `path`. Against any real corpus every preview resolves to a directory and the script errors. The existing test fixture encodes the wrong schema.

- [ ] **Step 1: Rewrite the test fixture to the real v2 schema and add resolution tests**

In `test_verify_entries.py`, replace the `sample_index` fixture and add tests:

```python
@pytest.fixture
def sample_index(tmp_path):
    """Real v2 schema: source = source id, path = relative path under docs_root."""
    index_yaml = tmp_path / "index.yaml"
    index_yaml.write_text(
        "meta:\n"
        "  entry_count: 3\n"
        "entries:\n"
        "  - id: 'src:intro.md'\n"
        "    title: Introduction\n"
        "    summary: Overview of the project\n"
        "    source: src\n"
        "    path: intro.md\n"
        "  - id: 'src:guide.md'\n"
        "    title: Guide\n"
        "    summary: How to use the tool\n"
        "    source: src\n"
        "    path: guide.md\n"
        "  - id: 'src:missing.md'\n"
        "    title: Missing\n"
        "    summary: This file does not exist\n"
        "    source: src\n"
        "    path: missing.md\n"
    )
    source_root = tmp_path / ".source"
    docs = source_root / "src" / "docs"
    docs.mkdir(parents=True)
    (docs / "intro.md").write_text("# Introduction\n\nThis is the overview of the project.\n" * 10)
    (docs / "guide.md").write_text("# Guide\n\nStep by step instructions.\n" * 5)
    config = tmp_path / "config.yaml"
    config.write_text(
        "sources:\n"
        "  - id: src\n"
        "    docs_root: docs\n"
    )
    return index_yaml, source_root, config


class TestV2PathResolution:
    def test_resolves_via_docs_root_from_config(self, sample_index):
        index_yaml, source_root, config = sample_index
        result = extract_previews(
            str(index_yaml), str(source_root), token_limit=500, config_path=str(config)
        )
        existing = [r for r in result if r["content_preview"] is not None]
        assert {r["entry_id"] for r in existing} == {"src:intro.md", "src:guide.md"}
        assert "Introduction" in next(
            r for r in existing if r["entry_id"] == "src:intro.md"
        )["content_preview"]

    def test_missing_file_yields_null_preview(self, sample_index):
        index_yaml, source_root, config = sample_index
        result = extract_previews(
            str(index_yaml), str(source_root), token_limit=500, config_path=str(config)
        )
        missing = [r for r in result if r["content_preview"] is None]
        assert [r["entry_id"] for r in missing] == ["src:missing.md"]

    def test_fallback_without_config_tries_source_id_slash_path(self, tmp_path):
        """docs_root '.' case: files directly under source_root/<id>/."""
        index_yaml = tmp_path / "index.yaml"
        index_yaml.write_text(
            "entries:\n"
            "  - id: 'src:intro.md'\n"
            "    title: Introduction\n"
            "    summary: Overview\n"
            "    source: src\n"
            "    path: intro.md\n"
        )
        src = tmp_path / ".source" / "src"
        src.mkdir(parents=True)
        (src / "intro.md").write_text("# Introduction\n\ncontent here\n" * 5)
        result = extract_previews(str(index_yaml), str(tmp_path / ".source"), token_limit=500)
        assert result[0]["content_preview"] is not None

    def test_section_entries_are_skipped(self, tmp_path):
        index_yaml = tmp_path / "index.yaml"
        index_yaml.write_text(
            "entries:\n"
            "  - id: 'src:a.md'\n"
            "    title: A\n"
            "    summary: file entry\n"
            "    source: src\n"
            "    path: a.md\n"
            "  - id: 'src:a.md#part'\n"
            "    title: A part\n"
            "    summary: section entry\n"
            "    source: src\n"
            "    path: a.md\n"
            "    tier: section\n"
        )
        src = tmp_path / ".source" / "src"
        src.mkdir(parents=True)
        (src / "a.md").write_text("# A\n\ncontent\n")
        result = extract_previews(str(index_yaml), str(tmp_path / ".source"), token_limit=500)
        assert [r["entry_id"] for r in result] == ["src:a.md"]
```

Update the three existing `TestExtractPreviews` tests to unpack the new 3-tuple fixture and pass `config_path=str(config)`.

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_verify_entries.py -v`
Expected: new tests FAIL (`config_path` unexpected kwarg / previews all None).

- [ ] **Step 3: Implement**

In `verify_entries.py`:

```python
def _load_docs_roots(config_path: str | None) -> dict[str, str]:
    """Map source id -> normalized docs_root ('' when '.', missing, or root)."""
    if not config_path or not Path(config_path).exists():
        return {}
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return {}
    roots = {}
    for source in config.get("sources", []) or []:
        sid = source.get("id")
        if not sid:
            continue
        docs_root = (source.get("docs_root") or "").strip()
        roots[sid] = "" if docs_root in (".", "") else docs_root
    return roots


def _resolve_entry_file(source_root: Path, entry: dict, docs_roots: dict[str, str]) -> Path | None:
    """Resolve the on-disk file for an index entry.

    v2 schema: entry has source (id) + path (relative). Candidates in order:
      source_root/<id>/<docs_root>/<path>   (when docs_root known)
      source_root/<id>/<path>
    Legacy fixture shape (no 'path' key): source_root/<source> as a file.
    """
    source_id = entry.get("source", "")
    rel_path = entry.get("path")
    if rel_path:
        candidates = []
        docs_root = docs_roots.get(source_id)
        if docs_root:
            candidates.append(source_root / source_id / docs_root / rel_path)
        candidates.append(source_root / source_id / rel_path)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None
    legacy = source_root / source_id
    return legacy if legacy.is_file() else None
```

Update `extract_previews` signature to `(index_path, source_root, token_limit=500, sample=None, entry_ids=None, config_path=None)`. In the loop: skip entries where `entry.get("tier") == "section"` (before sampling, so samples are file entries); replace the `file_path = source / source_path` logic with `file_path = _resolve_entry_file(source, entry, docs_roots)`; set `source_path` in the output dict to `entry.get("path") or entry.get("source", "")`. Add `--config` to `parse_args` and pass through in `main()`. Update the module docstring usage line.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest lib/corpus/scripts/tests/test_verify_entries.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Sanity-check against a real corpus**

Run: `uv run lib/corpus/scripts/verify_entries.py --index /Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb/index.yaml --source-root /Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb/.source --config /Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb/config.yaml --sample 3`
Expected: JSON array of 3 entries with non-null `content_preview` (read-only — touches nothing in the corpus repo).

- [ ] **Step 6: Update call sites in skills**

In `skills/hiivmind-corpus-build/SKILL.md` (Phase 7c) and `skills/hiivmind-corpus-refresh/SKILL.md` (Post-Refresh Verification), add `--config config.yaml` to the `verify_entries.py` invocations.

- [ ] **Step 7: Commit**

```bash
git add lib/corpus/scripts/verify_entries.py lib/corpus/scripts/tests/test_verify_entries.py skills/hiivmind-corpus-build/SKILL.md skills/hiivmind-corpus-refresh/SKILL.md
git commit -m "fix(verify): resolve entry files via v2 source id + docs_root + path"
```

---

### Task 9: The `hiivmind-corpus-enrich-headless` skill

**Files:**
- Create: `skills/hiivmind-corpus-enrich-headless/SKILL.md`
- Modify: `CLAUDE.md`, `commands/hiivmind-corpus.md`, and Related Skills sections of `skills/hiivmind-corpus-refresh-headless/SKILL.md`, `skills/hiivmind-corpus-refresh/SKILL.md`, `skills/hiivmind-corpus-build/SKILL.md`, `skills/hiivmind-corpus-enhance/SKILL.md`, `skills/hiivmind-corpus-status/SKILL.md`
- Check: `.claude-plugin/plugin.json` — if it enumerates skills explicitly, add the new one; if skills are directory-discovered, no change

**Interfaces:**
- Consumes: result contract (Task 5), index-updating pattern (Task 7), fixed `verify_entries.py` (Task 8), `source-scanner` agent's "Entry Metadata Generation" output format (`agents/source-scanner.md`), `embed.py` incremental upsert.
- Produces: `enrich-result.yaml` per the Task 5 schema; index.yaml entries with `stale: false` and regenerated metadata; scheduler tasks (Task 11) invoke this skill after refresh.

- [ ] **Step 1: Write the skill**

Create `skills/hiivmind-corpus-enrich-headless/SKILL.md` with this full content:

````markdown
---
name: hiivmind-corpus-enrich-headless
description: >
  Headless (non-interactive) enrichment of stale index entries. Re-scans changed source
  files to regenerate entry metadata (title, summary, tags, keywords, category), assigns
  concepts from the existing graph.yaml, verifies summaries against content, clears stale
  flags, re-renders, and re-embeds. Run after hiivmind-corpus-refresh-headless in automated
  pipelines, or standalone to repair a corpus with accumulated stale entries. Requires a
  v2 index (index.yaml).
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
inputs:
  - name: corpus_path
    type: string
    required: false
    description: Absolute path to the corpus root (uses current working directory if not provided)
  - name: result_path
    type: string
    required: false
    description: Where to write enrich-result.yaml (defaults to {corpus_root}/enrich-result.yaml)
  - name: entry_ids
    type: array
    required: false
    description: Specific entry IDs to enrich (defaults to all entries with stale = true)
outputs:
  - name: result
    type: yaml
    description: enrich-result.yaml per patterns/headless-contract.md
---

# Corpus Enrichment (Headless)

Closes the stale-entry loop that refresh opens. Refresh marks changed entries
`stale: true` and inserts placeholder entries ("Pending re-scan"); this skill
regenerates their metadata from source content — no human decisions required,
the evidence (file content, existing metadata, graph concepts) is all local.

**v2 only.** If `index.yaml` does not exist, abort with an error in the result
file — v1 indexes embed real content at refresh time and have no stale state.

---

## State

```yaml
computed:
  corpus_root: null
  config: null
  stale_entries: []            # entries with stale=true (or entry_ids input)
  enriched: []                 # entry ids successfully regenerated
  skipped: []                  # entry ids that could not be enriched (+reason in errors)
  concepts_assigned: 0
  new_concept_candidates: []   # [{label, evidence: [entry ids]}]
  verification: {sampled: 0, failed: 0, drift_entries: []}
  embedding_status: null
  errors: []
```

---

## Phase 1: Validate

Resolve corpus root from `corpus_path` input or cwd. Abort (write result file
with error, exit) if:
- `config.yaml` missing
- `index.yaml` missing (v1 corpus — not supported; suggest migration)

Read `config.yaml` (need per-source `docs_root`) and `index.yaml`. Read
`graph.yaml` if present (concept definitions for Phase 3).

Collect target entries: entries where `stale == true`, or the `entry_ids`
input if provided. Exclude entries with `tier: section` whose parent file
entry is also targeted (the parent re-scan regenerates its sections' context;
section entries themselves keep their line_range until the next build).

If no target entries: write result with `enriched: 0` and exit.

---

## Phase 2: Re-scan Changed Files

Group target entries by source. For each entry resolve the source file:
`.source/{source_id}/{docs_root}/{path}` (normalize `docs_root: "."` to
nothing; `uploads/{source_id}/{path}` for local sources; `.cache/web/...` /
`.cache/llms-txt/...` per source type — see
`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/paths.md`).

If a file cannot be read: mark the entry id in `computed.skipped`, log to
`computed.errors`, continue.

Dispatch `source-scanner` agents (Task tool) in parallel, one per source with
targeted entries, prompt per agent:

```
Scan ONLY the following files of source '{source_id}' (type: {type}) at corpus
path '{corpus_path}': {list of relative paths}.
For each file, return entry metadata per
${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md § "Entry Metadata Generation":
path, title, summary, tags, keywords, category, content_type, size, grep_hint, headings.
Return YAML only.
```

Batch limit: at most 30 files per agent; split a source's list into multiple
agents if larger. Launch all agents in a single response.

For each returned entry, update the matching index.yaml entry in place:
- Replace: `title`, `summary`, `tags`, `keywords`, `category`, `content_type`, `size`, `grep_hint`, `headings`
- Preserve: `id`, `source`, `path`, `links_to`, `links_from`, `frontmatter`, existing `concepts`
- Set `stale: false`, `stale_since: null`, `last_indexed: now()`
- Append id to `computed.enriched`

An agent failure marks its entries skipped and logs the error; other agents
proceed.

---

## Phase 3: Concept Assignment

**Skip if:** no `graph.yaml`, or it has no concepts.

For each enriched entry with empty `concepts[]`, match against EXISTING
concept definitions only (this is evidence-based; inventing new concepts is
an interactive decision):

1. **Tag overlap:** entry `tags`/`keywords` ∩ concept `tags` — any overlap → candidate.
2. **Description match:** concept `label`/`description` terms appearing in the
   entry title or summary → candidate.
3. Assign every concept with ≥1 signal from both rules, or ≥2 tag overlaps
   from rule 1 alone. Multiple concepts per entry allowed.

Increment `computed.concepts_assigned` per entry that received at least one
concept.

Entries matching NO existing concept: group by shared directory prefix or
shared tags; groups of 3+ entries become a new-concept candidate:
`{label: <proposed from shared tag/directory>, evidence: [entry ids]}` in
`computed.new_concept_candidates`. Do NOT write these to graph.yaml — they go
in the result file for human review.

---

## Phase 4: Verification

Sample check that regenerated summaries describe actual content:

```
sample = min(len(computed.enriched), 10)
uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/verify_entries.py \
  --index index.yaml --source-root .source/ --config config.yaml \
  --entries {comma-joined sample of enriched ids}
```

For each returned preview, judge: does the summary accurately describe the
content_preview? Inaccurate → regenerate the summary directly from the
preview, count in `verification.failed`, list in `verification.drift_entries`
(after fixing). Record `verification.sampled`.

If the script fails, log to errors and continue — verification is best-effort.

---

## Phase 5: Save, Render, Embed

1. Update `index.yaml`: `meta.generated_at = now()`, recount `meta.entry_count`. Save.
2. Re-render: `bash ./render-index.sh index.yaml` (if present).
3. Embeddings — only if `index-embeddings.lance/` exists:
   - `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py`
   - "ready" → `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/`
     (incremental — re-embeds entries whose metadata text changed) → `embedding_status: updated`
   - "no-model" → `no-model` (never download during automation); "not-installed" → `not-installed`
   - Doesn't exist → `skipped`

---

## Output Contract

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

Ensure the corpus `.gitignore` lists `enrich-result.yaml` (append if missing),
then write `result_path` (default `{corpus_root}/enrich-result.yaml`):

```yaml
contract_version: 1
kind: enrich
corpus: {name from config}
run_at: {ISO timestamp}
enriched: {len(computed.enriched)}
skipped: {len(computed.skipped)}
concepts_assigned: {n}
new_concept_candidates:
  - label: {proposed label}
    evidence: [{entry ids}]
verification:
  sampled: {n}
  failed: {n}
  drift_entries: [{entry ids}]
embeddings: updated | skipped | no-model | not-installed
errors:
  - {description}
```

Echo the same YAML between `---headless-result` and `---` as a log block.
Write the file even on abort or zero-work runs.

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| No config.yaml / no index.yaml | Abort: write result with error, exit |
| Source file unreadable | Entry marked skipped, logged, continue |
| Scanner agent failed | Its entries skipped, logged, others proceed |
| Verification script failed | Logged, continue (best-effort) |
| Embed failed | `embedding_status` per detect output, error logged |

---

## Pattern Documentation

- **Result contract:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`
- **Index updating:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-updating.md`
- **Paths:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/paths.md`
- **Graph:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md`
- **Embeddings:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`
- **Index v2 schema:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-format-v2.md`

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

## Related Skills

- Headless refresh (runs before this): `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh-headless/SKILL.md`
- Interactive refresh: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Concept graph: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md`
````

- [ ] **Step 2: Register the skill everywhere the conventions require**

- `.claude-plugin/plugin.json`: read it; if it lists skills explicitly, add `hiivmind-corpus-enrich-headless`; if not, no change.
- `CLAUDE.md`: add to the Architecture tree (`skills/` listing), the Naming Convention build-skills list, the Skill Lifecycle diagram (`refresh → enrich (headless, automated)`), the Skill Dependency Chain (`refresh-headless ──► enrich-headless ──► index-embeddings.lance/`), and a Cross-Cutting Concerns row: `| Headless enrichment | refresh-headless, enrich-headless, graph, build | stale-entry resolution, concept assignment from existing graph, result contract |`.
- `commands/hiivmind-corpus.md`: add enrich-headless to the routing list with a note that it is pipeline-facing (users normally want `enhance` or `refresh`).
- Add a Related Skills line pointing to the new skill in: `refresh-headless`, `refresh`, `build`, `enhance`, `status` SKILL.md files.

- [ ] **Step 3: Verify consistency**

```bash
grep -rln "enrich-headless" skills/ CLAUDE.md commands/ lib/corpus/patterns/headless-contract.md
```
Expected: the new skill dir, the five updated skills, CLAUDE.md, the gateway command, and the contract pattern all appear.

- [ ] **Step 4: Commit**

```bash
git add skills/ CLAUDE.md commands/ .claude-plugin/
git commit -m "feat(enrich): headless enrichment skill — closes the stale-entry loop"
```

---

### Task 10: Point refresh-headless at enrichment

**Files:**
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md`

**Interfaces:**
- Consumes: `embeddings: deferred` semantics (Task 6), enrich-headless (Task 9).

- [ ] **Step 1: Add a "Next Stage" section**

After the Output Contract section of `refresh-headless/SKILL.md`, add:

```markdown
## Next Stage: Enrichment

This skill intentionally leaves changed entries `stale: true` with
placeholder metadata — it detects and records change; it does not interpret
content. When the result file shows `index_changes.stale_entries` non-empty
(and `embeddings: deferred`), the pipeline MUST follow with:

    CALL_SKILL("hiivmind-corpus:hiivmind-corpus-enrich-headless", { corpus_path })

before committing, so the branch/PR contains a complete refresh: regenerated
summaries, concept assignments, verification results, and current embeddings.
Standalone/manual runs may skip enrichment, but the stale flags then persist
until enrich-headless or a rebuild runs.
```

Add to Related Skills: `- Enrichment (run after refresh): ${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enrich-headless/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add skills/hiivmind-corpus-refresh-headless/SKILL.md
git commit -m "docs(refresh-headless): document mandatory enrichment stage for pipelines"
```

---

### Task 11: Scheduler wiring (separate repo: `hiivmind-corpus-scheduler`)

**Files (in `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler`):**
- Modify: all seven `corpus-refresh-*/SKILL.md` (identical edit; only Constants blocks differ between files — verify with `diff` before and after)
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: `refresh-result.yaml` / `enrich-result.yaml` files (Tasks 6, 9), `validate_result.py` (Task 5).

- [ ] **Step 1: Update Phase 3 of every task SKILL.md**

Replace the `PARSE_RESULT` pseudocode block (which extracts the prose `---headless-result` block) in each of the seven files with:

```markdown
Read the result FILE (not the prose block) and validate it:

```pseudocode
PARSE_RESULT():
  result_file = computed.corpus_path + "/refresh-result.yaml"
  Bash("uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py " + result_file + " --kind refresh")
  IF exit != 0: computed.error = "invalid refresh result"; GOTO ABORT

  r = parse_yaml(Read(result_file))
  computed.sources_checked  = r.sources.map(s => s.id)
  computed.sources_updated  = r.sources.filter(s => s.status == "updated").map(s => s.id)
  computed.sources_manual   = r.sources.filter(s => s.status == "skipped-manual").map(s => s.id)
  computed.index_changes    = r.index_changes
  computed.embedding_status = r.embeddings
  computed.errors           = r.errors OR []
```
```

- [ ] **Step 2: Insert Phase 3b (Enrich) into every task SKILL.md**

Between Phase 3 and Phase 4, add:

```markdown
## Phase 3b: Enrich Stale Entries

**Outputs:** `computed.enrich_result`

Skip if `computed.index_changes.stale_entries` is empty.

```
CALL_SKILL("hiivmind-corpus:hiivmind-corpus-enrich-headless", { corpus_path: computed.corpus_path })
```

Read and validate `{corpus_path}/enrich-result.yaml` (validate_result.py
--kind enrich). Store as `computed.enrich_result`. Log errors but continue
to commit — a partially enriched refresh still beats an unenriched one.
```

Add `enrich_result: null` to each State block.

- [ ] **Step 3: Update Phase 4 (Commit and PR) body-building in every task SKILL.md**

Replace the PR-body instruction paragraph ("Build a separate PR body that additionally lists stale entry IDs...") with:

```markdown
Build a PR body reporting: sources updated (and any `skipped-manual` sources —
these need an interactive refresh), index change counts, enrichment counts
(`enriched`/`skipped`), verification results (`sampled`/`failed`, drift entry
ids), `new_concept_candidates` (call these out for reviewer decision — they
are the only items needing human judgment), embedding status, and any errors
from either result file. If enrichment did not run or left entries stale,
list the remaining stale entry IDs explicitly under a "Needs attention"
heading.
```

Note: result files are gitignored in corpus repos (the skills ensure this),
so `git add -A` will not stage them — no change needed to the staging step.

- [ ] **Step 4: Verify uniformity**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler
for f in corpus-refresh-*/SKILL.md; do diff corpus-refresh-lancedb/SKILL.md "$f" | grep -v "^[0-9]" | grep -cv "CORPUS_PATH\|CORPUS_REPO\|BRANCH_PREFIX\|name:" ; done
```
Expected: differences confined to name/Constants lines, as before the change.

- [ ] **Step 5: Update scheduler CLAUDE.md**

In "Common tasks", replace the headless-refresh bullet's description of parsing with: tasks read `refresh-result.yaml` / `enrich-result.yaml` result files and validate them with `validate_result.py`; the refresh→enrich sequence is mandatory when stale entries exist.

- [ ] **Step 6: Commit (scheduler repo)**

```bash
git add corpus-refresh-*/SKILL.md CLAUDE.md
git commit -m "feat: parse result files, validate contract, run enrichment stage after refresh"
```

---

### Task 12: Operational backfill — repair the lancedb corpus (manual, after merge)

Not a code task; run after the plugin changes are merged and the plugin version in use is updated.

- [ ] **Step 1:** In `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb`, create branch `automated/corpus-enrich-backfill-{date}` and invoke `hiivmind-corpus-enrich-headless` with `corpus_path` set to the corpus root. Expect it to enrich the 148 stale entries (52 placeholders among them).
- [ ] **Step 2:** Validate: `uv run <plugin>/lib/corpus/scripts/validate_result.py enrich-result.yaml --kind enrich`; then `grep -c 'stale: true' index.yaml` → expect 0; `grep -c 'Pending re-scan' index.yaml` → expect 0.
- [ ] **Step 3:** Commit, push, open PR; review new_concept_candidates in the PR body. This run is the acceptance test for backlog item 01.

---

## Self-Review Notes

- **Spec coverage:** backlog 04 tasks → Tasks 1–4 (scheduler stale root pyproject dropped — verified absent; per-task pyproject deletion deferred to item 05 per its dependency note). Backlog 02 tasks → Tasks 5–7 (schema+doc, file-writing, skipped-manual, de-dupe, schema validation in test suite). Backlog 01 tasks → Tasks 8–12 (separate-skill decision taken as the backlog recommends — standalone repair capability needed for the lancedb backfill; scanner prompt/batching in Task 9 Phase 2; concept matching in Phase 3; verification in Phase 4; contract extension in Task 5's enrich schema; scheduler wiring Task 11; backfill Task 12).
- **Type consistency:** `extract_previews(..., config_path=None)` used identically in Tasks 8 tests and implementation; contract field names identical across Task 5 schema, Task 6 skill text, Task 9 skill text, Task 11 pseudocode (`index_changes.stale_entries`, `embeddings`, `contract_version`, `kind`). `constants.py` names match embed.py's existing definitions.
- **Ordering:** Tasks 1–4 independent of B/C; Task 6 depends on 5; Task 7 independent of 5–6; Tasks 9–11 depend on 5, 7, 8; Task 10 depends on 9.
