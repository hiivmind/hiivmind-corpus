---
name: hiivmind-corpus-refresh-headless
description: >
  Headless (non-interactive) variant of hiivmind-corpus-refresh for use by automated pipelines
  and scheduled tasks. Always runs in update mode, selects all stale sources automatically,
  and emits a machine-readable YAML result block instead of prose. Use hiivmind-corpus-refresh
  for interactive use.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, WebFetch, Task
inputs:
  - name: corpus_path
    type: string
    required: false
    description: Absolute path to the corpus root (uses current working directory if not provided)
  - name: result_path
    type: string
    required: false
    description: Where to write refresh-result.yaml (defaults to {corpus_root}/refresh-result.yaml)
outputs:
  - name: result
    type: yaml
    description: Structured result written to result_path and echoed as a log block — see patterns/headless-contract.md
---

# Corpus Refresh (Headless)

Non-interactive corpus refresh for automated pipelines. Always updates all stale sources.
Emits a structured YAML result block on completion — no prose summaries, no prompts.

Follows the same source-type patterns as `hiivmind-corpus-refresh`. Refer to pattern
documentation for source-type-specific logic.

---

## State

```yaml
computed:
  corpus_root: null
  config: null
  sources: []
  index_format: null           # "v1" | "v2"
  status_report: []            # per-source { id, type, status, old_sha, new_sha }
                               # status: current | updated | failed | skipped-manual
  updated_sources: []
  index_changes:
    added: 0
    modified: 0
    removed: 0
    stale_entries: []
  embedding_status: null       # "updated" | "skipped" | "no-model" | "not-installed" | "deferred"
  errors: []
```

---

## Phase 1: Validate

**Outputs:** `computed.config`, `computed.sources`, `computed.index_format`

Resolve corpus root from `corpus_path` input or cwd. Read and parse `config.yaml`.
Abort (emit result with error) if any of these fail:
- `config.yaml` missing
- No sources in `config.sources`
- `index.md` is a placeholder (not built)

Detect index format: `index.yaml` exists → v2, otherwise v1.

---

## Phase 2: Check Freshness

**Outputs:** `computed.status_report`

Check each source for upstream changes. Run in parallel (Task agents) where possible.
Per-source logic by type:

| Type | Check | Pattern doc |
|------|-------|-------------|
| git | `git ls-remote` SHA vs `last_commit_sha` | `patterns/sources/git.md` |
| local | Always "skipped-manual" (no auto-detection — needs interactive refresh) | `patterns/sources/local.md` |
| web | Cache age > 7 days → stale | `patterns/sources/web.md` |
| llms-txt | SHA-256 of fetched manifest vs `manifest.last_hash` | `patterns/sources/llms-txt.md` |
| generated-docs | Same as git, using `source_repo` | `patterns/sources/generated-docs.md` |
| self | `git log -1 --format=%H -- {docs_root}` vs `last_commit_sha` | `patterns/sources/self.md` |

If all sources are current: emit result with no changes and exit.

---

## Phase 3: Update Sources

**Outputs:** `computed.updated_sources`, file-level changes per source

Update every source with `status != "current"`. Wrap each source in error handling —
a failure marks that source `status: failed` and logs to `computed.errors`, but the
run continues for other sources.

### Git source update

`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/git.md`:

Clone to `.source/{id}` if not present (depth 50). Then ensure the tracked SHA is
reachable for diffing:

```pseudocode
DEEPEN_IF_NEEDED(clone_dir, source):
  IF repo is shallow:
    IF cat-file cannot resolve source.last_commit_sha:
      fetch --shallow-since={source.last_indexed_at} origin {source.branch}
      IF still cannot resolve:
        fetch --unshallow origin {source.branch}
```

Pull latest. Diff `last_commit_sha..HEAD` under `docs_root` to get changed files
with their status (A/M/D).

### Other source types

- **Local:** scan `uploads/{id}/` for files newer than `last_indexed_at`
- **Web:** re-fetch all URLs to `.cache/web/{id}/` — see `patterns/sources/web.md`
- **llms-txt:** re-fetch manifest, diff pages, re-cache changes — see `patterns/sources/llms-txt.md`
- **Generated-docs:** same shallow-clone strategy as git, using `source_repo`
- **Self:** `git diff --name-status {old_sha}..{new_sha} -- {docs_root}`, filtered by `include_patterns`

---

## Phase 4: Apply Changes to Index

**Outputs:** `computed.index_changes`

Apply every change per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-updating.md`:
v2 → stale-marking rules (M/A/D); v1 → direct entry edits with real titles
extracted from `.source/` (single or tiered). Then update config metadata per
the same pattern. Track counts into `computed.index_changes`.

---

## Phase 5: Embeddings

**Outputs:** `computed.embedding_status`

`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`:

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

---

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
abort): a missing result file is indistinguishable from a crashed run. A source
that fails is `status: failed` with the error in `errors[]`; other sources
proceed normally.

---

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

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| No config.yaml / no sources / index not built | Abort: write result file with error, emit log block, exit |
| Clone/fetch failed | Source marked `failed`, logged in `errors[]`, continue |
| Shallow deepen failed | Fallback: `--shallow-since` → full unshallow → fail source |
| Index update failed | Logged in `errors[]`, partial changes saved |
| Config save failed | Logged in `errors[]` |

---

## Pattern Documentation

- **Git sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/git.md`
- **Local sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/local.md`
- **Web sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/web.md`
- **llms-txt sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/llms-txt.md`
- **Generated docs:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/generated-docs.md`
- **Self sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/self.md`
- **Index v2 schema:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-format-v2.md`
- **Index updating:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-updating.md`
- **Freshness checks:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/freshness.md`
- **Index rendering:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-rendering.md`
- **Embeddings:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`
- **Result contract:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

## Related Skills

- Enrichment (run after refresh): `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enrich-headless/SKILL.md`
- Interactive refresh: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
