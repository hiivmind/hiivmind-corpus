# Migration Plan: Executable Scripts to Pattern Documentation

**Status:** Proposed
**Created:** 2025-12-15
**Issue:** [#8](https://github.com/hiivmind/hiivmind-corpus/issues/8)

## Summary

Migrate from executable bash scripts (`lib/corpus/*.sh`) to tool-agnostic pattern documentation (`lib/corpus/patterns/*.md`). This removes platform lock-in, eliminates hard tool dependencies, and lets the LLM adapt to whatever environment it's running in.

## Problem Statement

### Current Architecture

The `lib/corpus/` directory contains 6 bash script files with functions that skills source and call:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
discover_all | filter_built | list_names
```

### Issues

| Problem | Impact |
|---------|--------|
| **Platform lock-in** | Windows users cannot use bash scripts |
| **Hard dependencies** | Requires yq 4.0+, assumes specific tool versions |
| **Version fragility** | yq 3.x vs 4.x have incompatible syntax |
| **Maintenance burden** | Scripts need testing across environments |
| **Opacity** | LLM can't see function internals without reading source |
| **Inflexibility** | Can't adapt to what's actually available at runtime |

### Current Dependencies

From `lib/corpus/corpus-index.md`:
```markdown
## Dependencies

- `bash` 4.0+
- `yq` 4.0+ (for YAML parsing in status/path functions)
- `git` (for clone operations in status functions)
```

## Proposed Solution

Replace executable scripts with **pattern documentation** that describes:
1. What to accomplish (algorithm)
2. Multiple ways to accomplish it (tool implementations)
3. How to detect available tools
4. How to gracefully degrade when tools are missing

The LLM reads these patterns and synthesizes appropriate commands for the current environment.

### Example Transformation

**Before (executable script):**
```bash
get_corpus_keywords() {
    local corpus_path="$1"
    local config_file="${corpus_path}data/config.yaml"
    yq -r '.corpus.keywords // empty | .[]?' "$config_file" 2>/dev/null | tr '\n' ','
}
```

**After (pattern documentation):**
```markdown
## Pattern: Extract Corpus Keywords

### Purpose
Get routing keywords from a corpus config.

### Location
`{corpus_path}/data/config.yaml` at YAML path `.corpus.keywords[]`

### Algorithm
1. Read config.yaml from corpus data directory
2. Extract the `corpus.keywords` array
3. If not present, infer from corpus directory name
4. Return comma-separated list

### Implementations

**Using yq:**
yq -r '.corpus.keywords[]' config.yaml | paste -sd,

**Using Python:**
python3 -c "import yaml; print(','.join(yaml.safe_load(open('config.yaml')).get('corpus',{}).get('keywords',[])))"

**Using grep (fallback):**
grep -A20 'keywords:' config.yaml | grep '^ *-' | sed 's/.*- //' | paste -sd,
```

---

## Tool Detection Strategy

### Detect-Once-Per-Session

At the start of corpus operations, detect available tools once and plan accordingly.

### Tool Capability Matrix

| Capability | Required For | Preferred | Alternatives | Fallback |
|------------|--------------|-----------|--------------|----------|
| YAML parsing | Config reading | yq | python+pyyaml | grep+sed |
| Git operations | Git sources | git | (none) | Web URLs only |
| File search | Doc discovery | Claude Glob/Grep | rg, grep | find |
| JSON parsing | (rare) | jq | python | grep |

### Tool Tiers

**Tier 1: Required (no alternative)**
- `git` - Required for git-based sources. Cannot proceed without it for git operations.

**Tier 2: Strongly Recommended (degraded without)**
- `yq` OR `python+pyyaml` - YAML parsing. Grep fallback exists but is fragile and may fail on complex YAML.

**Tier 3: Optional (Claude tools usually sufficient)**
- `rg` (ripgrep) - Faster search, but Claude's Grep tool works well
- `jq` - JSON parsing, rarely needed in corpus operations

### Detection Commands

```bash
# YAML parsing capability
command -v yq >/dev/null 2>&1 && echo "yq:$(yq --version 2>&1 | head -1)"
command -v python3 >/dev/null 2>&1 && python3 -c "import yaml; print('pyyaml:available')" 2>/dev/null

# Git capability
command -v git >/dev/null 2>&1 && echo "git:$(git --version)"

# Search capability (optional)
command -v rg >/dev/null 2>&1 && echo "rg:$(rg --version | head -1)"
```

### Recommendation Messages

**Critical (blocks operation):**
```
Git is required for git-based documentation sources but wasn't found.

Install git:
- Linux: sudo apt install git
- macOS: xcode-select --install
- Windows: https://git-scm.com/downloads

Cannot proceed with git source operations without git.
```

**Strong (degraded experience):**
```
No YAML parsing tool found (yq or python+pyyaml).
Operations will use grep-based fallback which may be unreliable for complex YAML.

For best results, install one of:
- yq (recommended): https://github.com/mikefarah/yq#install
- Python PyYAML: pip install pyyaml

Proceeding with fallback method...
```

**Informational:**
```
Note: Using grep for file search (ripgrep not found).
This works fine but may be slower for large codebases.
```

---

## Pattern Documentation Structure

### Directory Layout

```
lib/corpus/
├── patterns/
│   ├── tool-detection.md      # Foundation - capabilities and detection
│   ├── config-parsing.md      # YAML config field extraction
│   ├── discovery.md           # Finding installed corpora
│   ├── status.md              # Index status and freshness
│   ├── paths.md               # Path resolution (cross-platform)
│   ├── sources.md             # Git/local/web source operations
│   └── scanning.md            # Documentation file analysis
├── corpus-index.md            # Updated: Pattern index (was function index)
└── *.sh                       # DELETED after migration
```

### Pattern Document Template

```markdown
# Pattern: [Name]

## Purpose
One-line description of what this pattern accomplishes.

## When to Use
- Bullet points describing use cases
- Which skills use this pattern

## Prerequisites
- Required capabilities (from tool-detection)
- Required information/paths

## Algorithm
1. Step-by-step logic (tool-agnostic)
2. Decision points and branches
3. Expected outputs

## Implementations

### Using [Tool] (recommended)
\`\`\`bash
# Command with explanation
\`\`\`

### Using [Alternative]
\`\`\`bash
# Alternative approach
\`\`\`

### Fallback (no tools)
Description of manual/degraded approach.

## Cross-Platform Notes
- Path differences (Unix vs Windows)
- Tool availability differences
- Environment variable differences

## Error Handling
- What can go wrong
- How to detect failures
- Recovery strategies

## Examples

### Example 1: [Scenario]
Input: ...
Output: ...
```

---

## Detailed Pattern Specifications

### 1. tool-detection.md

**Purpose:** Establish available capabilities at session start.

**Contents:**
- Capability categories (YAML, Git, Search, JSON)
- Detection commands for each tool
- Version compatibility notes
- Recommendation tier system
- Message templates for missing tools
- Cross-platform detection differences

### 2. config-parsing.md

**Purpose:** Extract fields from corpus config.yaml files.

**Extractions covered:**
- `corpus.name`, `corpus.display_name`, `corpus.keywords`
- `sources[]` array iteration
- `sources[].id`, `sources[].type`, `sources[].last_commit_sha`
- `schema_version`

**Implementations:** yq, python, grep+sed

### 3. discovery.md

**Purpose:** Find all installed hiivmind-corpus corpora.

**Locations:**
| Type | Unix | Windows |
|------|------|---------|
| User-level | `~/.claude/skills/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\skills\hiivmind-corpus-*\` |
| Repo-local | `.claude-plugin/skills/hiivmind-corpus-*/` | (same) |
| Marketplace-single | `~/.claude/plugins/marketplaces/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\plugins\marketplaces\hiivmind-corpus-*\` |
| Marketplace-multi | `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\plugins\marketplaces\*\hiivmind-corpus-*\` |

**Operations:**
- List all corpora
- Filter by status (built/placeholder)
- Extract routing metadata (name, display_name, keywords)

### 4. status.md

**Purpose:** Check corpus index status and freshness.

**Status types:**
- `built` - Index has real content
- `placeholder` - Index needs building
- `no-index` - Index file missing

**Freshness checks:**
- Compare indexed SHA to local clone HEAD
- Compare indexed SHA to remote HEAD
- Calculate staleness

### 5. paths.md

**Purpose:** Resolve paths within corpus structure.

**Path types:**
- Data paths: `config.yaml`, `index.md`, `project-awareness.md`
- Source paths: `.source/{id}/`, `data/uploads/{id}/`, `.cache/web/{id}/`
- Navigate skill path (differs by corpus type)

**Cross-platform:** Path separator handling, home directory expansion

### 6. sources.md

**Purpose:** Git, local, and web source operations.

**Git operations:**
- Clone (shallow)
- Fetch and compare
- Get commit log between SHAs
- Get file changes (added/modified/deleted)

**Local operations:**
- List files
- Check modification times

**Web operations:**
- Cache management
- URL to filename conversion

### 7. scanning.md

**Purpose:** Analyze documentation structure.

**Operations:**
- Count doc files by extension
- Detect doc framework (docusaurus, mkdocs, etc.)
- Find large files needing GREP markers
- Extract section structure

---

## Skill Updates

Each skill needs updates to reference patterns instead of sourcing scripts.

### Update Template

**Before:**
```markdown
### Step N: Do Something

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
discover_all | filter_built | format_table
```
```

**After:**
```markdown
### Step N: Do Something

**See:** `lib/corpus/patterns/discovery.md`

1. Detect available tools (see `patterns/tool-detection.md`)
2. Scan corpus locations for each type
3. For each found corpus, verify `data/config.yaml` exists
4. Determine status by checking `data/index.md` content
5. Format results as: `name | type | status | path`

**Quick examples:**

Using Claude tools:
- Glob: `~/.claude/skills/hiivmind-corpus-*/data/config.yaml`
- Read each to verify

Using bash:
```bash
ls -d ~/.claude/skills/hiivmind-corpus-*/ 2>/dev/null
```

Using PowerShell:
```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\hiivmind-corpus-*" -Directory
```
```

### Skills to Update

| Skill | Primary Patterns Used |
|-------|----------------------|
| `hiivmind-corpus-discover` | tool-detection, discovery, status, config-parsing |
| `hiivmind-corpus-navigate` | tool-detection, discovery, config-parsing, paths |
| `hiivmind-corpus-init` | tool-detection, paths, sources |
| `hiivmind-corpus-build` | tool-detection, scanning, sources, config-parsing |
| `hiivmind-corpus-refresh` | tool-detection, status, sources, config-parsing |
| `hiivmind-corpus-enhance` | tool-detection, paths, config-parsing |
| `hiivmind-corpus-upgrade` | tool-detection, discovery, status, config-parsing |
| `hiivmind-corpus-add-source` | tool-detection, sources, config-parsing |

---

## Documentation Updates

### CLAUDE.md Changes

**Remove:**
```markdown
## Dependencies

- `bash` 4.0+
- `yq` 4.0+ (for YAML parsing in status/path functions)
```

**Add:**
```markdown
## Recommended Tools

hiivmind-corpus works across platforms by adapting to available tools.

### Required
- `git` - For git-based documentation sources (no alternative)

### Strongly Recommended
- `yq` OR `python3 + pyyaml` - YAML parsing. Fallback exists but is less reliable.

### Optional
- `rg` (ripgrep) - Faster search (Claude's built-in Grep usually sufficient)

### Tool Detection
Skills detect available tools at the start of operations and adapt accordingly.
See `lib/corpus/patterns/tool-detection.md` for details.
```

**Update architecture section:**
```markdown
├── lib/corpus/                       # Pattern documentation library
│   ├── patterns/                     # Tool-agnostic operation patterns
│   │   ├── tool-detection.md         # Capability detection
│   │   ├── config-parsing.md         # YAML config extraction
│   │   ├── discovery.md              # Finding corpora
│   │   ├── status.md                 # Index freshness
│   │   ├── paths.md                  # Path resolution
│   │   ├── sources.md                # Source operations
│   │   └── scanning.md               # Doc analysis
│   └── corpus-index.md               # Pattern index
```

### corpus-index.md Changes

Transform from function reference to pattern index:
- Remove all function tables
- Add pattern summaries with links
- Include "when to use" guidance
- Add cross-platform notes

---

## Implementation Order

### Phase 1: Foundation (2 files)
1. Create `lib/corpus/patterns/tool-detection.md`
2. Create `lib/corpus/patterns/config-parsing.md`

### Phase 2: Core Patterns (5 files)
3. Create `lib/corpus/patterns/discovery.md`
4. Create `lib/corpus/patterns/status.md`
5. Create `lib/corpus/patterns/paths.md`
6. Create `lib/corpus/patterns/sources.md`
7. Create `lib/corpus/patterns/scanning.md`

### Phase 3: Skill Migration (8 files)
8. Update `skills/hiivmind-corpus-discover/SKILL.md`
9. Update `skills/hiivmind-corpus-navigate/SKILL.md`
10. Update `skills/hiivmind-corpus-init/SKILL.md`
11. Update `skills/hiivmind-corpus-build/SKILL.md`
12. Update `skills/hiivmind-corpus-refresh/SKILL.md`
13. Update `skills/hiivmind-corpus-enhance/SKILL.md`
14. Update `skills/hiivmind-corpus-upgrade/SKILL.md`
15. Update `skills/hiivmind-corpus-add-source/SKILL.md`

### Phase 4: Documentation (2 files)
16. Update `CLAUDE.md`
17. Update `lib/corpus/corpus-index.md`

### Phase 5: Cleanup (6 files deleted)
18. Delete `lib/corpus/corpus-discovery-functions.sh`
19. Delete `lib/corpus/corpus-status-functions.sh`
20. Delete `lib/corpus/corpus-path-functions.sh`
21. Delete `lib/corpus/corpus-context-functions.sh`
22. Delete `lib/corpus/corpus-source-functions.sh`
23. Delete `lib/corpus/corpus-scan-functions.sh`

---

## File Summary

| Action | Count | Files |
|--------|-------|-------|
| Create | 7 | `lib/corpus/patterns/*.md` |
| Update | 10 | 8 skills + CLAUDE.md + corpus-index.md |
| Delete | 6 | `lib/corpus/*.sh` |
| **Total** | **23** | |

---

## Testing Strategy

### Verification Checklist

For each migrated skill:
- [ ] No remaining `source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/..."` references
- [ ] Pattern references are accurate
- [ ] Multi-platform examples included where relevant
- [ ] Tool detection guidance present

### Platform Testing

- [ ] Test discovery pattern on Linux
- [ ] Test discovery pattern on macOS
- [ ] Test discovery pattern on Windows (if available)
- [ ] Verify grep fallbacks work when yq unavailable

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Grep/sed fallbacks fail on complex YAML | Medium | High | Document limitations, strongly recommend yq/python |
| Windows path handling issues | Medium | Medium | Include PowerShell examples, test patterns |
| LLM misinterprets patterns | Low | Medium | Clear algorithm steps, explicit examples |
| Pattern docs become stale | Low | Low | Keep patterns conceptual, minimize version-specific syntax |

---

## Success Criteria

1. **Platform independence**: Skills work on Linux, macOS, and Windows
2. **No hard dependencies**: Skills function (possibly degraded) without yq
3. **Clear guidance**: Users know what tools to install for best experience
4. **Maintainability**: Pattern docs are easier to update than bash scripts
5. **Adaptability**: LLM can choose appropriate implementation at runtime

---

## References

- Current library: `lib/corpus/corpus-index.md`
- Shell functions: `lib/corpus/*.sh`
- Skill files: `skills/hiivmind-corpus-*/SKILL.md`
