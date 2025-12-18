# Pattern: Shared Source Utilities

Common operations used across all source types.

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

---

### Parse Repository Name

**Using bash:**
```bash
parse_repo_name() {
    local repo_url="$1"
    # Remove .git suffix and extract name
    echo "$repo_url" | sed -E 's#.*/([^/]+)(.git)?$#\1#' | sed 's/\.git$//'
}
```

---

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

---

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

---

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

## Related Patterns

- `../tool-detection.md` - Git availability check
- `../config-parsing.md` - Reading/writing source configuration
