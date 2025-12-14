---
name: hiivmind-corpus-init
description: Initialize a documentation corpus skill for any open source project. Use as the first step when setting up documentation access.
---

# Corpus Skill Generator

Generate a documentation corpus skill structure for any open source project.

## Scope Boundary

**This skill ONLY creates the directory structure and placeholder files.**

| This Skill Does | This Skill Does NOT Do |
|-----------------|------------------------|
| Create directories | Build the index |
| Clone source repos | Analyze documentation content |
| Generate config.yaml | Populate index.md with entries |
| Create placeholder index.md | Read/summarize doc files |
| Generate SKILL.md, README.md | Answer questions about the docs |

**STOP after Phase 6 (Verify).** Do not attempt to build the index - that is `hiivmind-corpus-build`'s job.

## Process

```
1. INPUT      →  2. SCAFFOLD    →  3. CLONE       →  4. RESEARCH  →  5. GENERATE  →  6. VERIFY  →  STOP
   (gather)       (create dir)      (into scaffold)   (analyze)      (files)         (confirm)      ↓
                                                                                              recommend
                                                                                            corpus-build
```

## Phase 1: Input Gathering

Before doing anything, **detect the current context** and collect required information.

### First: Detect Context

Run these checks to understand where you're running:

```bash
# Check if we're in a git repo
git rev-parse --show-toplevel 2>/dev/null && echo "GIT_REPO=true" || echo "GIT_REPO=false"

# Check for existing hiivmind-corpus marketplace
ls .claude-plugin/marketplace.json 2>/dev/null && echo "HAS_MARKETPLACE=true" || echo "HAS_MARKETPLACE=false"

# Check for existing corpus plugins (subdirectories with hiivmind-corpus- prefix)
ls -d hiivmind-corpus-*/ 2>/dev/null && echo "HAS_CORPUS_PLUGINS=true" || echo "HAS_CORPUS_PLUGINS=false"

# Check if this looks like an established project (non-corpus)
ls package.json pyproject.toml Cargo.toml go.mod setup.py requirements.txt 2>/dev/null && echo "ESTABLISHED_PROJECT=true" || echo "ESTABLISHED_PROJECT=false"

# Check for substantial code files
find . -maxdepth 2 -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.go" -o -name "*.rs" 2>/dev/null | head -5
```

Based on these checks, determine which **Context** applies:

---

### Context A: Established Non-Corpus Repository

**Detected when:** Running from a repo with project files (package.json, pyproject.toml, src/, etc.) that is NOT a hiivmind-corpus marketplace.

**Confirm with user:** "This looks like an established project ({detected type}). Is that correct?"

**Destination options:**

| Option | Location | Best For |
|--------|----------|----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-{lib}/` | Personal use across all projects |
| **Repo-local** | `{REPO_ROOT}/.claude-plugin/skills/hiivmind-corpus-{lib}/` | Team sharing, project-specific |

**User-level skill:**
- Lives in your personal Claude config (`~/.claude/skills/`)
- Available in all your projects automatically
- Not shared with teammates
- Example: "I want Polars docs everywhere I work"

**Repo-local skill:**
- Lives inside this project's `.claude-plugin/` directory
- No marketplace installation needed—just opening the project activates it
- Great for teams: everyone who clones the repo gets the skill automatically
- Scoped to this project's specific needs
- Example: A data analysis project where the whole team needs Polars docs

---

### Context B: Fresh Repository / New Directory

**Detected when:** Running from an empty or near-empty directory, OR a new git repo with minimal files.

**Destination options:**

| Option | Location | Best For |
|--------|----------|----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-{lib}/` | Personal use, no repo needed |
| **Single-corpus repo** | `{PWD}/` (marketplace + plugin at root) | One corpus per repo, simple structure |
| **Multi-corpus repo** | `{PWD}/hiivmind-corpus-{lib}/` (plugin as subdirectory) | Multiple corpora in one repo |

**User-level skill:**
- Same as Context A - personal use across all projects

**Single-corpus repo:**
- This directory becomes a standalone corpus plugin
- Marketplace and plugin manifests at the same level
- Simple structure for single-purpose repos
- Example: `hiivmind-corpus-react/` containing just React docs

