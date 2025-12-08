---
name: hiivmind-corpus-init
description: Initialize a documentation corpus skill for any open source project. Use as the first step when setting up documentation access.
---

# Corpus Skill Generator

Generate a documentation corpus skill structure for any open source project.

## Process

```
1. INPUT      →  2. SCAFFOLD    →  3. CLONE       →  4. RESEARCH  →  5. GENERATE  →  6. VERIFY
   (gather)       (create dir)      (into scaffold)   (analyze)      (files)         (confirm)
```

**Note:** After generating, run `hiivmind-corpus-build` to build the index collaboratively.

## Phase 1: Input Gathering

Before doing anything, collect required information:

### First: Where should this skill live?

**Ask the user** which approach they want:

| Approach | Location | Best For |
|----------|----------|----------|
| **Project-local** | `.claude-plugin/skills/hiivmind-corpus-{lib}/` | This project only, team sharing |
| **Standalone plugin** | `hiivmind-corpus-{lib}/` separate directory | Personal reuse across all repos |

**Project-local skill:**
- Lives inside the current project's `.claude-plugin/` directory
- No marketplace installation needed—just having the project open activates it
- Great for teams: everyone who clones the project gets the skill automatically
- Scoped to this project's specific needs
- Example: A data analysis project that needs Polars docs

**Standalone plugin:**
- Creates a separate `hiivmind-corpus-{lib}/` directory (typically its own repo, or a subdirectory of a broader corpus collection)
- Requires marketplace installation to use
- Reusable across all your projects and Claude instances
- Independent lifecycle from any specific project
- Example: "I always want React docs available everywhere"

### Then: Collect remaining inputs

| Input | Source | Example |
|-------|--------|---------|
| **Repo URL** | User provides | `https://github.com/pola-rs/polars` |
| **Skill name** | Derive from repo or ask user | `hiivmind-corpus-polars` |
| **Docs path** | Usually `docs/`, verify from URL or ask | `docs/` |

### Deriving Skill Name

Extract from repo URL and prefix with `hiivmind-corpus-`:
- `https://github.com/pola-rs/polars` → `hiivmind-corpus-polars`
- `https://github.com/prisma/docs` → `hiivmind-corpus-prisma`
- `https://github.com/ClickHouse/ClickHouse` → `hiivmind-corpus-clickhouse`

**If ambiguous, ask the user.**

### Determining Destination Path

Based on the user's choice:

**Project-local:**
```bash
SKILL_ROOT="${PWD}/.claude-plugin/skills/{skill-name}"
```

**Standalone plugin:**
```bash
PLUGIN_ROOT="${PWD}/{skill-name}"
```

## Phase 2: Scaffold

Create the directory structure **before cloning**.

### Project-local Scaffold

```bash
SKILL_NAME="hiivmind-corpus-polars"
SKILL_ROOT="${PWD}/.claude-plugin/skills/${SKILL_NAME}"

# Create skill directory (parent .claude-plugin/ may already exist)
mkdir -p "${SKILL_ROOT}"
```

### Standalone Plugin Scaffold

```bash
PLUGIN_NAME="hiivmind-corpus-polars"
PLUGIN_ROOT="${PWD}/${PLUGIN_NAME}"

# Create the plugin directory
mkdir -p "${PLUGIN_ROOT}"
```

Now you have a destination for everything that follows.

## Phase 3: Clone

Clone the source repo **inside the skill/plugin directory**:

### Project-local Clone

```bash
git clone --depth 1 {repo_url} "${SKILL_ROOT}/.source"
```

### Standalone Plugin Clone

```bash
git clone --depth 1 {repo_url} "${PLUGIN_ROOT}/.source"
```

This ensures:
- Clone is relative to the skill/plugin being created
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
ls .source/

# Find nav structure
find .source -name "sidebars*" -o -name "mkdocs.yml" -o -name "conf.py"

# Count doc files
find .source/{docs_path} -name "*.md" -o -name "*.mdx" | wc -l

# Sample frontmatter
head -30 .source/{docs_path}/some-file.md

