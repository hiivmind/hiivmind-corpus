#!/usr/bin/env bash
# Corpus Path Functions
# Layer 2 primitives for resolving corpus and source paths
#
# Source this file to use: source corpus-path-functions.sh
#
# This domain handles:
# - Corpus path resolution
# - Source path resolution (git, local, web)
# - Index file paths
# - Navigate skill paths
#
# Follows hiivmind-pulse-gh architecture principles:
# - Explicit scope prefixes (get_, resolve_)
# - Pipe-first composition pattern
# - Single responsibility per function

set -euo pipefail

# =============================================================================
# PATH RESOLUTION PRIMITIVES
# =============================================================================
# Pattern: get_{path_type}
# Purpose: Get specific paths within a corpus
# Output: Absolute path to stdout

# Get corpus data directory
# Args: corpus_path
# Output: /path/to/corpus/data/
get_data_path() {
    local corpus_path="$1"
    echo "${corpus_path%/}/data"
}

# Get corpus config file path
# Args: corpus_path
# Output: /path/to/corpus/data/config.yaml
get_config_path() {
    local corpus_path="$1"
    echo "${corpus_path%/}/data/config.yaml"
}

# Get corpus index file path
# Args: corpus_path
# Output: /path/to/corpus/data/index.md
get_index_path() {
    local corpus_path="$1"
    echo "${corpus_path%/}/data/index.md"
}

# Get corpus sub-index file path (for tiered indexes)
# Args: corpus_path, section_name
# Output: /path/to/corpus/data/index-{section}.md
get_subindex_path() {
    local corpus_path="$1"
    local section="$2"
    echo "${corpus_path%/}/data/index-${section}.md"
}

# Get project awareness file path
# Args: corpus_path
# Output: /path/to/corpus/data/project-awareness.md
get_awareness_path() {
    local corpus_path="$1"
    echo "${corpus_path%/}/data/project-awareness.md"
}

# Get source clone directory
# Args: corpus_path, source_id
# Output: /path/to/corpus/.source/{source_id}/
get_source_clone_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/.source/${source_id}"
}

# Get local uploads directory for a source
# Args: corpus_path, source_id
# Output: /path/to/corpus/data/uploads/{source_id}/
get_uploads_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/data/uploads/${source_id}"
}

# Get web cache directory for a source
# Args: corpus_path, source_id
# Output: /path/to/corpus/.cache/web/{source_id}/
get_web_cache_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/.cache/web/${source_id}"
}

# Get navigate skill path (for plugins)
# Args: corpus_path
# Output: /path/to/corpus/skills/navigate/SKILL.md or /path/to/corpus/SKILL.md
get_navigate_skill_path() {
    local corpus_path="$1"

    # Check plugin structure first
    local plugin_skill="${corpus_path%/}/skills/navigate/SKILL.md"
    if [ -f "$plugin_skill" ]; then
        echo "$plugin_skill"
        return 0
    fi

    # Fall back to user-level/repo-local structure
    local direct_skill="${corpus_path%/}/SKILL.md"
    if [ -f "$direct_skill" ]; then
        echo "$direct_skill"
        return 0
    fi

    # Return expected path even if doesn't exist
    echo "$plugin_skill"
}

# =============================================================================
# SOURCE PATH RESOLUTION
# =============================================================================
# Pattern: resolve_{source_type}_path
# Purpose: Resolve source references to actual file paths
# Output: Absolute path or URL

# Resolve a source:path reference to actual file path
# Args: corpus_path, source_ref (e.g., "polars:guides/intro.md")
# Output: Absolute file path
resolve_source_ref() {
    local corpus_path="$1"
    local source_ref="$2"

    # Parse source_ref format: source_id:relative_path
    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    local config_file
    config_file=$(get_config_path "$corpus_path")

    if [ ! -f "$config_file" ]; then
        echo "ERROR: Config not found: $config_file" >&2
        return 1
    fi

    local source_type
    source_type=$(yq ".sources[] | select(.id == \"$source_id\") | .type // \"\"" "$config_file" 2>/dev/null)

    case "$source_type" in
        git)
            local docs_root
            docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \".\"" "$config_file" 2>/dev/null)
            echo "$(get_source_clone_path "$corpus_path" "$source_id")/${docs_root}/${relative_path}"
            ;;
        local)
            echo "$(get_uploads_path "$corpus_path" "$source_id")/${relative_path}"
            ;;
        web)
            echo "$(get_web_cache_path "$corpus_path" "$source_id")/${relative_path}"
            ;;
        *)
            echo "ERROR: Unknown source type: $source_type" >&2
            return 1
            ;;
    esac
}

