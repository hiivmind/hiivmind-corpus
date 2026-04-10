# README Discoverability Patch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition `README.md` so PKM+LLM searchers recognise hiivmind-corpus and the shareable-corpus differentiator lands in the first three lines.

**Architecture:** A documentation-only patch. Three localised edits to a single file (`README.md`): (1) replace the opening paragraph with a fused hook, (2) reorder the Published Corpora table to put Obsidian first, (3) add a one-line Obsidian callout above that table. No code, no tests, no metadata.

**Tech Stack:** Markdown. Git.

**Spec:** `docs/superpowers/specs/2026-04-10-readme-discoverability-patch-design.md`

---

## Notes on testing

This plan has no automated tests — it is a prose edit to a single markdown file. "Verification" for each task is a visual re-read of the changed region plus a check against the spec's acceptance criteria. The final task runs an acceptance-criteria checklist against the rendered file.

---

### Task 1: Replace the opening paragraph with the fused hook

**Files:**
- Modify: `README.md:1-6`

**Context:** Current lines 1–6:

```markdown
# hiivmind-corpus

A Claude Code plugin for building persistent, curated documentation indexes with semantic search. One plugin creates, maintains, and queries documentation corpora from any source — git repos, local files, web pages, Obsidian vaults, PDFs, and more.

**Quick links:** [Using a Corpus](#using-a-corpus) | [Building a Corpus](#building-a-corpus) | [Semantic Search](#semantic-search-rag) | [Published Corpora](#published-corpora)
```

The H1 and the Quick links line stay. Only line 3 (the single-paragraph description) is replaced.

- [ ] **Step 1: Read the current opening to confirm line numbers**

Use the Read tool on `README.md` with `limit: 10`. Confirm that the H1 is on line 1, the description paragraph is on line 3, and the Quick links line is on line 5.

- [ ] **Step 2: Replace line 3 with the fused hook**

Use the Edit tool on `README.md`.

`old_string`:
```
A Claude Code plugin for building persistent, curated documentation indexes with semantic search. One plugin creates, maintains, and queries documentation corpora from any source — git repos, local files, web pages, Obsidian vaults, PDFs, and more.
```

`new_string`:
```
A Claude Code plugin for shareable, linkable LLM knowledge bases. If you have been following Andrej Karpathy's LLM wiki idea or building Obsidian-based PKM setups, hiivmind-corpus is the productised version of that pattern — raw sources compiled into a curated, interlinked index — but any corpus can be published as a plain git repo and registered by anyone else with a single command, queryable remotely via `gh api` with sparse-cloned embeddings and cross-corpus bridges that link concepts across independently maintained knowledge bases. Every other tool in this space (ObsidianRAG, Neural Composer, obsidian-notes-rag, Karpathy's LLM wiki) is single-user, single-vault, local-only; this one is a library, not a personal notebook.
```

- [ ] **Step 3: Re-read the opening in context**

Use the Read tool on `README.md` with `limit: 15`. Verify:

- H1 is intact on line 1.
- The new paragraph reads as one paragraph (no accidental line breaks).
- Quick links line is intact and still points to the same anchors.
- The five SEO terms appear naturally: `llm-wiki` (as "LLM wiki"), `knowledge-base` (as "LLM knowledge bases" / "knowledge bases"), `obsidian` (as "Obsidian"), `claude-code-plugin` (as "Claude Code plugin"), `pkm` (as "PKM").
- The shareable/linkable/publishable differentiator lands in the first three lines of prose after the H1.

If any SEO term feels bolted on rather than load-bearing in its sentence, revise the paragraph inline before proceeding.

- [ ] **Step 4: Spot-check "The Idea" section for redundancy**

Use the Read tool on `README.md`, `offset: 7`, `limit: 10`. Read `## The Idea` in the context of the new opening. Per the spec's risk section: if it reads as genuinely broken or duplicative, stop and flag it to the user — do NOT expand scope and rewrite it. If it reads fine (just expands on the hook), proceed.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): replace opening with fused PKM/LLM-wiki hook

