---
adr: 2
title: "Skill Refactoring for Progressive Disclosure"
status: Proposed
date: 2025-12-17
deciders: [nathanielramm]
---

# 2. Skill Refactoring for Progressive Disclosure

## Status

Proposed

## Context

Plugin validator and skill reviewer agents identified structural improvements needed:

- **Word count issues:** Two skills exceed the recommended 2,000 word limit:
  - `hiivmind-corpus-init`: 3,134 words
  - `hiivmind-corpus-upgrade`: 2,893 words
- **Code duplication:** Parallel-scanning logic is duplicated between build and refresh skills
- **Skill matching:** Missing trigger keywords reduce skill matching accuracy
- **Licensing:** No LICENSE file for marketplace distribution

The init skill contains verbose template examples (marketplace structures, implementation walkthroughs) inline. The upgrade skill embeds detailed checklists and code templates. Both violate progressive disclosure principles - Claude loads this content on every invocation even when not needed.

## Decision

### 1. Progressive Disclosure via references/

Extract verbose content to `references/` subdirectories within skills:

**init skill extractions:**
| File | Content |
|------|---------|
| `references/marketplace-templates.md` | Template-to-file mappings, directory structures |
| `references/implementation-examples.md` | Examples A-E (user-level, repo-local, single/multi-corpus) |
| `references/template-placeholders.md` | Placeholder reference table |

**upgrade skill extractions:**
| File | Content |
|------|---------|
| `references/upgrade-checklists.md` | File component, config schema, navigate sections tables |
| `references/upgrade-templates.md` | Missing sections code, report template |
| `references/batch-upgrade.md` | Batch commands, examples, consolidated report |

Skills reference extracted content with: `**See:** references/filename.md`

### 2. Shared Pattern Library

Create `lib/corpus/patterns/parallel-scanning.md` documenting:
- When to use parallel scanning (2+ sources)
- Agent invocation mechanics (Task tool with source-scanner)
- Performance expectations table
- Context-specific prompts (build vs refresh)

Both build and refresh skills reference this pattern instead of duplicating logic.

### 3. Enhanced Trigger Keywords

Add keywords to improve skill matching:

| Skill | Add |
|-------|-----|
| init | "index documentation", "create corpus" |
| refresh | "corpus outdated", "sync corpus", "update index" |
| upgrade | "migrate corpus", "update corpus format" |
| navigate | "search all corpora", "query documentation" |

### 4. MIT License

Add standard MIT license for open-source marketplace distribution.

## Consequences

### Positive

- Skills reduced to ~1,500 words (within best practice range)
- Single source of truth for parallel-scanning pattern
- Better skill matching from enriched descriptions
- Marketplace-ready with proper licensing
- Faster skill loading (less content parsed per invocation)

### Negative

- Skills now reference external files (minor navigation overhead)
- Pattern library adds one more file to maintain
- 8 new reference files to track

### Neutral

- Establishes `references/` convention for future skills
- Aligns with existing `lib/corpus/patterns/` approach

## Implementation

**New files (9):**
- `LICENSE`
- `skills/hiivmind-corpus-init/references/marketplace-templates.md`
- `skills/hiivmind-corpus-init/references/implementation-examples.md`
- `skills/hiivmind-corpus-init/references/template-placeholders.md`
- `skills/hiivmind-corpus-upgrade/references/upgrade-checklists.md`
- `skills/hiivmind-corpus-upgrade/references/upgrade-templates.md`
- `skills/hiivmind-corpus-upgrade/references/batch-upgrade.md`
- `lib/corpus/patterns/parallel-scanning.md`

**Files edited (5):**
- `skills/hiivmind-corpus-init/SKILL.md`
- `skills/hiivmind-corpus-upgrade/SKILL.md`
- `skills/hiivmind-corpus-build/SKILL.md`
- `skills/hiivmind-corpus-refresh/SKILL.md`
- `skills/hiivmind-corpus-navigate/SKILL.md`

## References

- [Plugin-dev skill-reviewer findings](plugin-dev:skill-reviewer agent results)
- [Plugin-dev plugin-validator findings](plugin-dev:plugin-validator agent results)
- [Progressive disclosure in skills](https://github.com/anthropics/claude-code/blob/main/docs/skills.md)
