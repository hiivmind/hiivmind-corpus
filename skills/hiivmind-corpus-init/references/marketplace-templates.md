# Marketplace and Plugin Structure Templates

## Single-corpus Repo Structure

The current directory becomes the plugin root:

```
{current-directory}/                  # e.g., hiivmind-corpus-react/
├── .claude-plugin/
│   └── plugin.json               # From plugin.json.template
├── commands/
│   └── navigate.md               # From navigate-command.md.template
├── data/
│   ├── config.yaml               # From config.yaml.template
│   ├── index.md                  # Placeholder
│   └── uploads/                  # For local sources (created when needed)
├── references/
│   └── project-awareness.md      # CLAUDE.md snippet for projects using this corpus
├── .source/                      # Cloned git sources (gitignored)
│   └── {source_id}/              # Each source in its own directory
├── .cache/                       # Cached web content (gitignored)
│   └── web/
├── CLAUDE.md                     # From claude.md.template
├── LICENSE                       # From license.template
├── .gitignore                    # From gitignore.template
└── README.md                     # From readme.md.template
```

**Files from templates:**
- `.claude-plugin/plugin.json` ← `templates/plugin.json.template`
- `commands/navigate.md` ← `templates/navigate-command.md.template`
- `data/config.yaml` ← `templates/config.yaml.template`
- `references/project-awareness.md` ← `templates/project-awareness.md.template`
- `CLAUDE.md` ← `templates/claude.md.template`
- `LICENSE` ← `templates/license.template`
- `.gitignore` ← `templates/gitignore.template`
- `README.md` ← `templates/readme.md.template`

**Create manually:**
- `data/index.md` - Simple placeholder

---

## Multi-corpus Repo Structure (New Marketplace)

The current directory becomes a marketplace with this corpus as first plugin:

```
{marketplace-root}/                   # e.g., hiivmind-corpus-frontend/
├── .claude-plugin/
│   ├── plugin.json               # Marketplace manifest (name, description)
│   └── marketplace.json          # References child plugins
├── CLAUDE.md                     # Marketplace CLAUDE.md (see below)
├── LICENSE                       # From license.template
├── .gitignore                    # From gitignore.template
├── README.md                     # Marketplace README
│
└── {plugin-name}/                    # e.g., hiivmind-corpus-react/
    ├── .claude-plugin/
    │   └── plugin.json           # From plugin.json.template
    ├── commands/
    │   └── navigate.md           # From navigate-command.md.template
    ├── data/
    │   ├── config.yaml           # From config.yaml.template
    │   ├── index.md              # Placeholder
    │   └── uploads/
    ├── references/
    │   └── project-awareness.md  # CLAUDE.md snippet for projects
    ├── .source/                  # Cloned git sources (gitignored)
    └── .cache/                   # Cached web content (gitignored)
```

**Marketplace files:**
- `.claude-plugin/plugin.json` - Marketplace manifest (create manually with marketplace name)
- `.claude-plugin/marketplace.json` ← `templates/marketplace.json.template`
- `CLAUDE.md` - Marketplace CLAUDE.md explaining multi-corpus structure
- `LICENSE` ← `templates/license.template`
- `.gitignore` ← `templates/gitignore.template`
- `README.md` - Marketplace README (create manually)

**Plugin files (in subdirectory):**
- Same as single-corpus, but inside `{plugin-name}/` subdirectory

---

## Add to Marketplace Structure (Existing Marketplace)

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
    ├── commands/
    │   └── navigate.md           # From navigate-command.md.template
    ├── data/
    │   ├── config.yaml           # From config.yaml.template
    │   ├── index.md              # Placeholder
    │   └── uploads/
    ├── references/
    │   └── project-awareness.md  # CLAUDE.md snippet for projects
    ├── .source/                  # Cloned git sources (gitignored)
    └── .cache/                   # Cached web content (gitignored)
```

**Update existing file:**
- `.claude-plugin/marketplace.json` - Add new plugin to the `plugins` array

**Create plugin files (in subdirectory):**
- Same as single-corpus, but inside `{new-plugin-name}/` subdirectory

---

## marketplace.json Update Example

When adding a new plugin to an existing marketplace:

```json
{
  "plugins": [
    { "path": "hiivmind-corpus-react" },
    { "path": "hiivmind-corpus-vue" }  // Added
  ]
}
```

---

## Command Invocation Pattern

Each corpus plugin exposes a single command: `/{{plugin_name}}:navigate`

The command handles:
1. **Navigation** (default) - Answer documentation questions directly
2. **Maintenance** - Delegate to parent hiivmind-corpus skills:
   - `refresh` → `hiivmind-corpus-refresh`
   - `enhance {topic}` → `hiivmind-corpus-enhance`
   - `add source {url}` → `hiivmind-corpus-add-source`
   - `awareness` → `hiivmind-corpus-awareness`

This pattern:
- Provides a unified entry point per corpus
- Avoids duplicating maintenance logic in each corpus
- Reuses parent skills with corpus context
