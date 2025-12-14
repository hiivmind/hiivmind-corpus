# Corpus Library Index

Shell function library for hiivmind-corpus operations. Source these files in skills or commands.

## Quick Start

```bash
# Source all functions
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-status-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-path-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-context-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-source-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-scan-functions.sh"

# Discover all corpora
discover_all | format_table

# Check specific corpus
get_index_status "/path/to/corpus"

# Detect context for init
analyze_context  # → "established-project" | "fresh" | "marketplace-existing"

# Clone a source
clone_source "https://github.com/user/repo" "source-id" "/path/to/corpus"

# Scan for docs
count_docs "/path/to/source"
```

## Files

| File | Purpose |
|------|---------|
| `corpus-discovery-functions.sh` | Find installed corpora |
| `corpus-status-functions.sh` | Check corpus status and freshness |
| `corpus-path-functions.sh` | Resolve paths within corpora |
| `corpus-context-functions.sh` | Detect execution context for init |
| `corpus-source-functions.sh` | Git/local/web source operations |
| `corpus-scan-functions.sh` | File scanning and analysis |
| `corpus-index.md` | This documentation |

---

## corpus-discovery-functions.sh

### Discovery Primitives

| Function | Args | Output |
|----------|------|--------|
| `discover_user_level` | - | `user-level\|name\|path` per corpus |
| `discover_repo_local` | `[base_dir]` | `repo-local\|name\|path` per corpus |
| `discover_marketplace` | - | `marketplace\|name\|path` per corpus |
| `discover_marketplace_single` | - | `marketplace-single\|name\|path` per corpus |
| `discover_all` | `[base_dir]` | All corpora from all locations |

### List Primitives

Pipe from `discover_*` functions:

| Function | Input | Output |
|----------|-------|--------|
| `list_names` | discover output | Corpus names only |
| `list_paths` | discover output | Corpus paths only |
| `list_types` | discover output | Corpus types only |

### Filter Primitives

Pipe from `discover_*` functions:

| Function | Args | Output |
|----------|------|--------|
| `filter_built` | - | Only corpora with built indexes |
| `filter_placeholder` | - | Only corpora needing build |
| `filter_name` | `pattern` | Corpora matching name pattern |

### Keyword Extraction Primitives

| Function | Args | Output |
|----------|------|--------|
| `get_corpus_keywords` | `corpus_path` | Comma-separated keywords (from config or inferred) |
| `get_corpus_display_name` | `corpus_path` | Display name (from config or inferred) |

### Format Primitives

Pipe from `discover_*` functions:

| Function | Output |
|----------|--------|
| `format_simple` | `name (type) - status` |
| `format_table` | `name\|type\|status\|path` |
| `format_routing` | `name\|display_name\|keywords\|status\|path` |

### Count Primitives

| Function | Input | Output |
|----------|-------|--------|
| `count_corpora` | any piped input | Integer count |

### Examples

```bash
# List all built marketplace corpora
discover_marketplace | filter_built | list_names

# Count user-level corpora
discover_user_level | count_corpora

# Find polars corpus
discover_all | filter_name "polars"

# Format for display
discover_all | format_simple

# Get routing metadata for all corpora (per-session routing)
discover_all | format_routing
# Output: name|display_name|keywords|status|path

# Get keywords for a specific corpus
keywords=$(get_corpus_keywords "/path/to/corpus")
echo "Keywords: $keywords"  # e.g., "polars,dataframe,lazy,expression"
```

---

## corpus-status-functions.sh

### Status Primitives

| Function | Args | Output |
|----------|------|--------|
| `get_index_status` | `corpus_path` | `built` \| `placeholder` \| `no-index` |
| `get_indexed_sha` | `corpus_path`, `[source_id]` | SHA string |
| `get_last_indexed` | `corpus_path`, `[source_id]` | ISO-8601 timestamp |
| `get_clone_sha` | `corpus_path`, `source_id` | SHA of local clone HEAD |
| `get_source_count` | `corpus_path` | Integer count |

### Check Primitives

Return exit codes (0=true, 1=false):

| Function | Args | True When |
|----------|------|-----------|
| `check_is_built` | `corpus_path` | Index has real entries |
| `check_has_sources` | `corpus_path` | Has configured sources |
| `check_is_stale` | `corpus_path`, `source_id` | Clone newer than indexed |

### Freshness Primitives

