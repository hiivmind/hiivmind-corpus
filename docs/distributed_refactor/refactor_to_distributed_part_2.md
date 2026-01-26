# Plan: Update BUILD Skills for Data-Only Architecture

## Overview

Update the remaining BUILD skills (init, add-source, build, refresh, enhance) and the upgrade skill to work with the new data-only corpus architecture where `config.yaml` and `index.md` are at the repository root instead of in a `data/` subdirectory.

## Path Changes Summary

| Old Path | New Path | Notes |
|----------|----------|-------|
| `data/config.yaml` | `config.yaml` | Root level |
| `data/index.md` | `index.md` | Root level |
| `data/index-*.md` | `index-*.md` | Root level |
| `data/uploads/` | `uploads/` | Root level |
| `data/logs/` | `logs/` | Root level (refresh logs) |
| `.source/` | `.source/` | No change |
| `.cache/` | `.cache/` | No change |

---

## Phase 1: Update Pattern Files

These patterns are referenced by multiple skills and must be updated first.

### 1.1 paths.md (53 occurrences) - CRITICAL
**File:** `lib/corpus/patterns/paths.md`

Update path resolution functions:
- `get_config_path()`: `{corpus_path}/data/config.yaml` → `{corpus_path}/config.yaml`
- `get_index_path()`: `{corpus_path}/data/index.md` → `{corpus_path}/index.md`
- `get_subindex_path()`: `{corpus_path}/data/index-{section}.md` → `{corpus_path}/index-{section}.md`
- `get_upload_path()`: `{corpus_path}/data/uploads/` → `{corpus_path}/uploads/`
- All validation functions checking for these paths

### 1.2 discovery.md (17 occurrences) - CRITICAL
**File:** `lib/corpus/patterns/discovery.md`

Update corpus detection logic:
- Change `[ -f "${d}data/config.yaml" ]` → `[ -f "${d}config.yaml" ]`
- Update Glob patterns from `*/data/config.yaml` → `*/config.yaml`

### 1.3 config-parsing.md (44 occurrences)
**File:** `lib/corpus/patterns/config-parsing.md`

Update all code examples:
- `yq '.field' data/config.yaml` → `yq '.field' config.yaml`
- `open('data/config.yaml')` → `open('config.yaml')`

### 1.4 status.md (13 occurrences)
**File:** `lib/corpus/patterns/status.md`

Update status check functions reading from `data/index.md` and `data/config.yaml`.

### 1.5 Other patterns (lower priority)
- `scanning.md` - 5 occurrences
- `template-generation.md` - 6 occurrences (already has data-only section)
- `refresh-logging.md` - 11 occurrences (`data/logs/` → `logs/`)
- `logging-configuration.md` - 4 occurrences
- `sources/local.md` - 8 occurrences (`data/uploads/` → `uploads/`)
- `sources/pdf.md` - 5 occurrences
- `tool-detection.md` - 3 occurrences

---

## Phase 2: Update Skill Workflows

### 2.1 hiivmind-corpus-init
**Files:** `skills/hiivmind-corpus-init/SKILL.md`, `workflow.yaml`

**workflow.yaml changes (~10 locations):**
- Line 619: `${computed.skill_root}/data` → `${computed.skill_root}`
- Line 620: `${computed.skill_root}/data/uploads` → `${computed.skill_root}/uploads`
- Line 649: `${computed.skill_root}/data/config.yaml` → `${computed.skill_root}/config.yaml`
- Line 652: `${computed.skill_root}/data/index.md` → `${computed.skill_root}/index.md`
- Lines 677, 679, 714, 717, 746-748, 787, 845: Similar path updates for plugin variants

**SKILL.md changes:**
- Update documentation to show root-level paths

### 2.2 hiivmind-corpus-add-source
**Files:** `skills/hiivmind-corpus-add-source/SKILL.md`, `workflow.yaml`

**workflow.yaml changes (~6 locations):**
- Line 241: `data/uploads/${computed.source_id}` → `uploads/${computed.source_id}`
- Line 691: `data/uploads/${computed.source_id}` → `uploads/${computed.source_id}`
- Line 702: Display message path update
- Line 1123: `data/index.md` → `index.md`

### 2.3 hiivmind-corpus-build
**Files:** `skills/hiivmind-corpus-build/SKILL.md`, `workflow.yaml`

**workflow.yaml changes (~8 locations):**
- Line 240: `'data/uploads/' + ...` → `'uploads/' + ...`
- Line 1182: `data/index.md` → `index.md`
- Line 1207: `data/${item.filename}` → `${item.filename}`
- Line 1210: Display message update
- Lines 1284-1286: Multiple `data/index.md` references
- Line 1316: Success message paths
- Line 1322: Git add command: `git add data/index.md` → `git add index.md`

### 2.4 hiivmind-corpus-refresh
**Files:** `skills/hiivmind-corpus-refresh/SKILL.md`, `workflow.yaml`

