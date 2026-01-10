---
description: Unified entry point for all corpus operations - describe what you need in natural language
argument-hint: Describe your goal (e.g., "index React docs", "refresh my polars corpus", or just a corpus name)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "TodoWrite", "AskUserQuestion", "Skill", "Task", "WebFetch"]
---

# Corpus Gateway

Unified entry point for all hiivmind-corpus operations.

**User request:** $ARGUMENTS

---

## Step 1: Check for Arguments

**If `$ARGUMENTS` is empty** → Go directly to **Mode: Interactive Menu** (no introspection needed first)

**If `$ARGUMENTS` is provided** → Continue to Step 2: Intent Detection

---

## Step 2: Intent Detection (only when arguments provided)

Analyze intent using these patterns:

### Intent → Skill Mapping

| Intent Keywords | Primary Skill | Secondary Skills |
|-----------------|---------------|------------------|
| create, new, index, set up, scaffold, initialize, start | `init` | Often followed by `build` |
| add, include, import, fetch, clone, source | `add-source` | May trigger `build` |
| build, analyze, create index, scan, index | `build` | - |
| expand, deepen, more detail, enhance, elaborate | `enhance` | - |
| update, refresh, sync, check, upstream, stale | `refresh` | May trigger `enhance` |
| upgrade, migrate, latest, standards, template | `upgrade` | - |
| validate, audit, check structure, verify, lint | `upgrade` (report-only) | - |
| status, info, up to date, current | `refresh` (status mode) | - |
| navigate, find, search, look up, what does, how do | `navigate` | - |
| list, show, available, installed, discover | Discovery mode | - |
| awareness, configure claude, setup claude, capabilities, tour, what can, claude.md | `awareness` | - |

### Compound Intent Detection

Some requests imply multiple skills - use TodoWrite to track:

| Request Pattern | Skill Sequence |
|-----------------|----------------|
| "index {project} docs" (not in corpus) | init → build |
| "add {source} and include in index" | add-source → build (partial) |
| "refresh and expand {section}" | refresh → enhance |
| "create corpus with {source1} and {source2}" | init → add-source → build |
| "set up {project} with blog posts too" | init → add-source (web) → build |

---

## Step 3: Context Detection (only when needed for routing)

When arguments are provided and context matters for routing, detect:

```bash
# Only run these when needed to determine valid operations
test -f data/config.yaml && echo "IN_CORPUS=true"
test -f .claude-plugin/marketplace.json && echo "IN_MARKETPLACE=true"
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null && echo "IN_PROJECT=true"
```

### Context + Intent Matrix

| Context | init | add-source | build | enhance | refresh | upgrade | navigate |
|---------|------|------------|-------|---------|---------|---------|----------|
| In corpus directory | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| In marketplace | ✅ (add) | Via child | Via child | Via child | Via child | ✅ (batch) | Via child |
| In project (no corpus) | ✅ | After init | After init | After build | After build | ❌ | ❌ |
| Fresh directory | ✅ | After init | After init | After build | After build | ❌ | ❌ |
| Has installed corpora | Ask which | Ask which | Ask which | Ask which | Ask which | Ask which | Ask which |

---

## Step 4: Routing

Based on detected intent, route appropriately:

### Single Skill Dispatch

**Run the appropriate skill.** Do NOT attempt to execute the skill's logic yourself.

| Intent | Skill to Run |
|--------|--------------|
| init, create, new | `/hiivmind-corpus-init` |
| add-source, add, include | `/hiivmind-corpus-add-source` |
| build, scan, index | `/hiivmind-corpus-build` |
| enhance, expand, deepen | `/hiivmind-corpus-enhance` |
| refresh, update, sync | `/hiivmind-corpus-refresh` |
| upgrade, migrate | `/hiivmind-corpus-upgrade` |
| navigate, find, search | `/hiivmind-corpus-navigate` |
| awareness, configure | `/hiivmind-corpus-awareness` |

**Example:** For "init" intent, run `/hiivmind-corpus-init`.

Before running the skill, briefly state the context:
```
**Context**: {detected context}
**Intent**: {detected intent}
**Target corpus**: {corpus name if identified}
```

**CRITICAL:** The skill contains all the instructions. Do NOT:
- Create directories with mkdir
- Copy patterns from existing corpora
- Generate files without reading templates
- Skip running the skill

