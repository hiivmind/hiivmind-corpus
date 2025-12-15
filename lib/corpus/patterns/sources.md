# Pattern: Sources

## Purpose

Manage git, local, and web documentation sources. Handle cloning, fetching, updating, and comparing source content.

## When to Use

- Adding new sources to a corpus
- Cloning git repositories for local access
- Updating sources to get latest content
- Comparing indexed content with upstream changes
- Managing local file uploads
- Caching web content

## Prerequisites

- **Tool detection** (see `tool-detection.md`) - Git is required for git sources
- **Config parsing** (see `config-parsing.md`) - Reading source configuration
- **Paths** (see `paths.md`) - Resolving source paths

## Source Types

| Type | Storage Location | Use Case |
|------|------------------|----------|
| `git` | `.source/{source_id}/` | GitHub/GitLab repos with docs |
| `local` | `data/uploads/{source_id}/` | User-uploaded files |
| `web` | `.cache/web/{source_id}/` | Blog posts, external articles |

---

## Git Source Operations

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

## URL Parsing

### Parse Repository Owner

**Using bash:**
```bash
parse_repo_owner() {
    local repo_url="$1"
    # Handle https://github.com/owner/repo and git@github.com:owner/repo
    echo "$repo_url" | sed -E 's#.*[:/]([^/]+)/[^/]+(.git)?$#\1#'
}
```

### Parse Repository Name

**Using bash:**
```bash
parse_repo_name() {
    local repo_url="$1"
    # Remove .git suffix and extract name
    echo "$repo_url" | sed -E 's#.*/([^/]+)(.git)?$#\1#' | sed 's/\.git$//'
}
```

### Generate Source ID from URL

**Using bash:**
```bash
generate_source_id() {
    local repo_url="$1"
    # lowercase, alphanumeric + hyphens only
    parse_repo_name "$repo_url" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-'
}
```

---

## Local Source Operations

### Setup Local Source Directory

**Using bash:**
```bash
setup_local_source() {
    local corpus_path="$1"
    local source_id="$2"
    local uploads_path="${corpus_path%/}/data/uploads/${source_id}"

    mkdir -p "$uploads_path"
    echo "$uploads_path"
}
```

---

### List Local Files

**Using bash:**
```bash
list_local_files() {
    local corpus_path="$1"
    local source_id="$2"
    local uploads_path="${corpus_path%/}/data/uploads/${source_id}"

    find "$uploads_path" -type f -name "*.md" -o -name "*.mdx" 2>/dev/null
}
```

---

### Count Local Files

**Using bash:**
```bash
count_local_files() {
    local corpus_path="$1"
    local source_id="$2"

    list_local_files "$corpus_path" "$source_id" | wc -l | tr -d ' '
}
```

---

## Web Source Operations

### Setup Web Cache Directory

**Using bash:**
```bash
setup_web_source() {
    local corpus_path="$1"
    local source_id="$2"
    local cache_path="${corpus_path%/}/.cache/web/${source_id}"

    mkdir -p "$cache_path"
    echo "$cache_path"
}
```

---

### Generate Cache Filename from URL

Convert URL to safe filename.

**Using bash:**
```bash
generate_cache_filename() {
    local url="$1"
    # Extract path, convert to slug
    echo "$url" | sed 's#https\?://##' | sed 's#/#-#g' | sed 's/[^a-zA-Z0-9-]/_/g' | sed 's/-*$//' | head -c 100
    echo ".md"
}
```

**Example:**
- `https://kentcdodds.com/blog/testing-details` → `kentcdodds-com-blog-testing-details.md`

---

### List Cached Web Content

**Using bash:**
```bash
list_web_cache() {
    local corpus_path="$1"
    local source_id="$2"
    local cache_path="${corpus_path%/}/.cache/web/${source_id}"

    ls "$cache_path"/*.md 2>/dev/null
}
```

---

### Get Cache Age (Days)

**Using bash:**
```bash
get_cache_age() {
    local corpus_path="$1"
    local source_id="$2"
    local filename="$3"
    local cache_file="${corpus_path%/}/.cache/web/${source_id}/${filename}"

    if [ -f "$cache_file" ]; then
        local file_time now_time
        file_time=$(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file")
        now_time=$(date +%s)
        echo $(( (now_time - file_time) / 86400 ))
    else
        echo "-1"
    fi
}
```