**Multi-corpus repo:**
- This directory becomes a marketplace containing multiple corpus plugins
- Each corpus is a subdirectory (e.g., `hiivmind-corpus-react/`, `hiivmind-corpus-vue/`)
- Marketplace at root references all plugins via `marketplace.json`
- Example: `hiivmind-corpus-frontend/` containing React, Vue, and Svelte corpora

---

### Context C: Existing Hiivmind-Corpus Marketplace

**Detected when:** Running from a repo that already has `.claude-plugin/marketplace.json` OR existing `hiivmind-corpus-*/` subdirectories.

**Confirm with user:** "This looks like an existing corpus marketplace. Add another corpus here?"

**Destination option:**

| Option | Location | Best For |
|--------|----------|----------|
| **Add to marketplace** | `{PWD}/hiivmind-corpus-{lib}/` | Extending an existing multi-corpus repo |

**Add to marketplace:**
- Creates new corpus plugin as a subdirectory
- Automatically registers in existing `marketplace.json`
- Shares marketplace infrastructure with sibling corpora
- Example: Adding Vue docs to an existing frontend corpus marketplace

---

### Then: Initial source type

Ask the user what type of initial source:

| Type | Description | Best For |
|------|-------------|----------|
| **Git repository** | Clone a docs repo | Most open source projects (default) |
| **Start empty** | No initial source | Will add sources later via `hiivmind-corpus-add-source` |

Note: Local documents and web pages can be added after init using `hiivmind-corpus-add-source`.

### Then: Collect remaining inputs (for git source)

| Input | Source | Example |
|-------|--------|---------|
| **Repo URL** | User provides | `https://github.com/pola-rs/polars` |
| **Skill name** | Derive from repo or ask user | `hiivmind-corpus-polars` |
| **Source ID** | Derive from repo name (lowercase) | `polars` |
| **Docs path** | Usually `docs/`, verify from URL or ask | `docs/` |

### Deriving Skill Name and Source ID

Extract from repo URL:
- **Skill name**: Prefix with `hiivmind-corpus-`
- **Source ID**: Lowercase repo name (used for `.source/{source_id}/` directory)

Examples:
- `https://github.com/pola-rs/polars` → skill: `hiivmind-corpus-polars`, source_id: `polars`
- `https://github.com/prisma/docs` → skill: `hiivmind-corpus-prisma`, source_id: `prisma`
- `https://github.com/ClickHouse/ClickHouse` → skill: `hiivmind-corpus-clickhouse`, source_id: `clickhouse`

**If ambiguous, ask the user.**

### Then: Collect Corpus Keywords

Ask the user for routing keywords that help the global navigate skill find this corpus:

> "What keywords should route documentation questions to this corpus?"
> "These help the global navigator find this corpus when users ask questions."

**Suggest defaults based on:**
- Project name (always included)
- Domain terms (dataframe, sql, api, etc.)
- Common aliases (pl for polars, gh for github)

**Example prompts:**
- Polars → suggest: `polars, dataframe, lazy, expression, series, pl`
- Ibis → suggest: `ibis, sql, backend, duckdb, bigquery, postgres`
- GitHub API → suggest: `github, actions, workflow, api, graphql, rest, gh`

**User can:**
- Accept defaults
- Add more keywords
- Remove suggested keywords

Store as `additional_keywords` list for `config.yaml` template.

### Determining Destination Path

Based on the detected context and user's choice:

**User-level skill** (Context A or B):
```bash
SKILL_ROOT="${HOME}/.claude/skills/{skill-name}"
DESTINATION_TYPE="user-level"
```

**Repo-local skill** (Context A):
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
SKILL_ROOT="${REPO_ROOT}/.claude-plugin/skills/{skill-name}"
DESTINATION_TYPE="repo-local"
```

**Single-corpus repo** (Context B):
```bash
PLUGIN_ROOT="${PWD}"
DESTINATION_TYPE="single-corpus"
```

**Multi-corpus repo** (Context B, new marketplace):
```bash
MARKETPLACE_ROOT="${PWD}"
PLUGIN_ROOT="${PWD}/{skill-name}"
DESTINATION_TYPE="multi-corpus-new"
```

**Add to marketplace** (Context C):
```bash
MARKETPLACE_ROOT="${PWD}"
PLUGIN_ROOT="${PWD}/{skill-name}"
DESTINATION_TYPE="multi-corpus-existing"
```

## Phase 2: Scaffold

Create the directory structure **before cloning**.

### User-level Skill Scaffold

```bash
SKILL_NAME="hiivmind-corpus-polars"
SKILL_ROOT="${HOME}/.claude/skills/${SKILL_NAME}"

