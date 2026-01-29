# Pattern: Paths

## Purpose

Resolve paths within corpus structures. Handle the `{source_id}:{relative_path}` format used in indexes and translate to actual file locations.

## When to Use

- Navigating from index entries to actual documentation files
- Finding config, index, and data files within a corpus
- Resolving source references to local clones or remote URLs
- Working with tiered indexes

## Prerequisites

- **Config parsing** (see `config-parsing.md`) - For reading source configuration
- Knowledge of corpus root path

## Corpus Directory Structure

### Data-Only Corpus (Recommended)

```
{corpus_path}/
├── config.yaml                       # Corpus configuration
├── index.md                          # Main index
├── index-{section}.md                # Sub-indexes (tiered)
├── uploads/                          # Local source files
│   └── {source_id}/
├── logs/                             # Refresh logs (optional)
├── CLAUDE.md                         # Data corpus documentation
├── README.md                         # Repository documentation
├── .source/                          # Git clones (gitignored)
│   └── {source_id}/
└── .cache/                           # Web caches (gitignored)
    └── web/
        └── {source_id}/
```

### Legacy Plugin Corpus

```
{corpus_path}/
├── SKILL.md                          # Navigate skill (or skills/navigate/SKILL.md)
├── data/
│   ├── config.yaml                   # Corpus configuration
│   ├── index.md                      # Main index
│   ├── index-{section}.md            # Sub-indexes (tiered)
│   └── uploads/                      # Local source files
│       └── {source_id}/
├── references/
│   └── project-awareness.md          # Snippet for project CLAUDE.md
├── .source/                          # Git clones (gitignored)
│   └── {source_id}/
└── .cache/                           # Web caches (gitignored)
    └── web/
        └── {source_id}/
```

---

## Standard Path Resolution

### Detect Corpus Type

**Algorithm:**
1. Check if `config.yaml` exists at root → data-only corpus
2. Check if `data/config.yaml` exists → legacy plugin corpus
3. Return corpus type and base path for data files

**Using bash:**
```bash
detect_corpus_type() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "data-only"
    elif [ -f "$corpus_path/data/config.yaml" ]; then
        echo "legacy-plugin"
    else
        echo "unknown"
    fi
}
```

---

### Get Config File Path

**Algorithm:**
```
Data-only: {corpus_path}/config.yaml
Legacy:    {corpus_path}/data/config.yaml
```

**Using bash:**
```bash
get_config_path() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/config.yaml"
    else
        echo "$corpus_path/data/config.yaml"
    fi
}
```

---

### Get Index File Path

**Algorithm:**
```
Data-only: {corpus_path}/index.md
Legacy:    {corpus_path}/data/index.md
```

**Using bash:**
```bash
get_index_path() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/index.md"
    else
        echo "$corpus_path/data/index.md"
    fi
}
```

---

### Get Sub-Index Path (Tiered)

**Algorithm:**
```
Data-only: {corpus_path}/index-{section}.md
Legacy:    {corpus_path}/data/index-{section}.md
```

**Using bash:**
```bash
get_subindex_path() {
    local corpus_path="${1%/}"
    local section="$2"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/index-${section}.md"
    else
        echo "$corpus_path/data/index-${section}.md"
    fi
}
```

---

### Get Uploads Path Base

**Algorithm:**
```
Data-only: {corpus_path}/uploads/
Legacy:    {corpus_path}/data/uploads/
```

**Using bash:**
```bash
get_uploads_base() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/uploads"
    else
        echo "$corpus_path/data/uploads"
    fi
}
```

---

### Get Logs Path

**Algorithm:**
```
Data-only: {corpus_path}/logs/
Legacy:    {corpus_path}/data/logs/
```

**Using bash:**
```bash
get_logs_path() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/logs"
    else
        echo "$corpus_path/data/logs"
    fi
}
```

---

### Get Navigate Skill Path

Varies by corpus type (skill vs plugin structure).

**Algorithm:**
1. Check for `SKILL.md` at corpus root
2. If not found, check `skills/navigate/SKILL.md`
3. Return found path

**Using bash:**
```bash
get_navigate_skill_path() {
    local corpus_path="${1%/}"

    if [ -f "$corpus_path/SKILL.md" ]; then
        echo "$corpus_path/SKILL.md"
    elif [ -f "$corpus_path/skills/navigate/SKILL.md" ]; then
        echo "$corpus_path/skills/navigate/SKILL.md"
    fi
}
```