---

## Existence Checks

### Check Git Source Exists

**Using bash:**
```bash
exists_git_source() {
    local corpus_path="$1"
    local source_id="$2"
    [ -d "${corpus_path%/}/.source/${source_id}/.git" ]
}
```

### Check Local Source Has Files

**Using bash:**
```bash
exists_local_source() {
    local corpus_path="$1"
    local source_id="$2"
    local uploads_path="${corpus_path%/}/data/uploads/${source_id}"

    [ -d "$uploads_path" ] && ls "$uploads_path"/*.md >/dev/null 2>&1
}
```

### Check Web Cache Has Files

**Using bash:**
```bash
exists_web_source() {
    local corpus_path="$1"
    local source_id="$2"
    local cache_path="${corpus_path%/}/.cache/web/${source_id}"

    [ -d "$cache_path" ] && ls "$cache_path"/*.md >/dev/null 2>&1
}
```

---

## Cross-Platform Notes

| Operation | Unix | Windows |
|-----------|------|---------|
| Git commands | Same | Same |
| File stats | `stat -c %Y` (GNU) or `stat -f %m` (BSD) | PowerShell: `(Get-Item file).LastWriteTime` |
| mkdir | `mkdir -p` | `New-Item -ItemType Directory -Force` |
| sed/grep | Native | PowerShell: `-replace`, `Select-String` |

### Windows (PowerShell) Equivalents

```powershell
function Clone-Source {
    param($RepoUrl, $SourceId, $CorpusPath = ".")
    $clonePath = Join-Path $CorpusPath ".source\$SourceId"
    New-Item -ItemType Directory -Path (Join-Path $CorpusPath ".source") -Force
    git clone --depth 1 $RepoUrl $clonePath
    return $clonePath
}

function Get-SourceSha {
    param($CorpusPath, $SourceId)
    $clonePath = Join-Path $CorpusPath ".source\$SourceId"
    git -C $clonePath rev-parse HEAD
}
```

---

## Error Handling

### Git Not Available

```
Git is required for git-based documentation sources but wasn't found.

Install git:
- Linux: sudo apt install git
- macOS: xcode-select --install
- Windows: https://git-scm.com/downloads

Cannot proceed with git source operations.
```

### Clone Failed

```
Failed to clone repository: https://github.com/owner/repo

Possible causes:
- Repository doesn't exist or is private
- Network connectivity issues
- Git credentials not configured

Check the repository URL and try again.
```

### Source Not Found

```
Source "unknown-id" not found in config.yaml.

Available sources:
- polars (git)
- team-docs (local)
```

---

## Examples

### Example 1: Adding a Git Source

**User request:** "Add the polars docs"

**Process:**
1. Parse URL: `https://github.com/pola-rs/polars`
2. Generate source_id: `polars`
3. Clone: `git clone --depth 1 https://github.com/pola-rs/polars .source/polars`
4. Get SHA: `git -C .source/polars rev-parse HEAD`
5. Update config.yaml with source entry

### Example 2: Checking for Updates

**User request:** "Are there updates to the polars docs?"

**Process:**
1. Get indexed SHA from config
2. Fetch upstream: `git ls-remote https://github.com/pola-rs/polars refs/heads/main`
3. Compare SHAs
4. If different, count commits and show file changes

**Sample output:**
```
polars source has updates:
- Indexed at: abc123 (2025-01-10)
- Upstream: def456
- 15 new commits
- Files changed: 8 added, 12 modified, 2 deleted

Run refresh to update the index.
```

### Example 3: Caching Web Content

**User request:** "Add Kent's testing article"

**Process:**
1. Setup cache directory: `.cache/web/kent-blog/`
2. Fetch URL content with WebFetch
3. Save to cache: `kentcdodds-com-blog-testing-implementation-details.md`
4. Add source entry to config.yaml
5. Add entry to index.md

---

## Related Patterns

- **tool-detection.md** - Git availability check
- **config-parsing.md** - Reading/writing source configuration
- **paths.md** - Resolving source locations
- **status.md** - Freshness checking using source operations
