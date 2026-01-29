---
name: hiivmind-corpus-discover
description: This skill should be used when the user asks "what corpora do I have installed?", "list my documentation corpora", "find installed corpus plugins", "what hiivmind-corpus plugins are available?", "check the docs", "search the documentation", "what do the docs say", "look up in corpus", or needs to discover installed documentation corpus skills. Also use when a generic documentation query doesn't specify which corpus to search.
---

# Corpus Discovery

Find and report all available documentation corpora, including:
- **Registered corpora** - Listed in project's `.hiivmind/corpus/registry.yaml`
- **Legacy plugin-based corpora** - Installed as Claude Code plugins (backward compatibility)

## When to Use

- **Generic doc queries**: User asks "check the docs" without specifying which documentation
- **Corpus inventory**: User asks what corpora are installed/registered
- **Before managing**: Find corpora to enhance, refresh, or upgrade
- **Troubleshooting**: Verify which corpora are available and their status

## Handling Generic Documentation Queries

When triggered by a generic query like "check the docs" or "what do the docs say about X":

1. Discover all available corpora (registry + legacy plugins)
2. List them with their domain keywords
3. Ask user to pick one or be more specific:
   > "I found these documentation corpora:
   > - **Fly.io** (registered) - flyio, deployment, hosting
   > - **Polars** (plugin) - dataframe, lazy, expressions
   >
   > Which would you like me to search? Or rephrase your question with a specific domain."
4. Route to navigate skill for the selected corpus

## Discovery Sources

### 1. Project Registry (Primary)

Check `.hiivmind/corpus/registry.yaml` for registered corpora:

```
Read: .hiivmind/corpus/registry.yaml
```

Registry corpora are data-only repositories accessed via GitHub or local paths.

**See:** `lib/corpus/patterns/registry-loading.md` for registry schema and loading.

### 2. Legacy Plugin Locations (Backward Compatibility)

Scan these locations for plugin-based corpora:

| Type | Location Pattern | Structure |
|------|------------------|-----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-*/` | Skill with `data/config.yaml` |
| **Repo-local** | `.claude-plugin/skills/hiivmind-corpus-*/` | Skill in current repo |
| **Marketplace single** | `~/.claude/plugins/marketplaces/hiivmind-corpus-*/` | Standalone corpus plugin |
| **Marketplace multi** | `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/` | Corpus inside a marketplace |

## Discovery Process

### Step 0: Check Project Registry (New Architecture)

First, check if the project has a corpus registry:

```
Read: .hiivmind/corpus/registry.yaml
```

If registry exists, extract registered corpora:

```yaml
# Registry structure
corpora:
  - id: flyio
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main
```

For each registered corpus, fetch its config to get keywords:

**Using gh api (preferred):**
```bash
gh api repos/{owner}/{repo}/contents/config.yaml?ref={ref} --jq '.content' | base64 -d
```

Then parse the YAML to extract: corpus.name, corpus.display_name, and corpus.keywords

**Fallback (WebFetch):**
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/{ref}/config.yaml
prompt: "Extract corpus.name, corpus.display_name, and corpus.keywords"
```

**See:** `lib/corpus/patterns/registry-loading.md` for detailed registry handling.

### Step 1: Detect Available Tools (Legacy)

Before discovery, check tool availability (see `lib/corpus/patterns/tool-detection.md`):
- YAML parsing: yq, python+pyyaml, or grep fallback
- Required for reading corpus config metadata

### Step 2: Discover All Corpora

Scan each location for `hiivmind-corpus-*/` directories with `data/config.yaml`:

**Using Claude tools:**
```
Glob: ~/.claude/skills/hiivmind-corpus-*/data/config.yaml
Glob: .claude-plugin/skills/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/hiivmind-corpus-*/data/config.yaml
```

