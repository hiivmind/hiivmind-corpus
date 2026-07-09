# Architectural & Procedural Evaluation: hiivmind-corpus

**Date:** 2026-07-09
**Scope:** Plugin skill suite, pattern library, Python scripts, scheduler repo (`hiivmind-corpus-scheduler`), and two reference corpora — `hiivmind-corpus-lancedb` (v2) and `hiivmind-corpus-flyio` (v1 tiered).
**Goal:** Enable richer headless orchestration (evidence-driven, no-human refresh flows), keep interactive workflows for corpus creation, rationalize source/output format patterns, and improve Python script portability.

Backlog items derived from this review are tracked in [index.md](index.md).

---

## TL;DR

The architecture is fundamentally sound — data-only corpus repos, a pattern library instead of hardcoded scripts, and a thin scheduler that delegates to a headless skill are all the right shapes. But the headless pipeline currently **opens loops it never closes**: the lancedb corpus has 148 of 193 entries flagged `stale: true` and 52 placeholder entries reading "Pending re-scan", merged to main on 2026-07-02 with nothing scheduled to ever resolve them. The single highest-value change is a headless *enrichment* stage that closes the stale loop before the PR is opened. Secondary priorities: retire the v1 index format (blocked on tiered-v2), consolidate the duplicated refresh logic and scheduler boilerplate, and give the Python scripts a real packaging story (PEP 723 + uv) instead of `python3` + `pip install` prose.

---

## 1. What's working well

- **Separation of engine and data.** Plugin = logic, corpus repos = data, scheduler = orchestration. Each layer is independently versionable and the recent commit history shows lessons flowing back upstream (e.g. the "entries go in existing sections" fix in v1.5.2 originated from automation behavior).
- **The headless/interactive split exists and is directionally right.** `refresh-headless` with a `---headless-result` YAML contract, and scheduler tasks that only handle branch/commit/PR, is a clean two-layer design.
- **Per-source-type patterns** (`patterns/sources/*.md`) with a decision tree in the README is a good taxonomy. Seven source types each with defined storage, change detection, and access methods.
- **v2 index as source of truth** with deterministic `render-index.sh` is the right derivation model — where it's actually used.

## 2. Headless workflows: the stale loop never closes (critical)

The headless refresh deliberately defers enrichment: modified entries get `stale: true`, added entries get `summary: "Pending re-scan"`, and the skill says recomputation "requires a full build." But there is **no headless skill that performs the re-scan**. The scheduler PR lists stale entry IDs "so the reviewer knows what to action" — pushing LLM-shaped work onto a human, which is exactly backwards. Enriching a changed file requires no human judgment: the diff, the file content, the existing entry metadata, and the graph's concept definitions are all available evidence.

Consequences visible in the lancedb corpus:

- 77% of entries stale five days after an approved automated refresh; the index's summaries no longer describe current content.
- Embeddings are built from `title | summary | tags | concepts` — placeholder summaries mean new entries are either embedded as junk text ("Pending re-scan") or skipped, so semantic search silently degrades precisely for the newest content.
- New entries get `concepts: []` and refresh never remaps, so **graph.yaml decays monotonically** under automation.

**Recommendation (highest priority):** add a Phase 4b to `refresh-headless` (or a separate `hiivmind-corpus-enrich-headless` that the scheduler calls after refresh): for each stale entry, dispatch `source-scanner` agents over just the changed files to regenerate `title/summary/tags/keywords/category`, assign concepts by matching against existing graph.yaml concept definitions (flagging only genuinely-new concept candidates for human review in the PR body), clear `stale`, re-render, re-embed. Then the PR is a *complete* refresh and the human review is a real quality gate rather than a to-do list. The interactive `verify_entries.py` + LLM verification loop should also run here in sampled form, with results in the PR body — verification is exactly the evidence-based check headless runs need and it's currently interactive-only.

**Also missing headless surfaces:** `status`, `graph validate`, and a v1→v2 migration are all decision-free and should emit the same result-block contract so an orchestrator can compose them. Today only refresh has a headless variant.

**Contract hardening:** the `---headless-result` block is extracted from LLM prose by the calling task — fragile. Have the headless skill *write* `refresh-result.yaml` to a known path (scratch or corpus root, gitignored) and have the orchestrator read the file; keep the printed block for logs. Version the schema (`contract_version: 1`).

**One silent hole:** local sources report "always current" in headless mode, meaning a corpus with a `local` source silently never refreshes under automation. The result block should at least report `status: skipped-manual` so it's visible.

## 3. Interactive workflows: capture decisions so they replay

The interactive build's human touchpoints (segmentation, use case, organization, indexing depth, skip-sections, embedding opt-in) are appropriate for corpus creation. The problem is that only some of these decisions persist into `config.yaml` (`sections:`, `chunking:`, `extraction:` do; use case, organization, source priorities, segmentation strategy, verify preferences don't). That means any future automated rebuild or enrichment can't honor the original design.

**Recommendation:** adopt the principle *interactive skills capture decisions; headless skills replay them*. Add a `build:` block to config.yaml recording every Phase 3/4 answer. This is also what would eventually make a `build-headless` possible for corpus re-builds (still human-gated for *new* corpora).

Relatedly: `refresh` and `refresh-headless` currently duplicate the entire Phase 4–6 index-update logic verbatim (the v1 "A/M/D" rules appear word-for-word in both files). That's a drift bomb — v1.5.2's fixes had to be applied twice. Move the update algorithm into `patterns/index-updating.md` and have both skills reference it; the interactive skill becomes mode selection + confirmation UX around the same pattern.

