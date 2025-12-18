# Pattern: Scanning

## Purpose

Discover and analyze documentation files within sources. Detect frameworks, find large files that need special handling, and extract content metadata.

## When to Use

- Building initial corpus index (analyzing what docs exist)
- Adding new sources (understanding doc structure)
- Detecting large files that need `GREP` markers
- Identifying documentation frameworks for navigation hints

## Prerequisites

- **Paths** (see `paths.md`) - Know where source files are located
- Source is cloned or uploaded

---

## File Discovery

### Scan for Documentation Files

Find all markdown/mdx files in a path.

**Algorithm:**
1. Recursively search directory
2. Find files with `.md` or `.mdx` extensions
3. Return list of paths

**Using bash:**
```bash
scan_docs() {
    local path="$1"
    find "$path" -type f \( -name "*.md" -o -name "*.mdx" \) 2>/dev/null
}
```

**Using Claude tools:**
```
Glob: {path}/**/*.md
Glob: {path}/**/*.mdx
```

---

### Scan by Extension

Find files with a specific extension.

**Using bash:**
```bash
scan_docs_ext() {
    local path="$1"
    local extension="$2"  # e.g., "rst", "adoc"
    find "$path" -type f -name "*.$extension" 2>/dev/null
}
```

---

### Count Documentation Files

**Using bash:**
```bash
count_docs() {
    local path="$1"
    find "$path" -type f \( -name "*.md" -o -name "*.mdx" \) 2>/dev/null | wc -l | tr -d ' '
}
```

---

### Find Files Matching Pattern

**Using bash:**
```bash
find_docs_matching() {
    local path="$1"
    local pattern="$2"  # e.g., "*hooks*", "*api*"
    find "$path" -type f \( -name "*.md" -o -name "*.mdx" \) -name "$pattern" 2>/dev/null
}
```

**Using Claude tools:**
```
Grep: {keyword}
  path: {source_path}
  glob: *.md
  output_mode: files_with_matches
```

---

### List Top-Level Sections

Get directory names at the top level of docs.

**Using bash:**
```bash
list_doc_sections() {
    local path="$1"
    find "$path" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | xargs -n1 basename | sort
}
```

**Example output:**
```
guides
reference
tutorials
api
```

---

## Framework Detection

### Detect Documentation Framework

Identify which doc framework is used (helps understand navigation structure).

**Algorithm:**
1. Check for framework-specific config files
2. Check for characteristic directory patterns
3. Return framework name or "unknown"

**Framework indicators:**

| Framework | Indicators |
|-----------|------------|
| Docusaurus | `docusaurus.config.js`, `sidebars.js`, `docs/` |
| MkDocs | `mkdocs.yml` |
| Sphinx | `conf.py`, `_build/`, `.rst` files |
| VitePress | `docs/.vitepress/` |
| Nextra | `theme.config.tsx`, `pages/` |
| mdBook | `book.toml`, `src/SUMMARY.md` |
| Antora | `antora.yml` |
| GitBook | `.gitbook.yaml`, `SUMMARY.md` |

**Using bash:**
```bash
detect_doc_framework() {
    local source_path="$1"

    # Docusaurus
    if [ -f "$source_path/docusaurus.config.js" ] || [ -f "$source_path/docusaurus.config.ts" ]; then
        echo "docusaurus"
        return
    fi

    # MkDocs
    if [ -f "$source_path/mkdocs.yml" ]; then
        echo "mkdocs"
        return
    fi

    # Sphinx
    if [ -f "$source_path/conf.py" ]; then
        echo "sphinx"
        return
    fi

    # VitePress
    if [ -d "$source_path/docs/.vitepress" ] || [ -d "$source_path/.vitepress" ]; then
        echo "vitepress"
        return
    fi

    # Nextra
    if [ -f "$source_path/theme.config.tsx" ] || [ -f "$source_path/theme.config.jsx" ]; then
        echo "nextra"
        return
    fi

    # mdBook
    if [ -f "$source_path/book.toml" ]; then
        echo "mdbook"
        return
    fi

    # Antora
    if [ -f "$source_path/antora.yml" ]; then
        echo "antora"
        return
    fi

    # GitBook
    if [ -f "$source_path/.gitbook.yaml" ] || [ -f "$source_path/SUMMARY.md" ]; then
        echo "gitbook"
        return
    fi

    echo "unknown"
}
```

---

### Find Navigation Config

Locate the navigation/sidebar configuration file.

**Using bash:**
```bash
find_nav_config() {
    local source_path="$1"

    # Docusaurus
    for f in "$source_path/sidebars.js" "$source_path/sidebars.ts" "$source_path/sidebars.json"; do
        [ -f "$f" ] && echo "$f" && return
    done

    # MkDocs
    [ -f "$source_path/mkdocs.yml" ] && echo "$source_path/mkdocs.yml" && return

    # mdBook
    [ -f "$source_path/src/SUMMARY.md" ] && echo "$source_path/src/SUMMARY.md" && return

    # VitePress
    for f in "$source_path/docs/.vitepress/config.js" "$source_path/.vitepress/config.js"; do
        [ -f "$f" ] && echo "$f" && return
    done
}
```

