# Marketplace Templates Reference (Legacy)

> **⚠️ Deprecation Notice:** These structures are for legacy plugin-based corpora. For new corpora, use the **data-only architecture** (see `lib/corpus/patterns/template-generation.md`).
>
> Data-only corpora are simpler and preferred:
> - No `.claude-plugin/` directory needed
> - No `skills/` or `commands/` directories needed
> - Just `config.yaml` + `index.md` at the root
> - Navigation handled by the hiivmind-corpus plugin

Directory structures and template mappings for plugin-type corpora (single-corpus, multi-corpus, add to marketplace).

## Single-corpus Repo Structure (Legacy)

A standalone corpus plugin in its own repository. **Templates located in `templates/deprecated/`.**

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

**Files from templates (`templates/deprecated/`):**

| File | Template |
|------|----------|
| `.claude-plugin/plugin.json` | `deprecated/plugin.json.template` |
| `skills/navigate/SKILL.md` | `deprecated/navigate-skill.md.template` |
| `commands/navigate.md` | `deprecated/navigate-command.md.template` |
| `data/config.yaml` | `config.yaml.template` |
| `references/project-awareness.md` | `deprecated/project-awareness.md.template` |
| `.gitignore` | `gitignore.template` |
| `CLAUDE.md` | `deprecated/claude.md.template` |
| `LICENSE` | `license.template` |
| `README.md` | `deprecated/readme.md.template` |

**Create manually:**
- `data/index.md` - Simple placeholder

---

## Multi-corpus Repo Structure (New Marketplace) (Legacy)

A marketplace containing multiple corpus plugins as subdirectories. **Templates located in `templates/deprecated/`.**

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

**Marketplace-level files from templates (`templates/deprecated/`):**

| File | Template |
|------|----------|
| `.claude-plugin/marketplace.json` | `deprecated/marketplace.json.template` |
| `CLAUDE.md` | `deprecated/marketplace-claude.md.template` |

**Per-plugin files from templates (`templates/deprecated/`):**

| File | Template |
|------|----------|
| `.claude-plugin/plugin.json` | `deprecated/plugin.json.template` |
| `skills/navigate/SKILL.md` | `deprecated/navigate-skill.md.template` |
| `commands/navigate.md` | `deprecated/navigate-command.md.template` |
| `data/config.yaml` | `config.yaml.template` |
| `references/project-awareness.md` | `deprecated/project-awareness.md.template` |
| `.gitignore` | `gitignore.template` |
| `README.md` | `deprecated/readme.md.template` |

---

## Add to Marketplace Structure (Existing Marketplace) (Legacy)

Adding a new corpus plugin to an existing marketplace. **Templates located in `templates/deprecated/`.**

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

## Key Differences: Data-Only vs Legacy Structures

| Aspect | Data-Only (Recommended) | Skills (user/repo-local) | Plugins (marketplace) |
|--------|-------------------------|--------------------------|----------------------|
| Config location | `config.yaml` (root) | `data/config.yaml` | `data/config.yaml` |
| Index location | `index.md` (root) | `data/index.md` | `data/index.md` |
| Navigate implementation | Handled by hiivmind-corpus | Single `SKILL.md` at root | Both `skills/navigate/SKILL.md` AND `commands/navigate.md` |
| Plugin manifest | None needed | None | `.claude-plugin/plugin.json` |
| Distribution | Register via registry.yaml | Local only | Publishable to marketplace |
| Complexity | Minimal | Low | High |

**Recommendation:** Use data-only for all new corpora. Legacy structures are maintained for backward compatibility.

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