Position hiivmind-corpus for PKM+LLM searchers by leading with the
shareable/linkable differentiator and bridging to Karpathy's LLM wiki
and Obsidian-based PKM patterns. Hits llm-wiki, knowledge-base,
obsidian, claude-code-plugin, and pkm search terms naturally in the
first paragraph after the H1.

Spec: docs/superpowers/specs/2026-04-10-readme-discoverability-patch-design.md
EOF
)"
```

---

### Task 2: Reorder the Published Corpora table to put Obsidian first

**Files:**
- Modify: `README.md` — the Published Corpora table (currently around lines 332–342, but line numbers may have shifted after Task 1; locate by heading `## Published Corpora`)

**Context:** The current table, in order:

```markdown
| Corpus | Source |
|---|---|
| [hiivmind-corpus-polars](https://github.com/hiivmind/hiivmind-corpus-data) | Polars documentation |
| [hiivmind-corpus-ibis](https://github.com/hiivmind/hiivmind-corpus-data) | Ibis documentation |
| [hiivmind-corpus-narwhals](https://github.com/hiivmind/hiivmind-corpus-data) | Narwhals documentation |
| [hiivmind-corpus-substrait](https://github.com/hiivmind/hiivmind-corpus-data) | Substrait specification |
| [hiivmind-corpus-flyio](https://github.com/hiivmind/hiivmind-corpus-flyio) | Fly.io platform docs |
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
| [hiivmind-corpus-lancedb](https://github.com/hiivmind/hiivmind-corpus-lancedb) | LanceDB documentation |
| [hiivmind-corpus-claude-agent-sdk](https://github.com/hiivmind/hiivmind-corpus-claude) | Claude Agent SDK |
```

Move the `hiivmind-corpus-obsidian` row to row 1 (immediately after the header separator). All other rows keep their current relative order.

- [ ] **Step 1: Locate the Published Corpora table**

Use the Grep tool: `pattern: "## Published Corpora"`, `path: "README.md"`, `output_mode: "content"`, `-n: true`. Note the line number. Then Read from that line with `limit: 20` to see the full table.

- [ ] **Step 2: Reorder the table via a single Edit**

Use the Edit tool on `README.md`.

`old_string`:
```
| Corpus | Source |
|---|---|
| [hiivmind-corpus-polars](https://github.com/hiivmind/hiivmind-corpus-data) | Polars documentation |
| [hiivmind-corpus-ibis](https://github.com/hiivmind/hiivmind-corpus-data) | Ibis documentation |
| [hiivmind-corpus-narwhals](https://github.com/hiivmind/hiivmind-corpus-data) | Narwhals documentation |
| [hiivmind-corpus-substrait](https://github.com/hiivmind/hiivmind-corpus-data) | Substrait specification |
| [hiivmind-corpus-flyio](https://github.com/hiivmind/hiivmind-corpus-flyio) | Fly.io platform docs |
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
| [hiivmind-corpus-lancedb](https://github.com/hiivmind/hiivmind-corpus-lancedb) | LanceDB documentation |
| [hiivmind-corpus-claude-agent-sdk](https://github.com/hiivmind/hiivmind-corpus-claude) | Claude Agent SDK |
```

`new_string`:
```
| Corpus | Source |
|---|---|
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
| [hiivmind-corpus-polars](https://github.com/hiivmind/hiivmind-corpus-data) | Polars documentation |
| [hiivmind-corpus-ibis](https://github.com/hiivmind/hiivmind-corpus-data) | Ibis documentation |
| [hiivmind-corpus-narwhals](https://github.com/hiivmind/hiivmind-corpus-data) | Narwhals documentation |
| [hiivmind-corpus-substrait](https://github.com/hiivmind/hiivmind-corpus-data) | Substrait specification |
| [hiivmind-corpus-flyio](https://github.com/hiivmind/hiivmind-corpus-flyio) | Fly.io platform docs |
| [hiivmind-corpus-lancedb](https://github.com/hiivmind/hiivmind-corpus-lancedb) | LanceDB documentation |
| [hiivmind-corpus-claude-agent-sdk](https://github.com/hiivmind/hiivmind-corpus-claude) | Claude Agent SDK |
```

