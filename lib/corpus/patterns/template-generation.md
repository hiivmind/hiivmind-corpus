# Template Generation Patterns

Generate files from templates for different corpus destination types.

**Templates location:** `${CLAUDE_PLUGIN_ROOT}/templates/`

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

## User-level or Repo-local Skill

Creates a simple skill structure without plugin manifests.

**Context required:**
- `skill_root` - Base directory for skill
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Files to Generate

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `navigate-skill.md.template` | `{skill_root}/SKILL.md` | Navigate skill |
| `config.yaml.template` | `{skill_root}/data/config.yaml` | Source configuration |
| `project-awareness.md.template` | `{skill_root}/references/project-awareness.md` | CLAUDE.md snippet |

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

## Single-corpus Plugin

Creates a standalone plugin with manifests, commands, and skills.

**Context required:**
- `plugin_root` - Base directory for plugin
- `skill_root` - Same as plugin_root for single-corpus
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Files to Generate

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` | Plugin manifest |
| `navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` | Navigate skill |
| `navigate-command.md.template` | `{plugin_root}/commands/navigate.md` | Navigate command |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` | Source configuration |
| `project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` | CLAUDE.md snippet |
| `gitignore.template` | `{plugin_root}/.gitignore` | Git ignore rules |
| `claude.md.template` | `{plugin_root}/CLAUDE.md` | Plugin CLAUDE.md |
| `license.template` | `{plugin_root}/LICENSE` | MIT license |
| `readme.md.template` | `{plugin_root}/README.md` | Plugin documentation |

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

## Multi-corpus Marketplace (New)

Creates a new marketplace with the first plugin.

**Context required:**
- `marketplace_root` - Base directory for marketplace
- `plugin_root` - Subdirectory for first plugin
- `skill_root` - Same as plugin_root
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Marketplace-level Files

| Source Template | Destination | Description |
|-----------------|-------------|-------------|
| `marketplace.json.template` | `{marketplace_root}/.claude-plugin/marketplace.json` | Marketplace registry |
| `marketplace-claude.md.template` | `{marketplace_root}/CLAUDE.md` | Marketplace CLAUDE.md |

### Plugin-level Files

Same as Single-corpus Plugin section, but paths are under `{plugin_root}/` instead of root.

| Source Template | Destination |
|-----------------|-------------|
| `plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` |
| `navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` |
| `navigate-command.md.template` | `{plugin_root}/commands/navigate.md` |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` |
| `project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` |
| `gitignore.template` | `{plugin_root}/.gitignore` |
| `readme.md.template` | `{plugin_root}/README.md` |

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

## Multi-corpus Marketplace (Existing)

Adds a new plugin to an existing marketplace.

**Context required:**
- `marketplace_root` - Existing marketplace directory
- `plugin_root` - Subdirectory for new plugin
- `skill_root` - Same as plugin_root
- `placeholders` - Template placeholders object
- `corpus_name` - Corpus identifier

### Plugin-level Files

Same as Plugin-level files in Multi-corpus Marketplace (New).

| Source Template | Destination |
|-----------------|-------------|
| `plugin.json.template` | `{plugin_root}/.claude-plugin/plugin.json` |
| `navigate-skill.md.template` | `{plugin_root}/skills/navigate/SKILL.md` |
| `navigate-command.md.template` | `{plugin_root}/commands/navigate.md` |
| `config.yaml.template` | `{plugin_root}/data/config.yaml` |
| `project-awareness.md.template` | `{plugin_root}/references/project-awareness.md` |
| `gitignore.template` | `{plugin_root}/.gitignore` |
| `readme.md.template` | `{plugin_root}/README.md` |

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

- **Template files:** `${CLAUDE_PLUGIN_ROOT}/templates/`
- **Placeholder reference:** `${CLAUDE_PLUGIN_ROOT}/references/template-placeholders.md`
- **Marketplace structures:** `${CLAUDE_PLUGIN_ROOT}/references/marketplace-templates.md`
