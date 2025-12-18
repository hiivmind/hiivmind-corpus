# Pattern: Git Sources

Manage git repository documentation sources. Clone, fetch, track SHAs, and compare changes.

## Storage Location

`.source/{source_id}/`

## Operations

### Clone a Git Repository

**Algorithm:**
1. Ensure git is available
2. Create `.source/` directory if needed
3. Clone with `--depth 1` (shallow) for efficiency
4. Return clone path

**Using bash:**
```bash
clone_source() {
    local repo_url="$1"
    local source_id="$2"
    local corpus_path="${3:-.}"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    # Create directory
    mkdir -p "${corpus_path%/}/.source"

    # Clone (shallow)
    git clone --depth 1 "$repo_url" "$clone_path"

    echo "$clone_path"
}
```

---

### Clone with Specific Branch

**Using bash:**
```bash
clone_source_branch() {
    local repo_url="$1"
    local source_id="$2"
    local branch="$3"
    local corpus_path="${4:-.}"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    mkdir -p "${corpus_path%/}/.source"
    git clone --depth 1 --branch "$branch" "$repo_url" "$clone_path"

    echo "$clone_path"
}
```

---

### Get Clone SHA

**Using bash:**
```bash
get_source_sha() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" rev-parse HEAD 2>/dev/null
}
```

---

### Get Short SHA (7 chars)

**Using bash:**
```bash
get_source_sha_short() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" rev-parse --short HEAD 2>/dev/null
}
```

---

### Get Clone Branch

**Using bash:**
```bash
get_source_branch() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" rev-parse --abbrev-ref HEAD 2>/dev/null
}
```

---

### Fetch Updates (Without Pulling)

**Using bash:**
```bash
fetch_source() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" fetch origin 2>/dev/null
}
```

---

### Pull Updates

**Using bash:**
```bash
pull_source() {
    local corpus_path="$1"
    local source_id="$2"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" pull origin 2>/dev/null
    git -C "$clone_path" rev-parse HEAD
}
```

---

### Fetch Upstream SHA (Remote Check)

Check remote without modifying local clone.

**Using bash:**
```bash
fetch_upstream_sha() {
    local repo_url="$1"
    local branch="${2:-main}"

    git ls-remote "$repo_url" "refs/heads/$branch" 2>/dev/null | cut -f1
}
```

---

### Get Commit Log Between SHAs

Show commits between two points, optionally filtered to a path.

**Using bash:**
```bash
get_commit_log() {
    local corpus_path="$1"
    local source_id="$2"
    local from_sha="$3"
    local to_sha="$4"
    local docs_path="${5:-}"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    if [ -n "$docs_path" ]; then
        git -C "$clone_path" log --oneline "$from_sha..$to_sha" -- "$docs_path"
    else
        git -C "$clone_path" log --oneline "$from_sha..$to_sha"
    fi
}
```

---

### Get File Changes Between SHAs

Show which files were added, modified, or deleted.

**Using bash:**
```bash
get_file_changes() {
    local corpus_path="$1"
    local source_id="$2"
    local from_sha="$3"
    local to_sha="$4"
    local docs_path="${5:-}"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    if [ -n "$docs_path" ]; then
        git -C "$clone_path" diff --name-status "$from_sha..$to_sha" -- "$docs_path"
    else
        git -C "$clone_path" diff --name-status "$from_sha..$to_sha"
    fi
}
```

**Output format:**
```
A       docs/new-file.md           # Added
M       docs/modified-file.md      # Modified
D       docs/deleted-file.md       # Deleted
R100    docs/old-name.md docs/new-name.md  # Renamed
```

---

### Count Commits Between SHAs

**Using bash:**
```bash
count_commits() {
    local corpus_path="$1"
    local source_id="$2"
    local from_sha="$3"
    local to_sha="$4"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    git -C "$clone_path" rev-list --count "$from_sha..$to_sha" 2>/dev/null
}
```

---

### Compare Clone to Indexed SHA

Determine relationship between local clone and indexed state.

**Using bash:**
```bash
compare_clone_to_indexed() {
    local corpus_path="$1"
    local source_id="$2"
    local indexed_sha="$3"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    local clone_sha
    clone_sha=$(git -C "$clone_path" rev-parse HEAD 2>/dev/null)

    if [ -z "$clone_sha" ]; then
        echo "unknown"
        return
    fi

    if [ "$indexed_sha" = "$clone_sha" ]; then
        echo "current"
    elif git -C "$clone_path" merge-base --is-ancestor "$indexed_sha" "$clone_sha" 2>/dev/null; then
        echo "ahead"
    elif git -C "$clone_path" merge-base --is-ancestor "$clone_sha" "$indexed_sha" 2>/dev/null; then
        echo "behind"
    else
        echo "diverged"
    fi
}
```

**Return values:**
- `current` - Clone is at indexed SHA
- `ahead` - Clone has new commits (index is stale)
- `behind` - Indexed SHA is newer (unusual, clone may have been reset)
- `diverged` - Branches have diverged
- `unknown` - Cannot determine

---

## Related Patterns

- `shared.md` - URL parsing, existence checks
- `../status.md` - Freshness checking
- `../tool-detection.md` - Git availability check