---

## Source Path Resolution

### Source Path Format

Index entries use the format: `{source_id}:{relative_path}`

Examples:
- `polars:reference/expressions.md` → Git source "polars", file at `reference/expressions.md`
- `local:team-docs/coding-guidelines.md` → Local source "local", file at `team-docs/coding-guidelines.md`
- `web:kent-blog/testing-article.md` → Web source "web", cached file

---

### Parse Source Reference

**Algorithm:**
1. Split on first colon
2. Part before = source_id
3. Part after = relative_path

**Using bash:**
```bash
parse_source_ref() {
    local ref="$1"
    local source_id="${ref%%:*}"
    local relative_path="${ref#*:}"
    echo "$source_id|$relative_path"
}

# Usage
IFS='|' read -r source_id path <<< "$(parse_source_ref "polars:reference/hooks.md")"
```

---

### Get Source Clone Path

For git sources, resolve to local clone.

**Algorithm:**
```
{corpus_path}/.source/{source_id}/
```

**Using bash:**
```bash
get_source_clone_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/.source/${source_id}"
}
```

---

### Get Local Uploads Path

For local (uploaded) sources.

**Algorithm:**
```
Data-only: {corpus_path}/uploads/{source_id}/
Legacy:    {corpus_path}/data/uploads/{source_id}/
```

**Using bash:**
```bash
get_uploads_path() {
    local corpus_path="${1%/}"
    local source_id="$2"
    if [ -f "$corpus_path/config.yaml" ]; then
        echo "$corpus_path/uploads/${source_id}"
    else
        echo "$corpus_path/data/uploads/${source_id}"
    fi
}
```

---

### Get Web Cache Path

For cached web content.

**Algorithm:**
```
{corpus_path}/.cache/web/{source_id}/
```

**Using bash:**
```bash
get_web_cache_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/.cache/web/${source_id}"
}
```

---

## Full Path Resolution

### Resolve Source Reference to File

Given a source reference like `polars:reference/hooks.md`, resolve to actual file path.

**Algorithm:**
1. Parse source_id and relative_path
2. Look up source in config.yaml
3. Based on source type:
   - `git`: `{corpus}/.source/{source_id}/{docs_root}/{relative_path}`
   - `local`: `{corpus}/uploads/{source_id}/{relative_path}` (data-only) or `{corpus}/data/uploads/{source_id}/{relative_path}` (legacy)
   - `web`: `{corpus}/.cache/web/{source_id}/{filename}`

**Using bash (with yq):**
```bash
resolve_source_ref() {
    local corpus_path="${1%/}"
    local source_ref="$2"

    # Parse reference
    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    # Detect corpus type and get config path
    local config_file
    local is_data_only=false
    if [ -f "$corpus_path/config.yaml" ]; then
        config_file="$corpus_path/config.yaml"
        is_data_only=true
    else
        config_file="$corpus_path/data/config.yaml"
    fi

    local source_type docs_root
    source_type=$(yq ".sources[] | select(.id == \"$source_id\") | .type" "$config_file")
    docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \"\"" "$config_file")

    case "$source_type" in
        git)
            if [ -n "$docs_root" ]; then
                echo "$corpus_path/.source/$source_id/$docs_root/$relative_path"
            else
                echo "$corpus_path/.source/$source_id/$relative_path"
            fi
            ;;
        local)
            if $is_data_only; then
                echo "$corpus_path/uploads/$source_id/$relative_path"
            else
                echo "$corpus_path/data/uploads/$source_id/$relative_path"
            fi
            ;;
        web)
            echo "$corpus_path/.cache/web/$source_id/$relative_path"
            ;;
    esac
}
```

