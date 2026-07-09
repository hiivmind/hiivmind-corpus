# Wave 2: Tiered v2 Rendering, v1→v2 Migration, v1 Read-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make tiering a render-time concern of `index.yaml` (one source of truth, N rendered files), ship a headless `hiivmind-corpus-migrate` skill, migrate flyio off v1 as the proving case, and declare v1 read-only in every write-path skill.

**Architecture:** A `render:` block in config.yaml (`strategy: single | tiered`, section definitions, optional quick-reference list) plus an optional per-entry `section` field drive `render-index.sh` to emit `index.md` + `index-{section}.md` deterministically from one `index.yaml`. Migration is mechanical: parse v1 entry lines, cross-reference `.source/` for metadata, LLM-assign category/tags, emit index.yaml + render block, render, and diff-check ID parity against the original. v1 write paths are *marked read-only this release* (skills detect v1 → instruct migration); deletion happens next release per the backlog.

**Tech Stack:** Markdown skills/patterns, bash + mikefarah yq v4 (render-index.sh), one small addition to `validate_result.py` (new `migrate` kind).

## Global Constraints

- Repo: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus`, branch `feature/wave2-tiered-v2` off up-to-date main. flyio migration happens in `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-flyio` on branch `migrate/v2` and needs the plugin work installed/available first — it is the LAST task.
- Follow the repo convention (user feedback, wave 1): **skills and pattern docs first, Python last**; tests stay light — features first, verify by direct runs.
- render-index.sh constraint: mikefarah yq v4 only — **no jq-style `if/then/else`** (lexer rejects it); use the existing hybrid yq-TSV + bash formatting approach and `env()` for variable passing.
- Contract stays `contract_version: 1` — adding a new `kind` is backward-compatible (documented in `patterns/headless-contract.md` versioning policy).
- v1 write logic is NOT deleted this wave — only gated. `patterns/index-updating.md` v1 sections get a deprecation banner but remain.
- CLAUDE.md "Maintaining Skill Alignment": adding the migrate skill requires updating architecture tree, naming list, lifecycle diagram, cross-cutting table, dependency chain, and every skill's `## Reference` section.
- Commits: conventional, ending `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Acceptance (backlog 03): flyio is v2 with tiered `index-*.md` rendered deterministically from one `index.yaml`; no skill *executes* v1 write logic; CLAUDE.md alignment table shrinks.

---

### Task 1: Schema — `render:` block and entry `section` field

**Files:**
- Modify: `lib/corpus/patterns/index-format-v2.md` (field table + new section)
- Modify: `lib/corpus/patterns/config-parsing.md` (document the `render:` block)
- Modify: `templates/config.yaml.template` (commented `render:` example near the `index:` block, ~line 50)

**Interfaces:**
- Produces: the `render:` schema and `section` entry field that Tasks 2 (renderer), 3 (migrate skill), and 5 (build skill) consume.

- [ ] **Step 1: Add `section` to the entry field table in index-format-v2.md**

After the `category` row in the Field Definitions table, add:

```markdown
| `section` | string | no | Render-time grouping key for tiered corpora. Must match a `render.sections[].id` in config.yaml. Entries without it render in the main index. Storage-agnostic: navigate/yq queries ignore it |
```

- [ ] **Step 2: Add the `render:` block documentation**

In `lib/corpus/patterns/config-parsing.md`, add a new top-level section (after the sources documentation):

````markdown
## The `render:` Block (tiered rendering)

Controls how `render-index.sh` turns `index.yaml` into markdown. Absent block =
`strategy: single` (one index.md, current behavior). Tiering is a **render-time
concern, not a storage concern** — there is exactly one `index.yaml` either way.

```yaml
render:
  strategy: tiered            # single (default) | tiered
  quick_reference:            # optional: entry IDs pinned at the top of index.md
    - "flyio:flyctl/install.html.markerb"
    - "flyio:getting-started/launch.html.markerb"
  sections:                   # required when strategy: tiered
    - id: getting-started     # slug; produces index-getting-started.md
      title: "Getting Started"
      description: "First steps - installation, signup, first deploy"
    - id: machines
      title: "Fly Machines"
      description: "Machines lifecycle, REST API, flyctl commands"
