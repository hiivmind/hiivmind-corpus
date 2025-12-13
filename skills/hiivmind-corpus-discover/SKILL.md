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

### Using the Corpus Library

Source the library functions for composable discovery:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-status-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-path-functions.sh"
```

### Step 1: Discover All Corpora

```bash
# Discover all corpora with name, type, status, and path
discover_all | format_table
# Output: name|type|status|path

# Or discover specific locations
discover_user_level
discover_repo_local
discover_marketplace
discover_marketplace_single
```

### Step 2: Filter and List

```bash
# Only built corpora
discover_all | filter_built | list_names

# Only placeholder corpora (need building)
discover_all | filter_placeholder

# Find specific corpus
discover_all | filter_name "polars"

# Count total
discover_all | count_corpora
```

### Step 3: Get Status Details

For detailed status on a specific corpus:

```bash
# Get index status
get_index_status "$corpus_path"  # Returns: built | placeholder | no-index

# Check freshness
compare_freshness "$corpus_path" "$source_id"  # Returns: current | stale | unknown

# Full status report
report_corpus_status "$corpus_path"
```

### Step 4: Resolve Paths

```bash
# Get key paths
get_index_path "$corpus_path"
get_config_path "$corpus_path"
get_navigate_skill_path "$corpus_path"

# List source IDs
list_source_ids "$corpus_path"
```

**Library reference:** See `lib/corpus/corpus-index.md` for full function documentation.

## Output Format

Present discovered corpora in a structured format:

```
## Installed Corpora

### User-level
(none)

### Repo-local
(none)

### Marketplace

| Name | Display | Status | Sources | Last Indexed |
|------|---------|--------|---------|--------------|
| hiivmind-corpus-polars | Polars | built | 1 | 2025-12-10 |
| hiivmind-corpus-ibis | Ibis | built | 1 | 2025-12-10 |
| hiivmind-corpus-github | GitHub | stale | 2 | 2025-12-01 |

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

## Quick Commands

Using the library for fast discovery:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"

# Count total installed corpora
discover_all | count_corpora

# List names only
discover_all | list_names

# Built corpora only
discover_all | filter_built | list_names

# Simple formatted list
discover_all | format_simple
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

- **Corpus library**: `lib/corpus/corpus-index.md` - Full function documentation
- Initialize new corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build corpus index: `skills/hiivmind-corpus-build/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
