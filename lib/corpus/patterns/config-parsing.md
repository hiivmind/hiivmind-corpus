# Pattern: Config Parsing

## Purpose

Extract fields from corpus `config.yaml` files using available YAML parsing tools.

## When to Use

- Reading corpus metadata (name, display_name, keywords)
- Accessing source configuration (repo_url, branch, last_commit_sha)
- Checking schema version
- Any operation that needs structured data from config.yaml

## Prerequisites

- **Tool detection** (see `tool-detection.md`) - Know which YAML parser is available
- Config file exists at `{corpus_path}/config.yaml` (data-only) or `{corpus_path}/config.yaml` (legacy plugin)

## Path Resolution

**See:** `paths.md` for full path detection logic.

Data-only corpora store config at root level:
```
{corpus_path}/config.yaml        # Data-only (preferred)
{corpus_path}/config.yaml   # Legacy plugin structure
```

Before parsing, detect the correct path:
```bash
# Detect config path
if [ -f "config.yaml" ]; then
    CONFIG_PATH="config.yaml"
elif [ -f "config.yaml" ]; then
    CONFIG_PATH="config.yaml"
else
    echo "No config.yaml found" && exit 1
fi
```

**Examples below use `config.yaml` (data-only format). For legacy plugins, substitute `config.yaml`.**

## Config Schema Reference

```yaml
schema_version: 2

corpus:
  name: "project-name"
  display_name: "Project Name"
  keywords:
    - keyword1
    - keyword2
  created_at: "2025-01-15T10:00:00Z"

sources:
  - id: "source-id"
    type: "git"  # git | local | web | generated-docs
    repo_url: "https://github.com/owner/repo"
    repo_owner: "owner"
    repo_name: "repo"
    branch: "main"
    docs_root: "docs"
    last_commit_sha: "abc123..."
    last_indexed_at: "2025-01-15T10:00:00Z"
```

---

## Source Type Schemas

### Git Source

Standard git repository with docs in the repo:

```yaml
- id: "polars"
  type: "git"
  repo_url: "https://github.com/pola-rs/polars"
  repo_owner: "pola-rs"
  repo_name: "polars"
  branch: "main"
  docs_root: "docs"
  last_commit_sha: "abc123..."
  last_indexed_at: "2025-01-15T10:00:00Z"
```

### Local Source

User-uploaded files stored in `uploads/` (data-only) or `data/uploads/` (legacy):

```yaml
- id: "team-standards"
  type: "local"
  path: "uploads/team-standards/"
  description: "Internal team documentation"
  files:
    - "coding-guidelines.md"
    - "pr-process.md"
  last_indexed_at: "2025-01-15T10:00:00Z"
```

### Web Source

Cached web pages (pre-fetched):

```yaml
- id: "kent-testing-blog"
  type: "web"
  description: "Testing best practices articles"
  base_url: "https://kentcdodds.com/blog"
  cache_dir: ".cache/web/kent-testing-blog/"
  urls:
    - path: "/testing-implementation-details"
      title: "Testing Implementation Details"
      fetched_at: "2025-01-15T10:00:00Z"
      content_hash: "sha256:abc123..."
      cached_file: "testing-implementation-details.md"
  last_indexed_at: "2025-01-15T10:00:00Z"
```

### Generated-Docs Source (NEW)

Auto-generated documentation sites where content is rendered from a source repository.
Tracks git for change detection, fetches content live from web.

**Use cases:** MkDocs, Sphinx, ReadTheDocs, gh CLI manual, API docs