### Multi-Skill Orchestration

For compound intents, run skills in sequence. **Each skill must be explicitly run.**

**Pattern:** After each skill completes, immediately run the next skill. Do NOT improvise between skills.

| Workflow | Skill Sequence |
|----------|----------------|
| "index {project} docs" | `init` → `build` |
| "add {source} and include in index" | `add-source` → `build` |
| "refresh and expand {section}" | `refresh` → `enhance` |
| "create corpus with multiple sources" | `init` → `add-source` → `build` |

**Execution:**
1. Run `/hiivmind-corpus-init`
2. When it completes → Run `/hiivmind-corpus-add-source`
3. When it completes → Run `/hiivmind-corpus-build`

Use TodoWrite to track progress, but **always run each skill** - don't try to execute skill logic yourself.

### Ambiguity Resolution

When intent is unclear, ask using AskUserQuestion:

```
I'm not sure what you'd like to do. Which of these fits?

1. **Create new corpus** - Set up documentation indexing for a project
2. **Add sources** - Include additional repos, files, or web pages
3. **Build/rebuild index** - Analyze docs and create the index
4. **Enhance coverage** - Add more detail to specific topics
5. **Refresh from upstream** - Check for and apply doc updates
6. **Upgrade structure** - Apply latest corpus template standards
7. **Navigate/search** - Ask questions about existing corpora
```

---

## Mode: Interactive Menu (No Arguments)

When invoked without arguments, **ask what the user wants first** before doing any discovery or introspection.

### Step 1: Ask Intent First

Use AskUserQuestion immediately:

```
What would you like to do?

1. **Navigate a corpus** - Ask questions about installed documentation
2. **Create a new corpus** - Index documentation for a project
3. **Manage existing corpus** - Refresh, enhance, or check status
4. **List installed corpora** - See what's available
5. **Configure CLAUDE.md awareness** - Teach Claude when to use this plugin
```

### Step 2: Route Based on Selection

**If "Navigate a corpus"**:
1. Now discover installed corpora (see Discovery Commands below)
2. Present list of built corpora
3. Ask which corpus to query
4. Run `/hiivmind-corpus-navigate`

**If "Create a new corpus"**:
1. Run `/hiivmind-corpus-init` directly
2. No discovery needed

**If "Manage existing corpus"**:
1. Now discover installed corpora
2. Present list with status indicators
3. Ask which corpus and what action
4. Run the appropriate skill (`/hiivmind-corpus-refresh`, `/hiivmind-corpus-enhance`, or `/hiivmind-corpus-upgrade`)

**If "List installed corpora"**:
1. Now discover and display all corpora with status

**If "Configure CLAUDE.md awareness"**:
1. Run `/hiivmind-corpus-awareness` directly
2. Skill guides through injection target choice and CLAUDE.md editing

### Discovery Commands (only run when needed)

**Preferred:** Run `/hiivmind-corpus-discover` - it handles all discovery logic and cache updates.

**Using Claude tools:**
```
# Find all corpora
Glob: ~/.claude/skills/hiivmind-corpus-*/data/config.yaml
Glob: .claude-plugin/skills/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/hiivmind-corpus-*/data/config.yaml

# For each found, read config to get metadata
Read: {path}/data/config.yaml
```

**Using bash (when needed):**
```bash
# User-level corpora
for d in ~/.claude/skills/hiivmind-corpus-*/; do
    [ -d "$d" ] && [ -f "${d}data/config.yaml" ] && echo "user-level|$(basename "$d")|$d"
done

# Marketplace corpora
for d in ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/; do
    [ -d "$d" ] && [ -f "${d}data/config.yaml" ] && echo "marketplace|$(basename "$d")|$d"
done
```

**Pattern documentation:** See `lib/corpus/patterns/discovery.md` for detailed algorithms.

### Status Detection (only when listing or managing)

For each corpus, determine status:
- **placeholder**: index.md contains "Run hiivmind-corpus-build"
- **built**: index.md has real entries
- **stale**: local clone HEAD differs from indexed SHA

### Corpus Action Menu

After corpus selection for management, show actions:

**For built/stale corpora:**
- Navigate - Ask questions about this documentation
- Check freshness - See if the source has updates
- Enhance - Add more depth to specific topics
- Refresh - Sync index with upstream changes

