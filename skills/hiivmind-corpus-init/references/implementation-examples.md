# Implementation Examples

## Example A: User-level skill (personal docs everywhere)

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

## Example B: Repo-local skill (team sharing)

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

## Example C: Single-corpus repo (dedicated React docs)

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

## Example D: Multi-corpus repo (new frontend docs collection)

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

## Example E: Add to existing marketplace

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
