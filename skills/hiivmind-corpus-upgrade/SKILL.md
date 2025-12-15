---
name: hiivmind-corpus-upgrade
description: Upgrade an existing corpus skill to the latest hiivmind-corpus standards. Use when templates or navigate skill features have been updated.
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

**Required files for all corpus types:**

| File | Template | Check |
|------|----------|-------|
| Navigate skill | `navigate-skill.md.template` | Compare sections |
| Config | `config.yaml.template` | Check schema |
| Project awareness | `project-awareness.md.template` | Exists? |

**Additional for plugins:**

| File | Template | Check |
|------|----------|-------|
| plugin.json | `plugin.json.template` | Structure valid? |
| .gitignore | `gitignore.template` | Has required entries? |
| README.md | `readme.md.template` | Exists? |
| CLAUDE.md | `claude.md.template` | Exists? |

### Config Schema Checks

**See:** `lib/corpus/patterns/config-parsing.md` for extraction methods with multiple tool implementations.

Read `data/config.yaml` and verify:

| Field | Added In | Purpose | Check |
|-------|----------|---------|-------|
| `schema_version` | v1 | Version tracking | Must be present |
| `corpus.keywords` | v4 | Per-session routing | Array of routing keywords |

**Keywords check (using yq if available, or fallback):**

Using Claude tools:
```
Read: data/config.yaml
Check for presence of: corpus.keywords
```

Using bash with yq:
```bash
yq '.corpus.keywords' data/config.yaml
```

If missing, suggest adding keywords based on corpus name and domain.

### Section Checks for Navigate Skill

Read the current navigate skill and check for these sections:

| Section | Added In | Purpose |
|---------|----------|---------|
| `## Process` | Original | Core navigation steps |
| `## Tiered Index Navigation` | v2 | Large corpus support |
| `## Large Structured Files` | v2 | GREP marker handling |
| `## Making Projects Aware` | v3 | Project awareness injection |

---

## Step 4: Report Findings

Present a clear report to the user:

```
Corpus: hiivmind-corpus-polars
Type: Standalone plugin
Location: /path/to/corpus

Upgrade Report:
═══════════════

✅ UP TO DATE:
  - data/config.yaml (schema_version 2)
  - skills/navigate/SKILL.md has Process section
  - .gitignore present

⚠️  MISSING FILES:
  - data/project-awareness.md

⚠️  MISSING CONFIG FIELDS:
  - corpus.keywords (for per-session routing)
    Suggested: polars, dataframe, lazy, expression

⚠️  MISSING SECTIONS in navigate skill:
  - "Tiered Index Navigation" section
  - "Large Structured Files" section
  - "Making Projects Aware" section

Would you like to apply these upgrades?
```

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

For each missing section, append to the navigate skill:

**Tiered Index Navigation section:**
```markdown
## Tiered Index Navigation

Large corpora may use **tiered indexes** with a main index linking to detailed sub-indexes:

```
data/
├── index.md              # Main index with section summaries
├── index-reference.md    # Detailed: Reference docs
├── index-guides.md       # Detailed: Guides/tutorials
```

**How to navigate:**

1. **Start with main index** (`data/index.md`)
2. **Identify the relevant section** from user's question
3. **If section links to sub-index** (e.g., `→ See [index-actions.md](index-actions.md)`):
   - Read that sub-index for detailed entries
   - The sub-index has the actual file paths
4. **Quick Reference entries** in main index have direct paths - use those for common lookups
```

**Large Structured Files section:**
```markdown
## Large Structured Files

For files marked with `⚡ GREP` in the index, use Grep instead of Read:

```bash
# Find a type/definition
grep -n "^type {Name}" file -A 30

# Find references
grep -n "{keyword}" file
```

**When to use Grep vs Read:**
- File > 1000 lines → prefer Grep
- Looking for specific definition → Grep with `-A` context
- Need surrounding context → Grep with `-B` and `-A`
```

**Making Projects Aware section:**
```markdown
## Making Projects Aware of This Corpus

If you're working in a project that uses {Project} but doesn't know about this corpus, you can add awareness to the project's CLAUDE.md.

**The `data/project-awareness.md` file** contains a ready-to-use snippet that can be added to any project's CLAUDE.md to make Claude aware of this corpus when working in that project.

### How to Inject

1. Read `data/project-awareness.md` from this corpus
2. Add its contents to the target project's CLAUDE.md (create if needed)
3. The project will now know to use this corpus for {Project} questions

### When to Suggest Injection

Suggest adding project awareness when:
- User is working in a project that heavily uses {Project}
- User repeatedly asks {Project} questions without invoking the corpus
- User says "I keep forgetting to use the docs"
```

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

For marketplaces with multiple corpora:

```bash
# From marketplace root
ls -d hiivmind-corpus-*/
```

Offer options:
1. **Upgrade all** - Apply same upgrades to all corpora
2. **Upgrade selected** - Choose which corpora to upgrade
3. **Report only** - Show what would change without applying

For batch upgrades, show consolidated report:
```
Batch Upgrade Report
════════════════════

hiivmind-corpus-polars:
  - Missing: project-awareness.md, 3 navigate sections

hiivmind-corpus-ibis:
  - Missing: project-awareness.md, 3 navigate sections

hiivmind-corpus-narwhals:
  - Missing: project-awareness.md, 3 navigate sections

Apply upgrades to all 3 corpora? [y/n]
```

---

## Example Session

**User**: "Upgrade my polars corpus"

**Step 1**: Locate - Found at current directory
**Step 2**: Detect - Standalone plugin type
**Step 3**: Compare:
- Navigate skill missing "Making Projects Aware" section
- No project-awareness.md file
**Step 4**: Report findings to user
**Step 5**: User confirms → Apply:
- Create data/project-awareness.md with Polars-specific content
- Append "Making Projects Aware" section to navigate skill
**Step 6**: Verify and show git status

---

## Version Tracking

When upgrades are applied, consider adding a version marker to config.yaml:

```yaml
# In data/config.yaml
corpus_version: "2025-12-13"  # Date of last upgrade
```

This helps track which corpora have been upgraded.

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
