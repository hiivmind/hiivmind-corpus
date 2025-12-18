# Pattern: Generated-Docs Sources

Manage auto-generated documentation that lives on the web but is tracked via git.

## Hybrid Nature

This source type combines:
- **Git tracking** - For change detection (see `git.md`)
- **Web fetching** - For content access (see `web.md`)

The source repository is tracked for changes, but content is fetched live from the web output.

## Storage Locations

- Source tracking: `.source/{source_id}/` (shallow clone)
- Optional cache: `.cache/web/{source_id}/`

## Operations

### Setup Generated-Docs Source

**Algorithm:**
1. Clone source repo (shallow) for SHA tracking
2. Discover URLs from web output (sitemap or crawl)
3. Store in config.yaml

**Using bash:**
```bash
setup_generated_docs_source() {
    local corpus_path="$1"
    local source_id="$2"
    local source_repo_url="$3"
    local branch="${4:-main}"
    local clone_path="${corpus_path%/}/.source/${source_id}"

    # Clone source repo for SHA tracking (shallow)
    mkdir -p "${corpus_path%/}/.source"
    git clone --depth 1 --branch "$branch" "$source_repo_url" "$clone_path"

    # Get initial SHA
    git -C "$clone_path" rev-parse HEAD
}
```

**Cross-reference:** For clone details, see `git.md#clone-a-git-repository`

---

### Discover URLs from Sitemap

Parse sitemap.xml to discover all available URLs.

**Using Claude tools (preferred):**
```
WebFetch: {sitemap_url}
Prompt: "Extract all URLs from this sitemap. Return as a list with path and title for each."
```

**Using bash (curl + grep):**
```bash
discover_urls_from_sitemap() {
    local sitemap_url="$1"
    local base_url="$2"

    # Fetch sitemap and extract URLs
    curl -s "$sitemap_url" | grep -oP '(?<=<loc>)[^<]+' | while read url; do
        # Convert full URL to path relative to base_url
        path=$(echo "$url" | sed "s|${base_url}||")
        echo "$path"
    done
}
```

**Example:**
```bash
discover_urls_from_sitemap "https://cli.github.com/sitemap.xml" "https://cli.github.com/manual"
# Output:
# /gh_pr_create
# /gh_issue_list
# /gh_auth_login
# ...
```

---

### Discover URLs by Crawling

For sites without sitemaps, crawl from base URL.

**Using Claude tools:**
```
WebFetch: {base_url}
Prompt: "Find all internal links on this page that appear to be documentation pages.
         Return as a list of paths relative to the base URL."
```

**Crawl depth:**
- Depth 1: Links from base URL only
- Depth 2: Links from base URL + one level deep
- Higher depths increase discovery but take longer

---

### Check Generated-Docs Source Freshness

Compare source repo SHA to detect when docs may have changed.

**Algorithm:**
1. Get `source_repo.last_commit_sha` from config
2. Fetch upstream SHA from `source_repo.url`
3. Compare and return status

**Using bash:**
```bash
check_generated_docs_freshness() {
    local corpus_path="$1"
    local source_id="$2"

    # Read config values (requires yq or Python)
    local source_url branch indexed_sha
    source_url=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.url" "${corpus_path%/}/data/config.yaml")
    branch=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.branch // \"main\"" "${corpus_path%/}/data/config.yaml")
    indexed_sha=$(yq ".sources[] | select(.id == \"$source_id\") | .source_repo.last_commit_sha // \"\"" "${corpus_path%/}/data/config.yaml")

    # Fetch upstream SHA
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

**Cross-reference:** For upstream SHA fetching, see `git.md#fetch-upstream-sha`

---

### Live Fetch Content

Fetch content from web output URL on demand (no caching by default).

**Using Claude tools:**
```
WebFetch: {base_url}{path}
Prompt: "Extract the main content from this documentation page.
         Return the command syntax, flags, options, and examples."
```

**Construct full URL:**
```bash
construct_doc_url() {
    local base_url="$1"
    local path="$2"

    # Remove trailing slash from base, ensure path starts with /
    base_url="${base_url%/}"
    path="/${path#/}"

    echo "${base_url}${path}"
}

# Example:
# construct_doc_url "https://cli.github.com/manual" "gh_pr_create"
# → https://cli.github.com/manual/gh_pr_create
```

---

### Optional: Cache Content for Offline Use

When `cache.enabled: true`, save fetched content locally.

**Using bash:**
```bash
cache_fetched_content() {
    local corpus_path="$1"
    local source_id="$2"
    local path="$3"
    local content="$4"
    local cache_dir="${corpus_path%/}/.cache/web/${source_id}"

    # Create cache directory
    mkdir -p "$cache_dir"

    # Generate filename from path
    local filename
    filename=$(echo "$path" | tr '/' '-' | sed 's/^-//')
    filename="${filename}.md"

    # Save content
    echo "$content" > "${cache_dir}/${filename}"
    echo "${cache_dir}/${filename}"
}
```

**Cross-reference:** For cache setup, see `web.md#setup-web-cache-directory`

---

### Re-discover URLs on Refresh

When source repo changes, sitemap may have new pages.

**Algorithm:**
1. Check source repo freshness
2. If stale, re-fetch sitemap
3. Compare discovered URLs to `web_output.discovered_urls`
4. Report new/removed pages
5. Update config with new URL list

---

## Config Schema

```yaml
- id: "gh-cli-manual"
  type: "generated-docs"

  # Git tracking (for change detection)
  source_repo:
    url: "https://github.com/cli/cli"
    branch: "trunk"
    docs_root: "cmd/"
    last_commit_sha: "abc123"

  # Web output (for live fetching)
  web_output:
    base_url: "https://cli.github.com/manual"
    sitemap_url: "https://cli.github.com/sitemap.xml"
    discovered_urls: []

  # Optional caching (default: live fetch)
  cache:
    enabled: false
    dir: ".cache/web/gh-cli-manual/"

  last_indexed_at: "2025-12-18T..."
```

---

## Related Patterns

- `git.md` - Clone operations, SHA tracking
- `web.md` - Cache operations
- `../status.md` - Source freshness checking
- `../config-parsing.md` - Reading source_repo/web_output config
