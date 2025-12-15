# Pattern: Config Parsing

## Purpose

Extract fields from corpus `data/config.yaml` files using available YAML parsing tools.

## When to Use

- Reading corpus metadata (name, display_name, keywords)
- Accessing source configuration (repo_url, branch, last_commit_sha)
- Checking schema version
- Any operation that needs structured data from config.yaml

## Prerequisites

- **Tool detection** (see `tool-detection.md`) - Know which YAML parser is available
- Config file exists at `{corpus_path}/data/config.yaml`

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
    type: "git"  # git | local | web
    repo_url: "https://github.com/owner/repo"
    repo_owner: "owner"
    repo_name: "repo"
    branch: "main"
    docs_root: "docs"
    last_commit_sha: "abc123..."
    last_indexed_at: "2025-01-15T10:00:00Z"
```

## Extraction Patterns

### Get Corpus Name

**Algorithm:**
1. Read `.corpus.name` from config.yaml
2. If not found, return empty string

**Using yq:**
```bash
yq '.corpus.name' data/config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(yaml.safe_load(open('data/config.yaml')).get('corpus', {}).get('name', ''))"
```

**Using grep (fallback):**
```bash
grep -A1 '^corpus:' data/config.yaml | grep 'name:' | sed 's/.*name: *//' | tr -d '"'
```

---

### Get Corpus Display Name

**Algorithm:**
1. Read `.corpus.display_name` from config.yaml
2. If not found, infer from corpus directory name

**Using yq:**
```bash
yq '.corpus.display_name // empty' data/config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; c=yaml.safe_load(open('data/config.yaml')); print(c.get('corpus', {}).get('display_name', ''))"
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
yq -r '.corpus.keywords // empty | .[]?' data/config.yaml | paste -sd,
```

**Using Python:**
```bash
python3 -c "import yaml; print(','.join(yaml.safe_load(open('data/config.yaml')).get('corpus', {}).get('keywords', [])))"
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
yq '.schema_version // 1' data/config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(yaml.safe_load(open('data/config.yaml')).get('schema_version', 1))"
```

**Using grep:**
```bash
grep '^schema_version:' data/config.yaml | cut -d: -f2 | tr -d ' ' || echo "1"
```

---

### Get Source Count

**Algorithm:**
1. Read `.sources` array from config.yaml
2. Return length of array

**Using yq:**
```bash
yq '.sources | length' data/config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; print(len(yaml.safe_load(open('data/config.yaml')).get('sources', [])))"
```

**Using grep (approximate):**
```bash
grep -c '^ *- id:' data/config.yaml || echo "0"
```

---

### List Source IDs

**Algorithm:**
1. Read `.sources[].id` for each source
2. Return one ID per line

**Using yq:**
```bash
yq '.sources[].id' data/config.yaml
```

**Using Python:**
```bash
python3 -c "import yaml; [print(s['id']) for s in yaml.safe_load(open('data/config.yaml')).get('sources', [])]"
```

**Using grep:**
```bash
grep '^ *- id:' data/config.yaml | sed 's/.*id: *//' | tr -d '"'
```

---

### Get Source by ID

**Algorithm:**
1. Find source in `.sources[]` where `.id` matches
2. Return the full source object

**Using yq:**
```bash
yq '.sources[] | select(.id == "polars")' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('data/config.yaml')).get('sources', [])
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
yq '.sources[] | select(.id == "polars") | .repo_url' data/config.yaml

# Get last_commit_sha
yq '.sources[] | select(.id == "polars") | .last_commit_sha // ""' data/config.yaml

# Get branch (with default)
yq '.sources[] | select(.id == "polars") | .branch // "main"' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
sources = yaml.safe_load(open('data/config.yaml')).get('sources', [])
source = next((s for s in sources if s.get('id') == 'polars'), {})
print(source.get('repo_url', ''))
"
```

**Using grep (specific fields only):**
```bash
# This is fragile - only works for simple cases
grep -A20 "id: polars" data/config.yaml | grep 'repo_url:' | head -1 | sed 's/.*repo_url: *//' | tr -d '"'
```

---

### Iterate Over Sources

**Algorithm:**
1. Get all sources from `.sources[]`
2. For each source, extract needed fields

**Using yq:**
```bash
# Get id and type for each source
yq '.sources[] | .id + " " + .type' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
for s in yaml.safe_load(open('data/config.yaml')).get('sources', []):
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
yq -i '(.sources[] | select(.id == "polars")).last_commit_sha = "abc123"' data/config.yaml
yq -i '(.sources[] | select(.id == "polars")).last_indexed_at = "2025-01-15T10:00:00Z"' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml
from datetime import datetime

with open('data/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

for source in config.get('sources', []):
    if source.get('id') == 'polars':
        source['last_commit_sha'] = 'abc123'
        source['last_indexed_at'] = datetime.utcnow().isoformat() + 'Z'

with open('data/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

**Manual editing:**
If no tools available, guide user to edit the file manually.

---

### Add Corpus Keywords

**Using yq:**
```bash
yq -i '.corpus.keywords = ["polars", "dataframe", "lazy"]' data/config.yaml
```

**Using Python:**
```bash
python3 -c "
import yaml

with open('data/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config.setdefault('corpus', {})['keywords'] = ['polars', 'dataframe', 'lazy']

with open('data/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

---

## Cross-Platform Notes

| Operation | Unix | Windows (PowerShell) |
|-----------|------|---------------------|
| File path | `data/config.yaml` | `data\config.yaml` (or `/` works) |
| yq command | Same syntax | Same syntax |
| python3 | `python3` | `python` (usually) |

## Error Handling

### Config File Not Found

```
Configuration file not found at data/config.yaml

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

Try validating with: yq '.' data/config.yaml
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
- **sources.md** - Uses config parsing for source URLs and branches
