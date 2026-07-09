# Wave 4: Decision Capture + Headless Surfaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist every interactive build decision in a `build:` config block so headless skills can replay them; add contract-emitting headless surfaces for status and graph validation; and surface cumulative embedding drift (`embeddings_lag`) in status output and refresh PRs.

**Architecture:** Principle: **interactive skills capture decisions; headless skills replay them.** The existing (informal) `config.build.verify_on_build` / `verify_sample_size` keys grow into a documented `build:` block covering all Phase 3/4 answers. Two thin headless skills reuse the wave-1 result-file contract (`kind: status`, `kind: graph-validate`). `embeddings_lag` is computed by comparing entry `last_indexed` timestamps against the Lance `_meta` embed timestamp via a tiny read-only script.

**Tech Stack:** Markdown skills/patterns; Python tail: `lance_meta.py` (new, PEP 723), `validate_result.py` (two new kinds).

## Global Constraints

- Repo: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus`, branch `feature/wave4-decision-capture` off up-to-date main. **Prerequisite: wave 2 (backlog 03) is merged** — the `render:` block exists and segmentation persists there; this wave must not re-invent it. Depends conceptually on wave 1's contract (merged, PR #47).
- Order: skills/pattern docs first, Python last (user feedback, wave 1). Tests light.
- Contract stays `contract_version: 1`; new kinds are backward-compatible additions.
- `build-headless` (backlog stretch goal) is deliberately OUT of scope — YAGNI until a re-build consumer exists. The `build:` block makes it *possible* later; that is enough for acceptance.
- Scheduler repo change (optional pre-check wiring) is a single small edit to `TEMPLATE-corpus-refresh.md` (exists after wave 3) — own branch/PR in `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler`.
- Commits: conventional, ending `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Acceptance (backlog 06): an interactively built corpus records all build decisions in config.yaml; headless enrichment places new entries per recorded organization without prompting; `status` reports embedding lag; orchestrators can run status/validate across corpora with machine-readable results.

---

### Task 1: `build:` block schema + build skill writes it

**Files:**
- Modify: `lib/corpus/patterns/config-parsing.md` (new section documenting the block)
- Modify: `templates/config.yaml.template` (commented example)
- Modify: `skills/hiivmind-corpus-build/SKILL.md` (Phase 8 "Update config metadata", ~line 652; Phases 3/4/7/7c pointers)

**Interfaces:**
- Produces: `config.build.*` keys that Task 2 (replay) and any future build-headless read. Exact keys below are the contract.

- [ ] **Step 1: Document the schema in config-parsing.md**

Add a top-level section:

````markdown
## The `build:` Block (decision capture)

**Principle: interactive skills capture decisions; headless skills replay
them.** The build skill records every Phase 3/4 answer here at save time.
Enhance, refresh, and enrich-headless read these instead of guessing (or
re-asking). A future `build-headless` re-build becomes possible because this
block is a complete replay script of the interactive session.

```yaml
build:
  use_case: reference            # reference | learning | troubleshooting | mixed
  organization: by-topic         # by-topic | by-source | mixed
  segmentation: tiered           # single | tiered | by-source | by-section
                                 # (section definitions live in render.sections)
  source_priorities: [polars, polars-blog]   # ordered, multi-source only; omit if single
  skip_sections: [changelog, internal]       # [] if none
  embeddings: true               # user opted in during Phase 7
  verify_on_build: true          # Phase 7c preference (pre-existing key, now documented)
  verify_sample_size: 20         # pre-existing key, now documented
  decided_at: "2026-07-09T00:00:00Z"
```

Notes: `sections:`, `chunking:`, and `extraction:` remain per-source config
(indexing-depth answers already persist there). `render:` holds the section
definitions (see wave 2). Absent block = legacy corpus: skills fall back to
current heuristics and SHOULD write the block when the user next answers the
questions interactively.
````

Add the same block, commented out, to `templates/config.yaml.template`.

- [ ] **Step 2: Build skill writes the block**

In build SKILL.md Phase 8 "Update config metadata", add step:

