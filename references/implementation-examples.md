# Implementation Examples

Step-by-step examples for each corpus destination type.

## Example A: User-level Skill

**Scenario:** Personal Polars documentation accessible across all projects.

### Step 1: Input Gathering

```
User: "Create a corpus for Polars docs"
Context: Running from ~/projects/data-analysis (established project)
Detected: ESTABLISHED_PROJECT=true
Choice: User-level skill
```

### Step 2: Scaffold

```bash
SKILL_NAME="hiivmind-corpus-polars"
mkdir -p ~/.claude/skills/${SKILL_NAME}
```

### Step 3: Clone

```bash
git clone --depth 1 https://github.com/pola-rs/polars \
  ~/.claude/skills/hiivmind-corpus-polars/.source/polars
```

### Step 4: Research

```bash
# Detect framework
ls ~/.claude/skills/hiivmind-corpus-polars/.source/polars/
# Found: docs/ with mkdocs.yml

# Count docs
find ~/.claude/skills/hiivmind-corpus-polars/.source/polars/docs -name "*.md" | wc -l
# 47 files
```

### Step 5: Generate

Create files from templates:
- `SKILL.md` ← `navigate-skill.md.template`
- `data/config.yaml` ← `config.yaml.template`
- `references/project-awareness.md` ← `project-awareness.md.template`
- `data/index.md` ← placeholder

### Step 6: Verify

```bash
ls -la ~/.claude/skills/hiivmind-corpus-polars/
# SKILL.md, data/, references/, .source/
```

### Result

```
~/.claude/skills/hiivmind-corpus-polars/
├── SKILL.md
├── data/
│   ├── config.yaml
│   └── index.md
├── references/
│   └── project-awareness.md
└── .source/
    └── polars/
```

---

## Example B: Repo-local Skill

**Scenario:** Team wants Polars docs available when working in their data-analysis project.

### Step 1: Input Gathering

```
User: "Add Polars docs to this project"
Context: Running from ~/git/data-analysis (team project)
Detected: ESTABLISHED_PROJECT=true, GIT_REPO=true
Choice: Repo-local skill
```

### Step 2: Scaffold

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
mkdir -p ${REPO_ROOT}/.claude-plugin/skills/hiivmind-corpus-polars
```

### Step 3: Clone

```bash
git clone --depth 1 https://github.com/pola-rs/polars \
  ${REPO_ROOT}/.claude-plugin/skills/hiivmind-corpus-polars/.source/polars
```

### Step 4-5: Research & Generate

Same as user-level, but files go to repo-local path.

### Step 6: Verify & Update .gitignore

```bash
# Add to project .gitignore
echo ".claude-plugin/skills/*/.source/" >> .gitignore
echo ".claude-plugin/skills/*/.cache/" >> .gitignore
```

### Result

```
{repo}/.claude-plugin/skills/hiivmind-corpus-polars/
├── SKILL.md
├── data/
│   ├── config.yaml
│   └── index.md
├── references/
│   └── project-awareness.md
└── .source/
    └── polars/
```

---

## Example C: Single-corpus Repo

**Scenario:** Creating a dedicated React documentation corpus for marketplace publishing.

### Step 1: Input Gathering

```
User: "Create a corpus for React docs"
Context: Running from ~/git/hiivmind-corpus-react (empty directory)
Detected: GIT_REPO=false (or new repo)
Choice: Single-corpus repo
```

### Step 2: Scaffold

```bash
PLUGIN_ROOT="${PWD}"
mkdir -p ${PLUGIN_ROOT}/.claude-plugin
mkdir -p ${PLUGIN_ROOT}/skills/navigate
mkdir -p ${PLUGIN_ROOT}/commands
mkdir -p ${PLUGIN_ROOT}/data
mkdir -p ${PLUGIN_ROOT}/references
```

### Step 3: Clone

```bash
git clone --depth 1 https://github.com/reactjs/react.dev \
  ${PLUGIN_ROOT}/.source/react
