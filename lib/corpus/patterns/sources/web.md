# Pattern: Web Sources

Manage cached web content (blog posts, external articles).

## Storage Location

`.cache/web/{source_id}/`

## Operations

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

## Usage Notes

- Web sources require manual refresh - no automatic change detection
- Content is fetched once and cached locally
- Cache age helps identify stale content
- Use `hiivmind-corpus-refresh` to re-fetch cached content

## Related Patterns

- `shared.md` - Existence checks
- `generated-docs.md` - Uses web caching optionally
