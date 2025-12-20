# Template Placeholders Reference

Complete list of placeholders used in hiivmind-corpus templates.

## Core Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{plugin_name}}` | Full plugin name with prefix | `hiivmind-corpus-polars` |
| `{{project_name}}` | Project name (lowercase) | `polars` |
| `{{project_display_name}}` | Human-readable project name | `Polars` |
| `{{corpus_short_name}}` | Short name for commands | `polars` |

## Source Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{source_id}}` | Primary source identifier | `polars` |
| `{{repo_url}}` | Git repository URL | `https://github.com/pola-rs/polars` |
| `{{repo_owner}}` | Repository owner/org | `pola-rs` |
| `{{repo_name}}` | Repository name | `polars` |
| `{{branch}}` | Default branch | `main` |
| `{{docs_root}}` | Documentation root path | `docs/source` |

## Keyword Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{keywords_sentence}}` | Keywords as natural sentence | `Polars DataFrames, lazy evaluation, or expressions` |
| `{{keyword_list}}` | Comma-separated keyword list | `polars, dataframe, lazy, expression, series` |

## Metadata Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{year}}` | Current year (for LICENSE) | `2025` |
| `{{description}}` | Marketplace description | `Data processing library corpora` |
| `{{plugin_description}}` | Per-plugin description | `Polars documentation corpus` |
| `{{version}}` | Plugin version | `1.0.0` |

## Template Usage

### navigate-skill.md.template

```yaml
---
name: {{plugin_name}}-navigate
description: This skill answers questions about {{project_display_name}} documentation. Use when user asks about {{keywords_sentence}}. Triggers: {{keyword_list}}.
---
```

### navigate-command.md.template

```yaml
---
description: Ask questions about {{project_display_name}} documentation
argument-hint: Your question (e.g., "how does X work?", "API reference for Y")
---
```

### config.yaml.template

```yaml
corpus:
  name: "{{project_name}}"
  display_name: "{{project_display_name}}"
  keywords:
    - {{keyword_list}}

sources:
  - id: "{{source_id}}"
    type: "git"
    repo_url: "{{repo_url}}"
    branch: "{{branch}}"
    docs_root: "{{docs_root}}"
```

### plugin.json.template

```json
{
  "name": "{{plugin_name}}",
  "description": "{{plugin_description}}",
  "version": "{{version}}"
}
```

### license.template

```
MIT License

Copyright (c) {{year}} ...
```

## Deriving Values

### From Repository URL

Given: `https://github.com/pola-rs/polars`

| Derived | Value |
|---------|-------|
| `{{repo_owner}}` | `pola-rs` |
| `{{repo_name}}` | `polars` |
| `{{project_name}}` | `polars` |
| `{{plugin_name}}` | `hiivmind-corpus-polars` |
| `{{source_id}}` | `polars` |

### From User Input

These must be provided or confirmed by the user:

| Placeholder | Source |
|-------------|--------|
| `{{project_display_name}}` | Ask user or capitalize project_name |
| `{{docs_root}}` | Detect from repo or ask user |
| `{{keywords_sentence}}` | Suggest based on project, user confirms |
| `{{keyword_list}}` | Suggest based on project, user confirms |