**For placeholder corpora:**
- Build now - Create the index collaboratively
- Add sources - Add more documentation sources first

---

## Context-Aware Responses

### In Corpus Directory

```
You're in the hiivmind-corpus-polars corpus. What would you like to do?

- Navigate: Ask questions about Polars documentation
- Refresh: Check for upstream updates
- Enhance: Add more detail to specific topics
- Add sources: Include additional documentation
```

### In Marketplace with Multiple Corpora

```
This marketplace contains 4 corpora:
- hiivmind-corpus-polars
- hiivmind-corpus-ibis
- hiivmind-corpus-narwhals
- hiivmind-corpus-substrait

Which one would you like to work with? (Or "all" for batch operations)
```

### In Project Without Corpus

```
This looks like a {detected type} project. Would you like to:

1. **Create a repo-local corpus** - Team sharing via git
2. **Create a user-level corpus** - Personal use across projects
3. **Check for existing corpora** - See what's already installed
```

---

## Example Sessions

### Natural Language: New Corpus

**User:** `/hiivmind-corpus index the polars python library`

**Response:**
```
I'll help you create a Polars documentation corpus.

**Context**: Fresh directory
**Intent**: init → build
```

**Skill chain:**
1. Run `/hiivmind-corpus-init` → Creates structure, clones Polars docs
2. When it completes → Run `/hiivmind-corpus-build` → Builds the index

### Natural Language: Enhancement

**User:** `/hiivmind-corpus I need more detail on the lazy API`

**Response:**
```
You're in the Polars corpus. I'll enhance the lazy API coverage.

**Context**: In corpus directory
**Intent**: enhance
**Target**: lazy API section
```

Then run `/hiivmind-corpus-enhance`.

### Natural Language: Status Check

**User:** `/hiivmind-corpus is my polars corpus up to date?`

**Response:**
```
I'll check your Polars corpus status.

**Context**: Has installed corpora
**Intent**: refresh (status mode)
```

Then run `/hiivmind-corpus-refresh`.

### Natural Language: Multi-Source Setup

**User:** `/hiivmind-corpus set up react docs with kent's testing blog too`

**Response:**
```
I'll create a React corpus with both the official docs and Kent's blog.

**Context**: Fresh directory
**Intent**: init → add-source → build
```

**Skill chain:**
1. Run `/hiivmind-corpus-init` → Creates structure with React docs repo
2. When it completes → Run `/hiivmind-corpus-add-source` → Adds Kent's blog as web source
3. When it completes → Run `/hiivmind-corpus-build` → Builds combined index

### No Arguments: Interactive Menu

**User:** `/hiivmind-corpus`

**Response:**
```
What would you like to do with documentation corpora?

**Installed corpora:**
- hiivmind-corpus-polars (✓ built) - Polars DataFrame documentation
- hiivmind-corpus-ibis (✓ built) - Ibis SQL expressions
- hiivmind-corpus-github (⚠ stale) - GitHub API and Actions

**Quick actions:**
1. Select a corpus to navigate or manage
2. Create a new corpus
3. Refresh all stale corpora (1 stale)
```

---

## Error Handling

**No corpora and no clear intent:**
```
No documentation corpora are installed yet.

Would you like to:
1. **Create a new corpus** - Index documentation for a project
2. **Install from marketplace** - `/plugin install hiivmind-corpus-polars@hiivmind`

Or describe what you'd like to index: "/hiivmind-corpus index the react docs"
```

**Unrecognized project/library:**
```
I'm not familiar with "{project}". Could you provide:
1. The GitHub repository URL, or
2. The documentation website URL

I'll help set up a corpus from there.
```

**Conflicting context:**
```
You're already in the hiivmind-corpus-polars corpus.

Did you mean to:
1. Work with this corpus (navigate, enhance, refresh)
2. Create a different corpus elsewhere
3. Something else?
```

---

## Notes

- **Natural language first**: Describe your goal and the command routes automatically
- **Menu fallback**: No arguments shows interactive corpus selection
- **Multi-skill orchestration**: Compound requests chain skills with progress tracking
- **Context-aware**: Adapts suggestions based on current directory
- Uses `hiivmind-corpus-discover` logic for finding installed corpora
- Uses `hiivmind-corpus-navigate` for documentation queries
