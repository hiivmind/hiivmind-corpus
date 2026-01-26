# Template Generation Patterns

Generate files from templates for different corpus destination types.

**Templates location:** `${CLAUDE_PLUGIN_ROOT}/templates/`
- Data-only templates: `templates/` (root)
- Legacy plugin templates: `templates/deprecated/`

---

## Corpus Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Data-only** | Just data files, no plugin structure | New architecture (recommended) |
| **User-level skill** | Simple skill in ~/.claude/skills | Legacy, personal use |
| **Plugin** | Full plugin with manifests | Legacy, distribution |

**Recommendation:** Use data-only structure for new corpora. Register via `.hiivmind/corpus/registry.yaml`.

---

## Data-Only Corpus (New Architecture)

Creates a minimal data repository without any Claude Code plugin structure.

**Context required:**
- `corpus_root` - Base directory for corpus
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Files to Generate

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `config.yaml.template` | `{corpus_root}/config.yaml` | Source configuration |
| `claude-data-only.md.template` | `{corpus_root}/CLAUDE.md` | Data-only CLAUDE.md |
| `readme-data-only.md.template` | `{corpus_root}/README.md` | Data-only README |
| `gitignore.template` | `{corpus_root}/.gitignore` | Git ignore rules |
| `license.template` | `{corpus_root}/LICENSE` | MIT license |

### Directories to Create

| Directory | Purpose |
|-----------|---------|
| `{corpus_root}/uploads/` | Local document uploads |

**Note:** `.source/` and `.cache/` are created on-demand by skills, not at init.

### Index Placeholder

Create `{corpus_root}/index.md` with content:

```markdown
# {{project_display_name}} Documentation Corpus

> Run `/hiivmind-corpus build` to build this index.

This corpus is not yet populated. Add documentation sources and build the index.
```

### Execution

```
Create directories:
  mkdir -p {corpus_root}/uploads

FOR each file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Replace {{year}} with current year
  4. Write result to {destination}

Create index placeholder manually (not from template)
```

### What's NOT Created

Data-only corpora do NOT have:
- `.claude-plugin/` directory
- `skills/` directory
- `commands/` directory
- `references/` directory
- Any navigate skill (handled by hiivmind-corpus plugin)

---

## Template Processing

For each template file:

1. **Read template** from `${CLAUDE_PLUGIN_ROOT}/templates/{template-name}`
2. **Replace placeholders** using context values:
   - `{{plugin_name}}` → `context.placeholders.plugin_name`
   - `{{project_name}}` → `context.placeholders.project_name`
   - `{{project_display_name}}` → `context.placeholders.project_display_name`
   - `{{corpus_short_name}}` → `context.placeholders.corpus_short_name`
   - `{{keyword_list}}` → `context.placeholders.keyword_list`
   - `{{keywords_sentence}}` → `context.placeholders.keywords_sentence`
   - `{{year}}` → Current year (e.g., "2026")
3. **Write output** to destination path

---

## User-level or Repo-local Skill (Legacy)

Creates a simple skill structure without plugin manifests. **Deprecated:** Use data-only architecture instead.

**Context required:**
- `skill_root` - Base directory for skill
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Files to Generate

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `deprecated/navigate-skill.md.template` | `{skill_root}/SKILL.md` | Navigate skill |
| `config.yaml.template` | `{skill_root}/data/config.yaml` | Source configuration |
| `deprecated/project-awareness.md.template` | `{skill_root}/references/project-awareness.md` | CLAUDE.md snippet |

### Index Placeholder

Create `{skill_root}/data/index.md` with content:

```markdown
# {{project_display_name}} Documentation Corpus

> Run `/hiivmind-corpus-build` to build this index.

This corpus is not yet populated. Add documentation sources and build the index.
```

### Execution

```
FOR each file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Write result to {destination}

Create index placeholder manually (not from template)
```

---

## Single-corpus Plugin (Legacy)

Creates a standalone plugin with manifests, commands, and skills. **Deprecated:** Use data-only architecture instead.

**Context required:**
- `plugin_root` - Base directory for plugin
- `skill_root` - Same as plugin_root for single-corpus
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Files to Generate

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `deprecated/plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` | Plugin manifest |
| `deprecated/navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` | Navigate skill |
| `deprecated/navigate-command.md.template` | `{plugin_root}/commands/navigate.md` | Navigate command |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` | Source configuration |
| `deprecated/project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` | CLAUDE.md snippet |
| `gitignore.template` | `{plugin_root}/.gitignore` | Git ignore rules |
| `deprecated/claude.md.template` | `{plugin_root}/CLAUDE.md` | Plugin CLAUDE.md |
| `license.template` | `{plugin_root}/LICENSE` | MIT license |
| `deprecated/readme.md.template` | `{plugin_root}/README.md` | Plugin documentation |

### Index Placeholder

Create `{plugin_root}/data/index.md` with content:

```markdown
# {{project_display_name}} Documentation Corpus

