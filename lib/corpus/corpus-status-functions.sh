#!/usr/bin/env bash
# Corpus Status Functions
# Layer 2 primitives for checking corpus status and freshness
#
# Source this file to use: source corpus-status-functions.sh
#
# This domain handles:
# - Index status (placeholder, built, no-index)
# - Freshness checking (stale detection)
# - Source tracking metadata
#
# Follows hiivmind-pulse-gh architecture principles:
# - Explicit scope prefixes (get_, check_, is_)
# - Pipe-first composition pattern
# - Single responsibility per function

set -euo pipefail

# =============================================================================
# STATUS PRIMITIVES
# =============================================================================
# Pattern: get_{status_type}
# Purpose: Retrieve status information
# Output: Status value to stdout

# Get corpus index status
# Args: corpus_path
# Output: "built" | "placeholder" | "no-index"
get_index_status() {
    local corpus_path="$1"
    local index_file="${corpus_path}/data/index.md"

    # Normalize path (remove trailing slash if present)
    index_file="${corpus_path%/}/data/index.md"

    if [ ! -f "$index_file" ]; then
        echo "no-index"
        return 0
    fi

    if grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
        echo "placeholder"
    else
        echo "built"
    fi
}

# Get indexed commit SHA for a git source
# Args: corpus_path, source_id
# Output: SHA string or empty if not found
get_indexed_sha() {
    local corpus_path="$1"
    local source_id="${2:-}"
    local config_file="${corpus_path%/}/data/config.yaml"

    if [ ! -f "$config_file" ]; then
        return 0
    fi

    if [ -n "$source_id" ]; then
        # Get SHA for specific source
        yq ".sources[] | select(.id == \"$source_id\") | .last_commit_sha // \"\"" "$config_file" 2>/dev/null || true
    else
        # Get SHA for first/primary source
        yq ".sources[0].last_commit_sha // \"\"" "$config_file" 2>/dev/null || true
    fi
}

# Get last indexed timestamp
# Args: corpus_path, source_id (optional)
# Output: ISO-8601 timestamp or empty
get_last_indexed() {
    local corpus_path="$1"
    local source_id="${2:-}"
    local config_file="${corpus_path%/}/data/config.yaml"

    if [ ! -f "$config_file" ]; then
        return 0
    fi

    if [ -n "$source_id" ]; then
        yq ".sources[] | select(.id == \"$source_id\") | .last_indexed_at // \"\"" "$config_file" 2>/dev/null || true
    else
        yq ".sources[0].last_indexed_at // \"\"" "$config_file" 2>/dev/null || true
    fi
}

# Get current HEAD SHA from local clone
# Args: corpus_path, source_id
# Output: SHA string or empty if no clone
get_clone_sha() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    if [ -d "$clone_path/.git" ]; then
        git -C "$clone_path" rev-parse HEAD 2>/dev/null || true
    fi
}

# Get source count
# Args: corpus_path
# Output: Integer count
get_source_count() {
    local corpus_path="$1"
    local config_file="${corpus_path%/}/data/config.yaml"

    if [ ! -f "$config_file" ]; then
        echo "0"
        return 0
    fi

    yq ".sources | length" "$config_file" 2>/dev/null || echo "0"
}

# =============================================================================
# CHECK PRIMITIVES
# =============================================================================
# Pattern: check_{condition}
# Purpose: Verify conditions
# Output: 0 (true) or 1 (false) exit code

# Check if corpus has a built index
# Args: corpus_path
# Returns: 0 if built, 1 otherwise
check_is_built() {
    local corpus_path="$1"
    local status
    status=$(get_index_status "$corpus_path")
    [ "$status" = "built" ]
}

# Check if corpus has sources configured
# Args: corpus_path
# Returns: 0 if has sources, 1 otherwise
check_has_sources() {
    local corpus_path="$1"
    local count
    count=$(get_source_count "$corpus_path")
    [ "$count" -gt 0 ]
}

# Check if a git source is stale (clone newer than indexed)
# Args: corpus_path, source_id
# Returns: 0 if stale, 1 if fresh or unknown
check_is_stale() {
    local corpus_path="$1"
    local source_id="$2"

    local indexed_sha
    local clone_sha

    indexed_sha=$(get_indexed_sha "$corpus_path" "$source_id")
    clone_sha=$(get_clone_sha "$corpus_path" "$source_id")

    # Can't determine staleness without both SHAs
    if [ -z "$indexed_sha" ] || [ -z "$clone_sha" ]; then
        return 1
    fi

    # Stale if SHAs differ
    [ "$indexed_sha" != "$clone_sha" ]
}

# =============================================================================
# FRESHNESS PRIMITIVES
# =============================================================================
# Pattern: fetch_{what}
# Purpose: Check upstream for updates
# Output: Status information

# Fetch upstream SHA without pulling
# Args: repo_url, branch (default: main)
# Output: SHA string
fetch_upstream_sha() {
    local repo_url="$1"
    local branch="${2:-main}"

    git ls-remote "$repo_url" "refs/heads/$branch" 2>/dev/null | cut -f1 || true
}

# Compare indexed vs upstream
# Args: corpus_path, source_id
# Output: "current" | "stale" | "unknown"
compare_freshness() {
    local corpus_path="$1"
    local source_id="$2"
    local config_file="${corpus_path%/}/data/config.yaml"

    if [ ! -f "$config_file" ]; then
        echo "unknown"
        return 0
    fi

    local repo_url branch indexed_sha upstream_sha

    repo_url=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_url // \"\"" "$config_file" 2>/dev/null)
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .branch // \"main\"" "$config_file" 2>/dev/null)
    indexed_sha=$(get_indexed_sha "$corpus_path" "$source_id")

    if [ -z "$repo_url" ] || [ -z "$indexed_sha" ]; then
        echo "unknown"
        return 0
    fi

    upstream_sha=$(fetch_upstream_sha "$repo_url" "$branch")

    if [ -z "$upstream_sha" ]; then
        echo "unknown"
    elif [ "$indexed_sha" = "$upstream_sha" ]; then
        echo "current"
    else
        echo "stale"
    fi
}

# =============================================================================
# REPORT PRIMITIVES
# =============================================================================
# Pattern: report_{what}
# Purpose: Generate status reports
# Output: Formatted text

# Report full corpus status
# Args: corpus_path
# Output: Multi-line status report
report_corpus_status() {
    local corpus_path="$1"
    local name
    name=$(basename "$corpus_path")

    echo "Corpus: $name"
    echo "Path: $corpus_path"
    echo "Index: $(get_index_status "$corpus_path")"
    echo "Sources: $(get_source_count "$corpus_path")"

    local last_indexed
    last_indexed=$(get_last_indexed "$corpus_path")
    if [ -n "$last_indexed" ]; then
        echo "Last indexed: $last_indexed"
    fi
}
