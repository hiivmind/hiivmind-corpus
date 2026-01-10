# ADR 0006: Enhanced Corpus Validation in Upgrade Skill

## Status

Accepted (Implemented 2026-01-10)

## Context

During a comprehensive audit of 17 hiivmind-corpus repositories, several structural and content issues were discovered that the current upgrade skill does not detect:

### Issues Found During Audit

| Issue Type | Example | Current Detection |
|------------|---------|-------------------|
| Missing files | No `references/project-awareness.md` | ✅ Detected |
| Missing config fields | No `corpus.keywords` | ✅ Detected |
| Missing sections | No "Making Projects Aware" section | ✅ Detected |
| ADR-005 structure | Command exists but no skill | ✅ Detected |
| **Wrong file naming** | `commands/hiivmind-corpus-airtable.md` not `navigate.md` | ❌ Not detected |
| **Wrong directory naming** | `skills/hiivmind-corpus-better-auth/` not `skills/navigate/` | ❌ Not detected |
| **Wrong skill file naming** | `skills/navigate.md` not `skills/navigate/SKILL.md` | ❌ Not detected |
| **Wrong frontmatter format** | `name: navigate` not `name: hiivmind-corpus-htmx-navigate` | ❌ Not detected |
| **Generic template placeholders** | Worked Example uses `repo_owner: example` | ❌ Not detected |
| **Old format SKILL.md** | 60-line simple format vs 273-line full template | ❌ Not detected |
| **Old config schema fields** | `corpus.version` instead of `schema_version` | ❌ Partial |

### Root Cause

The upgrade skill currently checks:
1. **File presence** - but not file naming conventions
2. **Section presence** - but not section content quality
3. **Config field presence** - but not old/deprecated field formats

This leaves ~60% of real-world issues undetected, requiring manual audits to find problems.

## Decision

Enhance the existing upgrade skill with additional validation checks rather than creating a separate validate skill.

### Rationale

1. **Validation is already part of upgrade** - Steps 3 (Compare) and 4 (Report) already do validation
2. **Avoid duplication** - A separate validate skill would duplicate detection logic
3. **User expectations** - Users expect "upgrade" to find all issues
4. **Report-only mode** - Upgrade already asks "apply?" and can be declined

### New Validation Categories

#### 1. Naming Convention Checks

For plugins (has `.claude-plugin/plugin.json`):

| Component | Expected | Common Violations |
|-----------|----------|-------------------|
| Navigate command | `commands/navigate.md` | `commands/hiivmind-corpus-{name}.md` |
| Navigate skill dir | `skills/navigate/` | `skills/hiivmind-corpus-{name}/` |
| Navigate skill file | `skills/navigate/SKILL.md` | `skills/navigate.md` (file at wrong level) |

#### 2. Frontmatter Validation

| Field | Expected Format | Example |
|-------|-----------------|---------|
| `name` | `hiivmind-corpus-{project}-navigate` | `hiivmind-corpus-htmx-navigate` |
| `description` | Contains "Triggers:" keyword list | `Triggers: htmx, ajax, hx-get` |

#### 3. Content Quality Checks

| Check | Indicator | Issue |
|-------|-----------|-------|
| Generic worked example | `repo_owner: example` | Template placeholders not filled |
| Generic path format | `local:team-standards` | Default examples not customized |
| Unfilled placeholders | Contains `{{` | Template variables remain |
| Old format | < 200 lines | Needs full template replacement |

#### 4. Config Schema Migration

| Old Format | New Format | Action |
|------------|------------|--------|
| `corpus.version` | `schema_version` (top-level) | Migrate field |
| `sources[].name` | `sources[].id` | Rename field |
| `sources[].url` | `sources[].repo_url` | Rename field |
| Missing `display_name` | `corpus.display_name` | Add field |

### Expected Report Output

```
Corpus: hiivmind-corpus-htmx

✅ FILE STRUCTURE:
  - commands/navigate.md exists
  - skills/navigate/SKILL.md exists
  - references/project-awareness.md exists

❌ NAMING VIOLATIONS:
  - None detected

❌ FRONTMATTER:
  - name: "navigate" → should be "hiivmind-corpus-htmx-navigate"
  - description: Missing "Triggers:" keyword list

❌ CONTENT QUALITY:
  - Navigate skill uses old format (59 lines vs expected ~270)
  - Worked Example uses generic "repo_owner: example"

❌ CONFIG SCHEMA:
  - Missing schema_version field (found corpus.version)
  - Missing corpus.display_name

Would you like to apply these upgrades? [y/N]
```

