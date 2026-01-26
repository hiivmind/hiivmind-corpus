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
- When navigate skill has sections that belong elsewhere (e.g., "Making Projects Aware" should be in command)
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
# Check if we're in a corpus (data-only or legacy)
# Data-only: config.yaml at root
# Legacy: data/config.yaml
ls config.yaml 2>/dev/null && echo "IN_CORPUS=true (data-only)"
ls data/config.yaml 2>/dev/null && echo "IN_CORPUS=true (legacy)"

# Or check for corpus subdirectories
ls -d hiivmind-corpus-*/ 2>/dev/null
```

**If in a marketplace**: Ask user which corpus to upgrade, or offer to upgrade all.

---

## Step 2: Detect Corpus Type

Determine what kind of corpus this is:

```bash
# Check structure - detect data-only vs legacy first
if [ -f "config.yaml" ] && [ ! -d "data" ]; then
    echo "DATA_ONLY=true"  # Data-only corpus (preferred)
elif [ -f "data/config.yaml" ]; then
    echo "LEGACY=true"     # Legacy structure with data/ subdirectory
fi

# Check for plugin indicators
ls .claude-plugin/ 2>/dev/null
ls skills/ 2>/dev/null
ls commands/ 2>/dev/null
```

| Indicator | Corpus Type | Expected Structure |
|-----------|-------------|-------------------|
| `config.yaml` at root, NO `.claude-plugin/` | **Data-only corpus** (preferred) | `config.yaml`, `index.md`, `uploads/` |
| `SKILL.md` at root + `data/` | User-level or repo-local skill (legacy) | `SKILL.md`, `data/`, `references/` |
| `.claude-plugin/plugin.json` | Standalone plugin (legacy) | `skills/navigate/SKILL.md`, `commands/navigate.md`, `data/`, `references/` |
| Parent has `marketplace.json` | Plugin in marketplace (legacy) | Same as standalone plugin |

**Data-only corpora** are the preferred format. They have NO plugin structure and are consumed via the `hiivmind-corpus` plugin's navigate skill.

**Plugin types (ADR-005):** Must have BOTH:
- `skills/navigate/SKILL.md` - Auto-triggers based on domain keywords
- `commands/navigate.md` - Explicit entry point for users

Record the corpus type - it affects which templates and checks apply.

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
- **Naming convention checks** (ADR-006)
- **Frontmatter validation** (ADR-006)
- **Content quality checks** (ADR-006)
- Config schema field requirements
- Navigate skill section requirements

---

### Step 3b: Naming Convention Checks (Plugins Only)

**Skip this section for data-only corpora** - they have no plugin structure to validate.

**See:** `references/upgrade-checklists.md` → "Naming Convention Checks" section.

For plugins (has `.claude-plugin/plugin.json`), verify correct naming:

| Component | Expected | Violation Pattern |
|-----------|----------|-------------------|
| Navigate command | `commands/navigate.md` | `commands/hiivmind-corpus-*.md` |
| Navigate skill dir | `skills/navigate/` | `skills/hiivmind-corpus-*/` |
| Navigate skill file | `skills/navigate/SKILL.md` | `skills/navigate.md` (flat) |

**Detection:**
```bash
# Check for wrong command name
ls commands/hiivmind-corpus-*.md 2>/dev/null && echo "WRONG_COMMAND_NAME"

# Check for wrong skill directory
ls -d skills/hiivmind-corpus-*/ 2>/dev/null && echo "WRONG_SKILL_DIR"

# Check for flat skill file
[ -f skills/navigate.md ] && [ ! -d skills/navigate ] && echo "WRONG_SKILL_FILE"
```

---

### Step 3c: Frontmatter Validation

**See:** `references/upgrade-checklists.md` → "Navigate Skill Frontmatter Checks" section.

Read the navigate skill frontmatter and verify:

```bash
# Extract project short name
PROJECT_SHORT=$(basename "$PWD" | sed 's/hiivmind-corpus-//')

# Check name format
grep "^name:" skills/navigate/SKILL.md | grep -q "hiivmind-corpus-${PROJECT_SHORT}-navigate" || echo "WRONG_NAME_FORMAT"

# Check for Triggers keyword
grep -qi "triggers:" skills/navigate/SKILL.md || echo "MISSING_TRIGGERS"

# Check for fork context (ADR-007)
grep -q "^context: fork" skills/navigate/SKILL.md || echo "MISSING_FORK_CONTEXT"
grep -q "^agent: Explore" skills/navigate/SKILL.md || echo "MISSING_AGENT_EXPLORE"
grep -q "^allowed-tools:" skills/navigate/SKILL.md || echo "MISSING_ALLOWED_TOOLS"