**Using Python:**
```bash
python3 -c "
import yaml
import sys
import os

corpus_path = '$1'.rstrip('/')
source_ref = '$2'
source_id, relative_path = source_ref.split(':', 1)

# Detect corpus type
if os.path.exists(f'{corpus_path}/config.yaml'):
    config_file = f'{corpus_path}/config.yaml'
    uploads_base = f'{corpus_path}/uploads'
else:
    config_file = f'{corpus_path}/data/config.yaml'
    uploads_base = f'{corpus_path}/data/uploads'

config = yaml.safe_load(open(config_file))
source = next((s for s in config.get('sources', []) if s.get('id') == source_id), {})
source_type = source.get('type', 'git')
docs_root = source.get('docs_root', '')

if source_type == 'git':
    if docs_root:
        print(f'{corpus_path}/.source/{source_id}/{docs_root}/{relative_path}')
    else:
        print(f'{corpus_path}/.source/{source_id}/{relative_path}')
elif source_type == 'local':
    print(f'{uploads_base}/{source_id}/{relative_path}')
elif source_type == 'web':
    print(f'{corpus_path}/.cache/web/{source_id}/{relative_path}')
"
```

---

### Resolve Source Reference to URL

For git sources without local clone, resolve to a fetchable URL or gh api command.

**Algorithm:**
1. Parse source_id and relative_path
2. Get repo_owner, repo_name, branch, docs_root from config
3. Construct fetch command or URL

**Primary Method: gh api (Recommended)**

```bash
resolve_source_fetch() {
    local corpus_path="${1%/}"
    local source_ref="$2"

    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    # Detect corpus type and get config path
    local config_file
    if [ -f "$corpus_path/config.yaml" ]; then
        config_file="$corpus_path/config.yaml"
    else
        config_file="$corpus_path/data/config.yaml"
    fi

    local owner repo branch docs_root content_path
    owner=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_owner" "$config_file")
    repo=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_name" "$config_file")
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .branch // \"main\"" "$config_file")
    docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \"\"" "$config_file")

    if [ -n "$docs_root" ]; then
        content_path="$docs_root/$relative_path"
    else
        content_path="$relative_path"
    fi

    # Return gh api command to fetch content
    echo "gh api repos/$owner/$repo/contents/$content_path?ref=$branch --jq '.content' | base64 -d"
}
```

**Fallback Method: raw.githubusercontent.com URL**

```bash
resolve_source_url() {
    local corpus_path="${1%/}"
    local source_ref="$2"

    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    # Detect corpus type and get config path
    local config_file
    if [ -f "$corpus_path/config.yaml" ]; then
        config_file="$corpus_path/config.yaml"
    else
        config_file="$corpus_path/data/config.yaml"
    fi

    local owner repo branch docs_root
    owner=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_owner" "$config_file")
    repo=$(yq ".sources[] | select(.id == \"$source_id\") | .repo_name" "$config_file")
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .branch // \"main\"" "$config_file")
    docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \"\"" "$config_file")

    if [ -n "$docs_root" ]; then
        echo "https://raw.githubusercontent.com/$owner/$repo/$branch/$docs_root/$relative_path"
    else
        echo "https://raw.githubusercontent.com/$owner/$repo/$branch/$relative_path"
    fi
}
```

**Note:** Prefer `gh api` as it works consistently for all public repositories. Use raw.githubusercontent.com URLs only as a fallback when `gh` CLI is unavailable.

---

## Existence Checks

### Check If Clone Exists

**Using bash:**
```bash
exists_clone() {
    local corpus_path="$1"
    local source_id="$2"
    [ -d "${corpus_path%/}/.source/${source_id}/.git" ]
}
```

---

### Check If Config Exists

**Using bash:**
```bash
exists_config() {
    local corpus_path="${1%/}"
    [ -f "$corpus_path/config.yaml" ] || [ -f "$corpus_path/data/config.yaml" ]
}
```

---

### Check If Index Exists

**Using bash:**
```bash
exists_index() {
    local corpus_path="${1%/}"
    [ -f "$corpus_path/index.md" ] || [ -f "$corpus_path/data/index.md" ]
}
```

---

### Check If Has Sub-Indexes (Tiered)

**Using bash:**
```bash
exists_subindexes() {
    local corpus_path="${1%/}"
    ls "$corpus_path"/index-*.md >/dev/null 2>&1 || ls "$corpus_path"/data/index-*.md >/dev/null 2>&1
}
```

---

## Listing Functions

### List Sub-Indexes

