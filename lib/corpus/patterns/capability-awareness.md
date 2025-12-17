# Pattern: Plugin Skill Awareness

## Purpose

Define what skills hiivmind-corpus provides, when to use each skill, and how to invoke them. Used by the awareness skill to generate CLAUDE.md sections that teach Claude when to use this plugin.

## When to Use

- Adding plugin awareness to CLAUDE.md
- Teaching Claude when to invoke each skill
- Generating awareness documentation

---

## WHAT - Plugin Skills

hiivmind-corpus provides 8 skills, grouped by priority:

### Primary: Using Corpora

| Skill | Name | Purpose |
|-------|------|---------|
| `hiivmind-corpus-navigate` | Navigate | Query across all installed corpora |
| `hiivmind-corpus-discover` | Discover | Find all installed corpora, cache to CLAUDE.md |

### Secondary: Maintaining Corpora

| Skill | Name | Purpose |
|-------|------|---------|
| `hiivmind-corpus-refresh` | Refresh | Sync index with upstream changes |
| `hiivmind-corpus-enhance` | Enhance | Deepen coverage on specific topics |
| `hiivmind-corpus-upgrade` | Upgrade | Update corpus to latest template standards |

### Tertiary: Creating Corpora

| Skill | Name | Purpose |
|-------|------|---------|
| `hiivmind-corpus-init` | Init | Create corpus structure for any open-source project |
| `hiivmind-corpus-build` | Build | Collaboratively analyze docs and create the index |
| `hiivmind-corpus-add-source` | Add Source | Extend corpus with git repos, local docs, or web pages |

### Skill Descriptions

#### Navigate
- **What:** Query across ALL installed corpora from a single entry point
- **Does:** Routes queries to appropriate per-corpus navigate skills
- **Run when:** User asks documentation questions, "find in docs", "what does X say about..."
- **Optimization:** Checks CLAUDE.md cache first before running discover

#### Discover
- **What:** Find and report all installed documentation corpora
- **Does:** Scans 4 installation locations, extracts metadata
- **Run when:** "what corpora do I have?", "list my docs"
- **Side effect:** Updates cache table in `~/.claude/CLAUDE.md`

#### Refresh
- **What:** Sync corpus index with upstream changes
- **Does:** Checks each source for changes, updates index based on diffs
- **Run when:** "refresh docs", "sync with upstream", "docs are stale"

#### Enhance
- **What:** Expand and deepen specific sections of existing corpus index
- **Does:** Searches sources for undiscovered documents, adds new entries
- **Run when:** "more detail on X", "expand X section"

#### Upgrade
- **What:** Update existing corpus skills to latest template standards
- **Does:** Retrofits corpora with new features, updates templates
- **Run when:** "upgrade corpus", "update to latest"

#### Init
- **What:** Create corpus structure for any open-source project
- **Does:** Detects context, offers destination types, scaffolds structure
- **Run when:** "index docs for X", "create corpus for X"

#### Build
- **What:** Analyze documentation and build the initial corpus index
- **Does:** Scans sources, collaboratively builds index.md with user
- **Run when:** "build the index", "analyze the docs" (after init)

#### Add Source
- **What:** Add a new documentation source to an existing corpus
- **Does:** Supports git repos, local files, web content
- **Run when:** "add X to my corpus", "extend with X docs"

---

## WHEN - Trigger Mapping

Maps operational needs to skills:

### Navigation Triggers (Primary)

| User Says / Needs | Skill | Confidence |
|-------------------|-------|------------|
| "find in docs", "check documentation" | navigate | High |
| "what do the X docs say about..." | navigate | High |
| "how does X work?" (for indexed library) | navigate | High |
| "look up in corpus" | navigate | High |
| "what corpora do I have?", "list my docs" | discover | High |
| "find installed corpus plugins" | discover | High |
| User asks question about indexed library | navigate (proactive) | Medium |

### Maintenance Triggers

| User Says / Needs | Skill | Confidence |
|-------------------|-------|------------|
| "refresh docs", "sync with upstream" | refresh | High |
| "docs are stale", "update corpus" | refresh | High |
| "upgrade corpus", "update to latest" | upgrade | High |
| "more detail on X", "expand X section" | enhance | High |

### Creation Triggers (Less Common)

| User Says / Needs | Skill | Confidence |
|-------------------|-------|------------|
| "index docs for X", "create corpus for X" | init | High |
| "add X to my corpus", "extend with X docs" | add-source | High |
| "build the index", "analyze the docs" | build | High |
| First time using library, new dependency added | init (proactive) | Medium |

### Awareness Triggers