# Check skill has AskUserQuestion in allowed-tools
grep -q "AskUserQuestion" skills/navigate/SKILL.md || echo "MISSING_ASKUSERQUESTION_TOOL"
```

**Expected formats:**
- `name: hiivmind-corpus-{project}-navigate` (e.g., `hiivmind-corpus-htmx-navigate`)
- `description:` must include "Triggers:" with comma-separated keywords
- `context: fork` - runs skill in isolated sub-agent (ADR-007)
- `agent: Explore` - uses Explore agent for read-only operations (ADR-007)
- `allowed-tools: Read, Grep, Glob, WebFetch` - prevents permission prompts (ADR-007)

---

### Step 3d: Content Quality Checks

**See:** `references/upgrade-checklists.md` → "Navigate Skill Content Quality Checks" section.

Check for template placeholders and old format:

```bash
# Generic worked example
grep -q "repo_owner: example" skills/navigate/SKILL.md && echo "GENERIC_WORKED_EXAMPLE"

# Generic path examples
grep -q "local:team-standards" skills/navigate/SKILL.md && echo "GENERIC_PATH_EXAMPLES"

# Unfilled template variables
grep -q "{{" skills/navigate/SKILL.md && echo "UNFILLED_PLACEHOLDERS"

# Old format check (< 200 lines)
[ $(wc -l < skills/navigate/SKILL.md) -lt 200 ] && echo "OLD_FORMAT_SKILL"

# Check command file length (> 50 lines = duplicated logic)
[ -f commands/navigate.md ] && [ $(wc -l < commands/navigate.md) -gt 50 ] && echo "COMMAND_DUPLICATES_SKILL"

# Check skill still has maintenance references (should be removed)
grep -q "/hiivmind-corpus" skills/navigate/SKILL.md && echo "SKILL_HAS_MAINTENANCE_REFS"

# Check skill has project awareness section (should be in command, not skill)
grep -q "Making Projects Aware" skills/navigate/SKILL.md && echo "SKILL_HAS_PROJECT_AWARENESS"
```

**Note:** Skills with OLD_FORMAT_SKILL or GENERIC_WORKED_EXAMPLE require full regeneration, not section patching. See `references/upgrade-templates.md` → "Navigate Skill Regeneration".

---

### Step 3e: Config Schema Migration Detection

**See:** `references/upgrade-checklists.md` → "Config Schema Migration Checks" section.

Check for deprecated config fields:

```bash
# Detect config path (data-only vs legacy)
CONFIG_PATH="config.yaml"
[ -f "data/config.yaml" ] && CONFIG_PATH="data/config.yaml"

# Old corpus.version field (should be top-level schema_version)
grep -q "corpus:" "$CONFIG_PATH" && grep -qE "^\s+version:" "$CONFIG_PATH" && echo "OLD_CORPUS_VERSION"

# Missing schema_version
grep -q "^schema_version:" "$CONFIG_PATH" || echo "MISSING_SCHEMA_VERSION"

