# Template Placeholders Reference

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