# Create skill directory (creates ~/.claude/skills/ if needed)
mkdir -p "${SKILL_ROOT}"
```

### Repo-local Skill Scaffold

```bash
SKILL_NAME="hiivmind-corpus-polars"
REPO_ROOT=$(git rev-parse --show-toplevel)
SKILL_ROOT="${REPO_ROOT}/.claude-plugin/skills/${SKILL_NAME}"

# Create skill directory (parent .claude-plugin/ may already exist)
mkdir -p "${SKILL_ROOT}"
```

### Single-corpus Repo Scaffold

```bash
PLUGIN_ROOT="${PWD}"

# Directory already exists (we're in it)
# Just create subdirectories as needed in Phase 5
```

### Multi-corpus Repo Scaffold (New Marketplace)

```bash
PLUGIN_NAME="hiivmind-corpus-polars"
MARKETPLACE_ROOT="${PWD}"
PLUGIN_ROOT="${MARKETPLACE_ROOT}/${PLUGIN_NAME}"

# Create plugin subdirectory
mkdir -p "${PLUGIN_ROOT}"

# Create marketplace manifest if it doesn't exist
mkdir -p "${MARKETPLACE_ROOT}/.claude-plugin"
```

### Add to Marketplace Scaffold (Existing Marketplace)

```bash
PLUGIN_NAME="hiivmind-corpus-polars"
MARKETPLACE_ROOT="${PWD}"
PLUGIN_ROOT="${MARKETPLACE_ROOT}/${PLUGIN_NAME}"

# Create plugin subdirectory
mkdir -p "${PLUGIN_ROOT}"

# marketplace.json already exists - will update in Phase 5
```

Now you have a destination for everything that follows.

## Phase 3: Clone

Clone the source repo **inside the skill/plugin directory**, using the source ID as a subdirectory name.

**Skip this phase if user chose "Start empty".**

### User-level or Repo-local Skill Clone

```bash
git clone --depth 1 {repo_url} "${SKILL_ROOT}/.source/{source_id}"
```

### Plugin Clone (Single-corpus, Multi-corpus, or Add to Marketplace)

```bash
git clone --depth 1 {repo_url} "${PLUGIN_ROOT}/.source/{source_id}"
```

This ensures:
- Clone is relative to the skill/plugin being created
- Multiple sources can coexist in `.source/` directory
- Source ID matches config.yaml entry
- Easy cleanup later

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

**Skip if user chose "Start empty".**

All commands run from `${PLUGIN_ROOT}` (or `${SKILL_ROOT}` for project-local):

```bash
# Framework detection
ls .source/{source_id}/

# Find nav structure
find .source/{source_id} -name "sidebars*" -o -name "mkdocs.yml" -o -name "conf.py"

# Count doc files
find .source/{source_id}/{docs_path} -name "*.md" -o -name "*.mdx" | wc -l

# Sample frontmatter
head -30 .source/{source_id}/{docs_path}/some-file.md

# Check for external sources
grep -r "git clone" .source/{source_id}/scripts/ .source/{source_id}/package.json 2>/dev/null
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
| `navigate-skill.md.template` | The navigate skill | All types |
| `config.yaml.template` | Source config + index tracking | All types |
| `project-awareness.md.template` | CLAUDE.md snippet for projects using this corpus | All types |
| `plugin.json.template` | Plugin manifest | Plugin types only |
| `readme.md.template` | Plugin documentation | Single-corpus only |
| `gitignore.template` | Ignore `.source/` | Plugin types only |
| `claude.md.template` | CLAUDE.md for single corpus plugin | Single-corpus only |
| `marketplace.json.template` | Marketplace registry | Multi-corpus only |
| `marketplace-claude.md.template` | CLAUDE.md for multi-corpus marketplace | Multi-corpus only |

