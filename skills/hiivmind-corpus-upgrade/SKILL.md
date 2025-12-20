---
name: hiivmind-corpus-upgrade
description: >
  This skill should be used when the user asks to "upgrade corpus", "migrate corpus to new format",
  "update corpus structure", "corpus is missing features", "bring corpus up to date", or when
  hiivmind-corpus templates have been updated and existing corpora need migration. Triggers on
  "upgrade my [corpus name] corpus", "corpus needs updating", "missing project-awareness.md",
  "update to latest corpus format", or "hiivmind-corpus upgrade".
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
ls skills/ 2>/dev/null
ls commands/ 2>/dev/null
ls .claude-plugin/ 2>/dev/null
```

| Indicator | Corpus Type | Expected Structure |
|-----------|-------------|-------------------|
| `SKILL.md` at root + `data/` | User-level or repo-local skill | `SKILL.md`, `data/`, `references/` |
| `.claude-plugin/plugin.json` | Standalone plugin | `skills/navigate/SKILL.md`, `commands/navigate.md`, `data/`, `references/` |
| Parent has `marketplace.json` | Plugin in marketplace | Same as standalone plugin |

**Plugin types (ADR-005):** Must have BOTH:
- `skills/navigate/SKILL.md` - Auto-triggers based on domain keywords
- `commands/navigate.md` - Explicit entry point for users

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
3. Write to `references/project-awareness.md`

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

### ADR-005: Navigate Skill/Command Structure (Plugins Only)

**Applies to:** Standalone plugins and marketplace plugins (NOT user-level/repo-local skills)

**Detection:**
```bash
# Check for old structure (command only, no skill)
ls commands/navigate.md 2>/dev/null && echo "HAS_COMMAND=true"
ls skills/navigate/SKILL.md 2>/dev/null && echo "HAS_SKILL=true"

# Check for routing table in command (old pattern)
grep -q "hiivmind-corpus-refresh" commands/navigate.md 2>/dev/null && echo "HAS_ROUTING=true"
```

**Upgrade scenarios:**

| Current State | Action |
|---------------|--------|
| Has command, no skill | Create `skills/navigate/SKILL.md` |
| Has skill, no command | Create `commands/navigate.md` |
| Command has routing table | Simplify command (remove routing) |
| Both exist, no routing | Already compliant |

**Creating missing navigate skill:**

1. Create directory: `mkdir -p skills/navigate`
2. Read `data/config.yaml` for keywords
3. Generate from `navigate-skill.md.template`:
   - Set `name: {plugin_name}-navigate`
   - Set `description:` with domain keywords for auto-triggering
   - Copy navigation process from existing command (if present)
4. Write to `skills/navigate/SKILL.md`

**Simplifying old command (removing routing):**

Old commands may contain routing tables like:
```markdown
| Action | Skill |
|--------|-------|
| refresh | hiivmind-corpus-refresh |
| enhance | hiivmind-corpus-enhance |
```

Remove these sections:
- "Routing table" or "Parent skill routing" sections
- "How to invoke parent skills" sections

Replace with simple maintenance reference:
```markdown
## Corpus Maintenance

For corpus maintenance, use the parent plugin:

```
/hiivmind-corpus refresh {name}     - Update index from upstream
/hiivmind-corpus enhance {name} X   - Add depth to topic X
/hiivmind-corpus status {name}      - Check corpus freshness
```
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
  - references/project-awareness.md

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
