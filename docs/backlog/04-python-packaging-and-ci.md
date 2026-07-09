# 04 — Python script packaging (PEP 723 + uv), cache-path bug, CI

**Priority:** P2 (small, independent, contains a real bug fix)
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §5
**Depends on:** nothing. Enables deletion of scheduler pyprojects in [05-scheduler-consolidation](05-scheduler-consolidation.md).

## Problem

- Skills invoke `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/*.py` against whatever interpreter is on PATH; dependency installation is prose (`pip install fastembed lancedb pyyaml`).
- The scheduler compensates with **seven identical `pyproject.toml` files**, each dragging in `pymupdf` whether or not the corpus has PDFs, plus an acknowledged stale root pyproject.
- **Bug:** `detect.py` globs `~/.cache/fastembed` directly, ignoring `FASTEMBED_CACHE_PATH` — which the scheduler's own (archived) `run.sh` sets. On hosts with a custom cache path, detection reports `no-model` and headless embedding silently skips forever.
- `MODEL_NAME = "BAAI/bge-small-en-v1.5"` is independently defined in `detect.py` and `embed.py` (and repeated in docs).
- 13 test files exist under `lib/corpus/scripts/tests/` but the plugin repo has **no CI**.

## Recommendation

1. **PEP 723 inline script metadata** (`# /// script … dependencies = [...] ///`) in each script; standard invocation becomes `uv run script.py`, with a documented `python3` + manual-install fallback in `patterns/tool-detection.md`. Scripts become self-contained and portable; scheduler per-task pyprojects become deletable. Keep `pymupdf` only on the PDF tools (`lib/corpus/tools/`), not the embedding scripts.
2. **Fix `detect.py`** to honor `FASTEMBED_CACHE_PATH` (and ideally ask fastembed itself for its cache dir rather than globbing).
3. **Single source for constants**: `constants.py` (or detect imports from embed) for `MODEL_NAME`, dimensions, table names.
4. **CI workflow** on the plugin repo: `uv run pytest` over `lib/corpus/scripts/tests/` and `lib/corpus/tools/`, plus a smoke test that builds/refreshes a tiny fixture corpus and schema-validates the headless result file (ties into [02](02-result-contract-and-shared-update-pattern.md)). Given the skills are prose executed by an LLM, script tests + contract validation are the only deterministic regression net.

## Tasks

- [ ] Add PEP 723 blocks to all scripts in `lib/corpus/scripts/` and `lib/corpus/tools/`.
- [ ] Update every SKILL.md / pattern doc invocation to `uv run` with fallback guidance.
- [ ] Fix `FASTEMBED_CACHE_PATH` handling in `detect.py`; add a regression test.
- [ ] Consolidate model/table constants.
- [ ] Add `.github/workflows/ci.yml`: pytest + fixture-corpus smoke test + result-schema validation.
- [ ] Delete the scheduler repo's stale root `pyproject.toml` (noted stale in its CLAUDE.md).

## Acceptance

`uv run lib/corpus/scripts/embed.py --help` works from a clean machine with only uv installed. `FASTEMBED_CACHE_PATH=/custom detect.py` reports `ready` when the model is in the custom path. CI is green on PRs.