**workflow.yaml changes (~12 locations):**
- Line 131: `data/index.md` → `index.md`
- Line 165: `data/index-*.md` → `index-*.md`
- Line 240: `'data/uploads/' + ...` → `'uploads/' + ...`
- Line 241: `'data/logs/...'` → `'logs/...'`
- Line 1359: Index path context
- Line 1643: Write file path
- Line 1676: Sub-index write path
- Line 1790: Log location context
- Line 1951: Git add command
- Line 2016: Commit message paths

### 2.5 hiivmind-corpus-enhance
**Files:** `skills/hiivmind-corpus-enhance/SKILL.md` (no workflow.yaml)

**SKILL.md changes (4 locations):**
- Line 73: `data/index.md` → `index.md`
- Line 80: `data/index-*.md` → `index-*.md`
- Line 325: `git add data/index.md` → `git add index.md`
- Line 334: `git add data/index-{section}.md` → `git add index-{section}.md`

---

## Phase 3: Update Upgrade Skill

**Files:** `skills/hiivmind-corpus-upgrade/SKILL.md`, `references/upgrade-checklists.md`

### 3.1 Add Data-Only Architecture Recognition

The upgrade skill currently only recognizes plugin-based corpora. Add recognition of data-only structure:

```
Data-only corpus detection:
- Has config.yaml at root (not in data/)
- Has index.md at root (not in data/)
- Does NOT have .claude-plugin/, skills/, commands/
```

### 3.2 Remove Plugin-Related Checks for Data-Only

When corpus is data-only:
- Skip checks for `.claude-plugin/plugin.json`
- Skip checks for `skills/navigate/SKILL.md`
- Skip checks for `commands/navigate.md`
- Skip checks for `references/`

### 3.3 Update Validation Logic

**SKILL.md lines 48-71:** Update corpus type detection to include data-only type
**SKILL.md lines 101-123:** Skip naming convention checks for data-only corpora
**SKILL.md lines 163-190:** Skip maintenance reference checks for data-only corpora

---

## Phase 4: Update Templates

### 4.1 Legacy Templates (for backward compatibility)
These templates are used when creating plugin-based corpora (legacy mode):

- `templates/claude.md.template` - 11 refs to `data/`
- `templates/navigate-skill.md.template` - 8 refs to `data/`
- `templates/readme.md.template` - 2 refs to `data/`
- `templates/marketplace-claude.md.template` - 4 refs to `data/`

**Decision:** Keep legacy templates unchanged for backward compatibility. The init skill will use data-only templates by default and legacy templates only when explicitly requested.

### 4.2 Data-Only Templates (already created)
Verify these templates have correct root-level paths:
- `templates/claude-data-only.md.template` ✓
- `templates/readme-data-only.md.template` ✓

---

## Verification Plan

### Test 1: Init creates correct structure
```bash
# Create new data-only corpus
/hiivmind-corpus init

# Verify structure:
ls config.yaml index.md uploads/
# Should exist at root, NOT in data/
```

### Test 2: Build writes to correct location
```bash
# In a corpus directory
/hiivmind-corpus build

# Verify:
cat index.md  # Should be at root
ls index-*.md  # Sub-indexes at root
```

### Test 3: Refresh reads/writes correctly
```bash
/hiivmind-corpus refresh

# Verify:
cat logs/refresh-*.log  # Logs at root/logs/
cat config.yaml  # Updated at root
```

### Test 4: Upgrade recognizes data-only
```bash
# In a data-only corpus
/hiivmind-corpus upgrade

# Should report: "Data-only corpus - no plugin structure required"
# Should NOT complain about missing skills/, commands/, .claude-plugin/
```

---

## Files to Modify (Summary)

| File | Changes |
|------|---------|
| `lib/corpus/patterns/paths.md` | ~53 path references |
| `lib/corpus/patterns/discovery.md` | ~17 path references |
| `lib/corpus/patterns/config-parsing.md` | ~44 path references |
| `lib/corpus/patterns/status.md` | ~13 path references |
| `lib/corpus/patterns/refresh-logging.md` | ~11 path references |
| `lib/corpus/patterns/logging-configuration.md` | ~4 path references |
| `lib/corpus/patterns/sources/local.md` | ~8 path references |
| `skills/hiivmind-corpus-init/workflow.yaml` | ~10 path references |
| `skills/hiivmind-corpus-add-source/workflow.yaml` | ~6 path references |
| `skills/hiivmind-corpus-build/workflow.yaml` | ~8 path references |
| `skills/hiivmind-corpus-refresh/workflow.yaml` | ~12 path references |
| `skills/hiivmind-corpus-enhance/SKILL.md` | ~4 path references |
| `skills/hiivmind-corpus-upgrade/SKILL.md` | Add data-only recognition |

**Estimated total: ~190 path references to update**