```markdown
5. Write the `build:` block (see patterns/config-parsing.md § build: block):
   use_case, organization, segmentation, source_priorities (multi-source only),
   skip_sections, embeddings (Phase 7 opt-in outcome), verify_on_build /
   verify_sample_size (Phase 7c settings), decided_at = now(). Preserve any
   existing keys the user set by hand.
```

In Phases 3 and 4, after each ASK, add the one-liner: `(Recorded in config.build at Phase 8 — see patterns/config-parsing.md.)` In Phase 7 (embeddings opt-in) note the outcome is recorded as `build.embeddings`.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(build): capture all interactive decisions in config.build block

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Replay in enhance / refresh / enrich-headless

**Files:**
- Modify: `skills/hiivmind-corpus-enhance/SKILL.md`
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md` and `skills/hiivmind-corpus-refresh-headless/SKILL.md`
- Modify: `skills/hiivmind-corpus-enrich-headless/SKILL.md`
- Modify: `lib/corpus/patterns/index-updating.md` (A-rule reads replayed prefs)

**Interfaces:**
- Consumes: `config.build.organization`, `config.build.skip_sections`, `config.build.use_case` (Task 1).

- [ ] **Step 1: index-updating.md — new-entry placement honors the block**

In the v2 "A (added file)" rule, add:

```markdown
Before creating a placeholder entry for an added file, consult `config.build`:
- `skip_sections`: if the file's path or section matches a skipped section,
  do NOT create an entry — log it as intentionally excluded instead.
- `organization`: assign `category` (and `section`, if tiered) consistent with
  the recorded organization — `by-source` corpora group new entries under
  their source's section; `by-topic` corpora place them by subject.
Absent block → current behavior (best-effort category, main index).
```

- [ ] **Step 2: Skill-side awareness**

- **enhance:** in the phase that decides where deepened entries go, replace the "infer organization from existing index" instruction with: read `config.build.organization` / `skip_sections` first; fall back to inference only when the block is absent. Never ask the user a question already answered by the block — display the replayed value instead (`"Using recorded organization: by-topic"`).
- **refresh / refresh-headless:** in the Phase that applies index changes, add one line: `Placement of added entries follows config.build (see patterns/index-updating.md) — skip_sections exclusions are logged in the result file's errors[] as "excluded-by-config: {path}" (informational, not a failure).`
- **enrich-headless:** in the concept-assignment/save phase, add: `Enriched entries keep their existing category/section; new placement decisions follow config.build.organization as documented in patterns/index-updating.md.`

- [ ] **Step 3: Verify and commit**

```bash
grep -n "config.build\|build\." skills/hiivmind-corpus-enhance/SKILL.md skills/hiivmind-corpus-refresh/SKILL.md skills/hiivmind-corpus-refresh-headless/SKILL.md skills/hiivmind-corpus-enrich-headless/SKILL.md lib/corpus/patterns/index-updating.md | grep -i "organization\|skip_sections"
git add -A && git commit -m "feat(replay): enhance/refresh/enrich honor recorded build decisions

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: `hiivmind-corpus-status-headless` skill

**Files:**
- Create: `skills/hiivmind-corpus-status-headless/SKILL.md`
- Modify: `lib/corpus/patterns/headless-contract.md` (status-result.yaml schema)

**Interfaces:**
- Consumes: existing status skill's freshness checks (`patterns/status.md`, `patterns/freshness.md`); `lance_meta.py` (Task 6 — the skill references it; script lands in the Python tail of this same branch).
- Produces: `{corpus_root}/status-result.yaml`, `kind: status`. The scheduler pre-check (Task 7) consumes `refresh_needed`.

- [ ] **Step 1: Write the skill**

`skills/hiivmind-corpus-status-headless/SKILL.md`, full content:

````markdown
---
name: hiivmind-corpus-status-headless
description: >
  Non-interactive corpus freshness check for pipelines. Compares upstream SHAs
  against config.yaml, counts stale entries and embedding lag, and writes
  status-result.yaml (headless contract). Cheap: no clones, no index edits.
  Triggers: "headless status", "status result file", scheduler pre-checks.
---

# Corpus Status (Headless)

Read-only freshness snapshot of ONE corpus, written as a machine-readable
result file. Designed as a cheap pre-check before a full refresh (ls-remote,
not clone) and for nightly status sweeps across corpora.

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
   (see patterns/embeddings.md § Embedding Lag). No lance dir → `null`.
5. **Write result** (contract below), echo a one-line summary. Never modify
   the corpus. Write the result file even on ABORT, with `error` populated.

## Output Contract

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
Ensure `status-result.yaml` is in the corpus .gitignore.

## Reference

- Patterns: `status.md`, `freshness.md`, `config-parsing.md`, `embeddings.md`, `headless-contract.md`
- Related skills: hiivmind-corpus-status (interactive), hiivmind-corpus-refresh-headless, hiivmind-corpus-enrich-headless, hiivmind-corpus-migrate, hiivmind-corpus-discover, hiivmind-corpus-navigate, hiivmind-corpus-build, hiivmind-corpus-refresh, hiivmind-corpus-enhance, hiivmind-corpus-graph, hiivmind-corpus-bridge, hiivmind-corpus-init, hiivmind-corpus-add-source, hiivmind-corpus-register
````

- [ ] **Step 2: headless-contract.md**

Add the file-locations row (`hiivmind-corpus-status-headless | status-result.yaml | {corpus_root}/status-result.yaml`), the `### status-result.yaml` schema section (YAML above with required/optional annotations: `index_format` enum required; `sources[].freshness` enum required; `stale_entries` int required; `embeddings_lag` int-or-null required; `refresh_needed` bool required), and `--kind status` in the validation examples.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(status): headless status skill emitting status-result.yaml

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Headless mode for graph validation