### Template Placeholders

Fill these from Phase 1 inputs and Phase 4 research:

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{project_name}}` | Derived from repo (lowercase) | `polars` |
| `{{project_display_name}}` | Human-readable name | `Polars` |
| `{{plugin_name}}` | Full plugin directory name | `hiivmind-corpus-polars` |
| `{{marketplace_name}}` | Marketplace directory name (multi-corpus only) | `hiivmind-corpus-frontend` |
| `{{source_id}}` | Derived from repo (lowercase) | `polars` |
| `{{repo_url}}` | User input | `https://github.com/pola-rs/polars` |
| `{{repo_owner}}` | Extracted from URL | `pola-rs` |
| `{{repo_name}}` | Extracted from URL | `polars` |
| `{{branch}}` | Usually `main` | `main` |
| `{{docs_root}}` | From research | `docs/` |
| `{{description}}` | Generated (marketplace) | `Documentation corpus for data tools` |
| `{{plugin_description}}` | Generated (per-plugin) | `Always-current Polars documentation` |
| `{{author_name}}` | Ask or default | User's name |
| `{{keywords_json}}` | Generated (plugin only) | `"dataframes", "python", "rust"` |
| `{{additional_keywords}}` | From user (routing keywords) | `dataframe`, `lazy`, `expression` |
| `{{example_questions}}` | Generated (plugin only) | Example usage questions |
| `{{skill_topics}}` | Generated (plugin only) | Topics the skill covers |

**For "Start empty" corpora:** Leave the `sources:` array empty in config.yaml. User will add sources later via `hiivmind-corpus-add-source`.

### User-level Skill Structure

```
~/.claude/skills/{skill-name}/
├── SKILL.md              # From navigate-skill.md.template
├── data/
│   ├── config.yaml       # From config.yaml.template
│   ├── index.md          # Placeholder (see below)
│   ├── project-awareness.md  # CLAUDE.md snippet for projects
│   └── uploads/          # For local sources (created when needed)
├── .source/              # Cloned git sources
│   └── {source_id}/      # Each source in its own directory
└── .cache/               # Cached web content
    └── web/
```

**Files from templates:**
- `SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `data/project-awareness.md` ← `templates/project-awareness.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder:
  ```markdown
  # {Project} Documentation Corpus

  > Run `hiivmind-corpus-build` to build this index.
  ```

---

### Repo-local Skill Structure

```
{repo-root}/.claude-plugin/
└── skills/
    └── {skill-name}/
        ├── SKILL.md              # From navigate-skill.md.template
        ├── data/
        │   ├── config.yaml       # From config.yaml.template
        │   ├── index.md          # Placeholder
        │   ├── project-awareness.md  # CLAUDE.md snippet (usually not needed for repo-local)
        │   └── uploads/          # For local sources (created when needed)
        ├── .source/              # Cloned git sources (gitignored)
        │   └── {source_id}/      # Each source in its own directory
        └── .cache/               # Cached web content (gitignored)
            └── web/
```

**Files from templates:**
- `SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `data/project-awareness.md` ← `templates/project-awareness.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder (same as user-level)

**Parent `.gitignore`** - Ensure the project's `.gitignore` includes:
```
.claude-plugin/skills/*/.source/
.claude-plugin/skills/*/.cache/
```

---

### Single-corpus Repo Structure

The current directory becomes the plugin root:

```
{current-directory}/                  # e.g., hiivmind-corpus-react/
├── .claude-plugin/
│   └── plugin.json               # From plugin.json.template
├── skills/
│   └── navigate/
│       └── SKILL.md              # From navigate-skill.md.template
├── data/
│   ├── config.yaml               # From config.yaml.template
│   ├── index.md                  # Placeholder
│   ├── project-awareness.md      # CLAUDE.md snippet for projects using this corpus
│   └── uploads/                  # For local sources (created when needed)
├── .source/                      # Cloned git sources (gitignored)
│   └── {source_id}/              # Each source in its own directory
├── .cache/                       # Cached web content (gitignored)
│   └── web/
├── CLAUDE.md                     # From claude.md.template
├── .gitignore                    # From gitignore.template
└── README.md                     # From readme.md.template
```