```

Entries opt into a section via their `section:` field in index.yaml (see
`index-format-v2.md`). Entries with no `section` (or one not listed here) render
inline in the main index under their category. Deleting a section from this list
does not lose data — its entries just fall back to the main index on next render.
````

Also add the same `render:` example as a commented block in `templates/config.yaml.template` under the `index:` section.

- [ ] **Step 3: Verify and commit**

```bash
grep -n "render:" lib/corpus/patterns/config-parsing.md templates/config.yaml.template
grep -n "section.*Render-time" lib/corpus/patterns/index-format-v2.md
git add -A && git commit -m "docs(patterns): render: block schema and entry section field for tiered v2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Tiered rendering in `render-index.sh` + `index-rendering.md`

**Files:**
- Modify (full rewrite): `templates/render-index.sh`
- Modify: `lib/corpus/patterns/index-rendering.md` (algorithm + tiered rules)

**Interfaces:**
- Consumes: `render:` schema from Task 1.
- Produces: `bash render-index.sh index.yaml` emitting `index.md` (+ `index-{id}.md` per section when tiered). Tasks 3 and 6 call it unchanged.

- [ ] **Step 1: Replace templates/render-index.sh with the tiered-capable version**

```bash
#!/usr/bin/env bash
# render-index.sh — Deterministic index.yaml → index.md renderer
# Copied to corpus root during build/migrate. Used by build, refresh, and CI.
#
# Usage: bash render-index.sh index.yaml
# Reads config.yaml from the same directory for corpus name, source count, and
# the render: block (strategy: single | tiered).
# Requires: yq 4.0+ (mikefarah/yq)

set -euo pipefail

INDEX_YAML="${1:?Usage: render-index.sh <path-to-index.yaml>}"
DIR=$(dirname "$INDEX_YAML")
CONFIG_YAML="${DIR}/config.yaml"

[ -f "$INDEX_YAML" ] || { echo "Error: $INDEX_YAML not found" >&2; exit 1; }
[ -f "$CONFIG_YAML" ] || { echo "Error: $CONFIG_YAML not found (needed for corpus name)" >&2; exit 1; }

CORPUS_NAME=$(yq '.corpus.display_name // .corpus.name' "$CONFIG_YAML")
SOURCE_COUNT=$(yq '.sources | length' "$CONFIG_YAML")
ENTRY_COUNT=$(yq '.meta.entry_count' "$INDEX_YAML")
GENERATED_AT=$(yq '.meta.generated_at' "$INDEX_YAML")
STRATEGY=$(yq '.render.strategy // "single"' "$CONFIG_YAML")

# Emit entry lines grouped by category (h2), for the subset selected by MODE:
#   MODE=all                  every entry
#   MODE=main                 entries with no .section (or empty)
#   MODE=section SECTION=<id> entries with .section == <id>
# Uses yq for extraction (TSV) and bash for formatting; mikefarah yq v4 has no
# jq-style if/then/else, and env() avoids all quote-escaping issues.
render_entries() {
  local mode="$1" section="${2:-}"
  local categories
  categories=$(MODE="$mode" SECTION="$section" yq -r '
    .entries
    | map(select(
        (env(MODE) == "all")
        or (env(MODE) == "main" and (.section // "") == "")
        or (env(MODE) == "section" and (.section // "") == env(SECTION))
      ))
    | .[].category
  ' "$INDEX_YAML" | sort -u)

  for CAT in $categories; do
    echo ""
    CAT_HEADING=$(echo "$CAT" | sed 's/\b\(.\)/\u\1/g')
    echo "## ${CAT_HEADING}"
    echo ""
    MODE="$mode" SECTION="$section" CAT_FILTER="$CAT" yq -r '
      .entries
      | map(select(
          ((env(MODE) == "all")
           or (env(MODE) == "main" and (.section // "") == "")
           or (env(MODE) == "section" and (.section // "") == env(SECTION)))
          and .category == env(CAT_FILTER)
        ))
      | sort_by(.title)
      | .[]
      | [.title, .id, .summary, .size, (.grep_hint // ""), (.stale | tostring)]
      | @tsv
    ' "$INDEX_YAML" | while IFS=$'\t' read -r title id summary size grep_hint stale; do
      line="- **${title}** \`${id}\` - ${summary}"
      if [[ "$size" == "large" && -n "$grep_hint" ]]; then
        line+=" ⚡ GREP - \`${grep_hint}\`"
      fi
      if [[ "$stale" == "true" ]]; then
        line+=" ⏳ STALE"
      fi
      echo "$line"
    done
  done
}

count_section_entries() {
  local section="$1"
  SECTION="$section" yq -r '[.entries[] | select((.section // "") == env(SECTION))] | length' "$INDEX_YAML"
}

render_single() {
  {
    echo "# ${CORPUS_NAME} Documentation Index"
    echo ""
    echo "> Sources: ${SOURCE_COUNT} | Entries: ${ENTRY_COUNT} | Generated: ${GENERATED_AT}"
    echo '> Generated from `index.yaml` — do not edit directly'
    echo ""
    echo "---"
    render_entries all
    echo ""
    echo "---"
    echo ""
    echo "*Rendered from index.yaml at ${GENERATED_AT}*"
  } > "${DIR}/index.md"
  echo "Rendered ${DIR}/index.md (${ENTRY_COUNT} entries)"
}

render_tiered() {
  local section_ids
  section_ids=$(yq -r '.render.sections[].id' "$CONFIG_YAML")

  # --- main index.md ---
  {
    echo "# ${CORPUS_NAME} Documentation Index"
    echo ""
    echo "> Sources: ${SOURCE_COUNT} | Entries: ${ENTRY_COUNT} | Generated: ${GENERATED_AT}"
    echo '> Generated from `index.yaml` — do not edit directly'
    echo ""
    echo "This corpus uses a **tiered index**. Start here, then drill into the"
    echo "sub-index files for detailed entries."
    echo ""
    echo "---"

    # Quick reference (pinned entry IDs, in config order)
    QR_COUNT=$(yq -r '.render.quick_reference // [] | length' "$CONFIG_YAML")
    if [[ "$QR_COUNT" -gt 0 ]]; then
      echo ""
      echo "## Quick Reference"
      echo ""
      yq -r '.render.quick_reference[]' "$CONFIG_YAML" | while read -r qid; do
        QID="$qid" yq -r '
          .entries[] | select(.id == env(QID))
          | [.title, .id, .summary] | @tsv
        ' "$INDEX_YAML" | while IFS=$'\t' read -r title id summary; do
          echo "- **${title}** \`${id}\` - ${summary}"
        done
      done
      echo ""
      echo "---"
    fi

    # Section summaries
    for SID in $section_ids; do
      S_TITLE=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .title' "$CONFIG_YAML")
      S_DESC=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .description // ""' "$CONFIG_YAML")
      N=$(count_section_entries "$SID")
      echo ""
      echo "## ${S_TITLE}"
      [[ -n "$S_DESC" ]] && { echo "*${S_DESC}*"; echo ""; }
      echo "→ See [index-${SID}.md](index-${SID}.md) for ${N} detailed entries"
      echo ""
      echo "---"
    done

    # Unsectioned entries render inline
    MAIN_COUNT=$(yq -r '[.entries[] | select((.section // "") == "")] | length' "$INDEX_YAML")
    if [[ "$MAIN_COUNT" -gt 0 ]]; then
      render_entries main
      echo ""
      echo "---"
    fi

    echo ""
    echo "*Rendered from index.yaml at ${GENERATED_AT}*"
  } > "${DIR}/index.md"

  # --- one sub-index per section ---
  for SID in $section_ids; do
    S_TITLE=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .title' "$CONFIG_YAML")
    {
      echo "# ${CORPUS_NAME} — ${S_TITLE}"
      echo ""
      echo "> Part of the ${CORPUS_NAME} Documentation Index — back to [main index](index.md)"
      echo '> Generated from `index.yaml` — do not edit directly'
      echo ""
      echo "---"
      render_entries section "$SID"
      echo ""
      echo "---"
      echo ""
      echo "*Rendered from index.yaml at ${GENERATED_AT}*"
    } > "${DIR}/index-${SID}.md"
  done

  # Remove sub-indexes for sections no longer defined (rename/removal hygiene)
  for f in "${DIR}"/index-*.md; do
    [ -e "$f" ] || continue
    base=$(basename "$f" .md); sid="${base#index-}"
    echo "$section_ids" | grep -qx "$sid" || rm "$f"
  done

  echo "Rendered ${DIR}/index.md + $(echo "$section_ids" | wc -w | tr -d ' ') sub-indexes (${ENTRY_COUNT} entries)"
}

if [[ "$STRATEGY" == "tiered" ]]; then
  render_tiered
else
  render_single
fi
```