# Missing display_name
grep -qE "^\s+display_name:" "$CONFIG_PATH" || echo "MISSING_DISPLAY_NAME"
```

---

## Step 4: Report Findings

**See:** `references/upgrade-templates.md` for report format templates (including Enhanced Report Template).

Present a clear report showing:
- ✅ UP TO DATE items
- ⚠️ NAMING VIOLATIONS (wrong command/skill paths)
- ⚠️ FRONTMATTER ISSUES (wrong name format, missing triggers, missing AskUserQuestion tool)
- ⚠️ CONTENT QUALITY (generic examples, old format, unfilled placeholders)
- ⚠️ COMMAND/SKILL SEPARATION (command duplicates skill logic, skill has maintenance references, skill has project awareness section)
- ⚠️ CONFIG SCHEMA (deprecated fields, missing fields)
- ⚠️ MISSING FILES
- ⚠️ MISSING CONFIG FIELDS (with suggestions)
- ⚠️ MISSING SECTIONS in navigate skill
- ⚠️ INCORRECT ROUTING (ADR-005 violations)
  - Old routing tables
  - Child command routing (`:navigate enhance`)
  - Direct parent routing (`/hiivmind-corpus` instead of `/hiivmind-corpus:hiivmind-corpus`)

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
3. Add to `config.yaml` (or `data/config.yaml` for legacy):
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

### Fixing Naming Violations (ADR-006)

**See:** `references/upgrade-templates.md` → "Naming Convention Fixes" section.

For each naming violation detected, apply the fix:

**WRONG_COMMAND_NAME:**
```bash
OLD_CMD=$(ls commands/hiivmind-corpus-*.md | head -1)
git mv "$OLD_CMD" commands/navigate.md
```

**WRONG_SKILL_DIR:**
```bash
OLD_DIR=$(ls -d skills/hiivmind-corpus-*/ | head -1)
git mv "$OLD_DIR" skills/navigate/
```

**WRONG_SKILL_FILE:**
```bash
mkdir -p skills/navigate
git mv skills/navigate.md skills/navigate/SKILL.md
```

### Fixing Frontmatter Issues (ADR-006)

**WRONG_NAME_FORMAT:**
Edit the frontmatter `name:` field to match pattern `hiivmind-corpus-{project}-navigate`:
```yaml
---
name: hiivmind-corpus-{project}-navigate
description: This skill answers questions about {Project} documentation. Use when user asks about {topics}. Triggers: {keyword1}, {keyword2}, {keyword3}.
---
```

**MISSING_TRIGGERS:**
Add or update the description to include `Triggers:` with comma-separated domain keywords.

### Fixing Fork Context Issues (ADR-007)

**See:** `references/upgrade-templates.md` → "Fork Context Migration (ADR-007)" section.

**MISSING_FORK_CONTEXT / MISSING_AGENT_EXPLORE / MISSING_ALLOWED_TOOLS:**
Add the missing fields to the frontmatter after the `description:` line:
```yaml
---
name: hiivmind-corpus-{project}-navigate
description: This skill answers questions about {Project} documentation. Triggers: {keywords}.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebFetch
---
```

This runs the navigate skill in an isolated sub-agent context, keeping the main conversation clean.

### Fixing Missing AskUserQuestion Tool

**MISSING_ASKUSERQUESTION_TOOL:**
Add `AskUserQuestion` to the allowed-tools in frontmatter:
```yaml
---
name: hiivmind-corpus-{project}-navigate
description: ...
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebFetch, AskUserQuestion
---
```

### Simplifying Navigate Command (Duplicated Logic)

**COMMAND_DUPLICATES_SKILL:**
The command should be a thin wrapper that invokes the skill, not duplicate navigation logic.

Replace `commands/navigate.md` with minimal version:
```markdown
---
description: Ask questions about {Project} documentation
argument-hint: Your question (e.g., "how does X work?")
allowed-tools: ["Skill"]
---

# {Project} Navigator

**User request:** $ARGUMENTS

---

## If No Arguments Provided

Show a brief help message with 2-3 example queries.

---

## If Arguments Provided

Invoke the navigate skill to handle the query:

**Skill:** {plugin_name}-navigate
**Args:** $ARGUMENTS
```

### Removing Maintenance References from Skill

**SKILL_HAS_MAINTENANCE_REFS:**
The navigate skill should be pure navigation - no maintenance references.

1. Remove the "Corpus Maintenance" section if present
2. In Step 4 (Clarify Before Exploring), replace maintenance suggestions with:
   - "This topic isn't covered in the current index."
   - "The source documentation may have content not yet indexed."

### Removing Project Awareness from Skill

**SKILL_HAS_PROJECT_AWARENESS:**
The navigate skill should be pure navigation - project awareness guidance belongs in the command.

1. Remove the "Making Projects Aware of This Corpus" section from `skills/navigate/SKILL.md`
2. Ensure `commands/navigate.md` mentions `references/project-awareness.md` in its help output

### Regenerating Navigate Skill (ADR-006 Content Quality)

**See:** `references/upgrade-templates.md` → "Navigate Skill Regeneration" section.

When OLD_FORMAT_SKILL, GENERIC_WORKED_EXAMPLE, or UNFILLED_PLACEHOLDERS are detected, the skill needs **full regeneration** rather than patching:

1. Read `config.yaml` (or `data/config.yaml` for legacy) for project metadata:
   - `corpus.name`, `corpus.display_name`
   - `sources[0].id`, `sources[0].type`
   - For git sources: `repo_owner`, `repo_name`, `branch`, `docs_root`
   - For web sources: `urls` array or `base_url`

2. Load the navigate skill template from hiivmind-corpus

3. Generate project-specific content for:
   - **Path Format examples** (use actual source IDs from config)
   - **Worked Example section** (use actual repo/web source details)
   - **Example Sessions** (use domain-relevant questions)

4. Write the regenerated SKILL.md to `skills/navigate/SKILL.md`

**Note:** This is a full replacement. The existing skill structure is preserved but content is project-specific.

### Migrating Config Schema (ADR-006)

**OLD_CORPUS_VERSION / MISSING_SCHEMA_VERSION:**
Add at top level of config.yaml:
```yaml
schema_version: 2

corpus:
  name: "{project}"
  ...
```

**MISSING_DISPLAY_NAME:**
Add under corpus section:
```yaml
corpus:
  name: "{project}"
  display_name: "{Project Display Name}"
  keywords:
    - keyword1
    - keyword2
