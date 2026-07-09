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

- Migrate v1→v2 (headless): `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-migrate/SKILL.md`
- Headless refresh (runs before this): `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh-headless/SKILL.md`
- Interactive refresh: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Concept graph: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md`
