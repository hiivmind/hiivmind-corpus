---
name: hiivmind-corpus-build-headless
description: >
  Non-interactive (re)build of a corpus index for pipelines. Replays the
  decisions captured in config.build (segmentation, organization, skip_sections,
  embeddings, verify prefs) instead of prompting, regenerates index.yaml + the
  rendered markdown, optional graph and embeddings, and writes build-result.yaml
  (headless contract). Triggers: "headless build", "rebuild corpus headless",
  "build result file", scheduled rebuilds. Users normally want `build`.
---

# Corpus Build (Headless)

Non-interactive variant of `hiivmind-corpus-build`. Reconstructs `index.yaml`
(and the rendered markdown, optional `graph.yaml`, optional embeddings) by
**replaying** the decisions the interactive build captured in `config.build`.
No prompts, no `AskUserQuestion` — every Phase 3/4/7 answer comes from config.

**Principle: interactive skills capture decisions; headless skills replay them.**
This skill is the replay counterpart of the interactive build's decision capture
(see `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md` § The `build:`
Block). It follows the SAME phase pipeline as `hiivmind-corpus-build`; only the
interactive prompts are replaced by config reads.

**Inputs:**
- `corpus_path` (optional; defaults to cwd)
- `result_path` (optional; defaults to `{corpus_path}/build-result.yaml`)

## State

```yaml
computed:
  corpus_root: null
  config: null
  build: null              # config.build replay block (REQUIRED)
  sources: []
  scan_results: null
  strategy: null           # single | tiered (from config.render)
  index: null
  entry_count: 0
  graph_status: null       # generated | skipped | not-configured
  embedding_status: null   # updated | skipped | no-model | not-installed
  verification: null       # { sampled, failed, drift_entries }
  errors: []
  error: null              # fatal → ABORT
```

## Phase 1: Validate & Load Decisions

Resolve corpus root from `corpus_path` or cwd. Read `config.yaml`
(`${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md`). ABORT (write a
result with `error` populated) if:

- `config.yaml` missing, or `sources` is empty.
- **`config.build` is absent.** Headless build has nothing to replay — the
  decisions were never captured. Write `errors: ["no-build-block — run the
  interactive hiivmind-corpus-build once to capture decisions"]` and ABORT.
  (This is the deliberate gate: build-headless never *invents* organization.)

Load `computed.build = config.build` and `computed.strategy = config.render.strategy // "single"`.

## Phase 2: Prepare & Scan Sources

Identical to `hiivmind-corpus-build` Phases 1–2 — reuse them, do not re-describe:
- Prepare each source (clone/cache/verify) per its type; for git prefer the
  sparse clone in `patterns/sources/git.md`.
- Scan with parallel `source-scanner` agents (2+ sources) or inline (single).
  Indexing depth (sections/chunking) comes from each source's persisted
  `sections:`/`chunking:` config — no prompt.

Record per-source `{id, type, files_scanned}` for the result.

## Phase 3: Segmentation (replayed)

No prompt. Use `computed.strategy` and, when `tiered`, the section definitions
already in `config.render.sections`. "By source" corpora are tiered with one
section per source id (as recorded during the interactive build).

## Phase 4: Index Generation (replayed)

Generate `index.yaml` exactly as build Phase 5, but drive organization from
`computed.build` instead of asking:
- **`skip_sections`:** files under a skipped section are NOT indexed — count them
  into `errors[]` as `"excluded-by-config: {path}"` (informational).
- **`organization`:** `by-source` → assign each entry `section = source.id`;
  `by-topic` → assign `section`/`category` by subject; `mixed` → topic-first.
- **`use_case` / `source_priorities`:** bias entry depth/ordering as the
  interactive build would (higher-priority sources get richer entries).

See `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-updating.md` § New-entry
placement — the same placement rules the headless refresh uses.

## Phase 5: Graph (optional, deterministic)

Only if at least one source produced `extraction:` data (build Phase 6
precondition). Non-interactive: **auto-accept** the clustered concepts (no
rename/merge/discard prompt), generate relationships, write `graph.yaml`, and
populate `concepts[]` on the matched index.yaml entries. Set
`computed.graph_status = generated`. No extraction data → `not-configured`.
Extraction present but clustering yields nothing → `skipped`.

