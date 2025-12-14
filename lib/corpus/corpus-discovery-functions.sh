#!/usr/bin/env bash
# Corpus Discovery Functions
# Layer 2 primitives for finding installed hiivmind-corpus corpora
#
# Source this file to use: source corpus-discovery-functions.sh
#
# This domain handles:
# - User-level corpora (~/.claude/skills/)
# - Repo-local corpora (.claude-plugin/skills/)
# - Marketplace corpora (~/.claude/plugins/marketplaces/)
#
# Follows hiivmind-pulse-gh architecture principles:
# - Explicit scope prefixes (discover_, list_)
# - Pipe-first composition pattern
# - Single responsibility per function

set -euo pipefail

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

_get_corpus_script_dir() {
    local source="${BASH_SOURCE[0]}"
    while [ -h "$source" ]; do
        local dir
        dir=$(cd -P "$(dirname "$source")" && pwd)
        source=$(readlink "$source")
        [[ $source != /* ]] && source="$dir/$source"
    done
    cd -P "$(dirname "$source")" && pwd
}

# =============================================================================
# DISCOVERY PRIMITIVES
# =============================================================================
# Pattern: discover_{location}
# Purpose: Find corpora in specific locations
# Output: Pipe-delimited records: type|name|path

# Discover user-level corpora
# Location: ~/.claude/skills/hiivmind-corpus-*/
# Output: user-level|{name}|{path}
discover_user_level() {
    local skills_dir="${HOME}/.claude/skills"

    for d in "$skills_dir"/hiivmind-corpus-*/; do
        [ -d "$d" ] || continue
        local name
        name=$(basename "$d")
        echo "user-level|$name|$d"
    done
}

# Discover repo-local corpora (relative to current directory)
# Location: .claude-plugin/skills/hiivmind-corpus-*/
# Output: repo-local|{name}|{path}
discover_repo_local() {
    local base_dir="${1:-.}"

    for d in "$base_dir"/.claude-plugin/skills/hiivmind-corpus-*/; do
        [ -d "$d" ] || continue
        local name
        name=$(basename "$d")
        echo "repo-local|$name|$d"
    done
}

# Discover marketplace corpora (multi-corpus marketplaces)
# Location: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/
# Output: marketplace|{name}|{path}
discover_marketplace() {
    local marketplaces_dir="${HOME}/.claude/plugins/marketplaces"

    for d in "$marketplaces_dir"/*/hiivmind-corpus-*/; do
        [ -d "$d" ] || continue
        local name
        name=$(basename "$d")
        echo "marketplace|$name|$d"
    done
}

# Discover single-corpus marketplace plugins
# Location: ~/.claude/plugins/marketplaces/hiivmind-corpus-*/
# Output: marketplace-single|{name}|{path}
discover_marketplace_single() {
    local marketplaces_dir="${HOME}/.claude/plugins/marketplaces"

    for d in "$marketplaces_dir"/hiivmind-corpus-*/; do
        [ -d "$d" ] || continue
        # Skip if this is a multi-corpus marketplace (has child corpus dirs)
        if ls "$d"/hiivmind-corpus-*/ >/dev/null 2>&1; then
            continue
        fi
        local name
        name=$(basename "$d")
        echo "marketplace-single|$name|$d"
    done
}

# Discover all corpora across all locations
# Output: {type}|{name}|{path} for each corpus found
discover_all() {
    discover_user_level
    discover_repo_local "${1:-.}"
    discover_marketplace
    discover_marketplace_single
}

# =============================================================================
# LIST PRIMITIVES
# =============================================================================
# Pattern: list_{what}
# Purpose: Extract specific fields from discovery output
# Input: Pipe from discover_* functions
# Output: Single column of values

# List corpus names only
# Input: discover_* output
# Output: corpus names, one per line
list_names() {
    cut -d'|' -f2
}

# List corpus paths only
# Input: discover_* output
# Output: corpus paths, one per line
list_paths() {
    cut -d'|' -f3
}

# List corpus types only
# Input: discover_* output
# Output: corpus types, one per line
list_types() {
    cut -d'|' -f1
}

# =============================================================================
# FILTER PRIMITIVES
# =============================================================================
# Pattern: filter_{criteria}
# Purpose: Filter discovery output by criteria
# Input: Pipe from discover_* functions
# Output: Filtered records

# Filter to only built corpora (have real index.md)
# Input: discover_* output
# Output: Only corpora with built indexes
filter_built() {
    while IFS='|' read -r type name path; do
        local index_file="${path}data/index.md"
        if [ -f "$index_file" ]; then
            if ! grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
                echo "$type|$name|$path"
            fi
        fi
    done
}

# Filter to only placeholder corpora (need building)
# Input: discover_* output
# Output: Only corpora with placeholder indexes
filter_placeholder() {
    while IFS='|' read -r type name path; do
        local index_file="${path}data/index.md"
        if [ -f "$index_file" ]; then
            if grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
                echo "$type|$name|$path"
            fi
        fi
    done
}

# Filter to corpora matching a name pattern
# Args: pattern (grep regex)
# Input: discover_* output
# Output: Matching corpora
filter_name() {
    local pattern="$1"
    grep "|${pattern}|" || true
}

# =============================================================================
# COUNT PRIMITIVES
# =============================================================================
# Pattern: count_{what}
# Purpose: Count items
# Input: Pipe from discover_* or filter_* functions
# Output: Integer count

# Count records
count_corpora() {
    wc -l | tr -d ' '
}

# =============================================================================
# FORMAT PRIMITIVES
# =============================================================================
# Pattern: format_{style}
# Purpose: Transform output for display
# Input: Pipe from discover_* functions
# Output: Formatted text

# Format as simple list with status
# Input: discover_* output
# Output: name (type) - status
format_simple() {
    while IFS='|' read -r type name path; do
        local status="unknown"
        local index_file="${path}data/index.md"

        if [ -f "$index_file" ]; then
            if grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
                status="placeholder"
            else
                status="built"
            fi
        else
            status="no-index"
        fi

        echo "$name ($type) - $status"
    done
}

# Format as table row (pipe-delimited for further processing)
# Input: discover_* output
# Output: name|type|status|path
format_table() {
    while IFS='|' read -r type name path; do
        local status="unknown"
        local index_file="${path}data/index.md"

        if [ -f "$index_file" ]; then
            if grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
                status="placeholder"
            else
                status="built"
            fi
        else
            status="no-index"
        fi

        echo "$name|$type|$status|$path"
    done
}

# =============================================================================
# KEYWORD EXTRACTION
# =============================================================================
# Pattern: get_{what}
# Purpose: Extract corpus metadata for routing
# Input: Corpus path
# Output: Keyword data

# Get corpus keywords from config.yaml
# Falls back to inferring from corpus name if no keywords field
# Args: corpus_path
# Output: Comma-separated keywords
get_corpus_keywords() {
    local corpus_path="$1"
    local config_file="${corpus_path}data/config.yaml"

    # Try explicit keywords first (from corpus.keywords array)
    if [ -f "$config_file" ]; then
        local keywords
        keywords=$(yq -r '.corpus.keywords // empty | .[]?' "$config_file" 2>/dev/null | tr '\n' ',' | sed 's/,$//')

        if [ -n "$keywords" ]; then
            echo "$keywords"
            return 0
        fi
    fi

    # Fall back to name inference
    local name
    name=$(basename "$corpus_path" | sed 's/hiivmind-corpus-//' | tr '-' ',')
    echo "$name"
}

# Get corpus display name from config.yaml
# Falls back to corpus name if not set
# Args: corpus_path
# Output: Display name string
get_corpus_display_name() {
    local corpus_path="$1"
    local config_file="${corpus_path}data/config.yaml"

    if [ -f "$config_file" ]; then
        local display_name
        display_name=$(yq -r '.corpus.display_name // empty' "$config_file" 2>/dev/null)

        if [ -n "$display_name" ]; then
            echo "$display_name"
            return 0
        fi
    fi

    # Fall back to name from directory
    basename "$corpus_path" | sed 's/hiivmind-corpus-//' | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g'
}

# Format for routing (includes keywords for query matching)
# Input: discover_* output
# Output: name|display_name|keywords|status|path
format_routing() {
    while IFS='|' read -r type name path; do
        local status="unknown"
        local index_file="${path}data/index.md"

        if [ -f "$index_file" ]; then
            if grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
                status="placeholder"
            else
                status="built"
            fi
        else
            status="no-index"
        fi

        local display_name
        display_name=$(get_corpus_display_name "$path")

        local keywords
        keywords=$(get_corpus_keywords "$path")

        echo "$name|$display_name|$keywords|$status|$path"
    done
}