| User Says / Needs | Skill | Confidence |
|-------------------|-------|------------|
| "add awareness", "plugin awareness" | awareness | High |
| "configure Claude for corpus", "setup CLAUDE.md" | awareness | High |
| "what can corpus do", "capabilities tour" | awareness | High |
| "enable corpus features" | awareness | High |

---

## HOW - Invocation Methods

### Gateway Command (Recommended)

```
/hiivmind-corpus [describe what you want]
```

The gateway auto-detects intent and routes to the appropriate skill.

**Examples:**
```
/hiivmind-corpus what does Polars say about lazy evaluation
/hiivmind-corpus list my corpora
/hiivmind-corpus refresh my React docs
/hiivmind-corpus create corpus for FastAPI
```

### Direct Skill Invocation

When you know exactly which skill is needed:

```
Invoke skill: hiivmind-corpus:hiivmind-corpus-navigate
Invoke skill: hiivmind-corpus:hiivmind-corpus-discover
Invoke skill: hiivmind-corpus:hiivmind-corpus-init
```

### Interactive Menu

```
/hiivmind-corpus
```

Without arguments, presents numbered menu of all operations.

---

## Two Injection Targets

The awareness skill supports two injection locations:

| Target | Location | Best For |
|--------|----------|----------|
| **User-level** | `~/.claude/CLAUDE.md` | Personal corpus collection across all projects |
| **Repo-level** | `{repo}/CLAUDE.md` | Team projects using specific corpora |

### User-Level Injection

Includes corpus cache for fast lookup:
- Run discover to find all installed corpora
- Build cache table with corpus names, keywords, locations
- Navigate checks cache before running discover

### Repo-Level Injection

Simpler template focused on specific corpora:
- List project-specific corpora
- Document when to suggest navigate
- No caching (project-scoped)

---

## Cache Format

The user-level cache uses HTML comments as markers for machine-updateable content:

```markdown
<!-- Cache populated by discover skill - navigate checks this first -->
| Corpus | Keywords | Location |
|--------|----------|----------|
| polars | dataframe, lazy, expressions | ~/.claude/plugins/marketplaces/hiivmind-corpus-polars |
| react | components, hooks, jsx | ~/.claude/skills/hiivmind-corpus-react |
<!-- End corpus cache -->
```

### Navigate Behavior

1. Check `~/.claude/CLAUDE.md` for cache table
2. If found and not empty, use cached corpus locations directly
3. If not found or empty, run discover skill
4. Discover skill updates cache after scanning

### Discover Behavior

1. Scan all 4 installation locations
2. Extract corpus keywords from config.yaml
3. Update cache table in `~/.claude/CLAUDE.md` (if exists)
4. Return discovery results

---

## CLAUDE.md Templates

### User-Level Template (with Corpus Cache)

```markdown
## Documentation Corpora (hiivmind-corpus)

Use [hiivmind-corpus](https://github.com/hiivmind/hiivmind-corpus) for documentation navigation.

### Installed Corpora

<!-- Cache populated by discover skill - navigate checks this first -->
| Corpus | Keywords | Location |
|--------|----------|----------|
<!-- End corpus cache -->

### When to Use

| You Need To... | Use This |
|----------------|----------|
| Find in indexed docs | Navigate skill (checks cache first) |
| List all corpora | Discover skill (updates cache) |
| Sync stale docs | Refresh skill |
| More detail on topic | Enhance skill |
| Create new corpus | Init skill |

### Proactive Suggestions

Suggest using this plugin when:
- User asks about library functionality (suggest navigate)
- User mentions "docs are outdated" (suggest refresh)
- User adds new library/dependency (suggest init)
- User wants more detail on indexed topic (suggest enhance)

### How to Invoke

**Gateway (recommended):**
```
/hiivmind-corpus [query or action]
```

**Direct skill invocation** when you know which skill:
```
Skill: hiivmind-corpus-navigate
Skill: hiivmind-corpus-discover
```
```

### Repo-Level Template (Specific Corpora)

```markdown
## Documentation Corpus (hiivmind-corpus)

This project uses [hiivmind-corpus](https://github.com/hiivmind/hiivmind-corpus) for documentation.

### Project Corpora

| Corpus | Purpose |
|--------|---------|
| {corpus_name} | {description} |

### When to Use

Suggest navigate skill when user asks about:
- {topic_1}
- {topic_2}
- {topic_3}

### How to Invoke

```
/hiivmind-corpus what does {corpus_name} say about [topic]
```
```

---

## Related Patterns

- `discovery.md` - Find installed corpora across all 4 location types
- `status.md` - Check corpus freshness

## Related Skills

- **hiivmind-corpus-awareness** - Uses this pattern to generate CLAUDE.md sections
- **hiivmind-corpus-discover** - Updates corpus cache
- **hiivmind-corpus-navigate** - Uses corpus cache for fast lookup
