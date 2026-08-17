---
name: hiivmind-corpus-status-headless
description: >
  Non-interactive corpus freshness check for pipelines. Compares upstream SHAs
  against config.yaml, counts stale entries and embedding lag, and writes
  status-result.yaml (headless contract). Cheap: no clones, no index edits.
  Triggers: "headless status", "status result file", scheduler pre-checks.
---

# Corpus Status (Headless)

Freshness snapshot of ONE corpus, written as a machine-readable result file.
Never modifies corpus source-of-truth files. It writes the configured result artifact.
It may append its path to `.gitignore`, runs bounded validation and process
commands, and may contact configured upstream git remotes via `git ls-remote`.
Designed as a cheap pre-check before a full refresh (no clone) and for nightly
status sweeps across corpora.

**Inputs:**
- `corpus_path` (required)
- `result_path` (optional, default `{corpus_path}/status-result.yaml`)

## Phases

1. **Validate:** read `{corpus_path}/config.yaml`; ABORT if missing. Detect
   index format (index.yaml → v2, index.md only → v1, neither → unbuilt).
2. **Source freshness (no clones, no fetches into .source/):** per source —
   git/generated-docs/self: `git ls-remote <repo_url> refs/heads/<branch>`
   (or local `git log -1` for self) vs `last_commit_sha` → `current | behind |
   unknown`; local: newest mtime under `uploads/{id}/` vs `last_indexed_at`;
   web: `current` if cache exists (manual refresh semantics); llms-txt:
   manifest hash comparison per `patterns/sources/llms-txt.md`.
3. **Index staleness:** v2 → `yq '[.entries[] | select(.stale == true)] |
   length' index.yaml`; v1 → count `⏳ STALE` markers in index*.md.
4. **Embedding lag:** if `index-embeddings.lance/` exists, run
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/lance_meta.py index-embeddings.lance/`
   to get `embedded_at`, then count entries whose `last_indexed` postdates it
   (see `patterns/embeddings.md` § Embedding Lag). No lance dir → `null`.
5. **Write result** (contract below), echo a one-line summary. Never modify
   corpus source-of-truth files. Write the result file even on ABORT, with
   `errors` populated.

## Output Contract

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

```yaml
contract_version: 1
kind: status
corpus: {name}
run_at: {ISO 8601}
index_format: v2 | v1 | none
sources:
  - id: {source id}
    type: {source type}
    freshness: current | behind | unknown
stale_entries: {int}             # entries flagged stale in the index
embeddings_lag: {int|null}       # entries indexed after last embed; null = no embeddings
refresh_needed: {bool}           # any source behind OR stale_entries > 0
errors: []
```

Validate: `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py {result_path} --kind status`
Ensure `status-result.yaml` is in the corpus `.gitignore` (append if missing).

## Reference

- Patterns: `status.md`, `freshness.md`, `config-parsing.md`, `embeddings.md`, `headless-contract.md`
- Related skills: hiivmind-corpus-status (interactive), hiivmind-corpus-build-headless, hiivmind-corpus-refresh-headless, hiivmind-corpus-enrich-headless, hiivmind-corpus-migrate, hiivmind-corpus-discover, hiivmind-corpus-navigate, hiivmind-corpus-build, hiivmind-corpus-refresh, hiivmind-corpus-enhance, hiivmind-corpus-graph, hiivmind-corpus-bridge, hiivmind-corpus-init, hiivmind-corpus-add-source, hiivmind-corpus-register