```yaml
- id: "gh-cli-manual"
  type: "generated-docs"

  # Git tracking (for change detection)
  source_repo:
    url: "https://github.com/cli/cli"
    branch: "trunk"
    docs_root: "cmd/"                    # Path containing source files
    last_commit_sha: "abc123..."         # Last checked SHA

  # Web output (for live fetching)
  web_output:
    base_url: "https://cli.github.com/manual"
    sitemap_url: "https://cli.github.com/sitemap.xml"  # Optional
    discovered_urls:                     # Auto-populated by discovery
      - path: "/gh_pr_create"
        title: "gh pr create"
      - path: "/gh_issue_list"
        title: "gh issue list"

  # Optional caching (default: live fetch)
  cache:
    enabled: false                       # true = cache for offline
    dir: ".cache/web/gh-cli-manual/"

  last_indexed_at: "2025-01-15T10:00:00Z"
```

**Key differences from `web` type:**
- **Change detection**: Tracks `source_repo` git SHA to know when docs may have changed
- **Content access**: Default is live WebFetch (no mandatory caching)
- **URL discovery**: Auto-discovers URLs via sitemap or patterns
- **No pre-caching required**: URLs stored but content fetched on demand

**Validation rules:**
- `source_repo.url` is required (must be valid git URL)
- `source_repo.branch` defaults to "main" if not specified
- `web_output.base_url` is required
- `cache.enabled` defaults to `false`
- `discovered_urls` can be empty (populated by discovery)

## Extraction Patterns

### Get Corpus Name

**Algorithm:**
1. Read `.corpus.name` from config.yaml
2. If not found, return empty string

**Using yq:**
```bash
yq '.corpus.name' config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')).get('corpus', {}).get('name', ''))"
```

**Using grep (fallback):**
```bash
grep -A1 '^corpus:' config.yaml | grep 'name:' | sed 's/.*name: *//' | tr -d '"'
```

---

### Get Corpus Display Name

**Algorithm:**
1. Read `.corpus.display_name` from config.yaml
2. If not found, infer from corpus directory name

**Using yq:**
```bash
yq '.corpus.display_name // empty' config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(c.get('corpus', {}).get('display_name', ''))"
```

**Fallback inference:**
```bash
# From corpus directory name: hiivmind-corpus-polars → Polars
basename "$(pwd)" | sed 's/hiivmind-corpus-//' | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g'
```

---

### Get Corpus Keywords

**Algorithm:**
1. Read `.corpus.keywords[]` array from config.yaml
2. If not found or empty, infer from corpus name
3. Return comma-separated list

**Using yq:**
```bash
yq -r '.corpus.keywords // empty | .[]?' config.yaml | paste -sd,
```

**Using Python:**
```bash
python3 -c "import yaml; print(','.join(yaml.safe_load(open('config.yaml')).get('corpus', {}).get('keywords', [])))"
```

**Fallback inference:**
```bash
# From corpus name: hiivmind-corpus-polars → polars
basename "$(pwd)" | sed 's/hiivmind-corpus-//'
```

---

### Get Schema Version

**Algorithm:**
1. Read `.schema_version` from config.yaml
2. Default to 1 if not found

**Using yq:**
```bash
yq '.schema_version // 1' config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')).get('schema_version', 1))"
```

**Using grep:**
```bash
grep '^schema_version:' config.yaml | cut -d: -f2 | tr -d ' ' || echo "1"
```

---

### Get Source Count

**Algorithm:**
1. Read `.sources` array from config.yaml
2. Return length of array

**Using yq:**
```bash
yq '.sources | length' config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(len(yaml.safe_load(open('config.yaml')).get('sources', [])))"
```

**Using grep (approximate):**
```bash
grep -c '^ *- id:' config.yaml || echo "0"
```

---

### List Source IDs

**Algorithm:**
1. Read `.sources[].id` for each source
2. Return one ID per line

**Using yq:**
```bash
yq '.sources[].id' config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; [print(s['id']) for s in yaml.safe_load(open('config.yaml')).get('sources', [])]"
```

**Using grep:**
```bash
grep '^ *- id:' config.yaml | sed 's/.*id: *//' | tr -d '"'
```

---

### Get Source by ID

**Algorithm:**
1. Find source in `.sources[]` where `.id` matches
2. Return the full source object