**Files from templates:**
- `.claude-plugin/plugin.json` ← `templates/plugin.json.template`
- `skills/navigate/SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `data/project-awareness.md` ← `templates/project-awareness.md.template`
- `CLAUDE.md` ← `templates/claude.md.template`
- `.gitignore` ← `templates/gitignore.template`
- `README.md` ← `templates/readme.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder

---

### Multi-corpus Repo Structure (New Marketplace)

The current directory becomes a marketplace with this corpus as first plugin:

```
{marketplace-root}/                   # e.g., hiivmind-corpus-frontend/
├── .claude-plugin/
│   ├── plugin.json               # Marketplace manifest (name, description)
│   └── marketplace.json          # References child plugins
├── CLAUDE.md                     # Marketplace CLAUDE.md (see below)
├── .gitignore                    # From gitignore.template
├── README.md                     # Marketplace README
│
└── {plugin-name}/                    # e.g., hiivmind-corpus-react/
    ├── .claude-plugin/
    │   └── plugin.json           # From plugin.json.template
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md          # From navigate-skill.md.template
    ├── data/
    │   ├── config.yaml           # From config.yaml.template
    │   ├── index.md              # Placeholder
    │   ├── project-awareness.md  # CLAUDE.md snippet for projects
    │   └── uploads/
    ├── .source/                  # Cloned git sources (gitignored)
    └── .cache/                   # Cached web content (gitignored)
```

**Marketplace files:**
- `.claude-plugin/plugin.json` - Marketplace manifest (create manually with marketplace name)
- `.claude-plugin/marketplace.json` ← `templates/marketplace.json.template`
- `CLAUDE.md` - Marketplace CLAUDE.md explaining multi-corpus structure
- `.gitignore` ← `templates/gitignore.template`
- `README.md` - Marketplace README (create manually)

**Plugin files (in subdirectory):**
- Same as single-corpus, but inside `{plugin-name}/` subdirectory

---

### Add to Marketplace Structure (Existing Marketplace)

Add new plugin as a sibling to existing plugins:

```
{marketplace-root}/                   # Already exists
├── .claude-plugin/
│   ├── plugin.json               # Already exists
│   └── marketplace.json          # UPDATE to add new plugin reference
├── CLAUDE.md                     # Already exists
├── existing-plugin-1/            # Already exists
├── existing-plugin-2/            # Already exists
│
└── {new-plugin-name}/                # NEW - e.g., hiivmind-corpus-vue/
    ├── .claude-plugin/
    │   └── plugin.json           # From plugin.json.template
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md          # From navigate-skill.md.template
    ├── data/
    │   ├── config.yaml           # From config.yaml.template
    │   ├── index.md              # Placeholder
    │   ├── project-awareness.md  # CLAUDE.md snippet for projects
    │   └── uploads/
    ├── .source/                  # Cloned git sources (gitignored)
    └── .cache/                   # Cached web content (gitignored)
```

**Update existing file:**
- `.claude-plugin/marketplace.json` - Add new plugin to the `plugins` array

**Create plugin files (in subdirectory):**
- Same as single-corpus, but inside `{new-plugin-name}/` subdirectory

## Phase 6: Verify

Confirm the structure is complete:

**User-level or Repo-local skill:**
```bash
ls -la "${SKILL_ROOT}"
ls -la "${SKILL_ROOT}/data"
```

**Single-corpus repo:**
```bash
ls -la "${PLUGIN_ROOT}"
ls -la "${PLUGIN_ROOT}/skills/navigate"
ls -la "${PLUGIN_ROOT}/data"
```

**Multi-corpus repo (new or existing):**
```bash
ls -la "${MARKETPLACE_ROOT}"
ls -la "${PLUGIN_ROOT}"
ls -la "${PLUGIN_ROOT}/skills/navigate"
cat "${MARKETPLACE_ROOT}/.claude-plugin/marketplace.json"
```

**Keep `.source/`** - it will be reused by `hiivmind-corpus-build`, `hiivmind-corpus-enhance`, and `hiivmind-corpus-refresh`.

## Next Step: STOP HERE and Offer Options

**Your work is done.** Do NOT proceed to build the index. Instead:

