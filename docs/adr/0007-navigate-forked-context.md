# ADR 0007: Navigate Skills with Forked Context Execution

## Status

Accepted

## Context

Claude Code 2.1.0 introduced `context: fork` for skills, which runs skills in an isolated sub-agent context with its own conversation history. Navigate skills are ideal candidates for this feature because they:

1. **Search indexes** - Multiple grep/read operations to find relevant entries
2. **Read multiple files** - Fetch documentation from git sources, web, or local files
3. **Synthesize answers** - Combine information from multiple sources

Currently, all this intermediate work (index searches, file reads, path resolution) appears in the main conversation, cluttering context. Users see the "journey" instead of just the answer.

### Available Skill Metadata Fields (SKILL.md frontmatter)

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars, lowercase/numbers/hyphens |
| `description` | Yes | Max 1024 chars, triggers skill routing |
| `context` | No | Set to `fork` for isolated sub-agent |
| `agent` | No | Agent type when forked (Explore, Plan, task, general-purpose, or custom) |
| `allowed-tools` | No | Tools available without permission prompts |
| `model` | No | Model for this skill (e.g., `claude-haiku-4-5-20251001`) |
| `hooks` | No | PreToolUse, PostToolUse, Stop hooks scoped to skill |
| `user-invocable` | No | Show in slash command menu (default: true) |
| `disable-model-invocation` | No | Block programmatic invocation via Skill tool |

### What `context: fork` Does

- Runs skill in **isolated sub-agent context** with its own conversation history
- Main conversation stays clean - only final output returned
- Perfect for skills that read many files or do complex multi-step operations

### Agent Types for Forked Skills

| Agent Type | Best For |
|------------|----------|
| `Explore` | Fast, read-only exploration - **best match for navigate** |
| `general-purpose` | Default, full capabilities |
| `Plan` | Design/planning tasks |
| `task` | Autonomous task execution |

## Decision

Add `context: fork` with `agent: Explore` to navigate skill template:

```yaml
---
name: {{plugin_name}}-navigate
description: This skill answers questions about {{project_display_name}} documentation...
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebFetch
---
```

### Rationale

1. **Explore agent** - Navigate is read-only exploration, matches agent's purpose
2. **allowed-tools** - Explicit list prevents permission prompts for routine operations
3. **Isolated context** - Users see clean answers, not index searches and file reads

## Consequences

### Positive

- **Cleaner conversations** - Users see answers, not intermediate steps
- **Better context management** - Main conversation not polluted with tool outputs
- **Faster perceived response** - Final answer appears without intermediate noise
- **Scalable** - Large corpora with many file reads stay contained

### Negative

- **Hidden work** - Users can't see the skill's reasoning process
- **Debugging harder** - Intermediate steps not visible for troubleshooting
- **Compatibility** - Requires Claude Code 2.1.0+

### Neutral

- **allowed-tools declaration** - Makes tool usage explicit and predictable

## Alternatives Considered

1. **No fork, keep inline execution** - Rejected: Context pollution with large corpora
2. **model: haiku only** - Rejected: Speed improvement without isolation doesn't address context clutter
3. **general-purpose agent** - Rejected: Explore better matches read-only pattern
4. **task agent** - Rejected: Overkill for navigation, designed for autonomous execution

## Implementation

### Files to Modify

| File | Change |
|------|--------|
| `templates/navigate-skill.md.template` | Add context, agent, allowed-tools to frontmatter |
| `skills/hiivmind-corpus-upgrade/SKILL.md` | Detect and migrate existing navigate skills |
| `CLAUDE.md` | Document new fields in Cross-Cutting Concerns |

### Template Change

**Before:**
```yaml
---
name: {{plugin_name}}-navigate
description: This skill answers questions about {{project_display_name}} documentation. Use when user asks about {{keywords_sentence}}. Triggers: {{keyword_list}}.
---
```

**After:**
```yaml
---
name: {{plugin_name}}-navigate
description: This skill answers questions about {{project_display_name}} documentation. Use when user asks about {{keywords_sentence}}. Triggers: {{keyword_list}}.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebFetch
---
```

### Upgrade Skill Addition

Add to upgrade detection checklist:
- Navigate skill exists without `context: fork` → flag for upgrade
- Report includes command to regenerate from template

## Verification

1. **Create test corpus** with new template
2. **Invoke navigate skill** and verify:
   - Main conversation shows only final answer
   - No intermediate tool outputs visible
   - Skill correctly answers documentation questions
3. **Test upgrade skill** on existing corpus without fork context
4. **Verify allowed-tools** - Read/Grep/Glob/WebFetch work without prompts

## References

- [Claude Code 2.1.0 Skills Update](https://www.linkedin.com/pulse/claude-code-210-skills-update-changes-everything-yaron-been-99yaf) - context: fork feature explanation
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - Official skill metadata reference
- ADR-0005: Corpus Skill/Command Architecture - Navigate skill structure
