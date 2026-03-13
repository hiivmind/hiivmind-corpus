# Pattern: Registry Loading

## Purpose

Load and parse the per-project corpus registry (`.hiivmind/corpus/registry.yaml`) to discover which corpora are configured for a project.

## When to Use

- When navigating corpus content (need to find registered corpora)
- When checking corpus status
- When routing queries based on keywords
- When updating corpus configuration

## Prerequisites

**See:** `lib/corpus/patterns/tool-detection.md`

For fetching remote corpus configs from GitHub, detect available tools:

| Tool | Purpose | Detection | Fallback |
|------|---------|-----------|----------|
| `gh` (GitHub CLI) | Fetch GitHub content via API | `command -v gh` | raw.githubusercontent.com URLs |

## Registry Location

The registry file is stored at:

```
{project_root}/.hiivmind/corpus/registry.yaml
```

## Registry Schema

```yaml
schema_version: 1

corpora:
  - id: flyio                          # Unique identifier
    source:
      type: github                     # github | local
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main                        # branch, tag, or commit
      path: null                       # subdirectory (for mono-repos)
    cache:
      strategy: clone                  # clone | fetch | none
      path: .corpus-cache/flyio        # local cache location
      ttl: 7d                          # refresh interval

  - id: polars
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-data
      path: hiivmind-corpus-polars     # subdirectory
      ref: main
    cache:
      strategy: fetch
      ttl: 1d

  - id: internal
    source:
      type: local
      path: ./docs/corpus              # relative or absolute path
    cache:
      strategy: none                   # already local
```

## Loading Algorithm

### Step 1: Locate Registry

```bash
# Check for registry file
if [ -f ".hiivmind/corpus/registry.yaml" ]; then
    echo "Registry found"
else
    echo "No registry - run /hiivmind-corpus register"
fi
```

**Using Claude tools:**
```
Read: .hiivmind/corpus/registry.yaml
```

If file doesn't exist, the navigate skill should:
1. Check for legacy plugin-based corpora (backward compatibility)
2. Offer to run the register command

### Step 2: Parse Registry

**Using yq:**
```bash
# Get all corpus IDs
yq -r '.corpora[].id' .hiivmind/corpus/registry.yaml

# Get source info for a specific corpus
yq -r '.corpora[] | select(.id == "flyio") | .source' .hiivmind/corpus/registry.yaml
```

**Using Claude Read tool:**
Read the file and parse the YAML structure directly.

### Step 3: Build Corpus Index

For each registered corpus, build an in-memory index:

```yaml
corpora_index:
  flyio:
    source_type: github
    repo: hiivmind/hiivmind-corpus-flyio
    ref: main
    path: null
    cache_path: .corpus-cache/flyio
    keywords: []           # populated from corpus config
    last_fetched: null     # populated from cache metadata
  polars:
    source_type: github
    repo: hiivmind/hiivmind-corpus-data
    path: hiivmind-corpus-polars
    ref: main
    cache_path: null
    keywords: []
    last_fetched: null
```

## Fetching Corpus Config

Once a corpus is identified from the registry, fetch its `config.yaml` to get keywords:

### From GitHub

**Using gh api (preferred):**
```bash
# Parse owner/repo from registry
owner=$(echo "$repo" | cut -d'/' -f1)
name=$(echo "$repo" | cut -d'/' -f2)

# Fetch config.yaml content
gh api "repos/${owner}/${name}/contents/${path:+$path/}config.yaml${ref:+?ref=$ref}" --jq '.content' | base64 -d
```

**Using Claude Bash tool (preferred):**
```bash
gh api repos/hiivmind/hiivmind-corpus-flyio/contents/config.yaml --jq '.content' | base64 -d
```

**Fallback: Using curl with raw.githubusercontent.com:**
```bash
# Fetch config.yaml from GitHub
curl -sL "https://raw.githubusercontent.com/${repo}/${ref}/${path:+$path/}config.yaml"
```

**Fallback: Using Claude WebFetch:**
```
WebFetch: https://raw.githubusercontent.com/hiivmind/hiivmind-corpus-flyio/main/config.yaml
prompt: "Extract the corpus.keywords array from this YAML config"
```

**Note:** Prefer `gh api` as it works consistently for all public repositories. The raw.githubusercontent.com fallback may return 404 for some repositories.

### From Local Path

```bash
# Read local config
cat "${path}/config.yaml"
```

**Using Claude Read:**
```
Read: {path}/config.yaml
```

## Cache Integration

When `cache.strategy` is `clone`:
1. Check if `.corpus-cache/{id}/` exists
2. If exists and within TTL, use cached copy
3. If stale or missing, clone/pull from source

When `cache.strategy` is `fetch`:
1. Always fetch from source
2. Use GitHub raw content or WebFetch
3. No local caching

When `cache.strategy` is `none`:
1. Source is already local
2. Read directly from `source.path`

## Error Handling

**Registry not found:**
```
No corpus registry found at .hiivmind/corpus/registry.yaml

To register a corpus, use:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

**Invalid registry format:**
```
Registry file is invalid YAML. Please check:
  .hiivmind/corpus/registry.yaml

Run /hiivmind-corpus register to recreate it.
```

**Corpus not found in registry:**
```
Corpus 'unknown' is not registered.

Available corpora:
  - flyio
  - polars

Register with: /hiivmind-corpus register github:owner/repo
```

## Related Patterns

- **Tool Detection:** `tool-detection.md` - Detecting gh CLI and other tools
- **Index Fetching:** `index-fetching.md` - How to fetch index.md from sources
- **Corpus Routing:** `corpus-routing.md` - Keyword-based corpus selection
- **Config Parsing:** `config-parsing.md` - Parsing corpus config.yaml