| Function | Args | Output |
|----------|------|--------|
| `fetch_upstream_sha` | `repo_url`, `[branch]` | SHA from remote |
| `compare_freshness` | `corpus_path`, `source_id` | `current` \| `stale` \| `unknown` |

### Report Primitives

| Function | Args | Output |
|----------|------|--------|
| `report_corpus_status` | `corpus_path` | Multi-line status report |

### Examples

```bash
# Check if corpus is built
if check_is_built "/path/to/corpus"; then
    echo "Ready to navigate"
fi

# Compare with upstream
freshness=$(compare_freshness "/path/to/corpus" "polars")
if [ "$freshness" = "stale" ]; then
    echo "Updates available"
fi

# Full status report
report_corpus_status "/path/to/corpus"
```

---

## corpus-path-functions.sh

### Path Resolution Primitives

| Function | Args | Output |
|----------|------|--------|
| `get_data_path` | `corpus_path` | `/path/to/corpus/data` |
| `get_config_path` | `corpus_path` | `/path/to/corpus/data/config.yaml` |
| `get_index_path` | `corpus_path` | `/path/to/corpus/data/index.md` |
| `get_subindex_path` | `corpus_path`, `section` | `/path/to/corpus/data/index-{section}.md` |
| `get_awareness_path` | `corpus_path` | `/path/to/corpus/data/project-awareness.md` |
| `get_source_clone_path` | `corpus_path`, `source_id` | `/path/to/corpus/.source/{source_id}` |
| `get_uploads_path` | `corpus_path`, `source_id` | `/path/to/corpus/data/uploads/{source_id}` |
| `get_web_cache_path` | `corpus_path`, `source_id` | `/path/to/corpus/.cache/web/{source_id}` |
| `get_navigate_skill_path` | `corpus_path` | Path to navigate SKILL.md |

### Source Resolution Primitives

| Function | Args | Output |
|----------|------|--------|
| `resolve_source_ref` | `corpus_path`, `source:path` | Absolute file path |
| `resolve_source_url` | `corpus_path`, `source:path` | GitHub raw URL |

### Existence Checks

Return exit codes (0=exists, 1=not exists):

| Function | Args | True When |
|----------|------|-----------|
| `exists_clone` | `corpus_path`, `source_id` | Local clone exists |
| `exists_config` | `corpus_path` | Config file exists |
| `exists_index` | `corpus_path` | Index file exists |
| `exists_subindexes` | `corpus_path` | Has tiered index files |

### List Primitives

| Function | Args | Output |
|----------|------|--------|
| `list_subindexes` | `corpus_path` | Sub-index filenames |
| `list_source_ids` | `corpus_path` | Source IDs from config |

### Examples

```bash
# Read corpus index
cat "$(get_index_path "$corpus_path")"

# Check if has local clone
if exists_clone "$corpus_path" "polars"; then
    cat "$(resolve_source_ref "$corpus_path" "polars:guides/intro.md")"
else
    # Fetch from GitHub
    curl -s "$(resolve_source_url "$corpus_path" "polars:guides/intro.md")"
fi

# List all sources
for source_id in $(list_source_ids "$corpus_path"); do
    echo "Source: $source_id"
done
```

---

## Dependencies

- `bash` 4.0+
- `yq` 4.0+ (for YAML parsing in status/path functions)
- `git` (for clone operations in status functions)

---

## corpus-context-functions.sh

Context detection for `hiivmind-corpus-init` routing.

### Detection Primitives

Return exit codes (0=true, 1=false):

| Function | True When |
|----------|-----------|
| `detect_is_git_repo` | Current dir is in a git repo |
| `detect_is_marketplace` | Has `.claude-plugin/marketplace.json` |
| `detect_is_corpus` | Has `data/config.yaml` |
| `detect_has_corpus_plugins` | Has `hiivmind-corpus-*/` subdirs |
| `detect_is_project` | Has project files (package.json, etc.) |
| `detect_is_fresh` | Empty or near-empty directory |
| `detect_is_plugin` | Has `.claude-plugin/plugin.json` |

### Analysis Primitives

| Function | Args | Output |
|----------|------|--------|
| `analyze_context` | - | `established-project` \| `fresh` \| `marketplace-existing` \| `corpus` |
| `get_destination_options` | - | Space-separated destination types |
| `get_repo_root` | - | Absolute path to git root |
| `get_project_type` | - | `python` \| `node` \| `rust` \| `go` \| `java` \| `unknown` |

### Path Resolution