**Using bash:**
```bash
# User-level corpora
for d in ~/.claude/skills/hiivmind-corpus-*/; do
    [ -d "$d" ] && [ -f "${d}data/config.yaml" ] && echo "user-level|$(basename "$d")|$d"
done

# Repo-local corpora
for d in ./.claude-plugin/skills/hiivmind-corpus-*/; do
    [ -d "$d" ] && [ -f "${d}data/config.yaml" ] && echo "repo-local|$(basename "$d")|$d"
done

# Marketplace corpora (see patterns/discovery.md for full list)
```

### Step 3: Get Status for Each Corpus

For each discovered corpus, determine status by reading `data/index.md`:

**Algorithm:**
1. If file missing → `no-index`
2. If contains "Run hiivmind-corpus-build" → `placeholder`
3. Otherwise → `built`

**Using Claude tools:**
```
Read: {corpus_path}/data/index.md
Check for "Run hiivmind-corpus-build" text
```

### Step 4: Extract Routing Metadata

For built corpora, extract keywords and display name for routing:

**See:** `lib/corpus/patterns/config-parsing.md` for YAML extraction methods.

Fields to extract from `data/config.yaml`:
- `.corpus.display_name` (or infer from name)
- `.corpus.keywords[]` (or infer from name)

### Step 5: Resolve Paths

Path resolution patterns in `lib/corpus/patterns/paths.md`:
- Config: `{corpus_path}/data/config.yaml`
- Index: `{corpus_path}/data/index.md`
- Navigate skill: `{corpus_path}/SKILL.md` or `{corpus_path}/skills/navigate/SKILL.md`

**Pattern documentation:** See `lib/corpus/patterns/` for full pattern library.

## Output Format

Present discovered corpora in a structured format:

```
## Available Corpora

### Registered (via registry.yaml)

| ID | Display | Source | Keywords | Status |
|----|---------|--------|----------|--------|
| flyio | Fly.io | github:hiivmind/hiivmind-corpus-flyio | flyio, deployment | healthy |
| polars | Polars | github:hiivmind/hiivmind-corpus-data/.../polars | polars, dataframe | healthy |

### Legacy Plugins (backward compatibility)

| Name | Display | Keywords | Status | Sources | Last Indexed |
|------|---------|----------|--------|---------|--------------|
| hiivmind-corpus-github | GitHub | github, actions, api | built | 2 | 2025-12-01 |

**Total: 3 corpora (2 registered, 1 legacy plugin)**

---

To register a new corpus:
  /hiivmind-corpus register github:owner/repo

To navigate a corpus:
  /hiivmind-corpus navigate flyio "your question"
```

## Cache Update (Optional)

After discovery, optionally update the corpus cache in `~/.claude/CLAUDE.md`:

### Step 6: Update User-Level Cache

If `~/.claude/CLAUDE.md` exists:

1. Read the file
2. Look for cache markers: `<!-- hiivmind-corpus-cache -->` ... `<!-- /hiivmind-corpus-cache -->`
3. If found: Replace content between markers with new table
4. If not found: Do not add (awareness skill handles initial injection)

**Cache table format:**

```markdown
<!-- hiivmind-corpus-cache -->
| Corpus | Keywords | Location |
|--------|----------|----------|
| {name without hiivmind-corpus- prefix} | {keywords from config, comma-separated} | {full path} |
<!-- /hiivmind-corpus-cache -->
```

**Using Claude Edit tool:**
- old_string: existing cache block (including markers)
- new_string: updated cache block with new discovery results

**Example:**

```
old_string:
<!-- hiivmind-corpus-cache -->
| Corpus | Keywords | Location |
|--------|----------|----------|
| polars | dataframe, lazy | ~/.claude/plugins/... |
<!-- /hiivmind-corpus-cache -->

new_string:
<!-- hiivmind-corpus-cache -->
| Corpus | Keywords | Location |
|--------|----------|----------|
| polars | dataframe, lazy, expressions | ~/.claude/plugins/marketplaces/hiivmind-corpus-data/hiivmind-corpus-polars |
| ibis | ibis, sql, backend | ~/.claude/plugins/marketplaces/hiivmind-corpus-data/hiivmind-corpus-ibis |
<!-- /hiivmind-corpus-cache -->
```