1. **Confirm completion** to the user:
   > "The corpus structure has been created at `{path}`. The `data/index.md` is a placeholder."

2. **Offer next step options**:

   | Option | Skill | When to Recommend |
   |--------|-------|-------------------|
   | **Add more sources** | `hiivmind-corpus-add-source` | User mentioned multiple sources, or corpus would benefit from additional docs |
   | **Build the index** | `hiivmind-corpus-build` | Single source is sufficient, user ready to proceed |

   Example recommendation:
   > "What would you like to do next?
   > - **Add more sources** - Run `hiivmind-corpus-add-source` to add web pages, additional git repos, or local documents
   > - **Build the index** - Run `hiivmind-corpus-build` to analyze the documentation and create the index collaboratively"

3. **Do NOT**:
   - Read documentation files to summarize them
   - Populate `data/index.md` with entries
   - Analyze the cloned repo's content beyond basic framework detection (Phase 4)
   - Offer to "continue" or "also build the index"
   - Automatically proceed to either next step without user confirmation

The index building is intentionally a separate step because:
- It requires user collaboration to prioritize topics
- It can take significant time and context
- The user may want to add more sources first (web docs, examples repo, blog posts, etc.)

## Example Walkthroughs

### Example A: User-level skill (personal docs everywhere)

**User**: "I want Polars docs available in all my projects"

**Context Detection**
- Running from: `~/projects/my-python-app/` (a Python project)
- Detected: Established non-corpus project (pyproject.toml found)
- Confirm: "This looks like a Python project. Is that correct?"
- User chooses: **User-level** skill

**Phase 1 - Input**
- Destination: **User-level** (`~/.claude/skills/hiivmind-corpus-polars/`)
- Initial source: **Git repository**
- Repo URL: `https://github.com/pola-rs/polars`
- Skill name: `hiivmind-corpus-polars`
- Source ID: `polars`

**Phase 2 - Scaffold**
```bash
mkdir -p ~/.claude/skills/hiivmind-corpus-polars
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/pola-rs/polars ~/.claude/skills/hiivmind-corpus-polars/.source/polars
```

**Phase 5 - Generate**
Create skill files in `~/.claude/skills/hiivmind-corpus-polars/`

**Result:** Skill structure created. Not shared with teammates.

**Next Steps:**
- To add more sources (web docs, examples): `hiivmind-corpus-add-source`
- To build the index now: `hiivmind-corpus-build`

---

### Example B: Repo-local skill (team sharing)

**User**: "I'm working on a data analysis project and the whole team needs Polars docs"

**Context Detection**
- Running from: `~/projects/team-analytics/` (a team Python project)
- Detected: Established non-corpus project (pyproject.toml found)
- Confirm: "This looks like a Python project. Is that correct?"
- User chooses: **Repo-local** skill

**Phase 1 - Input**
- Destination: **Repo-local** (`{repo}/.claude-plugin/skills/hiivmind-corpus-polars/`)
- Initial source: **Git repository**
- Repo URL: `https://github.com/pola-rs/polars`
- Skill name: `hiivmind-corpus-polars`
- Source ID: `polars`

**Phase 2 - Scaffold**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
mkdir -p "${REPO_ROOT}/.claude-plugin/skills/hiivmind-corpus-polars"
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/pola-rs/polars "${REPO_ROOT}/.claude-plugin/skills/hiivmind-corpus-polars/.source/polars"
```

**Phase 5 - Generate**
Create skill files in `.claude-plugin/skills/hiivmind-corpus-polars/`

**Phase 6 - Additional**
Add to project's `.gitignore`:
```
.claude-plugin/skills/*/.source/
.claude-plugin/skills/*/.cache/
```

**Result:** Skill structure created. Commit the skill (minus `.source/`).

**Next Steps:**
- To add more sources (web docs, examples): `hiivmind-corpus-add-source`
- To build the index now: `hiivmind-corpus-build`

---

### Example C: Single-corpus repo (dedicated React docs)

**User**: "Create a standalone React docs corpus I can publish"

**Context Detection**
- Running from: `~/corpus/hiivmind-corpus-react/` (empty new directory)
- Detected: Fresh/empty directory
- User chooses: **Single-corpus repo**

**Phase 1 - Input**
- Destination: **Single-corpus** (this directory becomes the plugin)
- Initial source: **Git repository**
- Repo URL: `https://github.com/reactjs/react.dev`
- Plugin name: `hiivmind-corpus-react`
- Source ID: `react`

