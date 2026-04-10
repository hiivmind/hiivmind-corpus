# README Discoverability Patch — Design

**Date:** 2026-04-10
**Status:** Approved
**Scope:** `README.md` only

## Goal

Reposition the README so PKM+LLM searchers (Karpathy LLM-wiki crowd, Obsidian
users, "claude-code-plugin" searchers) recognise hiivmind-corpus as what they
are looking for, and surface the shareable-corpus differentiator in the first
three lines.

## Context

Feedback from a reviewer (2026-04-10) flagged that the README is well-written
for someone who already knows what hiivmind-corpus is, but the opening does not
connect to anything the PKM+LLM community is currently searching for. Andrej
Karpathy's recent LLM-wiki post has made `llm-wiki` and `knowledge-base`
high-traffic search terms; `obsidian` is always high-traffic; and
`claude-code-plugin` is what people search when they are looking for exactly
what this is.

The reviewer also noted that the architectural differentiator —
publishable-as-git-repo, register-with-one-command, remote-queryable corpora
with cross-corpus bridges — is the killer feature that no comparable project
(ObsidianRAG, Neural Composer, obsidian-notes-rag, Karpathy's LLM wiki) has,
and it is currently buried.

The Obsidian community is the single largest pool of potential users, and the
`hiivmind-corpus-obsidian` corpus is currently buried in an alphabetical list.

## Non-Goals

- No code changes.
- No `plugin.json`, `marketplace.json`, or GitHub repo metadata changes.
- No cross-post drafts (Obsidian forum, Karpathy thread reply, Claude Code
  community post). Those are out of scope per the user's scope decision (option
  A: README-only).
- No new sections beyond what is listed below.
- No rewriting of existing sections beyond the opening.
- No emoji, no marketing-voice rewriting.

## Changes

### 1. Replace the opening (lines 1–6 of current README)

New structure:

- **Line 1:** `# hiivmind-corpus` (unchanged).
- **Lines 2–4 (fused hook):** A 3–4 line paragraph that lands, in one breath:
  1. It is a Claude Code plugin for shareable, linkable LLM knowledge bases.
  2. It is the productised version of patterns like Karpathy's LLM wiki and
     Obsidian-based PKM setups.
  3. The architectural differentiator: publish a corpus as a git repo, anyone
     registers it with one command, queryable remotely via `gh api` with
     sparse-cloned embeddings and cross-corpus bridges.
- The paragraph must hit the SEO terms `llm-wiki`, `knowledge-base`,
  `obsidian`, `claude-code-plugin`, and `pkm` naturally in prose — load-bearing
  in the sentence, not bolted on.
- **Quick links line:** unchanged.
- The existing `## The Idea` section is unchanged. After the new opening it
  reads as the expansion of the hook rather than the introduction.

### 2. Reorder Published Corpora table

Move the `hiivmind-corpus-obsidian` row to row 1 of the Published Corpora
table. All other rows retain their current order.

### 3. Add inline callout above the Published Corpora table

Immediately before the table, add one line:

> *Already use Obsidian? Register the Obsidian help corpus to get started:
> `/hiivmind-corpus register github:hiivmind/hiivmind-corpus-obsidian`*

## What is deliberately NOT changing

- `## The Idea`, `## Getting Started`, `## Installation`, `## Using a Corpus`,
  `## Building a Corpus`, `## What a Corpus Looks Like`, `## Three Layers`,
  `## Skills`, `## Source Types`, `## Semantic Search (RAG)`,
  `## Concept Graphs`, `## Cross-Corpus Bridges`, `## Per-Project Registry`,
  `## Dependencies`, `## Design Principles`, `## License` — all unchanged.
- The feedback explicitly says "worth a paragraph, not a rewrite." This spec
  takes that literally.
- No Obsidian-specific mini-section near Getting Started. The fused opening
  name-checks Obsidian and the Source Types table already lists `obsidian` as
  a first-class type.

## Tone constraints

- Match the existing README register: technical, plain, no hype.
- No emoji.
- The fused hook must read naturally — keyword stuffing is a failure mode to
  avoid. Each SEO term should be load-bearing in its sentence.

## Risks

- **Tone consistency.** The fused hook needs to sound like the rest of the
  README while still hitting search terms. Mitigation: write in the same
  register as `## The Idea`.
- **Keyword stuffing.** Hitting five SEO terms in 3–4 lines without sounding
  like spam is the main craft challenge. Mitigation: each term must do real
  work in its sentence; if a term feels bolted on, drop it.
- **"The Idea" redundancy.** After the new opening, `## The Idea` may feel
  slightly repetitive. Mitigation: re-read in context after editing. If it
  reads badly, flag for a follow-up — do not expand scope in this patch.

## Acceptance criteria

- [ ] Opening paragraph (lines 2–4) mentions `llm-wiki`, `knowledge-base`,
      `obsidian`, `claude-code-plugin`, and `pkm` naturally in prose.
- [ ] Opening paragraph states the shareable/linkable/publishable
      differentiator within the first three lines after the H1.
- [ ] Quick links line is preserved.
- [ ] `## The Idea` section is unchanged.
- [ ] `hiivmind-corpus-obsidian` is row 1 of the Published Corpora table.
- [ ] One-line Obsidian callout sits immediately above the Published Corpora
      table.
- [ ] No other sections are modified.
- [ ] No new files. No metadata changes. No code changes.
