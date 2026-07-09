# 02 — Harden the headless result contract; de-duplicate refresh logic

**Priority:** P2
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §2, §3
**Depends on:** nothing. Do before or alongside [01-headless-enrichment](01-headless-enrichment.md) since that extends the contract.

## Problem

**Contract fragility.** The `---headless-result` YAML block is emitted as LLM prose and the scheduler task extracts it by string-scanning the skill's conversational output. Any formatting drift breaks the orchestrator silently. The contract is also unversioned.

**Verbatim duplication.** `refresh/SKILL.md` and `refresh-headless/SKILL.md` contain the same Phase 4–6 index-update algorithm word-for-word (the v1 "A/M/D" rules, template-variable stripping, section-placement rules). v1.5.2's fixes had to be applied to both files — a proven drift bomb.

**Silent hole.** Local sources report "always current" in headless mode, so a corpus with a `local` source never refreshes under automation and nothing surfaces this.

## Recommendation

1. **Result as a file, not prose.** The headless skill writes `refresh-result.yaml` (gitignored, corpus root or scratch path passed as input); the orchestrator reads the file. Keep the printed block for logs only. Add `contract_version: 1` to the schema.
2. **Extract the shared algorithm** into `lib/corpus/patterns/index-updating.md` (v2 stale-marking rules, v1 A/M/D rules, config metadata updates, embedding-update procedure). Both refresh skills reference it; the interactive skill becomes mode-selection + confirmation UX around the same pattern.
3. **Report manual-only sources** as `status: skipped-manual` in the result block so local-source corpora aren't silently permanently stale.
4. Add a JSON-schema (or documented YAML schema) for the result file and validate it in tests / CI (see [04-python-packaging-and-ci](04-python-packaging-and-ci.md)).

## Tasks

- [ ] Define `refresh-result.yaml` schema with `contract_version`, document in a new `patterns/headless-contract.md`.
- [ ] Update `refresh-headless` to write the file; update scheduler task template to read it (fallback to prose block for one release).
- [ ] Create `patterns/index-updating.md`; strip duplicated logic from both refresh SKILL.md files, replacing with references.
- [ ] Add `skipped-manual` status for local sources.
- [ ] Schema-validate a sample result file in the test suite.

## Acceptance

`grep` finds the v1 A/M/D rules in exactly one file. A scheduler run parses results from `refresh-result.yaml`, not conversation text. A corpus with a local source shows `skipped-manual` in its result block.
