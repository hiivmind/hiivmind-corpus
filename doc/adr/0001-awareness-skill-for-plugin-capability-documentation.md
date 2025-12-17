---
adr: 1
title: "Awareness Skill for Plugin Capability Documentation"
status: Accepted
date: 2025-12-17
milestone: "v1.1.0 - Awareness Skill"
issue: 21
deciders: [nathanielramm]
---

# 1. Awareness Skill for Plugin Capability Documentation

## Status

Accepted

## Context

The hiivmind-corpus plugin provides 8 skills for documentation corpus management:
- **Primary (Using):** navigate, discover
- **Secondary (Maintaining):** refresh, enhance, upgrade
- **Tertiary (Creating):** init, build, add-source

Users installing the plugin don't know when to use each skill. Projects using hiivmind-corpus need awareness in their CLAUDE.md to enable proactive suggestions.

Additionally, hiivmind-corpus is primarily a **meta-skill** - most users will use pre-generated corpora (via navigate/discover) rather than creating new ones. The awareness skill should reflect this priority.

Current problems:
- Claude doesn't know which skill to suggest for documentation queries
- No fast lookup mechanism for installed corpora
- No standard way to inject corpus awareness into CLAUDE.md

## Decision

Add an awareness skill to hiivmind-corpus that:

1. **Two Injection Targets** - User can choose where to inject awareness:
   - User-level (`~/.claude/CLAUDE.md`) - for personal corpus collection across all projects
   - Repo-level (`{repo}/CLAUDE.md`) - for team projects using specific corpora

2. **What/When/How Structure** - Following the pattern established in hiivmind-pulse-gh:
   - **WHAT:** Present all 8 skills grouped by priority (Use → Maintain → Create)
   - **WHEN:** Trigger table mapping operational needs to skills (navigation triggers primary)
   - **HOW:** Gateway command vs direct skill invocation

3. **User-Level Caching** - When injecting at user-level:
   - Run discover to find all installed corpora
   - Cache the list in `~/.claude/CLAUDE.md` with corpus names and keywords
   - Navigate skill checks cache FIRST before running discovery

4. **Cache Format** - Machine-updateable section using HTML comment markers:
   ```markdown
   <!-- Cache populated by discover skill - navigate checks this first -->
   | Corpus | Keywords | Location |
   |--------|----------|----------|
   | polars | dataframe, lazy, expressions | ~/.claude/plugins/... |
   <!-- End corpus cache -->
   ```

5. **Pattern Library** - Create `lib/corpus/patterns/capability-awareness.md` with:
   - Skill registry (8 skills with descriptions)
   - Trigger → Skill mapping tables
   - CLAUDE.md templates (user-level and repo-level)

## Consequences

### Positive

- Claude automatically knows when to suggest corpus skills
- Fast corpus lookup via cached table (no discovery scan needed)
- Consistent with hiivmind-pulse-gh awareness pattern
- Users understand the meta-skill nature (using > creating)
- Team and personal use cases both supported

### Negative

- One more skill to maintain (9th skill)
- Caching adds complexity to discover and navigate skills
- Two templates to maintain (user-level and repo-level)

### Neutral

- Introduces `doc/adr/` directory convention to repository
- Requires updates to existing discover and navigate skills

## Alternatives Considered

### Alternative 1: Single CLAUDE.md Template (No Cache)

Use a single template without the caching mechanism.

**Rejected because:** Without caching, navigate would need to run discover on every query, which is slow for users with many corpora.

### Alternative 2: Project-Awareness Only (No User-Level)

Only support repo-level awareness, similar to per-corpus `project-awareness.md`.

**Rejected because:** Many users have personal corpus collections across multiple projects. User-level awareness serves this use case better.

### Alternative 3: Automatic Cache in Navigate Skill

Have navigate skill automatically manage its own cache file.

**Rejected because:** CLAUDE.md is the established location for Claude awareness. Putting the cache there keeps everything in one discoverable place.

## Implementation

| File | Purpose |
|------|---------|
| `skills/hiivmind-corpus-awareness/SKILL.md` | 5-phase awareness skill |
| `lib/corpus/patterns/capability-awareness.md` | Skill registry, trigger tables, templates |

Updates to existing skills:
- `skills/hiivmind-corpus-discover/SKILL.md` - Add cache update behavior
- `skills/hiivmind-corpus-navigate/SKILL.md` - Add cache-first lookup
- `commands/hiivmind-corpus.md` - Add awareness domain detection

## References

- [hiivmind-pulse-gh awareness skill](https://github.com/hiivmind/hiivmind-pulse-gh/blob/main/skills/hiivmind-pulse-gh-awareness/SKILL.md)
- [hiivmind-corpus architecture](https://github.com/hiivmind/hiivmind-corpus/blob/main/CLAUDE.md)