# Check for external sources
grep -r "git clone" .source/scripts/ .source/package.json 2>/dev/null
```

## Phase 5: Generate

Create files by reading templates and filling placeholders.

### Template Location

Templates are in this plugin's `templates/` directory. To find them:
1. Locate this skill file (`skills/hiivmind-corpus-init/SKILL.md`)
2. Navigate up to the plugin root
3. Templates are in `templates/`

**From this skill's perspective:** `../../templates/`

### Template Files

| Template | Purpose | Used By |
|----------|---------|---------|
| `navigate-skill.md.template` | The navigate skill | Both |
| `config.yaml.template` | Source config + index tracking | Both |
| `plugin.json.template` | Plugin manifest | Standalone only |
| `readme.md.template` | Plugin documentation | Standalone only |
| `gitignore.template` | Ignore `.source/` | Standalone only |

### Template Placeholders

Fill these from Phase 1 inputs and Phase 4 research:

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{project_name}}` | Derived from repo (lowercase) | `polars` |
| `{{project_display_name}}` | Human-readable name | `Polars` |
| `{{repo_url}}` | User input | `https://github.com/pola-rs/polars` |
| `{{repo_owner}}` | Extracted from URL | `pola-rs` |
| `{{repo_name}}` | Extracted from URL | `polars` |
| `{{branch}}` | Usually `main` | `main` |
| `{{docs_root}}` | From research | `docs/` |
| `{{description}}` | Generated | `Always-current Polars documentation` |
| `{{author_name}}` | Ask or default | User's name |
| `{{keywords_json}}` | Generated (standalone only) | `"dataframes", "python", "rust"` |
| `{{example_questions}}` | Generated (standalone only) | Example usage questions |
| `{{skill_topics}}` | Generated (standalone only) | Topics the skill covers |

### Project-local Structure

```
.claude-plugin/
└── skills/
    └── {skill-name}/
        ├── SKILL.md              # From navigate-skill.md.template
        ├── data/
        │   ├── config.yaml       # From config.yaml.template
        │   └── index.md          # Placeholder (see below)
        └── .source/              # Cloned source (gitignored by parent)
```

**Files from templates:**
- `SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`

**Create manually:**
- `data/index.md` - Simple placeholder:
  ```markdown
  # {Project} Documentation Corpus

  > Run `hiivmind-corpus-build` to build this index.
  ```

**Parent `.gitignore`** - Ensure the project's `.gitignore` includes:
```
.claude-plugin/skills/*/.source/
```

---

### Standalone Plugin Structure

```
{plugin-name}/
├── .claude-plugin/
│   └── plugin.json               # From plugin.json.template
├── skills/
│   └── navigate/
│       └── SKILL.md              # From navigate-skill.md.template
├── data/
│   ├── config.yaml               # From config.yaml.template
│   └── index.md                  # Placeholder
├── .source/
├── .gitignore                    # From gitignore.template
└── README.md                     # From readme.md.template
```

**Files from templates:**
- `.claude-plugin/plugin.json` ← `templates/plugin.json.template`
- `skills/navigate/SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `.gitignore` ← `templates/gitignore.template`
- `README.md` ← `templates/readme.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder (same as project-local)

## Phase 6: Verify

Confirm the structure is complete:

**Project-local:**
```bash
ls -la "${SKILL_ROOT}"
```

**Standalone plugin:**
```bash
ls -la "${PLUGIN_ROOT}"
```

**Keep `.source/`** - it will be reused by `hiivmind-corpus-build`, `hiivmind-corpus-enhance`, and `hiivmind-corpus-refresh`.

## Example Walkthroughs

### Example A: Project-local (data analysis project needs Polars)

**User**: "I'm working on a data analysis project and need better access to Polars docs. Can you set that up?"

**Phase 1 - Input**
- Destination: **Project-local** (user wants it for this project)
- Repo URL: `https://github.com/pola-rs/polars`
- Skill name: `hiivmind-corpus-polars`
- Docs path: `docs/`

**Phase 2 - Scaffold**
```bash
mkdir -p ./.claude-plugin/skills/hiivmind-corpus-polars
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/pola-rs/polars .claude-plugin/skills/hiivmind-corpus-polars/.source
```

**Phase 4 - Research**
- Framework: MkDocs
- 150 markdown files
- Docs root: `docs/`

**Phase 5 - Generate**
Create skill files in `.claude-plugin/skills/hiivmind-corpus-polars/`

**Phase 6 - Verify**
```bash
ls -la .claude-plugin/skills/hiivmind-corpus-polars/
```

**Result:** Skill is immediately available in this project. Teammates who clone the repo will also have access (after ensuring `.source/` is gitignored).

---

### Example B: Standalone plugin (reusable React docs)

**User**: "Create a corpus skill for React that I can use across all my projects"

**Phase 1 - Input**
- Destination: **Standalone plugin** (user wants reusability)
- Repo URL: `https://github.com/reactjs/react.dev`
- Plugin name: `hiivmind-corpus-react`
- Docs path: `src/content/`

**Phase 2 - Scaffold**
```bash
mkdir -p ./hiivmind-corpus-react
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/reactjs/react.dev ./hiivmind-corpus-react/.source
```

**Phase 4 - Research**
- Framework: Next.js with MDX
- Nav: Defined in `src/sidebarLearn.json`
- Docs root: `src/content/`

**Phase 5 - Generate**
Create full plugin structure in `hiivmind-corpus-react/`

**Phase 6 - Verify**
```bash
ls -la ./hiivmind-corpus-react/
```

**Next step**: User creates a git repo, publishes to marketplace, then installs via `/plugin install`.

## Reference

- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Original spec: `docs/doc-skill-plugin-spec.md`