> Run `/hiivmind-corpus-build` to build this index.

This corpus is not yet populated. Add documentation sources and build the index.
```

### Execution

```
FOR each file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Replace {{year}} with current year
  4. Write result to {destination}

Create index placeholder manually (not from template)
```

---

## Multi-corpus Marketplace (New) - Legacy

Creates a new marketplace with the first plugin. **Deprecated:** Use data-only architecture instead.

**Context required:**
- `marketplace_root` - Base directory for marketplace
- `plugin_root` - Subdirectory for first plugin
- `skill_root` - Same as plugin_root
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Marketplace-level Files

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `deprecated/marketplace.json.template` | `{marketplace_root}/.claude-plugin/marketplace.json` | Marketplace registry |
| `deprecated/marketplace-claude.md.template` | `{marketplace_root}/CLAUDE.md` | Marketplace CLAUDE.md |

### Plugin-level Files

Same as Single-corpus Plugin (Legacy) section, but paths are under `{plugin_root}/` instead of root.

| Source Template | Destination |
|-----------------|-------------|
| `deprecated/plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` |
| `deprecated/navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` |
| `deprecated/navigate-command.md.template` | `{plugin_root}/commands/navigate.md` |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` |
| `deprecated/project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` |
| `gitignore.template` | `{plugin_root}/.gitignore` |
| `deprecated/readme.md.template` | `{plugin_root}/README.md` |

### Marketplace JSON Content

The `marketplace.json.template` should produce:

```json
{
  "plugins": [
    {
      "name": "{{plugin_name}}",
      "path": "{{plugin_name}}"
    }
  ]
}
```

### Execution

```
# Marketplace-level files first
FOR each marketplace file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Write result to {destination}

# Then plugin-level files
FOR each plugin file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Replace {{year}} with current year
  4. Write result to {destination}

Create index placeholder in {plugin_root}/data/index.md
```

---

## Multi-corpus Marketplace (Existing) - Legacy

Adds a new plugin to an existing marketplace. **Deprecated:** Use data-only architecture instead.

**Context required:**
- `marketplace_root` - Existing marketplace directory
- `plugin_root` - Subdirectory for new plugin
- `skill_root` - Same as plugin_root
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Plugin-level Files

Same as Plugin-level files in Multi-corpus Marketplace (New) - Legacy.

| Source Template | Destination |
|-----------------|-------------|
| `deprecated/plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` |
| `deprecated/navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` |
| `deprecated/navigate-command.md.template` | `{plugin_root}/commands/navigate.md` |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` |
| `deprecated/project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` |
| `gitignore.template` | `{plugin_root}/.gitignore` |
| `deprecated/readme.md.template` | `{plugin_root}/README.md` |

### Marketplace Registry Update

After generating plugin files, update `{marketplace_root}/.claude-plugin/marketplace.json`:

```
1. Read existing marketplace.json
2. Parse JSON
3. Add new plugin entry to plugins array:
   {
     "name": "{{plugin_name}}",
     "path": "{{plugin_name}}"
   }
4. Write updated JSON back
```

### Execution

```
# Generate plugin-level files
FOR each plugin file mapping:
  1. Read template from ${CLAUDE_PLUGIN_ROOT}/templates/{source}
  2. Replace all {{placeholder}} with context.placeholders values
  3. Replace {{year}} with current year
  4. Write result to {destination}

Create index placeholder in {plugin_root}/data/index.md

# Update marketplace registry (handled by update_marketplace_json action)
```

---

## Placeholder Reference

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{plugin_name}}` | `placeholders.plugin_name` | `hiivmind-corpus-polars` |
| `{{project_name}}` | `placeholders.project_name` | `polars` |
| `{{project_display_name}}` | `placeholders.project_display_name` | `Polars` |
| `{{corpus_short_name}}` | `placeholders.corpus_short_name` | `polars` |
| `{{keyword_list}}` | `placeholders.keyword_list` | `polars, dataframe, lazy` |
| `{{keywords_sentence}}` | `placeholders.keywords_sentence` | `polars, dataframe, or lazy` |
| `{{year}}` | Current year | `2026` |
| `{{version}}` | Default: `1.0.0` | `1.0.0` |

---

## Error Handling

If template generation fails:

1. **Template not found:** Report missing template path
2. **Write failed:** Report file system error and path
3. **Invalid placeholder:** Leave as-is (don't fail)

Partial generation is acceptable - validation gates will catch missing files.

---

## Related Documentation

- **Data-only templates:** `${CLAUDE_PLUGIN_ROOT}/templates/`
- **Legacy plugin templates:** `${CLAUDE_PLUGIN_ROOT}/templates/deprecated/`
- **Placeholder reference:** `${CLAUDE_PLUGIN_ROOT}/references/template-placeholders.md`
- **Marketplace structures:** `${CLAUDE_PLUGIN_ROOT}/references/marketplace-templates.md`
