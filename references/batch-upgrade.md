# Batch Upgrade Guide

How to upgrade multiple corpora in a marketplace efficiently.

## When to Use Batch Upgrade

- After hiivmind-corpus updates with new features
- When onboarding a marketplace to latest standards
- For ADR-005 compliance across all plugins

## Batch Upgrade Options

When running upgrade from a marketplace root, offer these options:

```
Detected marketplace with 4 corpus plugins:
  - hiivmind-corpus-polars
  - hiivmind-corpus-ibis
  - hiivmind-corpus-narwhals
  - hiivmind-corpus-substrait

Options:
1. Upgrade all plugins
2. Select plugins to upgrade
3. Report only (no changes)

Which would you like? [1/2/3]
```

---

## Consolidated Report Format

For batch operations, present a single consolidated report:

```markdown
## Marketplace Upgrade Report: hiivmind-corpus-data

### Summary

| Plugin | Status | Actions Needed |
|--------|--------|----------------|
| hiivmind-corpus-polars | ⚠️ Needs upgrade | 2 items |
| hiivmind-corpus-ibis | ⚠️ Needs upgrade | 2 items |
| hiivmind-corpus-narwhals | ✅ Up to date | - |
| hiivmind-corpus-substrait | ⚠️ Needs upgrade | 1 item |

### Details

#### hiivmind-corpus-polars
- ❌ Missing `skills/navigate/SKILL.md` (ADR-005)
- ⚠️ `commands/navigate.md` has routing table

#### hiivmind-corpus-ibis
- ❌ Missing `skills/navigate/SKILL.md` (ADR-005)
- ⚠️ `commands/navigate.md` has routing table

#### hiivmind-corpus-substrait
- ❌ Missing `references/project-awareness.md`

### Recommended Actions

Apply upgrades to 3 plugins? [y/n]
```

---

## Batch Upgrade Process

### Step 1: Discover Plugins

```bash
# Find all corpus plugins in marketplace
ls -d hiivmind-corpus-*/ 2>/dev/null
```

### Step 2: Scan Each Plugin

For each plugin, run the compliance checks from `references/upgrade-checklists.md`.

### Step 3: Aggregate Findings

Group findings by:
1. **Critical** - Missing required files
2. **ADR-005** - Navigate skill/command structure
3. **Recommended** - Optional improvements

### Step 4: Apply Upgrades

Process plugins in order:

```bash
for plugin in hiivmind-corpus-*/; do
  echo "Upgrading $plugin..."
  # Apply upgrades
done
```

### Step 5: Verify All

```bash
# Check all plugins
for plugin in hiivmind-corpus-*/; do
  echo "=== $plugin ==="
  ls "$plugin/skills/navigate/SKILL.md" 2>/dev/null && echo "✅ Has navigate skill" || echo "❌ Missing navigate skill"
  ls "$plugin/commands/navigate.md" 2>/dev/null && echo "✅ Has navigate command" || echo "❌ Missing navigate command"
done
```

### Step 6: Commit

```bash
git add -A
git commit -m "Upgrade all corpus plugins to latest standards

- Add skills/navigate/SKILL.md for ADR-005 compliance
- Simplify commands/navigate.md (remove routing)
- Add missing references/project-awareness.md

Upgraded: polars, ibis, substrait
Already compliant: narwhals"
```

---

## Example Upgrade Session

```
User: Upgrade all corpora in this marketplace

Claude: I'll scan the marketplace for corpus plugins.

Detected marketplace: hiivmind-corpus-data
Found 4 corpus plugins:
  - hiivmind-corpus-polars
  - hiivmind-corpus-ibis
  - hiivmind-corpus-narwhals
  - hiivmind-corpus-substrait

Scanning each for compliance...

## Marketplace Upgrade Report

| Plugin | Status | Issues |
|--------|--------|--------|
| polars | ⚠️ | Missing navigate skill, has routing |
| ibis | ⚠️ | Missing navigate skill, has routing |
| narwhals | ⚠️ | Missing navigate skill, has routing |
| substrait | ⚠️ | Missing navigate skill, has routing |

All 4 plugins need ADR-005 upgrades.

Would you like to:
1. Upgrade all plugins
2. Select specific plugins
3. See detailed report first

User: 1

Claude: Upgrading all plugins...

✅ hiivmind-corpus-polars
   - Created skills/navigate/SKILL.md
   - Simplified commands/navigate.md

✅ hiivmind-corpus-ibis
   - Created skills/navigate/SKILL.md
   - Simplified commands/navigate.md

✅ hiivmind-corpus-narwhals
   - Created skills/navigate/SKILL.md
   - Simplified commands/navigate.md

✅ hiivmind-corpus-substrait
   - Created skills/navigate/SKILL.md
   - Simplified commands/navigate.md

All 4 plugins upgraded successfully.

Files changed:
  8 files changed, 480 insertions(+), 120 deletions(-)

Would you like me to commit these changes?
```

---

## Version Tracking

Consider adding version tracking to identify when corpora were last upgraded:

### In config.yaml

```yaml
corpus:
  name: "polars"
  display_name: "Polars"
  upgraded_at: "2025-01-15"          # When last upgraded
  hiivmind_corpus_version: "1.2.0"   # Which version of templates used
```

### Benefits

- Know which corpora need upgrades after hiivmind-corpus updates
- Track upgrade history
- Identify stale corpora quickly

### Checking Versions

```bash
# Find corpora with old or missing version info
for plugin in hiivmind-corpus-*/; do
  version=$(grep "hiivmind_corpus_version:" "$plugin/data/config.yaml" 2>/dev/null | cut -d'"' -f2)
  echo "$plugin: ${version:-NOT SET}"
done
```
