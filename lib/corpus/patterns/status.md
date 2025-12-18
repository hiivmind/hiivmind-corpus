# Pattern: Status

## Purpose

Check corpus index status and source freshness. Determine if a corpus is built, needs building, or has stale content.

## When to Use

- Before refresh operations (to show what needs updating)
- During discovery (to report corpus health)
- When navigating (to warn about stale content)
- To decide between build vs refresh

## Prerequisites

- **Tool detection** (see `tool-detection.md`) - For YAML parsing and git operations
- **Config parsing** (see `config-parsing.md`) - For reading source metadata
- Corpus exists with `data/config.yaml`

## Index Status Types

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `built` | Index has real content | Can navigate, may need refresh |
| `placeholder` | Index only has template text | Needs `hiivmind-corpus-build` |
| `no-index` | Index file missing | Needs `hiivmind-corpus-build` |

---

## Status Detection Patterns

### Get Index Status

**Algorithm:**
1. Check if `data/index.md` exists
2. If missing → `no-index`
3. If contains "Run hiivmind-corpus-build" → `placeholder`
4. Otherwise → `built`

**Using bash:**
```bash
get_index_status() {
    local corpus_path="$1"
    local index_file="${corpus_path%/}/data/index.md"

    if [ ! -f "$index_file" ]; then
        echo "no-index"
    elif grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
        echo "placeholder"
    else
        echo "built"
    fi
}
```

**Using Claude tools:**
```
Read: {corpus_path}/data/index.md
Check content for "Run hiivmind-corpus-build"
```

---

### Check If Corpus Is Built

**Algorithm:**
1. Get index status
2. Return true only if status is `built`

**Using bash:**
```bash
check_is_built() {
    local status
    status=$(get_index_status "$1")
    [ "$status" = "built" ]
}

# Usage
if check_is_built "/path/to/corpus"; then
    echo "Ready to navigate"
fi
```

---

### Check If Has Sources Configured

**Algorithm:**
1. Read `sources` array from config.yaml
2. Return true if length > 0

**Using yq:**
```bash
check_has_sources() {
    local corpus_path="$1"
    local count
    count=$(yq '.sources | length' "${corpus_path%/}/data/config.yaml" 2>/dev/null)
    [ "${count:-0}" -gt 0 ]
}
```

**Using Python:**
```bash
python3 -c "
import yaml
import sys
sources = yaml.safe_load(open('$1/data/config.yaml')).get('sources', [])
sys.exit(0 if len(sources) > 0 else 1)
"
```

---

## Freshness Checking

### Source Freshness States

| State | Meaning | How Detected |
|-------|---------|--------------|
| `current` | Indexed SHA matches upstream | SHA comparison |
| `stale` | Upstream has newer commits | SHA differs |
| `unknown` | Cannot determine (no clone, no SHA) | Missing data |

---

### Get Indexed SHA

Read the last indexed commit SHA for a git source.

**Using yq:**
```bash
# For specific source
yq '.sources[] | select(.id == "polars") | .last_commit_sha // ""' data/config.yaml

# For first/primary source
yq '.sources[0].last_commit_sha // ""' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('data/config.yaml')).get('sources', [])
source = next((s for s in sources if s.get('id') == 'polars'), {})
print(source.get('last_commit_sha', ''))
"
```

---

### Get Clone SHA

Read current HEAD from local git clone.

**Using bash:**
```bash
get_clone_sha() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    if [ -d "$clone_path/.git" ]; then
        git -C "$clone_path" rev-parse HEAD 2>/dev/null
    fi
}
```

---

### Fetch Upstream SHA (Without Pulling)

Check remote for latest commit without modifying local clone.

**Using bash (requires git):**
```bash
fetch_upstream_sha() {
    local repo_url="$1"
    local branch="${2:-main}"

    git ls-remote "$repo_url" "refs/heads/$branch" 2>/dev/null | cut -f1
}
```

**Example:**
```bash
upstream=$(fetch_upstream_sha "https://github.com/pola-rs/polars" "main")
echo "Upstream HEAD: $upstream"
```

---

### Compare Freshness

Compare indexed SHA against upstream.

**Algorithm:**
1. Read indexed SHA from config
2. Fetch upstream SHA
3. Compare and return status

