# Upgrade Templates

Ready-to-use templates for adding missing sections during corpus upgrades.

---

## Report Format: Data-Only Corpus (Recommended)

Use this format for data-only corpora:

```markdown
## Upgrade Report: {corpus_name}

**Corpus Type:** Data-only corpus (recommended)
**Location:** {path}

### Status

| Component | Status | Notes |
|-----------|--------|-------|
| config.yaml | ✅ Present | |
| index.md | ✅ Present | |
| corpus.keywords | ⚠️ Missing field | Will add |

### Optional Components

| Component | Status | Notes |
|-----------|--------|-------|
| CLAUDE.md | ○ Not present | Optional |
| README.md | ○ Not present | Optional |
| uploads/ | ○ Not present | Created when needed |

### Recommended Actions

1. Add `corpus.keywords` to config.yaml

Would you like to apply these upgrades?
```

### What's NOT Checked for Data-Only

Data-only corpora do not need:
- `.claude-plugin/` directory
- `skills/` or `commands/` directories
- `references/project-awareness.md`
- ADR-005 compliance (navigation handled by hiivmind-corpus)

---

## Report Format: Legacy Structures

Use this format for legacy plugin-based corpora:

```markdown
## Upgrade Report: {corpus_name}

**Corpus Type:** {User-level skill | Repo-local skill | Standalone plugin | Marketplace plugin} (Legacy)
**Location:** {path}

### Status

| Component | Status | Notes |
|-----------|--------|-------|
| data/config.yaml | ✅ Present | |
| data/index.md | ✅ Present | |
| references/project-awareness.md | ❌ Missing | Will create |
| corpus.keywords | ⚠️ Missing field | Will add |
| skills/navigate/SKILL.md | ❌ Missing | ADR-005 compliance |
| commands/navigate.md routing | ⚠️ Has routing | Will simplify |

### Recommended Actions

1. Create `references/project-awareness.md`
2. Add `corpus.keywords` to data/config.yaml
3. Create `skills/navigate/SKILL.md` (ADR-005)
4. Remove routing table from `commands/navigate.md`

💡 Consider migrating to data-only architecture for simpler maintenance.

Would you like to apply these upgrades?
```

---

## Navigate Skill Sections

### Making Projects Aware Section

Append to navigate skill if missing:

```markdown
---

## Making Projects Aware of This Corpus

If you're working in a project that uses {{project_display_name}} but doesn't know about this corpus, you can add awareness to the project's CLAUDE.md.

**The `references/project-awareness.md` file** contains a ready-to-use snippet.

### When to Suggest Injection

Suggest adding project awareness when:
- User is working in a project that uses {{project_display_name}}
- User repeatedly asks {{project_display_name}} questions without invoking the corpus
- User says "I keep forgetting to use the docs"
```

### Corpus Maintenance Section (for skills)

Append to navigate skill if missing or outdated:

```markdown
---

## Corpus Maintenance

For corpus maintenance, use the parent plugin:

```
/hiivmind-corpus refresh {{corpus_short_name}}     - Update index from upstream
/hiivmind-corpus enhance {{corpus_short_name}} X   - Add depth to topic X
/hiivmind-corpus status {{corpus_short_name}}      - Check corpus freshness
```
```

### Tiered Index Navigation Section

Append if corpus uses tiered indexes:

#### Data-Only Corpus (root-level paths)

```markdown
---

## Tiered Index Navigation

This corpus uses a tiered index structure for large documentation sets.

### Index Structure

```
{corpus_root}/
├── index.md           # Top-level index (always check first)
├── index-core.md      # Core concepts index
├── index-api.md       # API reference index
└── index-guides.md    # Guides and tutorials index
```

### Navigation Strategy

1. **Start with top-level index**: Read `index.md` first
2. **Check section pointers**: Top-level index points to sub-indexes (`index-*.md`)
3. **Drill into relevant section**: Read the appropriate sub-index
4. **Access source file**: Use path from sub-index entry
```

#### Legacy Corpus (`data/` directory)

```markdown
---

## Tiered Index Navigation

This corpus uses a tiered index structure for large documentation sets.

### Index Structure

```
data/
├── index.md           # Top-level index (always check first)
├── core/
│   └── index.md       # Core concepts index
├── api/
│   └── index.md       # API reference index
└── guides/
    └── index.md       # Guides and tutorials index