**Files:**
- Modify: `skills/hiivmind-corpus-graph/SKILL.md` (validate subcommand, ~lines 69-78)
- Modify: `lib/corpus/patterns/headless-contract.md` (graph-validate-result.yaml schema)

**Interfaces:**
- Produces: `{corpus_root}/graph-validate-result.yaml`, `kind: graph-validate`. Intended as a PR check on corpus repos.

- [ ] **Step 1: Extend the validate subcommand**

After the existing `### validate` procedure, add:

````markdown
**Headless mode** (`validate --headless`, or `headless: true` input): run the
same validation rules non-interactively and write
`{corpus_path}/graph-validate-result.yaml`:

```yaml
contract_version: 1
kind: graph-validate
corpus: {name}
run_at: {ISO 8601}
concepts: {int}
relationships: {int}
issues:
  - severity: error | warning
    rule: {rule id from patterns/graph.md § Validation Rules}
    detail: "{human-readable description with the offending id}"
valid: {bool}                    # true when zero error-severity issues
errors: []                       # runtime failures, not validation findings
```

Exit semantics for pipelines: emit the file always; `valid: false` when any
error-severity issue exists. Validate the file with
`uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py graph-validate-result.yaml --kind graph-validate`.
Ensure the filename is gitignored in the corpus. Note: rule 2 of the
interactive procedure loads `index.md`; headless mode loads `index.yaml` when
present (v2) since entry IDs are the join key being checked.
````

- [ ] **Step 2: headless-contract.md**

Add the locations-table row, the `### graph-validate-result.yaml` schema section (YAML above), and the `--kind graph-validate` example.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(graph): headless validate writing graph-validate-result.yaml

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: `embeddings_lag` in interactive status, refresh result, and docs wiring

**Files:**
- Modify: `skills/hiivmind-corpus-status/SKILL.md` (§ Embeddings, ~line 190)
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md` (Output Contract: optional field)
- Modify: `lib/corpus/patterns/embeddings.md` (new § Embedding Lag)
- Modify: `lib/corpus/patterns/headless-contract.md` (optional `embeddings_lag` on refresh-result)
- Modify: `CLAUDE.md` and `commands/hiivmind-corpus.md` (alignment sweep for the two new skills + lag)
- Modify: every existing skill's Reference list (add status-headless)

**Interfaces:**
- Consumes: `lance_meta.py` CLI (Task 6): `uv run …/lance_meta.py <lance_dir>` → JSON `{"embedded_at": "...", "model": "...", "row_count": N}` on stdout, exit 2 if no `_meta` table.

- [ ] **Step 1: patterns/embeddings.md — define the metric once**

```markdown
## Embedding Lag

