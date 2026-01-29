# Pattern: Index Fetching

## Purpose

Fetch documentation indexes (index.md, config.yaml) from remote GitHub repositories or local paths for registered corpora.

## When to Use

- When navigating a corpus (need to read index.md)
- When checking corpus status (need config.yaml for tracking info)
- When routing queries (need keywords from config.yaml)
- When refreshing cached content

## Fetch Strategies

### GitHub Sources

For corpora with `source.type: github`:

**Raw Content URL Pattern:**
```
https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}/{file}
```

**Examples:**
```bash
# Main repo, no subdirectory
https://raw.githubusercontent.com/hiivmind/hiivmind-corpus-flyio/main/index.md

# Mono-repo with subdirectory
https://raw.githubusercontent.com/hiivmind/hiivmind-corpus-data/main/hiivmind-corpus-polars/index.md
```

### Local Sources

For corpora with `source.type: local`:

**Direct Read:**
```
Read: {source.path}/index.md
Read: {source.path}/config.yaml
```

## Fetching Index Files

### Algorithm

```
1. Determine source type from registry
2. Build path to index.md:
   - GitHub: raw.githubusercontent.com/{repo}/{ref}/{path?}/index.md
   - Local: {source.path}/index.md
3. Fetch content
4. Parse for sub-index references
5. Optionally fetch sub-indexes
```

### Fetch Main Index (GitHub)

**Using Claude WebFetch:**
```
WebFetch: https://raw.githubusercontent.com/hiivmind/hiivmind-corpus-flyio/main/index.md
prompt: "Return the full content of this markdown file"
```

**Using bash (for caching):**
```bash
# Build URL
owner=$(echo "$repo" | cut -d'/' -f1)
name=$(echo "$repo" | cut -d'/' -f2)
url="https://raw.githubusercontent.com/${owner}/${name}/${ref}/${path:+$path/}index.md"

# Fetch
curl -sL "$url"
```

### Fetch Main Index (Local)

**Using Claude Read:**
```
Read: {source.path}/index.md
```

### Detect Sub-Indexes

Parse the main index for sub-index references:

```markdown
→ See [index-getting-started.md](index-getting-started.md) for 7 detailed entries
```

**Pattern to match:**
```regex
\[index-([a-z0-9-]+)\.md\]
```

### Fetch Sub-Indexes

When a query might match a specific section, fetch the relevant sub-index:

```
WebFetch: https://raw.githubusercontent.com/{repo}/{ref}/{path?}/index-{section}.md
prompt: "Return the full content of this markdown sub-index"
```

## Caching Strategy

### Clone-Based Caching

When `cache.strategy: clone`:

```bash
cache_dir=".corpus-cache/${corpus_id}"

# Check if cache exists and is fresh
if [ -d "$cache_dir" ]; then
    # Check TTL
    mtime=$(stat -c %Y "$cache_dir/index.md")
    now=$(date +%s)
    age=$((now - mtime))
    ttl_seconds=$((7 * 24 * 60 * 60))  # 7d

    if [ $age -lt $ttl_seconds ]; then
        # Use cache
        cat "$cache_dir/index.md"
        exit 0
    fi
fi

# Clone/pull fresh copy
if [ -d "$cache_dir/.git" ]; then
    git -C "$cache_dir" pull --quiet
else
    git clone --depth 1 --quiet "$repo_url" "$cache_dir"
fi

cat "$cache_dir/index.md"
```

### Fetch-Only (No Cache)

When `cache.strategy: fetch`:

Always fetch from source, no local caching:
```
WebFetch: {url}
```

## Extracting Document Paths

From index entries, extract the source:path reference:

**Index entry format:**
```markdown
- **Install flyctl** `flyio:flyctl/install.html.markerb` - Description
```

**Extraction pattern:**
```regex
`([^:]+):([^`]+)`
```
- Group 1: source_id (flyio)
- Group 2: relative_path (flyctl/install.html.markerb)

## Fetching Documentation Content

Once a path is identified from the index:

### From .source/ Clone

If corpus has local clone at `.corpus-cache/{id}/.source/`:
```
Read: .corpus-cache/{id}/.source/{source_id}/{path}
```

### From GitHub Raw

```bash
# Get source config from corpus config.yaml
source_repo=$(yq -r ".sources[] | select(.id == \"$source_id\") | .repo_url" config.yaml)
source_branch=$(yq -r ".sources[] | select(.id == \"$source_id\") | .branch" config.yaml)
docs_root=$(yq -r ".sources[] | select(.id == \"$source_id\") | .docs_root // \".\"" config.yaml)

# Build raw URL
url="https://raw.githubusercontent.com/${source_repo#https://github.com/}/${source_branch}/${docs_root}/${relative_path}"
```

**Using Claude WebFetch:**
```
WebFetch: https://raw.githubusercontent.com/superfly/docs/main/flyctl/install.html.markerb
prompt: "Return the full documentation content"
```

## Error Handling

**Index not found:**
```
Could not fetch index for corpus 'flyio'.
URL: https://raw.githubusercontent.com/hiivmind/hiivmind-corpus-flyio/main/index.md

The corpus may need to be built first:
  /hiivmind-corpus build flyio
```

**Network error:**
```
Network error fetching corpus index.

Try using a local cache:
  /hiivmind-corpus register --cache-strategy=clone github:hiivmind/hiivmind-corpus-flyio
```

**Invalid index format:**
```
Index file exists but appears invalid.
Missing expected structure (Quick Reference, section headers).

This corpus may need rebuilding:
  /hiivmind-corpus build flyio
```

## Performance Optimization

1. **Fetch config first** - Get keywords for routing before full index
2. **Cache keywords** - Store keywords in session memory for repeated queries
3. **Lazy sub-index loading** - Only fetch sub-indexes when query matches section
4. **Parallel fetching** - When searching multiple corpora, fetch in parallel

## Related Patterns

- **Registry Loading:** `registry-loading.md` - Finding registered corpora
- **Corpus Routing:** `corpus-routing.md` - Matching queries to corpora
- **Config Parsing:** `config-parsing.md` - Parsing corpus configurations