---

### Detect Frontmatter Type

Check what frontmatter format files use.

**Using bash:**
```bash
detect_frontmatter_type() {
    local source_path="$1"
    local sample_file

    sample_file=$(find "$source_path" -name "*.md" -type f | head -1)
    [ -z "$sample_file" ] && echo "none" && return

    local first_line
    first_line=$(head -1 "$sample_file")

    case "$first_line" in
        "---")
            echo "yaml"
            ;;
        "+++")
            echo "toml"
            ;;
        *)
            echo "none"
            ;;
    esac
}
```

---

## Large File Detection

### Find Large Files

Find files over a line threshold (default 1000 lines).

**Algorithm:**
1. Find all doc files
2. Count lines in each
3. Filter to those above threshold

**Using bash:**
```bash
find_large_files() {
    local path="$1"
    local min_lines="${2:-1000}"

    find "$path" -type f \( -name "*.md" -o -name "*.mdx" \) -exec wc -l {} \; 2>/dev/null | \
        awk -v min="$min_lines" '$1 >= min {print $2 "|" $1}'
}
```

**Output format:**
```
path/to/large-file.md|1500
path/to/another-file.md|2300
```

---

### Find Schema Files

Find GraphQL schemas, OpenAPI specs, JSON schemas.

**Using bash:**
```bash
find_schema_files() {
    local path="$1"

    # GraphQL
    find "$path" -type f -name "*.graphql" -o -name "*.gql" 2>/dev/null

    # OpenAPI/Swagger
    find "$path" -type f \( -name "openapi.yaml" -o -name "openapi.yml" -o -name "openapi.json" \
        -o -name "swagger.yaml" -o -name "swagger.yml" -o -name "swagger.json" \) 2>/dev/null

    # JSON Schema
    find "$path" -type f -name "*.schema.json" 2>/dev/null
}
```

---

### Get File Line Count

**Using bash:**
```bash
get_file_lines() {
    wc -l < "$1" | tr -d ' '
}
```

---

### Check If Large File

**Using bash:**
```bash
is_large_file() {
    local file_path="$1"
    local threshold="${2:-1000}"

    local lines
    lines=$(wc -l < "$file_path" | tr -d ' ')
    [ "$lines" -ge "$threshold" ]
}
```

---

### Suggest Grep Pattern

Generate appropriate grep pattern for a large file type.

**Using bash:**
```bash
suggest_grep_pattern() {
    local file_path="$1"

    case "$file_path" in
        *.graphql|*.gql)
            echo "grep -n \"^type {Name}\" $file_path -A 30"
            ;;
        *openapi*|*swagger*)
            echo "grep -n \"/{path}\" $file_path -A 20"
            ;;
        *.schema.json)
            echo "grep -n '\"{property}\"' $file_path -A 10"
            ;;
        *)
            echo "grep -n \"{keyword}\" $file_path -A 10"
            ;;
    esac
}
```

---

## Content Analysis

### Sample Frontmatter

Extract YAML frontmatter from a file.

**Using bash:**
```bash
sample_frontmatter() {
    local file_path="$1"

    # Get content between first --- and second ---
    awk '/^---$/{if(++n==1)next; if(n==2)exit} n==1' "$file_path"
}
```

---

### Sample File (First N Lines)

**Using bash:**
```bash
sample_file() {
    local file_path="$1"
    local num_lines="${2:-50}"

    head -n "$num_lines" "$file_path"
}
```

---

### Extract Title

Get title from frontmatter or first H1.

**Using bash:**
```bash
extract_title() {
    local file_path="$1"

    # Try frontmatter title
    local title
    title=$(awk '/^---$/,/^---$/' "$file_path" | grep "^title:" | sed 's/title: *//' | tr -d '"')

    if [ -n "$title" ]; then
        echo "$title"
        return
    fi

    # Try first H1
    grep -m1 "^# " "$file_path" | sed 's/^# //'
}
```

---

### Extract Description

Get description from frontmatter or first paragraph.

**Using bash:**
```bash
extract_description() {
    local file_path="$1"

    # Try frontmatter description
    local desc
    desc=$(awk '/^---$/,/^---$/' "$file_path" | grep "^description:" | sed 's/description: *//' | tr -d '"')

    if [ -n "$desc" ]; then
        echo "$desc"
        return
    fi

    # Try first paragraph after frontmatter/title
    awk 'BEGIN{in_front=0; found=0}
         /^---$/{in_front=!in_front; next}
         in_front{next}
         /^#/{next}
         /^$/{if(found)exit; next}
         {found=1; print}' "$file_path" | head -3
}
```