```

### Navigation Strategy

1. **Start with top-level index**: Read `data/index.md` first
2. **Check section pointers**: Top-level index points to sub-indexes
3. **Drill into relevant section**: Read the appropriate sub-index
4. **Access source file**: Use path from sub-index entry
```

### Large Structured Files Section

Append if corpus has large structured files:

```markdown
---

## Large Structured Files

Some documentation files are too large to read fully. The index marks these with `⚡ GREP`.

### Handling Large Files

When you see `⚡ GREP` in an index entry:

1. **Don't read the whole file** - Use grep to find relevant sections
2. **Search for keywords** from the user's question
3. **Read only matching sections** with context

**Example:**

Index entry:
```
- **API Reference** (`source:api/reference.md`) ⚡ GREP - Complete API documentation
```

Navigation:
```bash
# Search for specific function
grep -n "create_session" .source/docs/api/reference.md

# Read with context
grep -B5 -A20 "create_session" .source/docs/api/reference.md
```
```

---

## Navigate Command Sections

### Help Section (If No Arguments)

For commands, include a help section:

```markdown
---

## If No Arguments Provided

Show a brief help message:

```
{{project_display_name}} Corpus - ask me anything!

Examples:
  /{{plugin_name}}:navigate how does X work?
  /{{plugin_name}}:navigate API reference for Y
  /{{plugin_name}}:navigate configuration options

For maintenance, use the parent plugin:
  /hiivmind-corpus refresh {{corpus_short_name}}
  /hiivmind-corpus enhance {{corpus_short_name}} [topic]
```
```

### Simplified Maintenance Section (ADR-005)

Replace old routing tables with:

```markdown
---

## Corpus Maintenance

For corpus maintenance, use the parent plugin:

```
/hiivmind-corpus refresh {{corpus_short_name}}     - Update index from upstream
/hiivmind-corpus enhance {{corpus_short_name}} X   - Add depth to topic X
/hiivmind-corpus status {{corpus_short_name}}      - Check corpus freshness
```
```

---

## Config Additions

### Adding Keywords Field

**Data-only corpus:** Add to `config.yaml` (root level)
**Legacy corpus:** Add to `data/config.yaml`

Add under `corpus:`:

```yaml
corpus:
  name: "{{project_name}}"
  display_name: "{{project_display_name}}"
  keywords:                    # ADD THIS SECTION
    - {{keyword_1}}
    - {{keyword_2}}
    - {{keyword_3}}
```

**Keyword suggestions by domain:**

| Domain | Suggested Keywords |
|--------|-------------------|
| DataFrame library | dataframe, pandas, series, column, row |
| SQL/Database | sql, query, database, table, join |
| API/SDK | api, sdk, client, request, response |
| Web framework | web, http, server, route, middleware |
| ML/AI | model, training, inference, tensor |

---

## Complete File Templates

### project-awareness.md Template

Create at `references/project-awareness.md`:

```markdown
# {{project_display_name}} Documentation Awareness

Add this snippet to your project's CLAUDE.md to enable automatic corpus usage.

## CLAUDE.md Snippet

\`\`\`markdown
## {{project_display_name}} Documentation

This project uses {{project_display_name}}. For documentation questions, use:

- **Skill**: `{{plugin_name}}-navigate` (auto-triggers on {{keywords_sentence}})
- **Command**: `/{{plugin_name}}:navigate [question]`

Example questions:
{{example_questions}}
\`\`\`

## When to Add

Add this snippet when:
- Project uses {{project_display_name}} as a dependency
- Team members frequently ask {{project_display_name}} questions
- You want Claude to automatically use the corpus for relevant queries
```

### Navigate Skill Frontmatter Template

For `skills/navigate/SKILL.md`:

```yaml
---
name: {{plugin_name}}-navigate
description: This skill answers questions about {{project_display_name}} documentation. Use when user asks about {{keywords_sentence}}. Triggers: {{keyword_list}}.
---
```

### Navigate Command Frontmatter Template

For `commands/navigate.md`:

```yaml
---
description: Ask questions about {{project_display_name}} documentation
argument-hint: Your question (e.g., "how does X work?", "API reference for Y")
allowed-tools: ["Read", "Grep", "Glob", "WebFetch", "AskUserQuestion", "Task", "TodoWrite"]
---
```
