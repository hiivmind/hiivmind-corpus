# 01 — Headless enrichment: close the stale-entry loop

**Priority:** P1 (highest)
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §2, §7
**Depends on:** nothing (can start immediately). Pairs well with [02-result-contract-and-shared-update-pattern](02-result-contract-and-shared-update-pattern.md).

## Problem

`hiivmind-corpus-refresh-headless` marks changed entries `stale: true` and inserts placeholder entries (`summary: "Pending re-scan"`), deferring enrichment to "next build or LLM re-scan" — but no headless skill performs that re-scan. The scheduler PR lists stale entry IDs for the human reviewer to action, pushing LLM-shaped work onto a person.

**Evidence (hiivmind-corpus-lancedb, as of 2026-07-09):** 148 of 193 entries `stale: true`, 52 with placeholder summaries, unresolved since the 2026-07-02 automated refresh was merged. Consequences:

- Index summaries no longer describe current content.
- Embeddings are built from `title | summary | tags | concepts`, so new entries are embedded as placeholder junk or skipped — semantic search degrades for exactly the newest content.
- New entries get `concepts: []` and refresh never remaps → `graph.yaml` decays monotonically under automation.

## Recommendation

Add a headless enrichment stage that runs after source update and before commit/PR — either Phase 4b of `refresh-headless` or a separate `hiivmind-corpus-enrich-headless` skill the scheduler invokes. For each stale entry:

1. Dispatch `source-scanner` agents over **only the changed files** to regenerate `title`, `summary`, `tags`, `keywords`, `category`, `headings`.
2. **Assign concepts** by matching against existing `graph.yaml` concept definitions (tags + description similarity + embedding proximity). Flag genuinely-new concept candidates in the PR body for human review — matching existing concepts is evidence-based; proposing new ones stays interactive.
3. Run sampled verification (`verify_entries.py` + LLM check, currently interactive-only) and include results in the PR body.
4. Clear `stale`/`stale_since`, set `last_indexed`, update `meta`, re-render `index.md`, re-embed incrementally.

Outcome: automated PRs are *complete* refreshes; human review becomes an approve/reject quality gate instead of homework.

## Tasks

- [ ] Decide: Phase 4b in `refresh-headless` vs. separate `enrich-headless` skill (separate skill lets it also run standalone against a corpus with accumulated stale entries — needed to repair lancedb).
- [ ] Write the enrichment phase spec (scanner prompt reusing build Phase 2 entry-metadata instructions; batch size; error isolation per entry).
- [ ] Concept-matching algorithm in `patterns/graph.md` (existing-concept assignment only; new-concept candidates → PR body).
- [ ] Wire sampled `verify_entries.py` verification into the headless path with results in the result block.
- [ ] Extend the result contract: `enriched: {n}`, `verification: {sampled, failed}`, `new_concept_candidates: [...]`.
- [ ] Update scheduler task template to call enrichment (or confirm it's internal to refresh-headless).
- [ ] Backfill run against `hiivmind-corpus-lancedb` to clear the existing 148 stale entries.

## Acceptance

An automated scheduler run on a corpus with upstream changes produces a PR in which no entry is `stale: true`, no summary is a placeholder, concepts are populated for new entries, embeddings match final summaries, and verification results appear in the PR body.