- [ ] **Step 2: Smoke-test both strategies against a fixture in the scratchpad**

Create a scratchpad dir with a minimal `config.yaml` (name + 1 source + `render:` tiered block with 2 sections + 1 quick_reference id) and an `index.yaml` with 4 entries: 2 in section A, 1 in section B, 1 unsectioned. Run:

```bash
bash templates/render-index.sh <scratchpad>/index.yaml
ls <scratchpad>/          # expected: index.md, index-a.md, index-b.md
```

Verify: quick-ref entry pinned at top; section counts correct; unsectioned entry inline under its category; run twice → identical output (idempotent). Then delete section B from config, re-run, verify `index-b.md` is removed and B's entry falls back inline. Then set `strategy: single` (or remove `render:`), re-run, verify one `index.md` with all 4 entries and no sub-index files remain stale (note: single mode does not delete old sub-indexes — the migrate/build skill handles that transition; acceptable).

- [ ] **Step 3: Update index-rendering.md**

Add to the Rendering Algorithm section (after rule 7):

```markdown
8. **Tiered strategy** (`config.render.strategy: tiered`): the main `index.md`
   carries the header, an optional Quick Reference (entry IDs from
   `render.quick_reference`, in config order), one summary block per
   `render.sections[]` (title, italic description, entry count, link to
   `index-{id}.md`), and any unsectioned entries inline. Each section renders
   to `index-{id}.md` with a backlink header and the same category-grouped
   entry format. Sub-index files for sections removed from config are deleted
   on render. Sections are ordered as listed in config; everything else stays
   alphabetical.
```

