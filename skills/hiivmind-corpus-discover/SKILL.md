---
name: hiivmind-corpus-discover
description: This skill should be used when the user asks "what corpora do I have installed?", "list my documentation corpora", "find installed corpus plugins", "what hiivmind-corpus plugins are available?", or needs to discover installed documentation corpus skills before navigating or managing them.
---

# Corpus Discovery

Find and report all installed hiivmind-corpus documentation corpora across user-level skills, repo-local skills, and marketplace plugins.

## When to Use

- Before navigating: Discover available corpora to query
- Before managing: Find corpora to enhance, refresh, or upgrade
- Troubleshooting: Verify which corpora are installed and their status
- Inventory: Report all corpus locations and types

## Discovery Locations

Scan these locations in order to find all installed corpora:

| Type | Location Pattern | Structure |
|------|------------------|-----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-*/` | Skill with `data/config.yaml` |
| **Repo-local** | `.claude-plugin/skills/hiivmind-corpus-*/` | Skill in current repo |
| **Marketplace single** | `~/.claude/plugins/marketplaces/hiivmind-corpus-*/` | Standalone corpus plugin |
| **Marketplace multi** | `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/` | Corpus inside a marketplace |

## Discovery Process

**See:** `lib/corpus/patterns/discovery.md` for detailed algorithms and implementations.

### Step 1: Detect Available Tools

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
## Installed Corpora

### User-level
(none)

### Repo-local
(none)

### Marketplace

| Name | Display | Keywords | Status | Sources | Last Indexed |
|------|---------|----------|--------|---------|--------------|
| hiivmind-corpus-polars | Polars | polars, dataframe, lazy | built | 1 | 2025-12-10 |
| hiivmind-corpus-ibis | Ibis | ibis, sql, backend | built | 1 | 2025-12-10 |
| hiivmind-corpus-github | GitHub | github, actions, api | stale | 2 | 2025-12-01 |

**Total: 3 corpora installed**
```

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
- Initialize new corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build corpus index: `skills/hiivmind-corpus-build/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