`embeddings_lag` = number of index.yaml entries whose `last_indexed` postdates
the Lance `_meta.embedded_at` timestamp. It measures cumulative drift between
the index and its embeddings across runs (per-run status like
`embeddings: skipped | no-model | deferred` cannot see accumulation).

Compute:
1. `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/lance_meta.py index-embeddings.lance/`
   → `embedded_at` (exit 2 → no embeddings → lag is null)
2. `EMB_AT={embedded_at} yq '[.entries[] | select(.last_indexed > env(EMB_AT))] | length' index.yaml`

Lag > 0 with no pending stale entries means embeddings should be regenerated
(enhance or enrich-headless re-embed paths). Reported by: status (interactive),
status-headless (result file), refresh-headless (optional result field →
scheduler PR body).
```

- [ ] **Step 2: Skill wiring**

- **status SKILL.md § Embeddings:** add `Embedding lag: {n} entries indexed since last embed` line to the report, computed per patterns/embeddings.md § Embedding Lag (null → "no embeddings").
- **refresh-headless Output Contract:** add optional `embeddings_lag: {int|null}` field after `embeddings:`, computed the same way post-Phase-5 (null when no lance dir).
- **headless-contract.md refresh-result schema:** add `embeddings_lag` as optional int-or-null with the comment `# cumulative drift; see patterns/embeddings.md § Embedding Lag`.

- [ ] **Step 3: CLAUDE.md / gateway alignment sweep**

- Architecture tree, naming list, lifecycle "Headless pipeline" line: add `status-headless`; graph skill line mentions headless validate.
- Cross-cutting table: extend "Headless result contract" row's skill list with status-headless and graph; add row `Decision capture | build, enhance, refresh, refresh-headless, enrich-headless | config.build block — patterns/config-parsing.md`; extend Embeddings row with `embeddings_lag`.
- Dependency chain: add `status-headless ──► status-result.yaml` and `graph --headless ──► graph-validate-result.yaml`.
- `commands/hiivmind-corpus.md`: add status-headless row (pipeline-facing).
- Add `hiivmind-corpus-status-headless` to every skill's Reference section.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(status): embeddings_lag metric; alignment sweep for headless surfaces

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6 (Python tail): `lance_meta.py`, validator kinds, tests, PR

**Files:**
- Create: `lib/corpus/scripts/lance_meta.py`
- Modify: `lib/corpus/scripts/validate_result.py` (kinds `status`, `graph-validate`; optional `embeddings_lag` on refresh)
- Modify: `lib/corpus/scripts/tests/test_validate_result.py` (two tests)
- Modify: `.github/workflows/ci.yml` (smoke line), `docs/backlog/index.md` (06 → In progress)

**Interfaces:**
- Consumes: `META_TABLE` from `lib/corpus/scripts/constants.py`; existing `validate(data, kind)` / `_require()` internals.
- Produces: the exact CLI contract Task 5 documented.