Update the Prerequisites and Purpose lines to mention the `render:` block, and note in "When to Use" that refresh/enhance re-render both files whenever `index.yaml` changes — sub-indexes are never edited directly.

- [ ] **Step 4: Commit**

```bash
git add templates/render-index.sh lib/corpus/patterns/index-rendering.md
git commit -m "feat(render): tiered index.md + index-{section}.md rendering from one index.yaml

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: `hiivmind-corpus-migrate` skill (headless, result contract)

**Files:**
- Create: `skills/hiivmind-corpus-migrate/SKILL.md`
- Modify: `lib/corpus/patterns/headless-contract.md` (add migrate-result.yaml schema)

**Interfaces:**
- Consumes: `render:` schema (Task 1), tiered renderer (Task 2), existing `patterns/headless-contract.md` conventions (result file at corpus root, gitignored, `contract_version: 1`).
- Produces: skill writing `{corpus_root}/migrate-result.yaml` with `kind: migrate`; Task 7 adds the validator kind; Task 6 (flyio) executes it.

- [ ] **Step 1: Write the skill**

`skills/hiivmind-corpus-migrate/SKILL.md`, full content:

````markdown
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
- Related skills: hiivmind-corpus-build, hiivmind-corpus-refresh, hiivmind-corpus-refresh-headless, hiivmind-corpus-enrich-headless, hiivmind-corpus-enhance, hiivmind-corpus-status, hiivmind-corpus-navigate, hiivmind-corpus-graph, hiivmind-corpus-init, hiivmind-corpus-add-source, hiivmind-corpus-discover, hiivmind-corpus-register, hiivmind-corpus-bridge
````

- [ ] **Step 2: Add the migrate-result schema to headless-contract.md**

In `lib/corpus/patterns/headless-contract.md`: add a row to the file-locations table (`hiivmind-corpus-migrate | migrate-result.yaml | {corpus_root}/migrate-result.yaml`), add the `### migrate-result.yaml` schema section (the YAML block from the skill's Output Contract above, with field comments: `entries_migrated`/`entries_skipped` required, `id_parity` required boolean, `strategy` enum, `embeddings` always `skipped` for migrate), and extend the validation example with `--kind migrate`. Note under versioning: "adding a kind is backward-compatible; consumers reject only unknown `contract_version`."

- [ ] **Step 3: Commit**

