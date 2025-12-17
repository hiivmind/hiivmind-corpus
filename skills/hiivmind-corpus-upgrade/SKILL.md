---
name: hiivmind-corpus-upgrade
description: Upgrade an existing corpus skill to the latest hiivmind-corpus standards. Use when "migrate corpus", "update corpus format", "upgrade corpus", or when templates or navigate skill features have been updated.
---

# Corpus Upgrade

Bring an existing corpus skill up to date with the latest hiivmind-corpus templates and features.

## When to Use

- After hiivmind-corpus has been updated with new features
- When a corpus is missing files that newer corpora have (e.g., `project-awareness.md`)
- When navigate skill is missing sections (e.g., "Making Projects Aware", tiered index support)
- To ensure all your corpora follow current best practices

## Process

```
1. LOCATE  →  2. DETECT  →  3. COMPARE  →  4. REPORT  →  5. APPLY  →  6. VERIFY
```

---

## Step 1: Locate Corpus

Identify the corpus to upgrade. Can be run from:
- Inside a corpus directory
- Parent directory with corpus path specified

```bash
# Check if we're in a corpus (has data/config.yaml)
ls data/config.yaml 2>/dev/null && echo "IN_CORPUS=true"

# Or check for corpus subdirectories
ls -d hiivmind-corpus-*/ 2>/dev/null
```

**If in a marketplace**: Ask user which corpus to upgrade, or offer to upgrade all.

---

## Step 2: Detect Corpus Type

Determine what kind of corpus this is:

```bash
# Check structure
ls -la
ls data/
ls skills/
```

| Indicator | Corpus Type |
|-----------|-------------|
| `SKILL.md` at root + `data/` | User-level or repo-local skill |
| `.claude-plugin/plugin.json` + `skills/navigate/` | Standalone plugin |
| Parent has `marketplace.json` | Plugin in marketplace |

Record the corpus type - it affects which templates apply.

---

## Step 3: Compare Against Templates

**See:** `lib/corpus/patterns/config-parsing.md` for YAML extraction methods.

Locate the hiivmind-corpus templates and compare:

### Find Template Source

The templates are in the hiivmind-corpus plugin. Locate via:
1. Check if hiivmind-corpus is installed globally: `~/.claude/plugins/hiivmind-corpus/templates/`
2. Check common development locations
3. Ask user for hiivmind-corpus location if needed

### Check Each Component

**See:** `references/upgrade-checklists.md` for complete checklists:
- Required files for all corpus types
- Additional files for plugins
- Config schema field requirements
- Navigate skill section requirements

---

## Step 4: Report Findings

**See:** `references/upgrade-templates.md` for report format templates.

Present a clear report showing:
- ✅ UP TO DATE items
- ⚠️ MISSING FILES
- ⚠️ MISSING CONFIG FIELDS (with suggestions)
- ⚠️ MISSING SECTIONS in navigate skill

Ask user: "Would you like to apply these upgrades?"

---

## Step 5: Apply Upgrades

For each missing component, apply the upgrade:

### Adding Missing Config Fields

**corpus.keywords:**
1. Suggest keywords based on corpus name and domain:
   - Project name (e.g., `polars` from `hiivmind-corpus-polars`)
   - Domain terms (infer from index sections)
   - Common aliases
2. Ask user to confirm or modify suggestions
3. Add to `data/config.yaml`:
   ```yaml
   corpus:
     name: "polars"
     display_name: "Polars"
     keywords:           # NEW
       - polars
       - dataframe
       - lazy
       - expression
   ```

### Adding Missing Files

**project-awareness.md:**
1. Read `templates/project-awareness.md.template`
2. Fill placeholders from existing config:
   - `{{project_name}}` - from corpus directory name
   - `{{project_display_name}}` - capitalize project_name
   - `{{skill_topics}}` - extract from index.md sections
   - `{{example_questions}}` - generate based on topics
3. Write to `data/project-awareness.md`

### Adding Missing Sections to Navigate Skill

**See:** `references/upgrade-templates.md` for complete section templates to append:
- Tiered Index Navigation section
- Large Structured Files section
- Making Projects Aware section

### Updating .gitignore

Ensure these entries exist:
```
.source/
.cache/
```

---

## Step 6: Verify

After applying upgrades:

```bash
# List updated files
ls -la data/
ls -la skills/navigate/

# Show what changed
git status
git diff --stat
```

Present summary:
```
Upgrade Complete!
════════════════

Files added:
  - data/project-awareness.md

Files modified:
  - skills/navigate/SKILL.md (+45 lines)

Remember to commit:
  git add -A && git commit -m "Upgrade corpus to latest standards"
```

---

## Batch Upgrade (Marketplaces)

**See:** `references/batch-upgrade.md` for:
- Batch upgrade options (upgrade all, upgrade selected, report only)
- Consolidated report format
- Example upgrade session walkthrough
- Version tracking recommendations

---

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/config-parsing.md` - YAML config extraction
- `lib/corpus/patterns/discovery.md` - Corpus discovery algorithms
- `lib/corpus/patterns/status.md` - Index status checking
- `lib/corpus/patterns/paths.md` - Path resolution

**Related skills:**
- Initialize new corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