| Function | Args | Output |
|----------|------|--------|
| `resolve_user_level_path` | `skill_name` | `~/.claude/skills/{name}` |
| `resolve_repo_local_path` | `skill_name` | `{repo}/.claude-plugin/skills/{name}` |
| `resolve_single_corpus_path` | - | Current directory |
| `resolve_multi_corpus_path` | `plugin_name` | `{pwd}/{name}` |

### Scaffold Primitives

| Function | Args | Output |
|----------|------|--------|
| `scaffold_user_level` | `skill_name` | Created path |
| `scaffold_repo_local` | `skill_name` | Created path |
| `scaffold_single_corpus` | - | Created path |
| `scaffold_multi_corpus` | `marketplace_name`, `plugin_name` | Plugin path |
| `scaffold_add_to_marketplace` | `plugin_name` | Plugin path |

### Verification Primitives

| Function | Args | Returns |
|----------|------|---------|
| `verify_skill_structure` | `skill_path` | 0 if valid, 1 with errors to stderr |
| `verify_plugin_structure` | `plugin_path` | 0 if valid, 1 with errors to stderr |
| `verify_marketplace_structure` | `marketplace_path` | 0 if valid, 1 with errors to stderr |

### Examples

```bash
# Determine context and options
context=$(analyze_context)
echo "Context: $context"
echo "Options: $(get_destination_options)"

# Scaffold based on choice
if [ "$choice" = "user-level" ]; then
    path=$(scaffold_user_level "hiivmind-corpus-polars")
fi

# Verify result
verify_skill_structure "$path" || echo "Structure incomplete"
```

---

## corpus-source-functions.sh

Git, local, and web source management.

### Clone Primitives

| Function | Args | Output |
|----------|------|--------|
| `clone_source` | `repo_url`, `source_id`, `[corpus_path]` | Clone path |
| `clone_source_branch` | `repo_url`, `source_id`, `branch`, `[corpus_path]` | Clone path |

### Git Tracking Primitives

| Function | Args | Output |
|----------|------|--------|
| `get_source_sha` | `corpus_path`, `source_id` | Full HEAD SHA |
| `get_source_sha_short` | `corpus_path`, `source_id` | Short SHA (7 chars) |
| `get_source_branch` | `corpus_path`, `source_id` | Branch name |
| `get_source_remote_url` | `corpus_path`, `source_id` | Remote URL |

### Update Primitives

| Function | Args | Output |
|----------|------|--------|
| `fetch_source` | `corpus_path`, `source_id` | (fetches, no output) |
| `pull_source` | `corpus_path`, `source_id` | New HEAD SHA |
| `fetch_upstream_sha` | `repo_url`, `[branch]` | Remote SHA |

### Comparison Primitives

| Function | Args | Output |
|----------|------|--------|
| `get_commit_log` | `corpus_path`, `source_id`, `from_sha`, `to_sha`, `[docs_path]` | Oneline log |
| `get_file_changes` | `corpus_path`, `source_id`, `from_sha`, `to_sha`, `[docs_path]` | A/M/D/R + path |
| `count_commits` | `corpus_path`, `source_id`, `from_sha`, `to_sha` | Integer count |
| `compare_clone_to_indexed` | `corpus_path`, `source_id`, `indexed_sha` | `current` \| `ahead` \| `behind` \| `diverged` |

### Local Source Primitives

| Function | Args | Output |
|----------|------|--------|
| `setup_local_source` | `corpus_path`, `source_id` | Uploads path |
| `list_local_files` | `corpus_path`, `source_id` | File paths |
| `count_local_files` | `corpus_path`, `source_id` | Integer count |

### Web Source Primitives

| Function | Args | Output |
|----------|------|--------|
| `setup_web_source` | `corpus_path`, `source_id` | Cache path |
| `generate_cache_filename` | `url` | Filename (slug.md) |
| `list_web_cache` | `corpus_path`, `source_id` | File paths |
| `get_cache_age` | `corpus_path`, `source_id`, `filename` | Age in days |

### Existence Checks

| Function | Args | True When |
|----------|------|-----------|
| `exists_git_source` | `corpus_path`, `source_id` | Clone exists |
| `exists_local_source` | `corpus_path`, `source_id` | Has uploaded files |
| `exists_web_source` | `corpus_path`, `source_id` | Has cached files |

### URL Parsing

| Function | Args | Output |
|----------|------|--------|
| `parse_repo_owner` | `repo_url` | Owner name |
| `parse_repo_name` | `repo_url` | Repo name |
| `generate_source_id` | `repo_url` | Lowercase source ID |

