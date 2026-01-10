---
name: hiivmind-corpus-init
description: >
  This skill should be used when the user asks to "create a corpus", "initialize documentation",
  "set up docs for a library", "index this project's docs", "create documentation corpus",
  "scaffold corpus skill", or mentions wanting to create a new documentation corpus for any
  open source project. Also triggers on "new corpus", "corpus for [library name]", or
  "hiivmind-corpus init".
---

# Corpus Skill Generator

Generate a documentation corpus skill structure for any open source project.

## Scope Boundary

**This skill ONLY creates the directory structure and placeholder files, then delegates to add-source.**

| This Skill Does | This Skill Does NOT Do |
|-----------------|------------------------|
| Create directories | Clone source repos (delegated to add-source) |
| Generate config.yaml (empty sources) | Analyze documentation content |
| Create placeholder index.md | Populate index.md with entries |
| Generate SKILL.md, README.md | Read/summarize doc files |
| Delegate to `/hiivmind-corpus-add-source` | Build the index |

**After Phase 4 (Verify), run `/hiivmind-corpus-add-source`** to add the initial source.

## Process

```
1. INPUT      →  2. SCAFFOLD    →  3. GENERATE  →  4. VERIFY  →  5. ADD SOURCE
   (gather)       (create dir)      (files)         (confirm)      (delegate)
                                                                        ↓
                                                              run /hiivmind-corpus-add-source
```

## Phase 1: Input Gathering

Before doing anything, **detect the current context** and collect required information.

### First: Detect Context

**See:** `lib/corpus/patterns/discovery.md` for context detection algorithms.

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

### Then: Collect Source URL (for naming)

Ask the user what documentation they want to index:

> "What documentation would you like to index? Provide a URL (GitHub repo, docs site, or llms.txt manifest)."

| URL Pattern | Extract Name From |
|-------------|-------------------|
| `github.com/org/repo` | repo name → `hiivmind-corpus-{repo}` |
| `site.com/docs/llms.txt` | site name → `hiivmind-corpus-{site}` |
| `docs.project.io/` | project name → `hiivmind-corpus-{project}` |
| No URL provided | Ask user for corpus name |

**Examples:**
- `https://github.com/pola-rs/polars` → `hiivmind-corpus-polars`
- `https://code.claude.com/docs/llms.txt` → `hiivmind-corpus-claude-code`
- `https://docs.ibis-project.org/` → `hiivmind-corpus-ibis`

**If user says "start empty":** Skip source addition, just create scaffold.

**Store the URL** - it will be passed to `/hiivmind-corpus-add-source` in Phase 5.

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
# Just create subdirectories as needed in Phase 3 (Generate)
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

# marketplace.json already exists - will update in Phase 3 (Generate)
```

Now you have a destination for everything that follows.

## Phase 3: Generate

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
| `navigate-skill.md.template` | Navigate skill for auto-triggering | All types |
| `navigate-command.md.template` | Navigate command (explicit entry point) | Plugin types only |
| `config.yaml.template` | Source config + index tracking | All types |
| `project-awareness.md.template` | CLAUDE.md snippet for projects using this corpus | All types |
| `plugin.json.template` | Plugin manifest | Plugin types only |
| `readme.md.template` | Plugin documentation | Single-corpus only |
| `gitignore.template` | Ignore `.source/` and `.cache/` | Plugin types only |
| `license.template` | MIT license | Plugin types only |
| `claude.md.template` | CLAUDE.md for single corpus plugin | Single-corpus only |
| `marketplace.json.template` | Marketplace registry | Multi-corpus only |
| `marketplace-claude.md.template` | CLAUDE.md for multi-corpus marketplace | Multi-corpus only |

### Template Placeholders

**See:** `references/template-placeholders.md` for the full placeholder reference table.

### User-level Skill Structure

```
~/.claude/skills/{skill-name}/
├── SKILL.md              # From navigate-skill.md.template
├── data/
│   ├── config.yaml       # From config.yaml.template
│   ├── index.md          # Placeholder (see below)
│   └── uploads/          # For local sources (created when needed)
├── references/
│   └── project-awareness.md  # CLAUDE.md snippet for projects
├── .source/              # Cloned git sources
│   └── {source_id}/      # Each source in its own directory
└── .cache/               # Cached web content
    └── web/