**Using yq:**
```bash
yq '.sources[] | select(.id == "polars")' config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('config.yaml')).get('sources', [])
for s in sources:
    if s.get('id') == 'polars':
        print(yaml.dump(s))
        break
"
```

---

### Get Source Field

For a specific source, get any field.

**Using yq:**
```bash
# Get repo_url for source "polars"
yq '.sources[] | select(.id == "polars") | .repo_url' config.yaml

# Get last_commit_sha
yq '.sources[] | select(.id == "polars") | .last_commit_sha // ""' config.yaml

# Get branch (with default)
yq '.sources[] | select(.id == "polars") | .branch // "main"' config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('config.yaml')).get('sources', [])
source = next((s for s in sources if s.get('id') == 'polars'), {})
print(source.get('repo_url', ''))
"
```

**Using grep (specific fields only):**
```bash
# This is fragile - only works for simple cases
grep -A20 "id: polars" config.yaml | grep 'repo_url:' | head -1 | sed 's/.*repo_url: *//' | tr -d '"'
```

---

### Iterate Over Sources

**Algorithm:**
1. Get all sources from `.sources[]`
2. For each source, extract needed fields

**Using yq:**
```bash
# Get id and type for each source
yq '.sources[] | .id + " " + .type' config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
for s in yaml.safe_load(open('config.yaml')).get('sources', []):
    print(f\"{s['id']} {s['type']}\")
"
```

---

## Writing to Config

### Update Source SHA

**Algorithm:**
1. Find source by ID
2. Update `.last_commit_sha` and `.last_indexed_at`

**Using yq (in-place):**
```bash
yq -i '(.sources[] | select(.id == "polars")).last_commit_sha = "abc123"' config.yaml
yq -i '(.sources[] | select(.id == "polars")).last_indexed_at = "2025-01-15T10:00:00Z"' config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
from datetime import datetime

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

for source in config.get('sources', []):
    if source.get('id') == 'polars':
        source['last_commit_sha'] = 'abc123'
        source['last_indexed_at'] = datetime.utcnow().isoformat() + 'Z'

with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

**Manual editing:**
If no tools available, guide user to edit the file manually.

---

### Add Corpus Keywords

**Using yq:**
```bash
yq -i '.corpus.keywords = ["polars", "dataframe", "lazy"]' config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config.setdefault('corpus', {})['keywords'] = ['polars', 'dataframe', 'lazy']

with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

---

## Cross-Platform Notes

| Operation | Unix | Windows (PowerShell) |
|-----------|------|---------------------|
| File path | `config.yaml` | `config.yaml` (forward slashes work) |
| yq command | Same syntax | Same syntax |
| python3 | `python3` | `python` (usually) |

## Error Handling

### Config File Not Found

```
Configuration file not found (checked config.yaml and data/config.yaml)

This corpus may not be properly initialized. Try:
- Running hiivmind-corpus-init to create a new corpus
- Checking you're in the correct directory
```

### Parse Error

```
Failed to parse config.yaml - the file may be malformed.

Common issues:
- Incorrect indentation (YAML uses spaces, not tabs)
- Missing quotes around strings with special characters
- Duplicate keys

Try validating with: yq '.' config.yaml
```

### Field Not Found

Return empty/default values rather than erroring:
- `// empty` in yq
- `.get('field', '')` in Python
- Handle missing grep output gracefully

## Fallback Limitations

The grep/sed fallback has significant limitations:

| Works For | Fails For |
|-----------|-----------|
| Simple `key: value` pairs | Multi-line values |
| Top-level keys | Deeply nested structures |
| Single values | Arrays (partial support) |
| Unquoted strings | Quoted strings with colons |

**Recommendation:** If using grep fallback frequently, strongly encourage user to install yq or PyYAML.

## Related Patterns

- **tool-detection.md** - Determines which parsing method to use
- **discovery.md** - Uses config parsing for corpus metadata
- **status.md** - Uses config parsing for source tracking data
- **sources/** - Uses config parsing for source URLs and branches