---

## Index Analysis

### Detect Tiered Index

**Using bash:**
```bash
detect_tiered_index() {
    local corpus_path="$1"
    ls "${corpus_path%/}"/data/index-*.md >/dev/null 2>&1
}
```

---

### List Sub-Index Files

**Using bash:**
```bash
list_subindex_files() {
    local corpus_path="$1"
    ls "${corpus_path%/}"/data/index-*.md 2>/dev/null | xargs -n1 basename
}
```

---

### Count Index Entries

Approximate count of entries in an index file.

**Using bash:**
```bash
count_index_entries() {
    local index_file="$1"
    # Count lines starting with "- **" (entry format)
    grep -c "^- \*\*" "$index_file" 2>/dev/null || echo "0"
}
```

---

### Extract Index Sections

Get section headings from index.

**Using bash:**
```bash
extract_index_sections() {
    local index_file="$1"
    grep "^## " "$index_file" | sed 's/^## //'
}
```

---

## Batch Operations

### Scan All Sources

Scan all sources in a corpus.

**Using bash (with yq):**
```bash
scan_all_sources() {
    local corpus_path="$1"
    local config_file="${corpus_path%/}/data/config.yaml"

    for source_id in $(yq '.sources[].id' "$config_file"); do
        local source_type docs_root source_path count

        source_type=$(yq ".sources[] | select(.id == \"$source_id\") | .type" "$config_file")
        docs_root=$(yq ".sources[] | select(.id == \"$source_id\") | .docs_root // \"\"" "$config_file")

        case "$source_type" in
            git)
                if [ -n "$docs_root" ]; then
                    source_path="${corpus_path%/}/.source/${source_id}/${docs_root}"
                else
                    source_path="${corpus_path%/}/.source/${source_id}"
                fi
                ;;
            local)
                source_path="${corpus_path%/}/data/uploads/${source_id}"
                ;;
            web)
                source_path="${corpus_path%/}/.cache/web/${source_id}"
                ;;
        esac

        count=$(count_docs "$source_path")
        echo "$source_id|$count|$source_path"
    done
}
```

---

### Total Doc Count

**Using bash:**
```bash
count_all_docs() {
    local corpus_path="$1"
    local total=0

    while IFS='|' read -r id count path; do
        total=$((total + count))
    done < <(scan_all_sources "$corpus_path")

    echo "$total"
}
```

---

## Cross-Platform Notes

| Operation | Unix | Windows |
|-----------|------|---------|
| Find files | `find path -name "*.md"` | `Get-ChildItem -Recurse -Filter "*.md"` |
| Count lines | `wc -l < file` | `(Get-Content file).Length` |
| Head | `head -n 50 file` | `Get-Content file -Head 50` |
| Grep | `grep pattern file` | `Select-String -Pattern pattern file` |

### Windows (PowerShell) Equivalents

```powershell
function Scan-Docs {
    param([string]$Path)
    Get-ChildItem -Path $Path -Recurse -Include "*.md", "*.mdx" | Select-Object -ExpandProperty FullName
}

function Count-Docs {
    param([string]$Path)
    (Get-ChildItem -Path $Path -Recurse -Include "*.md", "*.mdx").Count
}

function Find-LargeFiles {
    param([string]$Path, [int]$MinLines = 1000)
    Get-ChildItem -Path $Path -Recurse -Include "*.md", "*.mdx" | ForEach-Object {
        $lines = (Get-Content $_.FullName).Length
        if ($lines -ge $MinLines) {
            "$($_.FullName)|$lines"
        }
    }
}
```

---

## Examples

### Example 1: Analyzing a New Source

**Process:**
1. Count total docs
2. Detect framework
3. Find large files
4. List top-level sections

**Sample output:**
```
Source Analysis: polars

Framework: mkdocs
Total docs: 245
Sections: reference, guides, examples, api

Large files (>1000 lines):
- api/schema.graphql (4500 lines) - use GREP marker
- reference/expressions.md (1200 lines) - use GREP marker

Recommended index structure:
- Single index sufficient (245 docs)
- Add GREP markers for 2 large files
```

### Example 2: Recommending Tiered Index

**Process:**
1. Count total docs across all sources
2. If > 500, recommend tiered index

**Sample output:**
```
Total documentation: 750 files across 3 sources

Recommendation: Use tiered indexing
- Main index: Section summaries with links to sub-indexes
- Sub-indexes: Detailed entries per section

Suggested structure:
- index.md (main)
- index-reference.md (300 entries)
- index-guides.md (200 entries)
- index-api.md (250 entries)
```

---

## Related Patterns

- **paths.md** - Resolving source locations
- **sources/** - Getting source content (git.md, local.md, web.md, generated-docs.md)
- **config-parsing.md** - Reading source configuration
- **status.md** - Using scan results for status reporting
