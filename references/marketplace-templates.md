# Marketplace Templates Reference

Directory structures and template mappings for plugin-type corpora (single-corpus, multi-corpus, add to marketplace).

## Single-corpus Repo Structure

A standalone corpus plugin in its own repository.

```
{plugin-name}/
├── .claude-plugin/
│   └── plugin.json           # From plugin.json.template
├── skills/
│   └── navigate/
│       └── SKILL.md          # From navigate-skill.md.template
├── commands/
│   └── navigate.md           # From navigate-command.md.template
├── data/
│   ├── config.yaml           # From config.yaml.template
│   ├── index.md              # Placeholder
│   └── uploads/              # For local sources (created when needed)
├── references/
│   └── project-awareness.md  # From project-awareness.md.template
├── .source/                  # Cloned git sources (gitignored)
│   └── {source_id}/
├── .cache/                   # Cached web content (gitignored)
│   └── web/
├── .gitignore                # From gitignore.template
├── CLAUDE.md                 # From claude.md.template
├── LICENSE                   # From license.template
└── README.md                 # From readme.md.template
```

**Files from templates:**

| File | Template |
|------|----------|
| `.claude-plugin/plugin.json` | `plugin.json.template` |
| `skills/navigate/SKILL.md` | `navigate-skill.md.template` |
| `commands/navigate.md` | `navigate-command.md.template` |
| `data/config.yaml` | `config.yaml.template` |
| `references/project-awareness.md` | `project-awareness.md.template` |
| `.gitignore` | `gitignore.template` |
| `CLAUDE.md` | `claude.md.template` |
| `LICENSE` | `license.template` |
| `README.md` | `readme.md.template` |

**Create manually:**
- `data/index.md` - Simple placeholder

---

## Multi-corpus Repo Structure (New Marketplace)

A marketplace containing multiple corpus plugins as subdirectories.

```
{marketplace-name}/
├── .claude-plugin/
│   ├── plugin.json           # Marketplace plugin manifest
│   └── marketplace.json      # From marketplace.json.template
├── CLAUDE.md                 # From marketplace-claude.md.template
├── README.md                 # Marketplace documentation (manual)
│
└── {plugin-name}/            # Each corpus plugin
    ├── .claude-plugin/
    │   └── plugin.json       # From plugin.json.template
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md      # From navigate-skill.md.template
    ├── commands/
    │   └── navigate.md       # From navigate-command.md.template
    ├── data/
    │   ├── config.yaml       # From config.yaml.template
    │   ├── index.md          # Placeholder
    │   └── uploads/
    ├── references/
    │   └── project-awareness.md  # From project-awareness.md.template
    ├── .source/              # Gitignored
    ├── .cache/               # Gitignored
    ├── .gitignore            # From gitignore.template
    └── README.md             # From readme.md.template
```

**Marketplace-level files from templates:**

| File | Template |
|------|----------|
| `.claude-plugin/marketplace.json` | `marketplace.json.template` |
| `CLAUDE.md` | `marketplace-claude.md.template` |

**Per-plugin files from templates:**

| File | Template |
|------|----------|
| `.claude-plugin/plugin.json` | `plugin.json.template` |
| `skills/navigate/SKILL.md` | `navigate-skill.md.template` |
| `commands/navigate.md` | `navigate-command.md.template` |
| `data/config.yaml` | `config.yaml.template` |
| `references/project-awareness.md` | `project-awareness.md.template` |
| `.gitignore` | `gitignore.template` |
| `README.md` | `readme.md.template` |

---

## Add to Marketplace Structure (Existing Marketplace)

Adding a new corpus plugin to an existing marketplace.

**Existing structure:**
```
{marketplace-name}/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json      # UPDATE to add new plugin
├── CLAUDE.md
├── README.md
└── {existing-plugin}/        # Existing plugins...
```

**Add new plugin:**
```
{marketplace-name}/
└── {new-plugin-name}/        # New corpus plugin
    ├── .claude-plugin/
    │   └── plugin.json       # From plugin.json.template
    ├── skills/
    │   └── navigate/
    │       └── SKILL.md      # From navigate-skill.md.template
    ├── commands/
    │   └── navigate.md       # From navigate-command.md.template
    ├── data/
    │   ├── config.yaml       # From config.yaml.template
    │   ├── index.md          # Placeholder
    │   └── uploads/
    ├── references/
    │   └── project-awareness.md  # From project-awareness.md.template
    ├── .source/
    ├── .cache/
    ├── .gitignore            # From gitignore.template
    └── README.md             # From readme.md.template
```

**Files from templates:**

Same as per-plugin files in Multi-corpus structure above.

**Update existing:**
- Add entry to `.claude-plugin/marketplace.json`

---

## Key Differences from User-level/Repo-local Skills

| Aspect | Skills (user/repo-local) | Plugins (marketplace) |
|--------|--------------------------|----------------------|
| Navigate implementation | Single `SKILL.md` at root | Both `skills/navigate/SKILL.md` AND `commands/navigate.md` |
| Plugin manifest | None | `.claude-plugin/plugin.json` |
| Distribution | Local only | Publishable to marketplace |
| .gitignore | Parent handles | Own `.gitignore` file |

---

## Template Placeholder Quick Reference

| Placeholder | Description |
|-------------|-------------|
| `{{plugin_name}}` | Full plugin name (e.g., `hiivmind-corpus-polars`) |
| `{{project_display_name}}` | Human-readable name (e.g., `Polars`) |
| `{{corpus_short_name}}` | Short name for commands (e.g., `polars`) |
| `{{source_id}}` | Primary source ID (e.g., `polars`) |
| `{{keywords_sentence}}` | Keywords as sentence for skill description |
| `{{keyword_list}}` | Comma-separated keywords |
| `{{year}}` | Current year for LICENSE |

See `references/template-placeholders.md` for the complete reference.