## 4. Source/format organization: kill v1, name the derivation DAG

The real structural cost is the **v1/v2 × single/tiered × optional-artifacts matrix**. CLAUDE.md needs a 25-row cross-cutting-concerns table to keep skills aligned — that table is a symptom. Evidence: flyio is still v1-tiered (9 hand-maintained markdown files, 704 lines) while lancedb is v2, so every write-path skill carries two complete code paths.

- **Tiered-v2 is the blocker.** Build Phase 8 notes "tiered v2 is deferred," which means large corpora *can't* migrate off v1. Resolve it the cheap way: tiering is a **render-time concern**, not a storage concern — one `index.yaml` remains the source of truth and `render-index.sh` emits `index.md` + `index-{section}.md` from `category`/section metadata. No new index format needed.
- Then ship a headless `migrate` skill (v1 → v2 is mechanical: parse entry lines, scan sources for metadata) and declare v1 read-only legacy. Refresh's v1 write path can be deleted a release later.
- **Name the derivation DAG explicitly** in one pattern doc: `config.yaml → scan → index.yaml → {index.md (rendered), index-embeddings.lance, graph concepts on entries}`, with the rule that skills only ever *write* `index.yaml`/`config.yaml`/`graph.yaml` and everything else is derived. Most of the alignment table then collapses into "does the skill respect the DAG."
- The source taxonomy itself is fine; the inconsistency is that `obsidian` and `pdf` appear in `sources/README.md` but not in the refresh skills' type tables — worth a sweep so every skill enumerates the same seven types (or explicitly defers, e.g. "obsidian behaves as git|local").

## 5. Python scripts & environment: adopt PEP 723 + uv properly

Current state: skills say `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py` against whatever interpreter is on PATH; install guidance is prose (`pip install fastembed lancedb pyyaml`); the scheduler compensates with **seven identical pyproject.toml files** (every one dragging in `pymupdf` whether the corpus has PDFs or not), plus an acknowledged stale root pyproject.

**Recommendations:**

1. Put **PEP 723 inline metadata** (`# /// script … dependencies = [...]`) in each script and standardize invocation as `uv run script.py` with a documented `python3` fallback in `tool-detection.md`. Scripts become self-contained and portable; the scheduler pyprojects can be deleted entirely.
2. **Fix the real bug:** `detect.py` globs `~/.cache/fastembed` directly, ignoring `FASTEMBED_CACHE_PATH` — which the archived scheduler `run.sh` sets. On any host using a custom cache path, detection reports "no-model" and headless embedding silently skips forever.
3. Deduplicate constants: `MODEL_NAME` is defined independently in `detect.py` and `embed.py` (and in docs). One `constants.py` or have detect read embed's value.
4. There are 13 test files but **no CI in the plugin repo**. Add a workflow: `uv run pytest` plus a smoke test that builds and refreshes a tiny fixture corpus and validates the result block against the contract schema. Given the skills are prose executed by an LLM, script-level tests + contract validation are the only deterministic regression net.

## 6. Scheduler repo improvements

- The seven task dirs differ **only** in `name` + three constants (verified by diff). Replace with one shared `SKILL.md` template plus per-corpus `constants.yaml` — or better, a single task that iterates a `corpora.yaml` registry, since the phases are identical and per-corpus failure isolation is already handled by the error model. Seven copies means seven edits per process change, and the scheduler CLAUDE.md already admits this ("propagate changes to the others").
- The **sparse-checkout / never-use-compare-API constraint** (300-file cap) is a hard-won operational lesson living only in the scheduler SKILL.md. Move it into the plugin's `patterns/sources/git.md` so interactive refresh and other consumers get it too; the scheduler note becomes a one-line pointer.
- Add lifecycle hygiene the tasks currently only "log": auto-close or rebase superseded `automated/*` branches, and report unmerged-PR age in the run summary so silent PR pile-up is visible.
- Once headless enrichment exists (§2), the task's PR body changes from "stale entries for the reviewer to action" to "here's what changed and how it was re-summarized" — review becomes approve/reject rather than homework.

## 7. Index / graph / embeddings extraction quality

- **Concept assignment should be two-tier:** matching entries to *existing* concepts is evidence-based (tags + description similarity + embedding proximity) and belongs in headless enrichment; proposing *new* concepts stays interactive. Today both live only in interactive build, so automation starves the graph.
- **Embedding staleness should be observable:** the result block reports `embeddings: skipped | no-model` but nothing tracks cumulative drift. Add an `embeddings_lag` count (entries whose `last_indexed` postdates the lance `_meta` timestamp) to status and the PR body.
- `embed.py`'s incremental model (re-embed on changed metadata text, `_meta` model check, IVF_PQ over 500 rows) is solid. The gap is upstream: it's only as good as the summaries fed to it, which returns to §2.

## Priority order

1. **Headless enrichment phase** (close the stale loop; concepts + verification + embeddings in the same pass) — everything else in automation is undermined without it.
2. **Result contract as a file** + shared index-update pattern (de-dupe refresh/refresh-headless).
3. **Tiered v2 rendering → v1 migration skill → delete v1 write paths.**
4. **PEP 723/uv script packaging**, `FASTEMBED_CACHE_PATH` fix, CI on the plugin repo.
5. **Scheduler consolidation** to template + constants (or registry-driven single task).
6. Decision capture in config.yaml for future replay; headless variants of status/graph-validate/migrate.

Items 1, 2, and 4 are independent; item 3 is the only one with internal sequencing.