```bash
git add skills/hiivmind-corpus-migrate/ lib/corpus/patterns/headless-contract.md
git commit -m "feat(migrate): headless v1→v2 migration skill with result contract

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Mark v1 read-only in refresh, refresh-headless, and enhance

**Files:**
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md` (Phase 1 format detection, ~lines 52-58)
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md` (Phase 1 validation)
- Modify: `skills/hiivmind-corpus-enhance/SKILL.md` (prerequisite validation)
- Modify: `lib/corpus/patterns/index-updating.md` (deprecation banner on v1 sections)

**Interfaces:**
- Consumes: `hiivmind-corpus-migrate` (Task 3) as the instructed remedy.

- [ ] **Step 1: Gate v1 in the three write-path skills**

In each skill's format-detection/validation phase, where `index_format == "v1"` is detected, replace the "proceed with v1 handling" path with:

- **refresh (interactive):** display
  `"This corpus uses the legacy v1 index (index.md as source of truth). v1 is read-only as of this release — refresh no longer updates it. Run hiivmind-corpus-migrate first (mechanical, headless), then refresh normally."`
  Offer: `"Run the migration now? [y/N]"` — if yes, CALL_SKILL hiivmind-corpus-migrate then re-enter refresh Phase 1; if no, EXIT without modifying anything.
- **refresh-headless:** write the result file with `errors: ["v1-index: read-only — run hiivmind-corpus-migrate"]`, all sources `status: skipped-manual`, zero index_changes, and ABORT. (Contract unchanged — this reuses existing fields.)
- **enhance:** same message as refresh, EXIT (no auto-offer — enhance sessions are topic-focused; migration is a separate decision).

Keep the format-detection code itself — v1 must still be *recognized* to route to the message.

- [ ] **Step 2: Banner in index-updating.md**

At the top of the v1 sections of `lib/corpus/patterns/index-updating.md`, insert:

```markdown
> **DEPRECATED — v1 is read-only.** As of wave 2, no skill writes v1 indexes;
> refresh/enhance detect v1 and instruct `hiivmind-corpus-migrate`. These rules
> are retained for one release for reference and for the migrate skill's
> understanding of the v1 entry-line format, then deleted.
```

- [ ] **Step 3: Verify and commit**

```bash
grep -n "read-only\|hiivmind-corpus-migrate" skills/hiivmind-corpus-refresh/SKILL.md skills/hiivmind-corpus-refresh-headless/SKILL.md skills/hiivmind-corpus-enhance/SKILL.md lib/corpus/patterns/index-updating.md
git add -A && git commit -m "feat(refresh,enhance): v1 indexes are read-only — instruct migration

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Un-defer tiered v2 in build; derivation DAG pattern; consistency sweep; CLAUDE.md

**Files:**
- Modify: `skills/hiivmind-corpus-build/SKILL.md` (Phase 3 ~line 227-247, Phase 8 ~line 645-673)
- Create: `lib/corpus/patterns/derivation-dag.md`
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md` (source-type table, Phase 2/3: add `obsidian` row; note `pdf` is a pre-processing concern of `local`, not a source type)
- Modify: `CLAUDE.md`
- Modify: `commands/hiivmind-corpus.md` (Available Skills table: add migrate)
- Modify: every other skill's `## Reference` / Related Skills list (add hiivmind-corpus-migrate): `init`, `add-source`, `build`, `enhance`, `refresh`, `refresh-headless`, `enrich-headless`, `discover`, `navigate`, `register`, `status`, `graph`, `bridge`

**Interfaces:**
- Consumes: renderer (Task 2), `render:` schema (Task 1).

- [ ] **Step 1: Build Phase 3 — segmentation now writes render config**

In the Phase 3 strategy table & follow-up, after "If tiered or by-source selected, collect section definitions from user." add:

```markdown
Record the decision as the `render:` block in config.yaml (see
`patterns/config-parsing.md`): `strategy: tiered` with the collected
`sections` (id, title, description), or `strategy: single`. "By source"
is tiered with one section per source id. Section membership is written
per-entry (`section:` field) during Phase 5 index generation, using the
section definitions as assignment targets.
```

- [ ] **Step 2: Build Phase 8 — replace the deferred line**

Old (line ~650): `4. If tiered: write each `index-{section}.md` sub-index file (v1 format only — tiered v2 is deferred)`

New: `4. Run \`bash render-index.sh index.yaml\` — with \`render.strategy: tiered\` this also emits every \`index-{section}.md\` sub-index (see patterns/index-rendering.md); no hand-written sub-indexes, ever.`