## Phase 6: Embeddings (optional, replayed)

Replay `computed.build.embeddings`:
- `false` → `computed.embedding_status = skipped`.
- `true` → run `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py`:
  - `ready` → `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/` → `updated`.
  - `no-model` → `no-model` (NEVER download a model during automation).
  - not installed → `not-installed`.
- If any source has `chunking.enabled`, also generate `chunks-embeddings.lance/`
  per build Phase 7b (same detect gating).

## Phase 7: Verification (replayed)

Replay `computed.build.verify_on_build`:
- `false` → `computed.verification = { sampled: 0, failed: 0, drift_entries: [] }`.
- `true` → run `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/verify_entries.py
  --index index.yaml --source-root .source/ --config config.yaml --sample
  {config.build.verify_sample_size // 20}`, then LLM-verify the sampled previews.
  Record `sampled`, `failed`, and the drifting entry ids in `drift_entries`.
  **Do NOT prompt to regenerate** — headless only reports drift; a later
  `enrich-headless`/`enhance` fixes it.

## Phase 8: Save, Render, Result

1. Write `index.yaml` (`meta.generated_at = now()`, `meta.entry_count`).
2. Copy `${CLAUDE_PLUGIN_ROOT}/templates/render-index.sh` to the corpus root
   (overwrite) and run `bash render-index.sh index.yaml` — with `tiered` this
   emits every `index-{section}.md`. Never hand-write sub-indexes.
3. Update config metadata: `index.last_updated_at = now()`, per-source
   `last_indexed_at` (and `last_commit_sha` for git sources at clone HEAD).
   Refresh `config.build.decided_at` is NOT changed — replay does not re-decide.
4. Write the result file (contract below).

## Output Contract

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/headless-contract.md`

Ensure the corpus `.gitignore` lists `build-result.yaml` (append if missing),
then write `result_path` (default `{corpus_root}/build-result.yaml`):

```yaml
contract_version: 1
kind: build
corpus: {name from config}
run_at: {ISO 8601}
entries: {int}                   # index.meta.entry_count
sources:                         # one per scanned source
  - id: {source id}
    type: {source type}
    files_scanned: {int}
strategy: single | tiered
sections: [{section ids}]        # [] when single
graph: generated | skipped | not-configured
embeddings: updated | skipped | no-model | not-installed
verification:
  sampled: {int}
  failed: {int}
  drift_entries: [{entry id}, ...]
errors: [{description}, ...]      # includes excluded-by-config notes
```

Validate before finishing:
`uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py {result_path} --kind build`

Write the result file even on ABORT (with `error`/`errors` populated). Echo the
same YAML between `---headless-result` and `---` markers as a log convenience —
pipelines MUST read the file.

## Error Handling

| Error | Handling |
|-------|----------|
| No config.yaml / no sources | ABORT with result `errors` populated |
| No `config.build` block | ABORT: "no-build-block — run interactive build once" |
| A source fails to prepare/scan | Mark that source failed in `errors[]`; continue with the rest |
| detect.py unavailable / no-model | Skip embeddings (`no-model`/`not-installed`); never download |
| render-index.sh missing | Copy it from the plugin templates before rendering |

## Reference

- Patterns: `config-parsing.md` (§ The `build:` Block), `index-format-v2.md`, `index-rendering.md`, `index-updating.md`, `scanning.md`, `embeddings.md`, `graph.md`, `headless-contract.md`, `sources/git.md`
- Related skills: hiivmind-corpus-build (interactive), hiivmind-corpus-refresh-headless, hiivmind-corpus-enrich-headless, hiivmind-corpus-status-headless, hiivmind-corpus-migrate, hiivmind-corpus-init, hiivmind-corpus-add-source, hiivmind-corpus-enhance, hiivmind-corpus-refresh, hiivmind-corpus-navigate, hiivmind-corpus-graph, hiivmind-corpus-bridge, hiivmind-corpus-discover, hiivmind-corpus-register, hiivmind-corpus-status