# Resolve source reference to raw GitHub URL (for remote access)
# Args: corpus_path, source_ref (e.g., "polars:guides/intro.md")
# Output: GitHub raw content URL
resolve_source_url() {
    local corpus_path="$1"
    local source_ref="$2"

    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    local config_file
    config_file=$(get_config_path "$corpus_path")

    if [ ! -f "$config_file" ]; then
        echo "ERROR: Config not found: $config_file" >&2
        return 1
    fi

    local source_type
    source_type=$(yq ".sources[] | select(.id == \"$source_id\") | .type // \"\"" "$config_file" 2>/dev/null)

    if [ "$source_type" != "git" ]; then
        echo "ERROR: URL resolution only works for git sources" >&2
        return 1
    fi

    local repo_url branch docs_root
    repo_url=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_url // \"\"" "$config_file" 2>/dev/null)
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .branch // \"main\"" "$config_file" 2>/dev/null)
    docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \".\"" "$config_file" 2>/dev/null)

    # Convert github.com URL to raw.githubusercontent.com
    local raw_base
    raw_base=$(echo "$repo_url" | sed 's|github.com|raw.githubusercontent.com|' | sed 's|\.git$||')

    echo "${raw_base}/${branch}/${docs_root}/${relative_path}"
}

# =============================================================================
# EXISTENCE CHECKS
# =============================================================================
# Pattern: exists_{what}
# Purpose: Check if paths exist
# Output: 0 (exists) or 1 (not exists) exit code

# Check if corpus has local clone for source
# Args: corpus_path, source_id
# Returns: 0 if exists, 1 otherwise
exists_clone() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path
    clone_path=$(get_source_clone_path "$corpus_path" "$source_id")
    [ -d "$clone_path/.git" ]
}

# Check if corpus has config file
# Args: corpus_path
# Returns: 0 if exists, 1 otherwise
exists_config() {
    local corpus_path="$1"
    local config_path
    config_path=$(get_config_path "$corpus_path")
    [ -f "$config_path" ]
}

# Check if corpus has index file
# Args: corpus_path
# Returns: 0 if exists, 1 otherwise
exists_index() {
    local corpus_path="$1"
    local index_path
    index_path=$(get_index_path "$corpus_path")
    [ -f "$index_path" ]
}

# Check if corpus has sub-indexes (tiered structure)
# Args: corpus_path
# Returns: 0 if has sub-indexes, 1 otherwise
exists_subindexes() {
    local corpus_path="$1"
    local data_path
    data_path=$(get_data_path "$corpus_path")
    ls "$data_path"/index-*.md >/dev/null 2>&1
}

# =============================================================================
# LIST PRIMITIVES
# =============================================================================
# Pattern: list_{what}
# Purpose: List items matching a pattern
# Output: One item per line

# List all sub-index files
# Args: corpus_path
# Output: Sub-index filenames (not full paths)
list_subindexes() {
    local corpus_path="$1"
    local data_path
    data_path=$(get_data_path "$corpus_path")

    for f in "$data_path"/index-*.md; do
        [ -f "$f" ] || continue
        basename "$f"
    done
}

# List all source IDs from config
# Args: corpus_path
# Output: Source IDs, one per line
list_source_ids() {
    local corpus_path="$1"
    local config_file
    config_file=$(get_config_path "$corpus_path")

    if [ -f "$config_file" ]; then
        yq '.sources[].id' "$config_file" 2>/dev/null || true
    fi
}
