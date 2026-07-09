# Pattern: Headless Result Contract

Headless skills communicate with orchestrators through **result files written
to disk**, not by prose parsing. The printed `---headless-result` block is
retained for human-readable logs only — orchestrators MUST read the file.

## File locations

| Skill | File | Default path |
|-------|------|--------------|
| hiivmind-corpus-refresh-headless | refresh-result.yaml | `{corpus_root}/refresh-result.yaml` |
| hiivmind-corpus-enrich-headless | enrich-result.yaml | `{corpus_root}/enrich-result.yaml` |
| hiivmind-corpus-migrate | migrate-result.yaml | `{corpus_root}/migrate-result.yaml` |
| hiivmind-corpus-status-headless | status-result.yaml | `{corpus_root}/status-result.yaml` |
| hiivmind-corpus-graph (--headless) | graph-validate-result.yaml | `{corpus_root}/graph-validate-result.yaml` |

Result files are transient run artifacts: the skill ensures both filenames are
listed in the corpus `.gitignore` (appending if missing) before writing.
Orchestrators should treat the file as consumed after parsing; a subsequent
run overwrites it.

## Versioning

`contract_version` is a required integer. Current version: **1**. Consumers
MUST reject files with versions they don't support (validate_result.py does).
Additive optional fields do not bump the version; renamed/removed/retyped
fields do. Adding a new `kind` (e.g. `migrate`) is backward-compatible;
consumers reject only unknown `contract_version`, not unknown kinds they were
not asked to validate.

## Validation

    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py refresh-result.yaml --kind refresh
    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py migrate-result.yaml --kind migrate
    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py status-result.yaml --kind status
    uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py graph-validate-result.yaml --kind graph-validate

Orchestrators should validate before consuming and treat exit 1/2 as a failed
run (report, do not commit). Exit codes: 0 valid, 1 invalid (errors on
stderr), 2 file missing/unparseable.

## Schemas

### refresh-result.yaml (written by hiivmind-corpus-refresh-headless)

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

### enrich-result.yaml (written by hiivmind-corpus-enrich-headless)

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

### migrate-result.yaml (written by hiivmind-corpus-migrate)

```yaml
contract_version: 1
kind: migrate
corpus: <name>                        # str, required
run_at: <ISO 8601>                    # str, required
entries_migrated: <int>               # required — entries written to index.yaml
entries_skipped:                      # required list (may be empty) — human review items
  - id: <entry id>                    # str, required
    reason: file-missing | clone-failed   # str, required
sections: [<str>, ...]                # required — section ids written to render.sections
strategy: tiered | single             # required enum
id_parity: <bool>                     # required — true only if the render preserved every non-skipped v1 ID
embeddings: skipped                   # required — migrate never generates embeddings
errors: [<str>, ...]                  # required
```

### status-result.yaml (written by hiivmind-corpus-status-headless)

```yaml
contract_version: 1
kind: status
corpus: <name>                        # str, required
run_at: <ISO 8601>                    # str, required
index_format: v2 | v1 | none          # required enum
sources:                              # required list (may be empty)
  - id: <source id>                   # str, required
    type: <source type>              # str, required
    freshness: current | behind | unknown   # required enum
stale_entries: <int>                  # required — entries flagged stale in the index
embeddings_lag: <int or null>         # required key; null = no embeddings present
refresh_needed: <bool>                # required — any source behind OR stale_entries > 0
errors: [<str>, ...]                  # required
```

### graph-validate-result.yaml (written by hiivmind-corpus-graph --headless)

```yaml
contract_version: 1
kind: graph-validate
corpus: <name>                        # str, required
run_at: <ISO 8601>                    # str, required
concepts: <int>                       # required — concept count
relationships: <int>                  # required — relationship count
issues:                               # required list (may be empty)
  - severity: error | warning         # required enum
    rule: <str>                       # required — rule id from patterns/graph.md
    detail: <str>                     # required — human-readable, includes offending id
valid: <bool>                         # required — true when zero error-severity issues
errors: [<str>, ...]                  # required — runtime failures, not findings
```

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
