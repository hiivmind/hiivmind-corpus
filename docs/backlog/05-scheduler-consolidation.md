# 05 — Scheduler consolidation: template + constants, upstream learned constraints

**Priority:** P3
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §6
**Repo:** `hiivmind/hiivmind-corpus-scheduler`
**Depends on:** [04](04-python-packaging-and-ci.md) removes the per-task pyproject need; [01](01-headless-enrichment.md)/[02](02-result-contract-and-shared-update-pattern.md) change what the task calls and parses.

## Problem

- The seven `corpus-refresh-*/SKILL.md` files differ **only** in `name:` and three Constants (verified by diff). Seven copies means seven edits per process change; the repo's CLAUDE.md already admits this ("propagate changes to the others").
- The seven `pyproject.toml` files are byte-identical except `name`, and all include `pymupdf` regardless of need.
- The **sparse-checkout constraint** (never use the GitHub compare API — it caps at 300 files and silently drops the rest; clone sparse into `.source/<id>/` and use local `git diff`) is a hard-won operational lesson living only in the scheduler SKILL.md, invisible to interactive refresh and other consumers.
- Stale `automated/*` branches and unmerged PRs are only "logged for the summary" — no lifecycle management, so pile-up is silent.

## Recommendation

1. **One template, per-corpus constants.** Either (a) a shared `SKILL.md` template + per-corpus `constants.yaml` consumed at run time, or (b) a single registry-driven task iterating `corpora.yaml` — phases are identical and per-corpus failure isolation already exists in the error model. Option (b) also gives one consolidated run summary across all corpora. Recommend (b) unless per-corpus scheduling cadences must differ.
2. **Upstream the git constraint** into the plugin's `patterns/sources/git.md` (sparse clone recipe, compare-API prohibition + rationale); scheduler note becomes a one-line pointer.
3. **Branch/PR hygiene:** detect superseded `automated/*` branches and close their PRs (or rebase), and report unmerged-PR age in `<run-summary>`.
4. Delete per-task pyprojects once PEP 723 scripts land (item 04); delete the stale root pyproject now.

## Tasks

- [ ] Decide template-vs-registry model; implement.
- [ ] Move sparse-checkout/compare-API guidance into `hiivmind-corpus/lib/corpus/patterns/sources/git.md`.
- [ ] Add stale-branch/PR-age handling to the task flow.
- [ ] Remove duplicated pyprojects (after 04) and the stale root pyproject (now).
- [ ] Update scheduler CLAUDE.md ("add a new corpus" becomes: add one line/file of constants).

## Acceptance

Adding a corpus to the schedule is a single constants entry. A process change edits exactly one SKILL.md. `git.md` in the plugin documents the compare-API limitation.