**Using bash:**
```bash
list_subindexes() {
    local corpus_path="${1%/}"
    if [ -f "$corpus_path/config.yaml" ]; then
        ls "$corpus_path"/index-*.md 2>/dev/null | xargs -n1 basename
    else
        ls "$corpus_path"/data/index-*.md 2>/dev/null | xargs -n1 basename
    fi
}
```

---

### List Source IDs

**Using yq:**
```bash
list_source_ids() {
    local corpus_path="${1%/}"
    local config_file
    if [ -f "$corpus_path/config.yaml" ]; then
        config_file="$corpus_path/config.yaml"
    else
        config_file="$corpus_path/data/config.yaml"
    fi
    yq '.sources[].id' "$config_file"
}
```

**Using Python:**
```bash
python3 -c "
import yaml
import os
corpus_path = '$1'.rstrip('/')
config_file = f'{corpus_path}/config.yaml' if os.path.exists(f'{corpus_path}/config.yaml') else f'{corpus_path}/data/config.yaml'
for s in yaml.safe_load(open(config_file)).get('sources', []):
    print(s.get('id', ''))
"
```

---

## Cross-Platform Notes

| Aspect | Unix | Windows |
|--------|------|---------|
| Path separator | `/` | `\` (PowerShell accepts `/`) |
| Home directory | `$HOME`, `~` | `$env:USERPROFILE` |
| Check dir exists | `[ -d path ]` | `Test-Path path -PathType Container` |
| Check file exists | `[ -f path ]` | `Test-Path path -PathType Leaf` |

### Windows Path Example

```powershell
function Get-CorpusConfigPath {
    param([string]$CorpusPath)
    # Check for data-only corpus first
    $dataOnlyPath = Join-Path $CorpusPath "config.yaml"
    if (Test-Path $dataOnlyPath) {
        return $dataOnlyPath
    }
    return Join-Path $CorpusPath "data\config.yaml"
}

function Resolve-SourceRef {
    param(
        [string]$CorpusPath,
        [string]$SourceRef
    )
    $parts = $SourceRef -split ':', 2
    $sourceId = $parts[0]
    $relativePath = $parts[1]

    # Read config and resolve...
}
```

---

## Error Handling

### Source Not Found in Config

```
Source "unknown-source" not found in config.yaml.

Available sources:
- polars (git)
- team-docs (local)

Check the index entry path format: {source_id}:{relative_path}
```

### Clone Not Available

```
Local clone not found for source "polars".
Path checked: .source/polars/

Options:
1. Clone the source: git clone --depth 1 {repo_url} .source/polars
2. Fetch from GitHub URL instead (requires network)
```

### File Not Found at Resolved Path

```
File not found: .source/polars/docs/reference/hooks.md

This could mean:
- The index is out of date (file was moved/deleted upstream)
- The docs_root path is incorrect in config.yaml
- The local clone needs updating (git pull)

Try running hiivmind-corpus-refresh to update the index.
```

---

## Examples

### Example 1: Fetch Documentation

**Index entry found:** `polars:reference/expressions.md`

**Resolution process:**
1. Parse: source_id=`polars`, relative_path=`reference/expressions.md`
2. Look up source in config: type=`git`, docs_root=`docs`
3. Check for clone: `.source/polars/` exists
4. Full path: `.source/polars/docs/reference/expressions.md`
5. Read file

**If no clone:**
1. Get repo info: owner=`pola-rs`, repo=`polars`, branch=`main`
2. Fetch with gh api (preferred):
   ```bash
   gh api repos/pola-rs/polars/contents/docs/reference/expressions.md --jq '.content' | base64 -d
   ```
3. Or fallback to WebFetch: `https://raw.githubusercontent.com/pola-rs/polars/main/docs/reference/expressions.md`

### Example 2: Tiered Index Navigation

**Main index shows:**
```markdown
## API Reference
→ See [index-reference.md](index-reference.md) for detailed API documentation
```

**Process:**
1. User asks about API
2. Read main index, find reference section links to sub-index
3. Resolve path: `{corpus}/index-reference.md` (data-only) or `{corpus}/data/index-reference.md` (legacy)
4. Read sub-index for detailed entries
5. Find specific entry and resolve its source path

---

## Related Patterns

- **config-parsing.md** - Reading source configuration
- **discovery.md** - Finding corpus root paths
- **sources/git.md** - Git clone and fetch operations
- **status.md** - Checking if paths/clones exist