### Examples

```bash
# Clone a new source
clone_path=$(clone_source "https://github.com/pola-rs/polars" "polars" "$corpus_path")
sha=$(get_source_sha "$corpus_path" "polars")

# Check for updates
fetch_source "$corpus_path" "polars"
status=$(compare_clone_to_indexed "$corpus_path" "polars" "$indexed_sha")
if [ "$status" = "ahead" ]; then
    echo "$(count_commits "$corpus_path" "polars" "$indexed_sha" "HEAD") new commits"
    get_file_changes "$corpus_path" "polars" "$indexed_sha" "HEAD" "docs/"
fi
```

---

## corpus-scan-functions.sh

File discovery and documentation analysis.

### File Discovery Primitives

| Function | Args | Output |
|----------|------|--------|
| `scan_docs` | `path` | All .md/.mdx file paths |
| `scan_docs_ext` | `path`, `extension` | Files with specific extension |
| `count_docs` | `path` | Integer count |
| `find_docs_matching` | `path`, `pattern` | Matching file paths |
| `list_doc_sections` | `path` | Top-level directory names |

### Framework Detection

| Function | Args | Output |
|----------|------|--------|
| `detect_doc_framework` | `source_path` | `docusaurus` \| `mkdocs` \| `sphinx` \| `vitepress` \| `nextra` \| `mdbook` \| `antora` \| `unknown` |
| `find_nav_config` | `source_path` | Path to navigation config file |
| `detect_frontmatter_type` | `source_path` | `yaml` \| `toml` \| `none` |

### Large File Detection

| Function | Args | Output |
|----------|------|--------|
| `find_large_files` | `path`, `[min_lines]` | `path\|lines` per file |
| `find_schema_files` | `path` | GraphQL/OpenAPI/JSON Schema paths |
| `get_file_lines` | `file_path` | Line count |
| `is_large_file` | `file_path`, `[threshold]` | Exit code (0=large) |
| `suggest_grep_pattern` | `file_path` | Suggested grep command |

### Content Analysis

| Function | Args | Output |
|----------|------|--------|
| `sample_frontmatter` | `file_path` | YAML frontmatter content |
| `sample_file` | `file_path`, `[num_lines]` | First N lines |
| `extract_title` | `file_path` | Title from frontmatter or H1 |
| `extract_description` | `file_path` | Description from frontmatter or first paragraph |

### Index Structure

| Function | Args | Output |
|----------|------|--------|
| `detect_tiered_index` | `corpus_path` | Exit code (0=tiered) |
| `list_subindex_files` | `corpus_path` | Sub-index filenames |
| `count_index_entries` | `index_file` | Approximate entry count |
| `extract_index_sections` | `index_file` | Section headings |

### Batch Scanning

| Function | Args | Output |
|----------|------|--------|
| `scan_all_sources` | `corpus_path` | `source_id\|count\|path` per source |
| `count_all_docs` | `corpus_path` | Total doc count across all sources |

### Examples

```bash
# Analyze a source
framework=$(detect_doc_framework ".source/polars")
echo "Framework: $framework"
echo "Doc count: $(count_docs ".source/polars/docs")"
echo "Sections: $(list_doc_sections ".source/polars/docs")"

# Find large files that need GREP markers
find_large_files ".source/polars" 1000 | while IFS='|' read -r path lines; do
    echo "Large file: $path ($lines lines)"
    echo "Suggest: $(suggest_grep_pattern "$path")"
done

# Check if tiered indexing needed
total=$(count_all_docs "$corpus_path")
if [ "$total" -gt 500 ]; then
    echo "Recommend tiered indexing ($total files)"
fi
```

---

## Architecture Notes

Functions follow the hiivmind-pulse-gh patterns:

1. **Explicit prefixes**: `discover_`, `get_`, `check_`, `filter_`, `format_`, `list_`, `count_`, `detect_`, `scan_`, `clone_`, `fetch_`, `pull_`, `parse_`, `scaffold_`, `verify_`
2. **Pipe-first composition**: Most functions accept piped input or produce pipeable output
3. **Single responsibility**: Each function does one thing
4. **Exit codes for booleans**: `check_*`, `exists_*`, `detect_*`, and `is_*` use exit codes, not stdout
5. **Consistent arg ordering**: `corpus_path` first, then `source_id`, then optional args
