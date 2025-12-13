# Corpus Library Index

Shell function library for hiivmind-corpus operations. Source these files in skills or commands.

## Quick Start

```bash
# Source all functions
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-status-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-path-functions.sh"

# Discover all corpora
discover_all | format_table

# Check specific corpus
get_index_status "/path/to/corpus"
```

## Files

| File | Purpose |
|------|---------|
| `corpus-discovery-functions.sh` | Find installed corpora |
| `corpus-status-functions.sh` | Check corpus status and freshness |
| `corpus-path-functions.sh` | Resolve paths within corpora |
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

### Format Primitives

Pipe from `discover_*` functions:

| Function | Output |
|----------|--------|
| `format_simple` | `name (type) - status` |
| `format_table` | `name\|type\|status\|path` |

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

## Architecture Notes

Functions follow the hiivmind-pulse-gh patterns:

1. **Explicit prefixes**: `discover_`, `get_`, `check_`, `filter_`, `format_`, `list_`, `count_`
2. **Pipe-first composition**: Most functions accept piped input or produce pipeable output
3. **Single responsibility**: Each function does one thing
4. **Exit codes for booleans**: `check_*` and `exists_*` use exit codes, not stdout