## Consequences

### Positive

- **Complete validation** - All structural and content issues detected in one pass
- **Consistent quality** - All corpora will meet the same standard
- **Reduced manual audits** - No need for human review to find issues
- **Clear upgrade path** - Each issue has a specific fix action

### Negative

- **Stricter validation** - May flag many existing corpora as needing updates
- **Template regeneration** - Old-format SKILL.md requires full replacement, not patching
- **Content extraction** - Must read config.yaml to generate project-specific examples

### Neutral

- **Same skill, more thorough** - Users invoke upgrade the same way, get better results
- **Backwards compatible** - Existing corpora with issues still function, just get flagged

## Alternatives Considered

### 1. Separate "validate" Skill

Create `hiivmind-corpus-validate` that only reports, never modifies.

**Rejected because:**
- Duplicates detection logic
- Two skills to maintain in sync
- Confusing UX (when to use validate vs upgrade?)

### 2. Gateway "validate" Alias

Add `/hiivmind-corpus validate {name}` that runs upgrade in report-only mode.

**Considered viable as enhancement:**
- No duplicate logic
- Clear user intent
- Could be added alongside improved upgrade

### 3. External Validation Script

Shell script that runs checks outside of Claude.

**Rejected because:**
- Loses Claude's ability to fix issues
- Doesn't integrate with skill workflow
- Requires separate tooling

## Implementation

### Files to Modify

1. **`skills/hiivmind-corpus-upgrade/SKILL.md`**
   - Add Step 3b: Naming convention detection
   - Add Step 3c: Frontmatter validation
   - Add Step 3d: Content quality checks
   - Add Step 3e: Config schema migration detection
   - Update Step 5: Add fix actions for new issue types

2. **`skills/hiivmind-corpus-upgrade/references/upgrade-checklists.md`**
   - Add "Naming Convention Checks" section
   - Add "Navigate Skill Frontmatter Checks" section
   - Add "Navigate Skill Content Quality Checks" section
   - Add "Config Schema Migration Checks" section

3. **`skills/hiivmind-corpus-upgrade/references/upgrade-templates.md`**
   - Add fix templates for naming violations
   - Add guidance for full SKILL.md regeneration

4. **`commands/hiivmind-corpus.md`** (optional)
   - Add `validate` action that routes to upgrade with report-only flag

### Detection Commands

```bash
# Naming conventions
ls commands/navigate.md 2>/dev/null || echo "WRONG_COMMAND_NAME"
ls -d skills/navigate/ 2>/dev/null || echo "WRONG_SKILL_DIR"
ls skills/navigate/SKILL.md 2>/dev/null || echo "WRONG_SKILL_FILE"

# Frontmatter
grep "^name:" skills/navigate/SKILL.md | grep -q "hiivmind-corpus-.*-navigate" || echo "WRONG_NAME_FORMAT"
grep -q "Triggers:" skills/navigate/SKILL.md || echo "MISSING_TRIGGERS"

# Content quality
grep -q "repo_owner: example" skills/navigate/SKILL.md && echo "GENERIC_EXAMPLE"
grep -q "{{" skills/navigate/SKILL.md && echo "UNFILLED_PLACEHOLDERS"
[ $(wc -l < skills/navigate/SKILL.md) -lt 200 ] && echo "OLD_FORMAT"

# Config schema
grep -q "^schema_version:" data/config.yaml || echo "MISSING_SCHEMA_VERSION"
grep -q "corpus:" data/config.yaml && grep -q "  version:" data/config.yaml && echo "OLD_VERSION_FIELD"
```

### Verification

Test against corpora with known issues:
- htmx (was old format) → should detect OLD_FORMAT, WRONG_NAME_FORMAT
- sonatype (was wrong file) → should detect WRONG_SKILL_FILE (before fix)
- better-auth (was wrong dir) → should detect WRONG_SKILL_DIR (before fix)
- airtable (was wrong command) → should detect WRONG_COMMAND_NAME (before fix)