**Phase 2 - Scaffold**
```bash
# Already in the directory, just create subdirs in Phase 5
PLUGIN_ROOT="${PWD}"
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/reactjs/react.dev ./.source/react
```

**Phase 5 - Generate**
Create full plugin structure at repo root:
- `.claude-plugin/plugin.json`
- `skills/navigate/SKILL.md`
- `data/config.yaml`, `data/index.md`
- `CLAUDE.md`, `README.md`, `.gitignore`

**Result:** Plugin structure created. Push to GitHub and install via marketplace.

**Next Steps:**
- To add more sources (tutorials, blog posts, examples repo): `hiivmind-corpus-add-source`
- To build the index now: `hiivmind-corpus-build`

---

### Example D: Multi-corpus repo (new frontend docs collection)

**User**: "I want to create a corpus repo that will hold React, Vue, and Svelte docs"

**Context Detection**
- Running from: `~/corpus/hiivmind-corpus-frontend/` (empty new directory)
- Detected: Fresh/empty directory
- User chooses: **Multi-corpus repo** (new marketplace)

**Phase 1 - Input**
- Destination: **Multi-corpus new** (marketplace at root, plugins as subdirectories)
- Marketplace name: `hiivmind-corpus-frontend`
- First plugin: `hiivmind-corpus-react`
- Repo URL: `https://github.com/reactjs/react.dev`
- Source ID: `react`

**Phase 2 - Scaffold**
```bash
MARKETPLACE_ROOT="${PWD}"
mkdir -p "${MARKETPLACE_ROOT}/.claude-plugin"
mkdir -p "${MARKETPLACE_ROOT}/hiivmind-corpus-react"
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/reactjs/react.dev ./hiivmind-corpus-react/.source/react
```

**Phase 5 - Generate**
Create marketplace files at root:
- `.claude-plugin/plugin.json` (marketplace manifest)
- `.claude-plugin/marketplace.json` (references child plugins)
- `CLAUDE.md`, `README.md`, `.gitignore`

Create plugin files in `hiivmind-corpus-react/`:
- Standard plugin structure

**Result:** Marketplace and first plugin structure created.

**Next Steps:**
- To add more corpora (Vue, Svelte): run `hiivmind-corpus-init` again
- To add more sources to React (tutorials, examples): `hiivmind-corpus-add-source`
- To build the React index now: `hiivmind-corpus-build`

---

### Example E: Add to existing marketplace

**User**: "Add Vue docs to my frontend corpus collection"

**Context Detection**
- Running from: `~/corpus/hiivmind-corpus-frontend/` (existing marketplace)
- Detected: Existing hiivmind-corpus marketplace (has `.claude-plugin/marketplace.json`)
- Confirm: "This looks like an existing corpus marketplace. Add another corpus here?"
- User confirms: Yes

**Phase 1 - Input**
- Destination: **Add to marketplace** (new plugin as subdirectory)
- Plugin name: `hiivmind-corpus-vue`
- Repo URL: `https://github.com/vuejs/docs`
- Source ID: `vue`

**Phase 2 - Scaffold**
```bash
mkdir -p ./hiivmind-corpus-vue
```

**Phase 3 - Clone**
```bash
git clone --depth 1 https://github.com/vuejs/docs ./hiivmind-corpus-vue/.source/vue
```

**Phase 5 - Generate**
Create plugin files in `hiivmind-corpus-vue/`:
- Standard plugin structure

Update existing `marketplace.json`:
```json
{
  "plugins": [
    { "path": "hiivmind-corpus-react" },
    { "path": "hiivmind-corpus-vue" }  // Added
  ]
}
```

**Result:** Vue corpus structure added alongside React in the same marketplace.

**Next Steps:**
- To add more sources to Vue (tutorials, composition API guide): `hiivmind-corpus-add-source`
- To build the Vue index now: `hiivmind-corpus-build`

## Reference

- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