(Also delete the now-redundant separate step 3/4 split if it duplicates the render call — steps become: write index.yaml → copy render-index.sh → render.)

- [ ] **Step 3: Create patterns/derivation-dag.md**

```markdown
# Pattern: Derivation DAG — what skills write vs what is derived

## The Rule

Skills only ever WRITE three files: `config.yaml`, `index.yaml`, `graph.yaml`.
Everything else in a corpus repository is a DERIVED ARTIFACT, regenerated
mechanically from those three:

```
config.yaml ─┐
             ├─→ render-index.sh ─→ index.md, index-{section}.md
index.yaml ──┤
             ├─→ embed.py ────────→ index-embeddings.lance/
graph.yaml ──┘                      chunks-embeddings.lance/
```

- `index.md` and every `index-*.md`: rendered by `render-index.sh`
  (patterns/index-rendering.md). Never hand-edited, never LLM-written.
- `*.lance/` embeddings: generated by `embed.py` from index.yaml (+ graph
  concepts). Regenerable at any time from the sources of truth.
- Result files (`*-result.yaml`): run outputs, gitignored, not corpus state.

## Why

One source of truth per fact. A hand edit to a derived file is lost on the
next render — if information belongs in the corpus, it goes in index.yaml
(entries), config.yaml (sources, render, build decisions), or graph.yaml
(concepts). The v1 format violated this (index.md was both storage and
presentation) and is read-only as of wave 2.

## Skill Checklist

| Skill | Writes | Renders/derives after |
|-------|--------|-----------------------|
| build | config.yaml, index.yaml, graph.yaml | render-index.sh, embed.py |
| refresh / refresh-headless | config.yaml, index.yaml | render-index.sh, embed.py |
| enhance | index.yaml, graph.yaml | render-index.sh, embed.py |
| enrich-headless | index.yaml | render-index.sh, embed.py |
| migrate | config.yaml, index.yaml | render-index.sh |
| graph | graph.yaml | embed.py (if concept text changed) |
| navigate / status / discover | nothing | — |

## Related Patterns

- index-rendering.md, index-format-v2.md, embeddings.md, headless-contract.md
```

- [ ] **Step 4: Source-type consistency sweep**

In `skills/hiivmind-corpus-refresh-headless/SKILL.md` Phase 2 detection table and Phase 3 "Other source types" list, add: `**Obsidian:** same as git when vault is a clone (`.source/{id}/`), or timestamp scan for direct local paths — see patterns/sources/obsidian.md`. Check `skills/hiivmind-corpus-refresh/SKILL.md` for the same gap and fix identically. PDF needs no row (it is `local`-source pre-processing per `sources/README.md`), but add that one-line clarification to the README taxonomy table's footnote.

- [ ] **Step 5: CLAUDE.md and reference sweeps**

In `CLAUDE.md`:
- Architecture tree + Naming Convention + Skill Lifecycle: add `hiivmind-corpus-migrate` (build-side, "one-shot v1→v2").
- Pattern table: add `derivation-dag.md` row.
- Key Design Decisions: add "**Tiering is render-time**: one index.yaml; `render:` block drives single vs tiered output. v1 is read-only legacy (migrate skill)."
- Cross-cutting table: collapse "Tiered indexes | build, enhance, refresh | Detection logic, update handling" to "Tiered rendering | build, migrate, refresh (re-render only) | `render:` block, section field — patterns/index-rendering.md"; update the "Index updating" row's skill list to note v1 is read-only.
- Dependency chain: add `migrate ──► index.yaml + render-index.sh (one-shot v1→v2)`.

In `commands/hiivmind-corpus.md`: add the migrate row to Available Skills.

Add `hiivmind-corpus-migrate` to every skill's Reference/Related Skills section (13 skills listed in Files above).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(build): tiered v2 via render config; derivation-dag pattern; migrate skill wiring

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6 (Python tail): `validate_result.py` migrate kind + backlog + PR

**Files:**
- Modify: `lib/corpus/scripts/validate_result.py`
- Modify: `lib/corpus/scripts/tests/test_validate_result.py` (one test)
- Modify: `docs/backlog/index.md` (03 → In progress)

**Interfaces:**
- Consumes: migrate-result schema (Task 3). Existing internals: `validate(data, kind) -> list[str]` with `_require()` helper; kind enums at module top.

- [ ] **Step 1: Add the migrate kind**

