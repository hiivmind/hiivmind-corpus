# 03 — Tiered v2 rendering, v1→v2 migration, retire v1 write paths

**Priority:** P3
**Status:** Proposed
**Source:** [Architecture review 2026-07-09](2026-07-09-architecture-review.md) §4
**Depends on:** internal sequencing only (rendering → migration → removal). Reduces scope of [02](02-result-contract-and-shared-update-pattern.md)'s shared pattern once complete.

## Problem

Every write-path skill (build, refresh, refresh-headless, enhance) carries two complete code paths: v1 (`index.md` as source of truth, hand-edited, optionally tiered) and v2 (`index.yaml` + rendered `index.md`). The 25-row cross-cutting-concerns table in CLAUDE.md is a symptom of this matrix.

The blocker is that **tiered v2 is deferred** (build Phase 8: "tiered v2 is deferred"), so large corpora cannot migrate. Evidence: `hiivmind-corpus-flyio` (761 files) remains v1-tiered with 9 hand-maintained markdown index files (704 lines), while `hiivmind-corpus-lancedb` is v2.

## Recommendation

Tiering is a **render-time concern, not a storage concern**. Sequence:

1. **Tiered rendering:** extend `render-index.sh` (and `patterns/index-rendering.md`) to emit `index.md` + `index-{section}.md` from a single `index.yaml`, driven by `category`/section metadata and a `render:` block in config.yaml (strategy: single | tiered, section definitions). No new index format.
2. **Migration skill:** headless `hiivmind-corpus-migrate` (v1 → v2 is mechanical: parse entry lines from index*.md, cross-reference `.source/` scans for metadata, emit index.yaml, render, diff-check against original). Emits the standard headless result block.
3. **Migrate flyio** as the proving case; verify rendered tiered output is navigationally equivalent.
4. **Declare v1 read-only legacy** — refresh skills detect v1 and instruct migration rather than updating; delete v1 write paths one release later.
5. Alongside: write `patterns/derivation-dag.md` naming the rule — skills only ever *write* `config.yaml` / `index.yaml` / `graph.yaml`; `index.md`, sub-indexes, and `*.lance/` are derived artifacts. Sweep skills for consistency (e.g. `obsidian`/`pdf` appear in `sources/README.md` but not in refresh type tables).

## Tasks

- [ ] `render:` config block schema + tiered rendering in `render-index.sh` / `index-rendering.md`.
- [ ] `hiivmind-corpus-migrate` skill (headless, result-block contract).
- [ ] Migrate `hiivmind-corpus-flyio`; validate against current index content.
- [ ] Mark v1 as read-only in refresh/enhance; remove v1 write logic in the following release.
- [ ] `patterns/derivation-dag.md` + source-type table consistency sweep.
- [ ] Collapse the CLAUDE.md cross-cutting table rows made obsolete.

## Acceptance

flyio is v2 with tiered `index-*.md` rendered deterministically from one `index.yaml`; no skill contains v1 write logic; CLAUDE.md alignment table shrinks accordingly.
