---
name: generate-docs-plugin
description: Generate a documentation skill plugin for any open source project. Use when setting up documentation access for a new project.
---

# Documentation Plugin Generator

Generate a documentation skill plugin structure for any open source project.

## Process

```
1. INPUT      →  2. SCAFFOLD    →  3. CLONE       →  4. RESEARCH  →  5. GENERATE  →  6. CLEANUP
   (gather)       (create dir)      (into scaffold)   (analyze)      (files)         (remove clone)
```

**Note:** After generating, run `docs-init` to build the index collaboratively.

## Phase 1: Input Gathering

Before doing anything, collect required information:

| Input | Source | Example |
|-------|--------|---------|
| **Repo URL** | User provides | `https://github.com/pola-rs/polars` |
| **Plugin name** | Derive from repo or ask user | `polars-docs` |
| **Docs path** | Usually `docs/`, verify from URL or ask | `docs/` |

### Deriving Plugin Name

Extract from repo URL:
- `https://github.com/pola-rs/polars` → `polars-docs`
- `https://github.com/prisma/docs` → `prisma-docs`
- `https://github.com/ClickHouse/ClickHouse` → `clickhouse-docs`

**If ambiguous, ask the user.**

### Plugin Destination

All doc plugins are created in:
```
~/.claude/plugins/marketplaces/hiivmind-skills-documentation-navigation/
```

## Phase 2: Scaffold

Create the plugin directory structure **before cloning**:

```bash
# Set variables (replace with actual values)
PLUGIN_NAME="polars-docs"
PLUGIN_ROOT="$HOME/.claude/plugins/marketplaces/hiivmind-skills-documentation-navigation/${PLUGIN_NAME}"

# Create the plugin directory
mkdir -p "${PLUGIN_ROOT}"
cd "${PLUGIN_ROOT}"
```

Now you have a destination for everything that follows.

## Phase 3: Clone

Clone the source repo **inside the plugin directory**:

```bash
cd "${PLUGIN_ROOT}"
git clone --depth 1 {repo_url} .temp-source
```

This ensures:
- Clone is relative to the plugin being created
- Easy cleanup later
- No confusion about working directory

## Phase 4: Research

Analyze the cloned documentation. **Do not assume** - investigate.

### Questions to Answer

| Question | How to Find |
|----------|-------------|
| Doc framework? | Look for `docusaurus.config.js`, `mkdocs.yml`, `conf.py` |
| Existing nav structure? | Check `sidebars.js`, `mkdocs.yml` nav, toctree |
| Frontmatter schema? | Sample 5-10 files, check YAML frontmatter |
| Multiple languages? | Look for `i18n/`, `/en/`, `/zh/` directories |
| External doc sources? | Check build scripts for git clones |

### Research Commands

All commands run from `${PLUGIN_ROOT}`:

```bash
# Framework detection
ls .temp-source/

# Find nav structure
find .temp-source -name "sidebars*" -o -name "mkdocs.yml" -o -name "conf.py"

# Count doc files
find .temp-source/{docs_path} -name "*.md" -o -name "*.mdx" | wc -l

# Sample frontmatter
head -30 .temp-source/{docs_path}/some-file.md

# Check for external sources
grep -r "git clone" .temp-source/scripts/ .temp-source/package.json 2>/dev/null
```

## Phase 5: Generate

Create the plugin files in `${PLUGIN_ROOT}`:

### Directory Structure

```
{plugin-name}/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── navigate/
│       └── SKILL.md
├── data/
│   ├── config.yaml
│   └── index.md          # Placeholder - built by docs-init
├── .temp-source/         # Temporary - removed in Phase 6
├── .gitignore
└── README.md
```

### Files to Create

**`.claude-plugin/plugin.json`**
```json
{
  "name": "{plugin-name}",
  "description": "Always-current {Project} documentation",
  "version": "1.0.0"
}
```

**`data/config.yaml`**
```yaml
source:
  repo_url: "{repo_url}"
  branch: "{branch}"
  docs_root: "{docs_path}"

index:
  last_commit_sha: null
  last_indexed_at: null
  format: "markdown"

settings:
  include_patterns:
    - "**/*.md"
  exclude_patterns:
    - "**/_*.md"
```

**`data/index.md`** (placeholder)
```markdown
# {Project} Documentation Index

> Run `docs-init` to build this index.
```

**`skills/navigate/SKILL.md`**
- Per-project skill with specific description for discoverability
- Include project name in the skill description

**`.gitignore`**
```
.temp-source/
```

**`README.md`**
- Brief description of the plugin
- Link to source documentation
- Instructions for updating index

## Phase 6: Cleanup

Remove the temporary clone:

```bash
cd "${PLUGIN_ROOT}"
rm -rf .temp-source
```

## Example Walkthrough

**User**: "Create a docs plugin for Polars: https://github.com/pola-rs/polars/tree/main/docs"

### Phase 1 - Input
- Repo URL: `https://github.com/pola-rs/polars`
- Plugin name: `polars-docs`
- Docs path: `docs/` (from URL)

### Phase 2 - Scaffold
```bash
mkdir -p ~/.claude/plugins/marketplaces/hiivmind-skills-documentation-navigation/polars-docs
cd ~/.claude/plugins/marketplaces/hiivmind-skills-documentation-navigation/polars-docs
```

### Phase 3 - Clone
```bash
git clone --depth 1 https://github.com/pola-rs/polars .temp-source
```

### Phase 4 - Research
- Framework: MkDocs (found `mkdocs.yml`)
- Nav: Defined in `mkdocs.yml`
- 150 markdown files
- Docs root: `docs/`

### Phase 5 - Generate
Create all plugin files with discovered values.

### Phase 6 - Cleanup
```bash
rm -rf .temp-source
```

**Next step**: Run `docs-init` from within `polars-docs/` to build the index.

## Reference

- Initialize index: `skills/docs-init/SKILL.md`
- Update index: `skills/docs-maintain/SKILL.md`
- Example implementation: `clickhouse-docs/`
- Original spec: `docs/doc-skill-plugin-spec.md`
