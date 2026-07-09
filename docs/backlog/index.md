# Backlog Index

Tracks recommendations from the [2026-07-09 architecture review](2026-07-09-architecture-review.md).
Update **Status** here as items move; details, tasks, and acceptance criteria live in each item's doc.

Statuses: `Proposed` → `Accepted` → `In progress` → `Done` (or `Rejected` / `Superseded`).

## Items by priority

| # | Item | Priority | Status | Effort | Depends on | One-liner |
|---|------|----------|--------|--------|------------|-----------|
| 01 | [Headless enrichment: close the stale-entry loop](01-headless-enrichment.md) | **P1** | In progress (merged in PR #47; awaiting lancedb backfill as acceptance) | M | — | Re-scan, re-summarize, concept-map, verify, and re-embed stale entries headlessly before the PR is opened. Fixes the 148-stale-entry decay seen in lancedb. |
| 02 | [Result contract as file + shared index-update pattern](02-result-contract-and-shared-update-pattern.md) | **P2** | Done (PR #47) | S | — | Write `refresh-result.yaml` instead of parsing prose; extract the duplicated refresh algorithm into one pattern doc; surface `skipped-manual` local sources. |
| 04 | [Python packaging (PEP 723 + uv), cache-path bug, CI](04-python-packaging-and-ci.md) | **P2** | Done (PR #47) | S | — | Self-contained `uv run` scripts, fix `FASTEMBED_CACHE_PATH` bug in detect.py, dedupe constants, add CI to the plugin repo. |
| 03 | [Tiered v2 rendering → v1 migration → retire v1](03-retire-v1-tiered-v2-rendering.md) | **P3** | In progress (wave 2) | L | internal sequencing | Make tiering a render-time concern of index.yaml, ship a migrate skill, move flyio off v1, delete v1 write paths. |
| 05 | [Scheduler consolidation](05-scheduler-consolidation.md) | **P3** | Done (PR #48 + scheduler #1) | S | 01, 02, 04 | Replace 7 copy-pasted tasks with template+constants or a registry-driven task; upstream the sparse-checkout lesson into git.md; branch/PR hygiene. |
| 06 | [Decision capture + more headless surfaces](06-decision-capture-and-headless-surfaces.md) | P4 | Proposed | M | 02, 03 | Persist build decisions in config.yaml for replay; headless status/graph-validate; `embeddings_lag` observability. |

## Suggested sequencing

```
Wave 1 (independent, start any):   01 headless enrichment   02 contract/de-dupe   04 packaging+CI
Wave 2:                            03 tiered-v2 → migrate → retire v1
Wave 3 (consumes wave 1):          05 scheduler consolidation
Wave 4:                            06 decision capture + headless surfaces
```

01, 02, and 04 are independent and each PR-sized on their own. 03 has internal sequencing (rendering before migration before removal). 05 should wait for 01/02 so the consolidated task template is written once against the final contract. 06 is the long tail that turns the suite into a fully composable headless toolkit.

## Adding items

Create `NN-short-slug.md` with: Priority, Status, Source, Depends on, Problem (with evidence), Recommendation, Tasks, Acceptance. Add a row above and keep the table sorted by priority.