In `validate_result.py`: add `"migrate"` to the CLI `--kind` choices and a `_validate_migrate(data, errors)` branch checking: `entries_migrated` int required; `entries_skipped` list required (each item needs `id` and `reason` strings); `sections` list of strings required; `strategy` in `{"tiered", "single"}`; `id_parity` bool required; `embeddings` == `"skipped"`; plus the shared header checks (contract_version 1, kind match, corpus, run_at, errors list) already applied by `validate()`.

- [ ] **Step 2: One test + suite**

Add to `test_validate_result.py` a `test_valid_migrate_result` mirroring the existing valid-refresh test with the YAML block from Task 3's Output Contract. Run:

```bash
uv run --group dev pytest lib/corpus/scripts/tests/test_validate_result.py -q
```

Expected: all pass.

- [ ] **Step 3: Backlog, full suite, push, PR**

Set backlog 03 → `In progress (wave 2)`. Then:

```bash
uv run --group dev pytest -q -m "not model"       # expected: all pass
git add -A && git commit -m "feat(contract): migrate kind in validate_result; backlog 03 in progress

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin feature/wave2-tiered-v2
gh pr create --title "feat: tiered v2 rendering, migrate skill, v1 read-only (backlog 03)" --body "$(cat <<'EOF'
Implements backlog item 03 (docs/backlog/03-retire-v1-tiered-v2-rendering.md), waves: rendering → migration → read-only gating. v1 write-path deletion is deliberately deferred one release.

- render: config block + entry section field; render-index.sh emits index.md + index-{section}.md from one index.yaml (tiering is render-time)
- New headless hiivmind-corpus-migrate skill (v1→v2, ID-parity diff-check, migrate-result.yaml contract kind)
- refresh / refresh-headless / enhance now treat v1 as read-only and instruct migration
- patterns/derivation-dag.md names the write-vs-derived rule; obsidian added to refresh type tables
- Build Phase 8 "tiered v2 is deferred" removed; segmentation decisions persist as the render: block

Proving-case migration of hiivmind-corpus-flyio follows in that repo once this merges.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 7: Migrate flyio (proving case — AFTER the plugin PR merges and the installed plugin updates)

**Files:** all in `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-flyio` — creates `index.yaml`, `render-index.sh`, rewrites `index.md` + 8 sub-indexes, adds `render:` block to `config.yaml`, gitignores `migrate-result.yaml`.

**Interfaces:**
- Consumes: the released migrate skill (Task 3) and renderer (Task 2). Precondition: the *installed* hiivmind-corpus plugin includes this wave.

- [ ] **Step 1: Branch and run the migration**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus-flyio
git checkout main && git pull && git checkout -b migrate/v2
```

Invoke `hiivmind-corpus-migrate` with `corpus_path: /Users/nathanielramm/git/hiivmind/hiivmind-corpus-flyio`. Expect: ~9 v1 files parsed, 8 sections + quick_reference derived, sparse clone of superfly/docs into `.source/flyio/`, entries with missing files reported as skipped (upstream moved files since 2026-07-02 — expected).

- [ ] **Step 2: Validate the result and the acceptance criteria**

```bash
uv run <plugin>/lib/corpus/scripts/validate_result.py migrate-result.yaml --kind migrate   # exit 0
yq '.render.strategy' config.yaml            # "tiered"
yq '.meta.entry_count' index.yaml            # > 0, ≈ v1 entry count minus skipped
ls index-*.md                                # 8 files matching render.sections ids
bash render-index.sh index.yaml && git diff --stat index*.md   # idempotent: no diff on re-render
```

Navigational equivalence spot-check: pick 5 entry IDs from the OLD index (use `git show main:index-machines.md`), confirm each appears in the new rendered output with the same title and summary.

- [ ] **Step 3: Commit, push, PR; report skipped entries for human review**

```bash
git add -A && git commit -m "feat: migrate index to v2 (index.yaml + tiered rendering)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin migrate/v2
gh pr create --title "Migrate to v2 index (tiered rendering from index.yaml)" --body "<summary: entries migrated/skipped with reasons, sections, id_parity result>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

List `entries_skipped` in the PR body — these are the only human-judgment items. After merge: flip backlog 03 → Done, and note in `docs/backlog/index.md` that v1 write-path *deletion* is the follow-up for the next release.