- [ ] **Step 1: lance_meta.py**

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["lancedb>=0.20.0", "pyarrow>=15.0.0"]
# ///
"""Print the _meta table of a Lance embeddings dir as JSON.

Usage: lance_meta.py <lance_dir>
Exit codes: 0 ok, 1 usage/open error, 2 no _meta table.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import META_TABLE


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lance_meta.py <lance_dir>", file=sys.stderr)
        return 1
    import lancedb

    try:
        db = lancedb.connect(sys.argv[1])
        names = db.table_names()
    except Exception as exc:  # unreadable / not a lance dir
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if META_TABLE not in names:
        print("error: no _meta table", file=sys.stderr)
        return 2
    row = db.open_table(META_TABLE).to_pandas().iloc[0].to_dict()
    row = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()}
    print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Check `embed.py` for the actual `_meta` column names before finishing — if the timestamp column is named differently than `embedded_at`, emit it as-is (the JSON passes all columns through) and align the docs in Task 5 Step 1 to the real name.

Smoke: `uv run lib/corpus/scripts/lance_meta.py /Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb/index-embeddings.lance/` → JSON on stdout, exit 0.

- [ ] **Step 2: validate_result.py kinds**

- `--kind` choices += `status`, `graph-validate`.
- `_validate_status`: `index_format` in `{v2, v1, none}`; `sources` list (each: `id` str, `type` str, `freshness` in `{current, behind, unknown}`); `stale_entries` int; `embeddings_lag` int or None (key required, value nullable); `refresh_needed` bool.
- `_validate_graph_validate`: `concepts` int; `relationships` int; `issues` list (each: `severity` in `{error, warning}`, `rule` str, `detail` str); `valid` bool.
- refresh kind: accept optional `embeddings_lag` (int or None) — no error when absent.

- [ ] **Step 3: Tests + suite + smoke + PR**

Add `test_valid_status_result` and `test_valid_graph_validate_result` to `test_validate_result.py` (mirror the existing valid-refresh test using the YAML blocks from Tasks 3/4). Append to the CI smoke step: `uv run lib/corpus/scripts/lance_meta.py --help 2>/dev/null || true` is NOT useful (no --help); instead add `uv run lib/corpus/scripts/validate_result.py --help` already covers the validator — add nothing for lance_meta (it needs a real lance dir; local smoke in Step 1 suffices).

```bash
uv run --group dev pytest -q -m "not model"    # expected: all pass
```

Set backlog 06 → `In progress (wave 4)`. Commit, push, PR:

```bash
git add -A && git commit -m "feat(contract): status + graph-validate kinds; lance_meta.py for embedding lag

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin feature/wave4-decision-capture
gh pr create --title "feat: decision capture in config.build + headless status/graph surfaces (backlog 06)" --body "$(cat <<'EOF'
Implements backlog item 06 (docs/backlog/06-decision-capture-and-headless-surfaces.md).

- build: block records every interactive decision (use_case, organization, segmentation, priorities, skip_sections, embeddings opt-in, verify prefs); enhance/refresh/enrich replay instead of guessing
- New hiivmind-corpus-status-headless: cheap ls-remote freshness snapshot → status-result.yaml (kind: status); scheduler can pre-check before a full refresh
- graph validate --headless → graph-validate-result.yaml (kind: graph-validate), usable as a corpus-repo PR check
- embeddings_lag drift metric (lance_meta.py + yq) in status output, status-result, and optionally refresh-result
- build-headless deliberately deferred (stretch); the block makes it possible later

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 7: Scheduler pre-check wiring (separate repo, AFTER Task 6's PR merges and the plugin updates)

**Files:**
- Modify: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md` (Phase 3 head; exists after wave 3)

**Interfaces:**
- Consumes: `status-result.yaml` → `refresh_needed` (Task 3).

- [ ] **Step 1: Branch and add the optional pre-check**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler
git checkout main && git pull && git checkout -b feature/status-precheck
```

At the top of Phase 3 in `TEMPLATE-corpus-refresh.md`, before the CALL_SKILL of refresh-headless, insert:

````markdown
**Pre-check (cheap):** run the headless status skill first —

```
CALL_SKILL("hiivmind-corpus:hiivmind-corpus-status-headless", { corpus_path: computed.corpus_path })
```

Read `{corpus_path}/status-result.yaml` (validate with
`uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/validate_result.py ... --kind status`).
If `refresh_needed: false` AND `embeddings_lag` in (0, null): skip the refresh
entirely — clean up the branch (`git checkout main && git branch -d {branch}`),
report "already current (pre-check)" in the summary, and go to SUMMARY. If the
pre-check itself fails, log it and proceed with the full refresh — the
pre-check is an optimization, never a gate.
````

Also add `embeddings_lag` to the PR-body instruction in Phase 4: `report embeddings_lag from refresh-result.yaml when present and > 0 ("N entries await re-embedding").`

- [ ] **Step 2: Commit, push, PR**

```bash
git add TEMPLATE-corpus-refresh.md
git commit -m "feat: cheap status-headless pre-check before full refresh; report embeddings_lag

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin feature/status-precheck
gh pr create --title "feat: status-headless pre-check + embeddings_lag in PR body" --body "Wires backlog 06's status-headless as an optional pre-check: skip the full refresh when nothing changed upstream and no drift exists. Pre-check failure never blocks a refresh.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

After both PRs merge: flip backlog 06 → Done in `docs/backlog/index.md`.