```

### Step 4: Research

```bash
ls .source/react/
# Found: src/content/ with MDX files
```

### Step 5: Generate

Create files from templates:
- `.claude-plugin/plugin.json` ← `plugin.json.template`
- `skills/navigate/SKILL.md` ← `navigate-skill.md.template`
- `commands/navigate.md` ← `navigate-command.md.template`
- `data/config.yaml` ← `config.yaml.template`
- `references/project-awareness.md` ← `project-awareness.md.template`
- `.gitignore` ← `gitignore.template`
- `CLAUDE.md` ← `claude.md.template`
- `LICENSE` ← `license.template`
- `README.md` ← `readme.md.template`
- `data/index.md` ← placeholder

### Step 6: Verify

```bash
ls -la
# .claude-plugin/, skills/, commands/, data/, references/, .source/, ...
cat .claude-plugin/plugin.json
```

### Result

```
hiivmind-corpus-react/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── navigate/
│       └── SKILL.md
├── commands/
│   └── navigate.md
├── data/
│   ├── config.yaml
│   └── index.md
├── references/
│   └── project-awareness.md
├── .source/
│   └── react/
├── .gitignore
├── CLAUDE.md
├── LICENSE
└── README.md
```

---

## Example D: Multi-corpus Repo (New Marketplace)

**Scenario:** Creating a new frontend docs marketplace with React and Vue.

### Step 1: Input Gathering

```
User: "Create a frontend docs collection starting with React"
Context: Running from ~/git/hiivmind-corpus-frontend (empty)
Choice: Multi-corpus repo (new marketplace)
```

### Step 2: Scaffold Marketplace

```bash
MARKETPLACE_ROOT="${PWD}"
mkdir -p ${MARKETPLACE_ROOT}/.claude-plugin
mkdir -p ${MARKETPLACE_ROOT}/hiivmind-corpus-react
```

### Step 3-5: Create First Plugin

Same as single-corpus, but inside `hiivmind-corpus-react/` subdirectory.

### Step 5b: Generate Marketplace Files

- `.claude-plugin/plugin.json` ← marketplace manifest
- `.claude-plugin/marketplace.json` ← `marketplace.json.template`
- `CLAUDE.md` ← `marketplace-claude.md.template`

### Step 6: Verify

```bash
cat .claude-plugin/marketplace.json
# Lists hiivmind-corpus-react
```

### Result

```
hiivmind-corpus-frontend/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── CLAUDE.md
├── README.md
│
└── hiivmind-corpus-react/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md
    ├── commands/
    │   └── navigate.md
    ├── data/
    │   ├── config.yaml
    │   └── index.md
    ├── references/
    │   └── project-awareness.md
    ├── .source/
    ├── .gitignore
    └── README.md
```

---

## Example E: Add to Existing Marketplace

**Scenario:** Adding Vue docs to the existing frontend marketplace.

### Step 1: Input Gathering

```
User: "Add Vue docs to this marketplace"
Context: Running from ~/git/hiivmind-corpus-frontend
Detected: HAS_MARKETPLACE=true
Choice: Add to marketplace
```

### Step 2: Scaffold New Plugin

```bash
mkdir -p hiivmind-corpus-vue/.claude-plugin
mkdir -p hiivmind-corpus-vue/skills/navigate
mkdir -p hiivmind-corpus-vue/commands
mkdir -p hiivmind-corpus-vue/data
mkdir -p hiivmind-corpus-vue/references
```

### Step 3: Clone

```bash
git clone --depth 1 https://github.com/vuejs/docs \
  hiivmind-corpus-vue/.source/vue
```

### Step 4-5: Research & Generate

Same as single-corpus plugin.

### Step 5b: Update Marketplace

Add to `.claude-plugin/marketplace.json`:
```json
{
  "plugins": [
    { "source": "./hiivmind-corpus-react", ... },
    { "source": "./hiivmind-corpus-vue", "name": "hiivmind-corpus-vue", ... }
  ]
}
```

### Step 6: Verify

```bash
cat .claude-plugin/marketplace.json
# Now lists both react and vue
```

### Result

```
hiivmind-corpus-frontend/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json  # Updated with vue
├── CLAUDE.md
├── hiivmind-corpus-react/
│   └── ...
└── hiivmind-corpus-vue/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md
    ├── commands/
    │   └── navigate.md
    ├── data/
    │   ├── config.yaml
    │   └── index.md
    ├── references/
    │   └── project-awareness.md
    ├── .source/
    │   └── vue/
    ├── .gitignore
    └── README.md
```

---

## Next Steps After Init

After any of these examples, offer:

1. **Add more sources** → `hiivmind-corpus-add-source`
2. **Build the index** → `hiivmind-corpus-build`