- [ ] **Step 3: Verify the reorder**

Re-read the table region. Confirm:

- `hiivmind-corpus-obsidian` is the first data row (immediately after `|---|---|`).
- All other rows are present exactly once, in their original relative order.
- No row was dropped or duplicated.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): move Obsidian corpus to top of Published Corpora table

The Obsidian community is the single largest pool of potential users
for hiivmind-corpus. Surfacing hiivmind-corpus-obsidian first in the
table makes the connection obvious to that audience.

Spec: docs/superpowers/specs/2026-04-10-readme-discoverability-patch-design.md
EOF
)"
```

---

### Task 3: Add the Obsidian callout above the Published Corpora table

**Files:**
- Modify: `README.md` — insert one line between the `## Published Corpora` heading and the reordered table

**Context:** After Task 2, the Published Corpora region looks like:

```markdown
## Published Corpora

| Corpus | Source |
|---|---|
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
...
```

We are inserting one line of italicised callout text between the heading and the table.

- [ ] **Step 1: Insert the callout via Edit**

Use the Edit tool on `README.md`.

`old_string`:
```
## Published Corpora

| Corpus | Source |
|---|---|
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
```

`new_string`:
```
## Published Corpora

*Already use Obsidian? Register the Obsidian help corpus to get started: `/hiivmind-corpus register github:hiivmind/hiivmind-corpus-obsidian`*

| Corpus | Source |
|---|---|
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
```

- [ ] **Step 2: Verify the callout renders as intended**

Re-read the region. Confirm:

- The callout sits on its own line with a blank line above (after the heading) and below (before the table).
- It is wrapped in single asterisks (italic), not bold, not blockquoted.
- The command inside backticks is exactly `/hiivmind-corpus register github:hiivmind/hiivmind-corpus-obsidian`.
- The table that follows is unchanged from Task 2.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): add Obsidian callout above Published Corpora table

One-line italicised callout giving Obsidian users an explicit
one-command path into the corpus ecosystem.

Spec: docs/superpowers/specs/2026-04-10-readme-discoverability-patch-design.md
EOF
)"
```

---

### Task 4: Final acceptance-criteria check

**Files:** None modified. This is a verification-only task.

- [ ] **Step 1: Re-read the full README top-to-bottom**

Use the Read tool on `README.md` with no offset/limit (or in chunks if it exceeds 2000 lines — it will not). Read it as a first-time visitor would.

- [ ] **Step 2: Walk the spec's acceptance criteria**

For each bullet in the spec (`docs/superpowers/specs/2026-04-10-readme-discoverability-patch-design.md`, "Acceptance criteria" section), confirm it holds:

- [ ] Opening paragraph mentions `llm-wiki`, `knowledge-base`, `obsidian`, `claude-code-plugin`, and `pkm` naturally in prose.
- [ ] Opening paragraph states the shareable/linkable/publishable differentiator within the first three lines after the H1.
- [ ] Quick links line is preserved.
- [ ] `## The Idea` section is unchanged.
- [ ] `hiivmind-corpus-obsidian` is row 1 of the Published Corpora table.
- [ ] One-line Obsidian callout sits immediately above the Published Corpora table.
- [ ] No other sections are modified.
- [ ] No new files. No metadata changes. No code changes.

- [ ] **Step 3: Confirm scope discipline via git**

Run:

```bash
git diff main...HEAD --stat
```

Expected: only `README.md` appears in the stat (plus the two spec/plan files from earlier commits on this branch, if applicable). No other files modified. If anything else appears, stop and investigate — it is out of scope.

- [ ] **Step 4: Report completion to the user**

Summarise in one message: what changed, which acceptance criteria were verified, and whether `## The Idea` reads cleanly in context or needs a follow-up. Do not create the follow-up — just flag it if needed.