```

**OLD_SOURCE_NAME_FIELD:**
Rename `name:` to `id:` in sources array:
```yaml
sources:
  - id: source-name        # was: name: source-name
    type: git
    ...
```

### ADR-005: Navigate Skill/Command Structure (Plugins Only)

**Applies to:** Standalone plugins and marketplace plugins (NOT user-level/repo-local skills)

**Detection:**
```bash
# Check for old structure (command only, no skill)
ls commands/navigate.md 2>/dev/null && echo "HAS_COMMAND=true"
ls skills/navigate/SKILL.md 2>/dev/null && echo "HAS_SKILL=true"

# Check for routing issues in command (ADR-005 violations)
grep -q "hiivmind-corpus-refresh" commands/navigate.md 2>/dev/null && echo "HAS_OLD_ROUTING_TABLE=true"
grep -q ":navigate enhance\|:navigate add source\|:navigate refresh" commands/navigate.md 2>/dev/null && echo "HAS_CHILD_ROUTING=true"
grep -q "/hiivmind-corpus enhance\|/hiivmind-corpus refresh" commands/navigate.md 2>/dev/null | grep -v "hiivmind-corpus:hiivmind-corpus" && echo "HAS_DIRECT_PARENT_ROUTING=true"
```

**Upgrade scenarios:**

| Current State | Action |
|---------------|--------|
| Has command, no skill | Create `skills/navigate/SKILL.md` |
| Has skill, no command | Create `commands/navigate.md` |
| Has old routing table | Remove routing table section |
| Has child routing (`:navigate enhance`) | Fix to use gateway (`/hiivmind-corpus:hiivmind-corpus`) |
| Has direct parent routing (`/hiivmind-corpus`) | Fix to use gateway (`/hiivmind-corpus:hiivmind-corpus`) |
| Both exist, correct routing | Already compliant |

**Creating missing navigate skill:**

1. Create directory: `mkdir -p skills/navigate`
2. Read `config.yaml` (or `data/config.yaml` for legacy) for keywords
3. Generate from `navigate-skill.md.template`:
   - Set `name: {plugin_name}-navigate`
   - Set `description:` with domain keywords for auto-triggering
   - Copy navigation process from existing command (if present)
4. Write to `skills/navigate/SKILL.md`

**Fixing routing issues (ADR-005 compliance):**

Per ADR-005, child navigate commands should have **NO maintenance routing**. All maintenance operations must route through the parent gateway: `/hiivmind-corpus:hiivmind-corpus`

**Issue 1: Old routing tables**
Old commands may contain routing tables like:
```markdown
| Action | Skill |
|--------|-------|
| refresh | hiivmind-corpus-refresh |
| enhance | hiivmind-corpus-enhance |
```
**Fix:** Remove entire routing table section.

**Issue 2: Child command routing (`:navigate enhance`)**
Commands may incorrectly route through the child navigate command:
```markdown
- `/{{plugin_name}}:navigate enhance {topic}`
- `/{{plugin_name}}:navigate add source {url}`
- `/{{plugin_name}}:navigate refresh`
```
**Fix:** Replace with gateway routing:
```markdown
- `/hiivmind-corpus:hiivmind-corpus enhance {{corpus_short_name}} {topic}`
- `/hiivmind-corpus:hiivmind-corpus add-source {{corpus_short_name}}`
- `/hiivmind-corpus:hiivmind-corpus refresh {{corpus_short_name}}`
```

**Issue 3: Direct parent routing (`/hiivmind-corpus`)**
Commands may use direct parent skill invocation instead of gateway:
```markdown
/hiivmind-corpus refresh {name}
/hiivmind-corpus enhance {name} X
```
**Fix:** Replace with gateway routing:
```markdown
/hiivmind-corpus:hiivmind-corpus refresh {{corpus_short_name}}
/hiivmind-corpus:hiivmind-corpus enhance {{corpus_short_name}} X
/hiivmind-corpus:hiivmind-corpus status {{corpus_short_name}}
```

**Correct maintenance section template:**
```markdown
## Corpus Maintenance

For corpus maintenance, use the corpus gateway:

```
/hiivmind-corpus:hiivmind-corpus refresh {{corpus_short_name}}     - Update index from upstream
/hiivmind-corpus:hiivmind-corpus enhance {{corpus_short_name}} X   - Add depth to topic X
/hiivmind-corpus:hiivmind-corpus status {{corpus_short_name}}      - Check corpus freshness
```
```

---

## Step 6: Verify

After applying upgrades:

```bash
# List updated files (data-only corpus)
ls -la *.md *.yaml uploads/ 2>/dev/null

# For legacy structure
ls -la data/ 2>/dev/null
ls -la skills/navigate/ 2>/dev/null

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