**Using bash:**
```bash
compare_freshness() {
    local corpus_path="$1"
    local source_id="$2"
    local config_file="${corpus_path%/}/data/config.yaml"

    # Get source info
    local repo_url branch indexed_sha

    repo_url=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_url // \"\"" "$config_file")
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .branch // \"main\"" "$config_file")
    indexed_sha=$(yq ".sources[] | select(.id == \"$source_id\") | .last_commit_sha // \"\"" "$config_file")

    if [ -z "$repo_url" ] || [ -z "$indexed_sha" ]; then
        echo "unknown"
        return
    fi

    local upstream_sha
    upstream_sha=$(git ls-remote "$repo_url" "refs/heads/$branch" 2>/dev/null | cut -f1)

    if [ -z "$upstream_sha" ]; then
        echo "unknown"
    elif [ "$indexed_sha" = "$upstream_sha" ]; then
        echo "current"
    else
        echo "stale"
    fi
}
```

---

### Check If Clone Is Stale

Compare local clone HEAD against indexed SHA.

**Algorithm:**
1. Get indexed SHA from config
2. Get clone HEAD SHA
3. Return true if they differ

**Using bash:**
```bash
check_is_stale() {
    local corpus_path="$1"
    local source_id="$2"

    local indexed_sha clone_sha

    indexed_sha=$(yq ".sources[] | select(.id == \"$source_id\") | .last_commit_sha // \"\"" "${corpus_path%/}/data/config.yaml")
    clone_sha=$(git -C "${corpus_path%/}/.source/$source_id" rev-parse HEAD 2>/dev/null)

    # Can't determine without both
    [ -z "$indexed_sha" ] || [ -z "$clone_sha" ] && return 1

    # Stale if different
    [ "$indexed_sha" != "$clone_sha" ]
}
```

---

## Generated-Docs Freshness Checking

Generated-docs sources track a source repository for change detection.
Unlike git sources (which have docs IN the repo), generated-docs have:
- Source repo: Code that generates the docs (tracked for freshness)
- Web output: Rendered docs site (fetched live when needed)

### Source Freshness States (Generated-Docs)

| State | Meaning | Implication |
|-------|---------|-------------|
| `current` | Source repo SHA unchanged | Docs likely unchanged |
| `stale` | Source repo has new commits | Docs may have been regenerated |
| `unknown` | Cannot check source repo | Network issue or missing config |

**Important:** "Stale" means the *source* changed, not the web output. There may be a lag between source commits and doc site rebuild (CI/CD pipeline time).

---

### Check Generated-Docs Freshness

**Algorithm:**
1. Read `source_repo.last_commit_sha` from config
2. Fetch upstream SHA from `source_repo.url`
3. Compare and return status

**Using bash:**
```bash
check_generated_docs_freshness() {
    local corpus_path="$1"
    local source_id="$2"
    local config_file="${corpus_path%/}/data/config.yaml"

    # Get source_repo fields (nested under source_repo)
    local source_url branch indexed_sha
    source_url=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.url // \"\"" "$config_file")
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.branch // \"main\"" "$config_file")
    indexed_sha=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.last_commit_sha // \"\"" "$config_file")

    if [ -z "$source_url" ] || [ -z "$indexed_sha" ]; then
        echo "unknown"
        return
    fi

    local upstream_sha
    upstream_sha=$(git ls-remote "$source_url" "refs/heads/$branch" 2>/dev/null | cut -f1)

    if [ -z "$upstream_sha" ]; then
        echo "unknown"
    elif [ "$indexed_sha" = "$upstream_sha" ]; then
        echo "current"
    else
        echo "stale"
    fi
}
```

---

### Generated-Docs Status Report Format

**Sample output:**
```
Source: gh-cli-manual (generated-docs)
  Source repo: https://github.com/cli/cli
  Branch: trunk
  Indexed SHA: abc123... (2025-01-10)
  Upstream SHA: def456...
  Source status: STALE (15 commits behind)
  Web output: https://cli.github.com/manual
  URLs discovered: 165
  Note: Source changed - docs may have been regenerated
```

**Key differences from git source report:**
- Reports "Source status" not "Index status"
- Shows web output URL
- Includes note about source → docs relationship

---

