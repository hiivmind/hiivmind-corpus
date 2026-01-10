# Pattern: llms-txt Sources

Manage documentation from sites providing llms.txt manifests - structured markdown files listing LLM-friendly content with direct links to raw markdown.

## Storage Location

`.cache/llms-txt/{source_id}/`

## Overview

The [llms.txt standard](https://llmstxt.org/) provides:
- **Manifest file** at `/llms.txt` or `/docs/llms.txt`
- **Structured discovery** - H1 title, optional summary, H2 sections with links
- **Raw markdown** - URLs point to `.md` versions (10-30x smaller than HTML)
- **Hash-based change detection** - Compare manifest hash to detect updates

## Operations

### Fetch Manifest

Fetch the llms.txt manifest file from a site.

**Algorithm:**
1. Try `{base_url}/llms.txt`
2. If 404, try `{base_url}/docs/llms.txt`
3. Return content and final URL

**Using Claude tools (preferred):**
```
WebFetch: {base_url}/llms.txt
Prompt: "Return the raw content of this llms.txt file"

If 404:
WebFetch: {base_url}/docs/llms.txt
```

**Using bash:**
```bash
fetch_manifest() {
    local base_url="$1"
    base_url="${base_url%/}"

    # Try /llms.txt first
    local content
    content=$(curl -sL "${base_url}/llms.txt" 2>/dev/null)
    if [ -n "$content" ] && ! echo "$content" | grep -q "404"; then
        echo "$content"
        return 0
    fi

    # Try /docs/llms.txt
    content=$(curl -sL "${base_url}/docs/llms.txt" 2>/dev/null)
    if [ -n "$content" ] && ! echo "$content" | grep -q "404"; then
        echo "$content"
        return 0
    fi

    return 1
}
```

---

### Parse Manifest

Extract structure from llms.txt content.

**Manifest format:**
```markdown
# Project Name             ← structure.title

> Brief description        ← structure.summary (optional)

## Section Name            ← sections[].name

- [Page Title](url.md): Description
- [Another Page](path/to/page.md)
```

**Algorithm:**
1. Extract H1 as title (first `# ` line)
2. Extract blockquote after H1 as summary (first `> ` line after title)
3. For each H2 (`## `), start a new section
4. Parse markdown links under each H2 as section URLs

**Using Claude tools (preferred):**
```
Read the llms.txt content and extract:
- title: Text from the first H1 heading
- summary: Text from the first blockquote (if any)
- sections: Array of {name, urls[]} from H2 headings and their list items
```

**Using bash (regex parsing):**
```bash
parse_manifest() {
    local content="$1"

    # Extract title (first H1)
    local title
    title=$(echo "$content" | grep -m1 "^# " | sed 's/^# //')

    # Extract summary (first blockquote after title)
    local summary
    summary=$(echo "$content" | grep -m1 "^> " | sed 's/^> //')

    # Extract sections and URLs
    local current_section=""
    echo "$content" | while IFS= read -r line; do
        if [[ "$line" =~ ^##\  ]]; then
            current_section=$(echo "$line" | sed 's/^## //')
            echo "SECTION:$current_section"
        elif [[ "$line" =~ ^\-\ \[.*\]\(.*\) ]]; then
            # Parse: - [Title](url): optional description
            local link_title link_path
            link_title=$(echo "$line" | sed 's/^- \[\([^]]*\)\].*/\1/')
            link_path=$(echo "$line" | sed 's/^- \[[^]]*\](\([^)]*\)).*/\1/')
            echo "URL:$link_title|$link_path"
        fi
    done

    echo "TITLE:$title"
    echo "SUMMARY:$summary"
}
```

**Link regex pattern:**
```regex
- \[([^\]]+)\]\(([^)]+)\)(?::\s*(.+))?
     ↓           ↓              ↓
   title       path      description (optional)
```

---

### Hash Manifest

Generate SHA256 hash for change detection.

**Using bash:**
```bash
hash_manifest() {
    local content="$1"
    echo -n "$content" | sha256sum | cut -d' ' -f1
}
```

**Using Python:**
```python
import hashlib
def hash_manifest(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
```

---

### Resolve URL

Construct full URL from relative path.

**Algorithm:**
1. If path is absolute (starts with `http`), use as-is
2. Otherwise, prepend `base_url`
3. Ensure `.md` suffix if configured

**Using bash:**
```bash
resolve_url() {
    local base_url="$1"
    local path="$2"
    local add_suffix="${3:-true}"

    base_url="${base_url%/}"

    # Absolute URL
    if [[ "$path" =~ ^https?:// ]]; then
        echo "$path"
        return
    fi

    # Relative path - prepend base_url
    path="${path#/}"
    local full_url="${base_url}/${path}"

    # Add .md suffix if needed
    if [ "$add_suffix" = "true" ] && ! [[ "$full_url" =~ \.md$ ]]; then
        full_url="${full_url}.md"
    fi

    echo "$full_url"
}
```

**Examples:**
```bash
resolve_url "https://code.claude.com/docs/en" "skills"
# → https://code.claude.com/docs/en/skills.md

resolve_url "https://code.claude.com/docs/en" "/agents/overview.md"
# → https://code.claude.com/docs/en/agents/overview.md

resolve_url "https://code.claude.com/docs/en" "https://other.com/page.md"
# → https://other.com/page.md
```

---

### Setup Cache Directory

**Using bash:**
```bash
setup_llms_txt_cache() {
    local corpus_path="$1"
    local source_id="$2"
    local cache_path="${corpus_path%/}/.cache/llms-txt/${source_id}"

    mkdir -p "$cache_path"
    echo "$cache_path"
}
```

---

### Fetch Page

Fetch a single markdown page.

**Using Claude tools (preferred):**
```
WebFetch: {resolved_url}
Prompt: "Return the markdown content from this page"
```

**Using bash:**
```bash
fetch_page() {
    local url="$1"
    curl -sL "$url" 2>/dev/null
}
```

---

### Cache Page

Save fetched content to cache.

**Using bash:**
```bash
cache_page() {
    local corpus_path="$1"
    local source_id="$2"
    local relative_path="$3"
    local content="$4"
    local cache_dir="${corpus_path%/}/.cache/llms-txt/${source_id}"

    # Create subdirectories if needed
    local file_dir
    file_dir=$(dirname "$relative_path")
    mkdir -p "${cache_dir}/${file_dir}"

    # Ensure .md extension
    local cache_file="$relative_path"
    if ! [[ "$cache_file" =~ \.md$ ]]; then
        cache_file="${cache_file}.md"
    fi

    # Write content
    echo "$content" > "${cache_dir}/${cache_file}"
    echo "${cache_dir}/${cache_file}"
}
```

---

### Check Freshness

Compare stored hash to current manifest.

**Algorithm:**
1. Fetch current manifest
2. Hash current content
3. Compare to `manifest.last_hash` in config

**Using bash:**
```bash
check_freshness() {
    local base_url="$1"
    local stored_hash="$2"

    local content
    content=$(fetch_manifest "$base_url")
    if [ -z "$content" ]; then
        echo "error"
        return 1
    fi

    local current_hash
    current_hash=$(hash_manifest "$content")

    if [ "$current_hash" = "$stored_hash" ]; then
        echo "current"
    else
        echo "stale"
    fi
}
```

**Return values:**
- `current` - Hash matches, no changes
- `stale` - Hash differs, manifest has changed
- `error` - Could not fetch manifest

---

### Diff Manifests

Compare two manifest structures to find changes.

**Algorithm:**
1. Parse old manifest → old_sections, old_urls
2. Parse new manifest → new_sections, new_urls
3. Compare to find added/removed sections and URLs

**Using bash:**
```bash
diff_manifests() {
    local old_content="$1"
    local new_content="$2"

    # Extract all URLs from each manifest
    local old_urls new_urls
    old_urls=$(echo "$old_content" | grep -oP '\]\([^)]+\)' | sed 's/](\|)//g' | sort)
    new_urls=$(echo "$new_content" | grep -oP '\]\([^)]+\)' | sed 's/](\|)//g' | sort)

    # Find added URLs
    echo "=== ADDED ==="
    comm -13 <(echo "$old_urls") <(echo "$new_urls")

    # Find removed URLs
    echo "=== REMOVED ==="
    comm -23 <(echo "$old_urls") <(echo "$new_urls")
}
```

---

### List Cached Pages

**Using bash:**
```bash
list_cached_pages() {
    local corpus_path="$1"
    local source_id="$2"
    local cache_dir="${corpus_path%/}/.cache/llms-txt/${source_id}"

    find "$cache_dir" -name "*.md" -type f 2>/dev/null | while read -r file; do
        # Return relative path from cache dir
        echo "${file#$cache_dir/}"
    done
}
```

---

### Get Cache Age (Days)

**Using bash:**
```bash
get_page_cache_age() {
    local corpus_path="$1"
    local source_id="$2"
    local relative_path="$3"
    local cache_file="${corpus_path%/}/.cache/llms-txt/${source_id}/${relative_path}"

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

## Config Schema

```yaml
- id: "claude-code-docs"
  type: "llms-txt"

  # Manifest location and tracking
  manifest:
    url: "https://code.claude.com/docs/llms.txt"
    last_hash: "sha256:abc123..."
    last_fetched_at: "2025-01-10T12:00:00Z"

  # URL resolution
  urls:
    base_url: "https://code.claude.com/docs/en"
    suffix: ".md"  # Append to URLs if not present

  # Caching strategy
  cache:
    enabled: true
    dir: ".cache/llms-txt/claude-code-docs/"
    strategy: "selective"  # "full" | "selective" | "on-demand"
    sections: ["skills", "agents"]  # For selective caching

  # Discovered structure (populated by parse_manifest)
  structure:
    title: "Claude Code"
    summary: "Anthropic's official CLI for Claude"
    sections:
      - name: "Getting Started"
        urls:
          - path: "getting-started/overview.md"
            title: "Overview"
          - path: "getting-started/installation.md"
            title: "Installation"
      - name: "Skills"
        urls:
          - path: "skills.md"
            title: "Skills"

  last_indexed_at: "2025-01-10T..."
```

---

## Caching Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `full` | Cache all pages from manifest | Offline access, large corpora |
| `selective` | Cache only specified sections | Focus on subset of docs |
| `on-demand` | Cache as pages are accessed | Minimal storage, live access |

---

## Usage Notes

- Manifest changes trigger re-indexing opportunity
- Hash comparison is fast (no repo cloning needed)
- Raw markdown content requires no HTML extraction
- Section structure can inform index organization
- Cache can be cleared with `rm -rf .cache/llms-txt/{source_id}/`

## Related Patterns

- `web.md` - Similar caching operations
- `shared.md` - URL parsing, existence checks
- `../status.md` - Freshness checking
