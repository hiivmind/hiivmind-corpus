# 06 — Decision capture in config.yaml; additional headless surfaces

**Priority:** P4
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §2, §3, §7
**Depends on:** contract work in [02](02-result-contract-and-shared-update-pattern.md); migrate skill overlaps with [03](03-retire-v1-tiered-v2-rendering.md).

## Problem

**Decisions evaporate.** The interactive build asks for segmentation strategy, use case, organization, source priorities, skip-sections, indexing depth, embedding opt-in, and verify preferences — but only `sections:`, `chunking:`, and `extraction:` persist into config.yaml. Future automated rebuilds/enrichment cannot honor the original design, and a `build-headless` (for *re*-builds of existing corpora) is impossible without replayable decisions.

**Headless coverage is refresh-only.** `status`, `graph validate`, v1→v2 `migrate`, and verification are all decision-free but have no headless, contract-emitting form, so orchestrators can't compose them (e.g. a nightly status sweep across all corpora, or graph validation as a PR check on corpus repos).

**Observability gap.** The result block reports `embeddings: skipped | no-model` per run, but nothing tracks cumulative drift between index and embeddings.

## Recommendation

1. **Principle: interactive skills capture decisions; headless skills replay them.** Add a `build:` block to config.yaml recording every build Phase 3/4 answer (segmentation, use_case, organization, source_priorities, skip_sections, verify_on_build/sample_size — some of which already have config keys — plus embeddings opt-in). Build writes it; enhance/refresh/enrichment read it.
2. **Headless variants** (thin, same result-file contract as 02): `status-headless` (per-corpus freshness YAML — the scheduler could use this for a cheap pre-check before spinning up a full refresh), `graph validate --headless`, and `migrate` (from item 03). A `build-headless` for re-builds becomes feasible once the `build:` block exists; new-corpus creation stays interactive by design.
3. **Embedding drift metric:** add `embeddings_lag` (count of entries whose `last_indexed` postdates the lance `_meta` timestamp) to `status` output and the refresh PR body.

## Tasks

- [ ] Define `build:` config block schema in `patterns/config-parsing.md` / index-format docs; build skill writes it.
- [ ] Teach enhance/refresh/enrichment to read replayed preferences (organization, skip-sections) instead of guessing.
- [ ] `status-headless` emitting per-corpus result files; wire as optional scheduler pre-check.
- [ ] Headless mode for `graph` validation.
- [ ] `embeddings_lag` in status + PR body.
- [ ] (Stretch) `build-headless` for re-building an existing corpus from captured decisions.

## Acceptance

A corpus built interactively records all its build decisions in config.yaml; a subsequent headless enrichment places new entries per the recorded organization without prompting. `status` reports embedding lag. Orchestrators can run status/validate across all corpora with machine-readable results.