## Timestamp Checking

### Get Last Indexed Timestamp

**Using yq:**
```bash
yq '.sources[] | select(.id == "polars") | .last_indexed_at // ""' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('data/config.yaml')).get('sources', [])
source = next((s for s in sources if s.get('id') == 'polars'), {})
print(source.get('last_indexed_at', ''))
"
```

### Calculate Age

**Using bash:**
```bash
# Get days since last indexed
last_indexed="2025-01-15T10:00:00Z"
last_epoch=$(date -d "$last_indexed" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_indexed" +%s)
now_epoch=$(date +%s)
age_days=$(( (now_epoch - last_epoch) / 86400 ))
echo "Last indexed $age_days days ago"
```

---

## Tiered Index Detection

### Check for Tiered Index

**Algorithm:**
1. Look for `data/index-*.md` files
2. If found, corpus uses tiered indexing

**Using bash:**
```bash
detect_tiered_index() {
    local corpus_path="$1"
    ls "${corpus_path%/}"/data/index-*.md >/dev/null 2>&1
}

# Usage
if detect_tiered_index "/path/to/corpus"; then
    echo "Tiered index structure"
fi
```

**Using Claude tools:**
```
Glob: {corpus_path}/data/index-*.md
```

### List Sub-Indexes

**Using bash:**
```bash
list_subindex_files() {
    local corpus_path="$1"
    ls "${corpus_path%/}"/data/index-*.md 2>/dev/null | xargs -n1 basename
}
```

---

## Status Reporting

### Full Corpus Status Report

**Output format:**
```
Corpus: hiivmind-corpus-polars
Path: ~/.claude/skills/hiivmind-corpus-polars/
Index: built
Index Structure: tiered (index.md + 3 sub-indexes)
Sources: 1

Source: polars (git)
  Indexed SHA: abc123...
  Indexed at: 2025-01-15T10:00:00Z
  Freshness: stale (upstream: def456...)
  Changes: 15 commits ahead
```

**Algorithm:**
1. Get index status
2. Detect tiered structure
3. Get source count
4. For each source:
   - Get indexed SHA and timestamp
   - Compare with upstream (if git source)
   - Report freshness

---

## Cross-Platform Notes

| Operation | Unix | Windows |
|-----------|------|---------|
| Git commands | `git -C path` | Same |
| Date parsing | `date -d` (GNU) or `date -j` (BSD) | PowerShell: `[datetime]::Parse()` |
| File existence | `[ -f file ]` | `Test-Path file` |

---

## Error Handling

### Config Not Found

```
Cannot check status: data/config.yaml not found.

This corpus may not be properly initialized.
```

### Git Not Available

```
Cannot check upstream freshness: git is not installed.

To check source freshness, install git:
- Linux: sudo apt install git
- macOS: xcode-select --install
- Windows: https://git-scm.com/downloads

Proceeding with local-only status check...
```

### Network Error

```
Cannot fetch upstream SHA for https://github.com/pola-rs/polars
Network may be unavailable or repository may be private.

Showing local status only...
```

---

## Examples

### Example 1: Check If Refresh Needed

**User request:** "refresh status"

**Process:**
1. Verify corpus has sources and is built
2. For each git source, compare indexed vs upstream
3. For local sources, check for modified files
4. Report findings

**Sample output:**
```
Source Status:

1. polars (git)
   - Indexed: abc123 (2025-01-10)
   - Upstream: def456
   - Status: UPDATES AVAILABLE (23 commits)

2. team-docs (local)
   - Last indexed: 2025-01-12
   - Modified files: 2
   - Status: UPDATES AVAILABLE

Overall: 2 sources have updates
```

### Example 2: Navigate With Staleness Warning

**User query:** "How do I use lazy evaluation?"

**Process:**
1. Route to polars corpus
2. Check freshness before answering
3. If stale, include warning

**Sample output:**
```
Note: The polars docs index is 15 days old. Run `hiivmind-corpus-refresh` for latest content.

[... answer from index ...]
```

---

## Related Patterns

- **tool-detection.md** - Required for YAML parsing and git
- **config-parsing.md** - Methods to read source metadata
- **discovery.md** - Uses status for corpus health reporting
- **sources/git.md** - Git operations for freshness checking