```

**Files from templates:**
- `SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `references/project-awareness.md` ← `templates/project-awareness.md.template`

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
        │   └── uploads/          # For local sources (created when needed)
        ├── references/
        │   └── project-awareness.md  # CLAUDE.md snippet (usually not needed for repo-local)
        ├── .source/              # Cloned git sources (gitignored)
        │   └── {source_id}/      # Each source in its own directory
        └── .cache/               # Cached web content (gitignored)
            └── web/
```

**Files from templates:**
- `SKILL.md` ← `templates/navigate-skill.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `references/project-awareness.md` ← `templates/project-awareness.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder (same as user-level)

**Parent `.gitignore`** - Ensure the project's `.gitignore` includes:
```
.claude-plugin/skills/*/.source/
.claude-plugin/skills/*/.cache/
```

---

### Single-corpus, Multi-corpus, and Marketplace Structures

**See:** `references/marketplace-templates.md` for detailed directory structures and template mappings for:
- Single-corpus repo structure
- Multi-corpus repo structure (new marketplace)
- Add to marketplace structure (existing marketplace)

## Phase 4: Verify

Confirm the structure is complete:

**User-level or Repo-local skill:**
```bash
ls -la "${SKILL_ROOT}"
ls -la "${SKILL_ROOT}/data"
```

**Single-corpus repo:**
```bash
ls -la "${PLUGIN_ROOT}"
ls -la "${PLUGIN_ROOT}/commands"
ls -la "${PLUGIN_ROOT}/data"
```

**Multi-corpus repo (new or existing):**
```bash
ls -la "${MARKETPLACE_ROOT}"
ls -la "${PLUGIN_ROOT}"
ls -la "${PLUGIN_ROOT}/commands"
cat "${MARKETPLACE_ROOT}/.claude-plugin/marketplace.json"
```

## Phase 5: Add Initial Source

**If user provided a source URL in Phase 1**, run `/hiivmind-corpus-add-source` to add it.

The add-source skill handles:
- Source type detection (git, llms-txt, web, local, generated-docs)
- Cloning git repos
- Fetching llms.txt manifests
- Framework research (docusaurus, mkdocs, sphinx detection)
- Updating config.yaml with source entry

**Pass context to add-source:**
```
Source URL: {url_from_phase_1}
Working directory: {SKILL_ROOT or PLUGIN_ROOT}
```

**If user chose "start empty"**, skip this phase and inform:
> "The corpus scaffold has been created at `{path}` with no sources.
> Run `/hiivmind-corpus-add-source` to add documentation sources."

## Next Step: Build the Index

After add-source completes, offer next steps:

| Option | Skill | When to Recommend |
|--------|-------|-------------------|
| **Build the index** | `/hiivmind-corpus-build` | Ready to analyze docs and create index |
| **Add another source** | `/hiivmind-corpus-add-source` | User mentioned multiple sources |

**Do NOT**:
- Read documentation files to summarize them
- Populate `data/index.md` with entries
- Automatically proceed without user confirmation

## Example Walkthroughs

**See:** `references/implementation-examples.md` for complete step-by-step examples of:
- **Example A:** User-level skill (personal docs everywhere)
- **Example B:** Repo-local skill (team sharing)
- **Example C:** Single-corpus repo (dedicated React docs)
- **Example D:** Multi-corpus repo (new frontend docs collection)
- **Example E:** Add to existing marketplace

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/discovery.md` - Context detection algorithms
- `lib/corpus/patterns/sources/` - Source type operations (git, local, web, generated-docs, llms-txt)
- `lib/corpus/patterns/scanning.md` - File discovery and analysis
- `lib/corpus/patterns/paths.md` - Path resolution

**Related skills:**
- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
