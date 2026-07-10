---
name: hiivmind-corpus-migrate
description: >
  Headless v1 → v2 index migration. Parses entry lines from index.md and
  index-*.md, cross-references .source/ for metadata, emits index.yaml plus a
  render: block, renders deterministically, and diff-checks ID parity against
  the original. Writes migrate-result.yaml (headless contract). Triggers:
  "migrate corpus", "migrate to v2", "convert index.md to index.yaml".
---

# Corpus Migrate (v1 → v2, Headless)

Mechanical migration of a v1 corpus (`index.md` as source of truth, optionally
tiered) to v2 (`index.yaml` + rendered markdown). Non-interactive: designed for
pipelines and one-shot runs; decisions are deterministic or recorded in the
result file for human review.

**Inputs:**
- `corpus_path` (required) — corpus repository root
- `result_path` (optional) — defaults to `{corpus_path}/migrate-result.yaml`

## State

```yaml
computed:
  v1_files: []          # index.md + index-*.md found
  parsed_entries: []    # {title, id, summary, grep_hint, stale, section, v1_heading}
  sections: []          # {id, title, description} derived from sub-index files
  skipped: []           # entries whose source file no longer exists
  entry_count: 0
  errors: []
  error: null           # fatal → ABORT
```

## Phase 1: Validate

Read `{corpus_path}/config.yaml` (see `patterns/config-parsing.md`).

- ABORT if `index.yaml` already exists → "already v2 — nothing to migrate".
- ABORT if no `index.md` → "no v1 index found".
- Collect `computed.v1_files`: `index.md` plus every `index-*.md` at corpus root.
- Detect tiering: >1 file → tiered v1.

## Phase 2: Parse v1 Entries

For each v1 file, extract entry lines with this exact shape (the v1 format):

```
- **{title}** `{id}` - {summary}[ ⚡ GREP - `{hint}`][ ⏳ STALE]
```

Regex: ``^- \*\*(.+?)\*\* `([^`]+)` - (.*)$`` then strip/capture the optional
`⚡ GREP - `...`` and `⏳ STALE` suffixes from the summary tail.

Record for each entry: `title`, `id`, `summary`, `grep_hint` (or null),
`stale` (true if the ⏳ marker was present), `section` (the sub-index slug the
line came from — `index-machines.md` → `machines`; null for entries in the
main index, including Quick Reference duplicates — dedupe by `id`, sub-index
wins), and `v1_heading` (the nearest preceding `## ` heading, kept as an
extra tag).

For each sub-index file, also record a section definition: `id` = file slug,
`title` = the sub-index h1 (strip " - Detailed Index" suffixes) or the main
index's corresponding `## ` heading, `description` = the italic line under
that heading in the main index (or empty).

If a main index lists a Quick Reference, record those entry IDs in order.

ABORT if zero entries parse — the index is not in the expected v1 format.

## Phase 3: Cross-Reference Sources

Ensure each git source is cloned at `.source/{id}/` (sparse clone is fine —
see "Sparse Checkout for Large Repositories" in `patterns/sources/git.md`).

For each parsed entry, split `id` into `{source}:{path}` and resolve the file
under `.source/{source}/{docs_root}/{path}` (fallback: `.source/{source}/{path}`).

- File exists → collect: `content_type` (by extension), `size`
  (`large` if >1000 lines, else `standard`), `headings` (h2s, slugified
  anchors), line count.
- File missing → move entry to `computed.skipped` with reason `file-missing`.
  Do not invent entries.

## Phase 4: Assemble index.yaml

For each surviving entry, build a v2 entry per `patterns/index-format-v2.md`:
`id`, `source`, `path`, `title`, `summary` (verbatim from v1), `tags`
(LLM-assigned from title + summary + v1_heading; include the slugified
v1_heading itself), `keywords` (LLM-assigned, function/command names from the
title and summary), `concepts: []`, `category` (LLM judgment mapped to the
enum: reference | tutorial | guide | api | config | navigation | journal —
default `reference` when unclear), `content_type`, `size`, `grep_hint`,
`section` (from Phase 2; omit if null), `headings`, `links_to: []`,
`links_from: []`, `frontmatter: {}`, `stale` (from the v1 ⏳ marker),
`stale_since: null`, `last_indexed: now()`.

Set `meta.generated_at = now()`, `meta.entry_count`.

## Phase 5: Render and Diff-Check

1. Write the `render:` block into config.yaml: `strategy: tiered` when tiered
   v1 (else `single`), `sections` from Phase 2 (config order = main-index
   order), `quick_reference` from Phase 2 if present.
2. Write `index.yaml`.
3. Copy `${CLAUDE_PLUGIN_ROOT}/templates/render-index.sh` to the corpus root
   (overwrite — the corpus needs the tiered-capable version).
4. `bash render-index.sh index.yaml`.
5. **Diff-check:** every entry ID present in the ORIGINAL v1 files must appear
   in the rendered output (skipped entries excepted — they are reported, not
   silently dropped). Extract IDs with `` grep -oh '`[a-z0-9-]*:[^`]*`' `` from
   old and new files and compare as sets. Any ID missing from the render that
   is not in `computed.skipped` → ABORT (do not commit a lossy migration).
6. Update config metadata: `index.last_updated_at = now()`.

Note: embeddings are NOT generated here — run build Phase 7 / enhance
afterwards if the corpus should gain them. `migrate-result.yaml` reports
`embeddings: skipped`.

## Output Contract

See `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`. Resolve
`result_path` (default `{corpus_path}/migrate-result.yaml`), ensure the
filename is in the corpus `.gitignore`, and Write:

```yaml
contract_version: 1
kind: migrate
corpus: {corpus name}
run_at: {ISO 8601}
entries_migrated: {int}
entries_skipped:                 # file-missing etc. — human review items
  - id: "flyio:old/path.md"
    reason: file-missing
sections: [{count} strings]      # section ids written to render.sections
strategy: tiered | single
id_parity: true                  # diff-check passed
embeddings: skipped
errors: []
```

Validate before finishing:
`uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py {result_path} --kind migrate`

Write the result file even on ABORT (with `error` populated and
`id_parity: false` where applicable).

## Error Handling

| Error | Handling |
|-------|----------|
| Already v2 | ABORT: "index.yaml exists — nothing to migrate" |
| No index.md | ABORT: "no v1 index found" |
| Zero entries parsed | ABORT: "index.md is not in v1 entry-line format" |
| Source clone failed | Entries of that source → skipped (reason clone-failed); continue |
| ID parity failure | ABORT — report missing IDs in result file |

## Reference

- Patterns: `config-parsing.md`, `index-format-v2.md`, `index-rendering.md`, `headless-contract.md`, `sources/git.md`
- Related skills: hiivmind-corpus-build, hiivmind-corpus-refresh, hiivmind-corpus-refresh-headless, hiivmind-corpus-enrich-headless, hiivmind-corpus-enhance, hiivmind-corpus-status, hiivmind-corpus-status-headless, hiivmind-corpus-navigate, hiivmind-corpus-graph, hiivmind-corpus-init, hiivmind-corpus-add-source, hiivmind-corpus-discover, hiivmind-corpus-register, hiivmind-corpus-bridge
