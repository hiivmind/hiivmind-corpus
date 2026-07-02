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
outputs:
  - name: result
    type: yaml
    description: Structured result block — see Output Contract section
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
  updated_sources: []
  index_changes:
    added: 0
    modified: 0
    removed: 0
    stale_entries: []
  embedding_status: null       # "updated" | "skipped" | "no-model" | "not-installed"
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
| local | Always "current" (no auto-detection) | `patterns/sources/local.md` |
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

### v2 format (index.yaml)

`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-format-v2.md` and `freshness.md`:

```pseudocode
UPDATE_INDEX_V2():
  index = parse_yaml(Read("index.yaml"))

  FOR EACH source IN computed.updated_sources:
    FOR EACH change IN source.files_changed:
      entry_id = source.id + ":" + relative_path(change.path, source.docs_root)

      SWITCH change.status:
        CASE "M":
          entry = find_entry(index, entry_id)
          IF entry:
            entry.stale = true
            entry.stale_since = now()
            # Preserve: summary, tags, keywords, concepts, links_from
            computed.index_changes.modified += 1
            computed.index_changes.stale_entries.append(entry_id)

        CASE "A":
          append_entry(index, {
            id: entry_id, source: source.id, path: relative_path,
            stale: true, stale_since: now(),
            category: "unknown", summary: "Pending re-scan",
            tags: [], keywords: [], concepts: []
          })
          computed.index_changes.added += 1
          computed.index_changes.stale_entries.append(entry_id)

        CASE "D":
          remove_entry(index, entry_id)
          remove_from_graph_if_referenced("graph.yaml", entry_id)
          computed.index_changes.removed += 1

  Update index.meta.generated_at and entry_count, save index.yaml
  Re-render: bash ./render-index.sh index.yaml (if render script exists)
```

`links_from` and `concepts` are preserved as-is — recomputing them requires a full build
or the graph skill respectively.

### v1 format (index.md)

Apply changes directly to `index.md`. If tiered (glob `index-*.md`), map changes to
affected sub-indexes and update each. See `patterns/sources/shared.md`.

Per-change rules:

- **D (deleted):** Remove the entry line from the relevant section file.
- **M (modified):** Path is unchanged — the entry reference remains valid. No section edit needed.
- **A (added):** Read the file from `.source/{id}/` and extract a real title and intro **before** writing the entry. Never write a directory summary or placeholder stub — v1 has no re-scan phase, so entries need real content from the start.

  ```pseudocode
  FOR EACH added_path IN source.files_changed WHERE status == "A":
    content = git_show(".source/{source.id}", "HEAD:{docs_root}/{relative_path}")
    title   = frontmatter.title OR frontmatter.shortTitle OR first_h1(content) OR filename_humanized
    intro   = frontmatter.intro (clean template vars, truncate to ~120 chars)
    entry   = "- **{title}** `{source.id}:{relative_path}`"
    IF intro: entry += " — {intro}"
    append entry to relevant section in index file
  ```

  Template variables (e.g. Liquid `{% data variables.X.Y %}`) must be resolved or stripped
  **before** truncating — truncating mid-tag leaves broken markup in the index.

  Place each entry in the appropriate existing `##` section based on path structure
  (e.g. `copilot/concepts/...` → `## Concepts`, `copilot/how-tos/...` → `## How-Tos`).
  Never stage entries under a temporary heading like "New in This Refresh" — the index
  is a durable source of truth, not a changelog.

### Update config.yaml (both formats)

For each updated source: advance `last_indexed_at`, and `last_commit_sha` (git/self/generated-docs)
or `manifest.last_hash` (llms-txt). Set `config.index.last_updated_at`. Save.

---

## Phase 5: Embeddings

**Outputs:** `computed.embedding_status`

`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`:

Skip if `index-embeddings.lance/` doesn't exist, or if no entries were added/modified.

Otherwise run `detect.py`: if "ready", run `embed.py index.yaml index-embeddings.lance/`
(incremental upsert). If "no-model", skip — never trigger a download during automated
refresh. If not installed, skip.

---

## Output Contract

Emit this YAML block as the final output. The calling pipeline extracts between
`---headless-result` and `---` and parses as YAML.

```yaml
---headless-result
corpus: {name from config}
run_at: {ISO timestamp}
sources:
  - id: {source id}
    type: {source type}
    status: current | updated | failed
    old_sha: {short sha, if applicable}
    new_sha: {short sha, if updated}
    files_changed: {count}
index_changes:
  added: {n}
  modified: {n}
  removed: {n}
  stale_entries:
    - {entry id}
embeddings: updated | skipped | no-model | not-installed
errors:
  - {description}
---
```

Emit even on partial failure. A source that fails is `status: failed` with the error
in `errors[]`; other sources proceed normally.

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| No config.yaml / no sources / index not built | Abort: emit result with error, exit |
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
- **Freshness checks:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/freshness.md`
- **Index rendering:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-rendering.md`
- **Embeddings:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`

## Related Skills

- Interactive refresh: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
