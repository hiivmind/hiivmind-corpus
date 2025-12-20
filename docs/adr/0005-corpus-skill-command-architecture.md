# ADR 0005: Corpus Skill/Command Architecture Restructure

## Status

Accepted

## Context

The hiivmind-corpus plugin system has a two-level architecture:
- **Parent plugin** (`hiivmind-corpus`): Meta-plugin for creating and managing documentation corpora
- **Child plugins** (e.g., `hiivmind-corpus-github-docs`): Individual corpus plugins with indexed documentation

The previous architecture had invocation ambiguity:

1. **Naming collision**: Parent had `hiivmind-corpus-navigate` skill, child had `navigate` command - both conceptually did "navigation" but at different levels
2. **Circular routing**: Parent navigate skill routed to child; child command routed maintenance back to parent skills
3. **Unclear entry points**: Users didn't know when to use parent vs child invocation

## Decision

Restructure to enforce clear separation of concerns:

| Concern | Owner | Mechanism |
|---------|-------|-----------|
| Corpus SETUP | Parent | Skills: `init`, `build`, `add-source` |
| Corpus MAINTENANCE | Parent | Skills: `refresh`, `enhance`, `upgrade`, `awareness` |
| Corpus DISCOVERY | Parent | Skill: `discover` (also handles generic "check the docs" queries) |
| Corpus USAGE | Child | Skill: `navigate` with domain-specific triggers |

### Key Changes

1. **DELETE parent `hiivmind-corpus-navigate` skill** - No longer needed
2. **UPDATE parent `discover` skill** - Handle generic doc queries by listing available corpora
3. **CREATE child navigate skill** - Templated, with domain-specific trigger keywords
4. **SIMPLIFY child navigate command** - Explicit entrypoint, no maintenance routing

### Query Flow

| Query Type | Triggers | Flow |
|------------|----------|------|
| Domain-specific ("GitHub Actions") | Child skill | Direct answer |
| Generic ("check the docs") | Parent discover | List corpora → user picks |
| Maintenance ("refresh corpus") | Parent skills | Parent operates on corpus |

## Consequences

### Positive

- **No circular routing** - Parent never calls child for queries, child never calls parent for queries
- **Domain-specific triggering** - Each corpus has keywords in its skill description
- **Scalable** - Adding corpora adds skills with specific triggers, no central routing table
- **Clear mental model** - Parent = lifecycle, Child = usage

### Negative

- **Template maintenance** - Navigate skill template must be kept up to date
- **Migration effort** - Existing child corpora need updating
- **Skill proliferation** - Each corpus adds a skill to Claude's available skills list

### Neutral

- Generic queries require an extra step (discover → pick → query) but this is appropriate UX for ambiguous requests

## Alternatives Considered

1. **Keep parent navigate with improved routing** - Rejected: Still requires parent to know all domain keywords, doesn't scale
2. **Commands only, no skills** - Rejected: Loses implicit triggering benefit
3. **Single monolithic plugin** - Rejected: Doesn't support distributed corpus publishing

## Implementation

### Files Modified

**Parent plugin:**
- Deleted: `skills/hiivmind-corpus-navigate/`
- Updated: `skills/hiivmind-corpus-discover/SKILL.md` - Added generic doc query triggers
- Created: `templates/navigate-skill.md.template`
- Updated: `templates/navigate-command.md.template` - Removed maintenance routing

**Child plugin (example: github-docs):**
- Created: `skills/navigate/SKILL.md` - Domain-specific navigate skill
- Updated: `commands/navigate.md` - Simplified, no maintenance routing
