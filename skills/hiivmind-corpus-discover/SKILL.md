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

### Step 1: Scan All Locations

Run these commands to find corpora:

```bash
# User-level corpora
ls -d ~/.claude/skills/hiivmind-corpus-*/ 2>/dev/null

# Repo-local corpora (in current working directory)
ls -d .claude-plugin/skills/hiivmind-corpus-*/ 2>/dev/null

# Marketplace single-corpus plugins
ls -d ~/.claude/plugins/marketplaces/hiivmind-corpus-*/ 2>/dev/null

# Marketplace multi-corpus (child plugins)
ls -d ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ 2>/dev/null
```

### Step 2: Validate Each Corpus

For each directory found, verify it's a valid corpus by checking for required files:

```bash
# Check for skill file
ls {corpus_path}/SKILL.md 2>/dev/null || ls {corpus_path}/skills/navigate/SKILL.md 2>/dev/null

# Check for config
ls {corpus_path}/data/config.yaml 2>/dev/null

# Check for index
ls {corpus_path}/data/index.md 2>/dev/null
```

### Step 3: Determine Status

For each valid corpus, determine its build status:

**Placeholder** - Index exists but contains only the placeholder text:
```bash
grep -q "Run.*hiivmind-corpus-build" {corpus_path}/data/index.md && echo "placeholder"
```

**Built** - Index has real entries (no placeholder text):
```bash
grep -qv "Run.*hiivmind-corpus-build" {corpus_path}/data/index.md && echo "built"
```

**Stale** (for git sources) - Local clone is newer than indexed SHA:
```bash
# Get indexed SHA from config
INDEXED_SHA=$(yq '.sources[0].last_commit_sha' {corpus_path}/data/config.yaml)

# Get current clone HEAD
CLONE_HEAD=$(git -C {corpus_path}/.source/{source_id} rev-parse HEAD 2>/dev/null)

# Compare
[ "$CLONE_HEAD" != "$INDEXED_SHA" ] && echo "stale"
```

### Step 4: Extract Metadata

For each corpus, extract display information:

```bash
# Get display name from skill
grep -m1 "^name:" {corpus_path}/SKILL.md | sed 's/name: //'

# Or from navigate skill for marketplace plugins
grep -m1 "^name:" {corpus_path}/skills/navigate/SKILL.md | sed 's/name: //'

# Count sources
yq '.sources | length' {corpus_path}/data/config.yaml

# Get last indexed date
yq '.index.last_updated_at' {corpus_path}/data/config.yaml
```

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

For fast discovery without detailed analysis:

```bash
# Count total installed corpora
(ls -d ~/.claude/skills/hiivmind-corpus-*/ ~/.claude/plugins/marketplaces/hiivmind-corpus-*/ ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ .claude-plugin/skills/hiivmind-corpus-*/ 2>/dev/null) | wc -l

# List names only
(ls -d ~/.claude/skills/hiivmind-corpus-*/ ~/.claude/plugins/marketplaces/hiivmind-corpus-*/ ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ .claude-plugin/skills/hiivmind-corpus-*/ 2>/dev/null) | xargs -I{} basename {}
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
    navigate_skill: hiivmind-corpus-polars-navigate
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

- Initialize new corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build corpus index: `skills/hiivmind-corpus-build/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