**Note:** Cache update is opportunistic. If CLAUDE.md doesn't have the cache section, skip silently. The awareness skill (`hiivmind-corpus-awareness`) is responsible for initial injection.

---

## Type Detection

Determine corpus type based on its location:

| Location Pattern | Type |
|------------------|------|
| `~/.claude/skills/hiivmind-corpus-*` | `user-level` |
| `.claude-plugin/skills/hiivmind-corpus-*` | `repo-local` |
| `~/.claude/plugins/marketplaces/hiivmind-corpus-*` (root has plugin.json) | `marketplace-single` |
| `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*` | `marketplace-multi` |

## Corpus Path Resolution

Different corpus types have different internal structures:

**User-level and Repo-local skills:**
```
hiivmind-corpus-{project}/
├── SKILL.md              # Navigate skill at root
└── data/
    ├── config.yaml
    └── index.md
```

**Marketplace plugins:**
```
hiivmind-corpus-{project}/
├── .claude-plugin/plugin.json
├── skills/navigate/SKILL.md    # Navigate skill in skills/
└── data/
    ├── config.yaml
    └── index.md
```

Adjust file lookups based on type.

## Quick Discovery Examples

**Using Claude tools (recommended):**
```
# Find all corpora
Glob: ~/.claude/skills/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/**/hiivmind-corpus-*/data/config.yaml

# For each found, read config.yaml to get metadata
Read: {path}/data/config.yaml
```

**Using bash (cross-platform examples in `lib/corpus/patterns/discovery.md`):**
```bash
# Count user-level corpora
ls -d ~/.claude/skills/hiivmind-corpus-*/ 2>/dev/null | wc -l

# List all corpus names
for d in ~/.claude/skills/hiivmind-corpus-*/; do basename "$d"; done
```

## Integration with Gateway Command

This skill is invoked by the `/hiivmind-corpus` gateway command to:
1. Build the interactive corpus selection list
2. Validate corpus names provided as arguments
3. Resolve corpus paths for dispatching to other skills

When invoked programmatically, output structured data:

```yaml
corpora:
  - name: hiivmind-corpus-polars
    display_name: Polars
    type: marketplace-multi
    location: ~/.claude/plugins/marketplaces/hiivmind-corpus-data/hiivmind-corpus-polars
    status: built
    keywords:                       # For per-session routing
      - polars
      - dataframe
      - lazy
      - expression
    sources: 1
    last_indexed: "2025-12-10"
    navigate_skill: hiivmind-corpus-navigate-polars
```

## Error Handling

**No corpora found:**
> No hiivmind-corpus documentation corpora are installed.
>
> To create one: Use `hiivmind-corpus-init` to generate a new corpus
> To install from marketplace: `/plugin install hiivmind-corpus-polars@hiivmind`

**Corpus directory exists but invalid:**
Skip and note in output:
> Skipped: ~/.claude/skills/hiivmind-corpus-broken (missing config.yaml)

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/tool-detection.md` - Detect available tools
- `lib/corpus/patterns/discovery.md` - Corpus discovery algorithms
- `lib/corpus/patterns/config-parsing.md` - YAML config extraction
- `lib/corpus/patterns/status.md` - Index status checking
- `lib/corpus/patterns/paths.md` - Path resolution

**Related skills:**
- **Navigate:** `skills/hiivmind-corpus-navigate/SKILL.md` - Query corpus documentation
- **Register:** `skills/hiivmind-corpus-register/SKILL.md` - Add corpus to registry
- **Status:** `skills/hiivmind-corpus-status/SKILL.md` - Check corpus health
- **Initialize:** `skills/hiivmind-corpus-init/SKILL.md` - Create new corpus
- **Build:** `skills/hiivmind-corpus-build/SKILL.md` - Build corpus index
- **Gateway:** `commands/hiivmind-corpus.md` - Unified entry point

**Note:** Navigation is now handled by `hiivmind-corpus-navigate` skill, which works with both registry-based and legacy plugin-based corpora.
