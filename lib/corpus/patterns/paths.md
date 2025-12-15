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

```
{corpus_path}/
├── SKILL.md                          # Navigate skill (or skills/navigate/SKILL.md)
├── data/
│   ├── config.yaml                   # Corpus configuration
│   ├── index.md                      # Main index
│   ├── index-{section}.md            # Sub-indexes (tiered)
│   ├── project-awareness.md          # Snippet for project CLAUDE.md
│   └── uploads/                      # Local source files
│       └── {source_id}/
├── .source/                          # Git clones (gitignored)
│   └── {source_id}/
└── .cache/                           # Web caches (gitignored)
    └── web/
        └── {source_id}/
```

---

## Standard Path Resolution

### Get Data Directory

**Algorithm:**
```
{corpus_path}/data/
```

**Using bash:**
```bash
get_data_path() {
    echo "${1%/}/data"
}
```

---

### Get Config File Path

**Algorithm:**
```
{corpus_path}/data/config.yaml
```

**Using bash:**
```bash
get_config_path() {
    echo "${1%/}/data/config.yaml"
}
```

---

### Get Index File Path

**Algorithm:**
```
{corpus_path}/data/index.md
```

**Using bash:**
```bash
get_index_path() {
    echo "${1%/}/data/index.md"
}
```

---

### Get Sub-Index Path (Tiered)

**Algorithm:**
```
{corpus_path}/data/index-{section}.md
```

**Using bash:**
```bash
get_subindex_path() {
    local corpus_path="$1"
    local section="$2"
    echo "${corpus_path%/}/data/index-${section}.md"
}
```

---

### Get Project Awareness Path

**Algorithm:**
```
{corpus_path}/data/project-awareness.md
```

**Using bash:**
```bash
get_awareness_path() {
    echo "${1%/}/data/project-awareness.md"
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
{corpus_path}/data/uploads/{source_id}/
```

**Using bash:**
```bash
get_uploads_path() {
    local corpus_path="$1"
    local source_id="$2"
    echo "${corpus_path%/}/data/uploads/${source_id}"
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
   - `local`: `{corpus}/data/uploads/{source_id}/{relative_path}`
   - `web`: `{corpus}/.cache/web/{source_id}/{filename}`

**Using bash (with yq):**
```bash
resolve_source_ref() {
    local corpus_path="${1%/}"
    local source_ref="$2"

    # Parse reference
    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    # Get source info from config
    local config_file="$corpus_path/data/config.yaml"
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
            echo "$corpus_path/data/uploads/$source_id/$relative_path"
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

corpus_path = '$1'.rstrip('/')
source_ref = '$2'
source_id, relative_path = source_ref.split(':', 1)

config = yaml.safe_load(open(f'{corpus_path}/data/config.yaml'))
source = next((s for s in config.get('sources', []) if s.get('id') == source_id), {})
source_type = source.get('type', 'git')
docs_root = source.get('docs_root', '')

if source_type == 'git':
    if docs_root:
        print(f'{corpus_path}/.source/{source_id}/{docs_root}/{relative_path}')
    else:
        print(f'{corpus_path}/.source/{source_id}/{relative_path}')
elif source_type == 'local':
    print(f'{corpus_path}/data/uploads/{source_id}/{relative_path}')
elif source_type == 'web':
    print(f'{corpus_path}/.cache/web/{source_id}/{relative_path}')
"
```

---

### Resolve Source Reference to URL

For git sources without local clone, resolve to GitHub raw URL.

**Algorithm:**
1. Parse source_id and relative_path
2. Get repo_owner, repo_name, branch, docs_root from config
3. Construct: `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{docs_root}/{path}`

**Using bash (with yq):**
```bash
resolve_source_url() {
    local corpus_path="${1%/}"
    local source_ref="$2"

    local source_id="${source_ref%%:*}"
    local relative_path="${source_ref#*:}"

    local config_file="$corpus_path/data/config.yaml"

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
    [ -f "${1%/}/data/config.yaml" ]
}
```

---

### Check If Index Exists

**Using bash:**
```bash
exists_index() {
    [ -f "${1%/}/data/index.md" ]
}
```

---

### Check If Has Sub-Indexes (Tiered)

**Using bash:**
```bash
exists_subindexes() {
    ls "${1%/}"/data/index-*.md >/dev/null 2>&1
}
```

---

## Listing Functions

### List Sub-Indexes

**Using bash:**
```bash
list_subindexes() {
    ls "${1%/}"/data/index-*.md 2>/dev/null | xargs -n1 basename
}
```

---

### List Source IDs

**Using yq:**
```bash
list_source_ids() {
    yq '.sources[].id' "${1%/}/data/config.yaml"
}
```

**Using Python:**
```bash
python3 -c "
import yaml
for s in yaml.safe_load(open('$1/data/config.yaml')).get('sources', []):
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
    Join-Path $CorpusPath "data\config.yaml"
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
2. URL: `https://raw.githubusercontent.com/pola-rs/polars/main/docs/reference/expressions.md`
3. WebFetch the URL

### Example 2: Tiered Index Navigation

**Main index shows:**
```markdown
## API Reference
→ See [index-reference.md](index-reference.md) for detailed API documentation
```

**Process:**
1. User asks about API
2. Read main index, find reference section links to sub-index
3. Resolve path: `{corpus}/data/index-reference.md`
4. Read sub-index for detailed entries
5. Find specific entry and resolve its source path

---

## Related Patterns

- **config-parsing.md** - Reading source configuration
- **discovery.md** - Finding corpus root paths
- **sources.md** - Git clone and fetch operations
- **status.md** - Checking if paths/clones exist
