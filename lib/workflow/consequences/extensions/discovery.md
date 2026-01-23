# Discovery Consequences

Consequences for discovering installed corpora and other plugin components.

---

## discover_installed_corpora

Scan for installed documentation corpora.

```yaml
- type: discover_installed_corpora
  store_as: computed.available_corpora
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `store_as` | string | Yes | State field for corpus array |

**Effect:**
Scans these locations for corpora:
1. User-level: `~/.claude/skills/hiivmind-corpus-*`
2. Repo-local: `.claude-plugin/skills/hiivmind-corpus-*`
3. Marketplace plugins: `*/hiivmind-corpus-*/.claude-plugin/plugin.json`

Returns array of corpus objects:
```yaml
- name: "polars"
  status: "built"        # built | stale | placeholder
  description: "Polars DataFrame documentation"
  path: "/path/to/corpus"
  keywords: ["polars", "dataframe"]
```

**Corpus Object Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Corpus identifier (without `hiivmind-corpus-` prefix) |
| `status` | string | One of: `built`, `stale`, `placeholder` |
| `description` | string | Human-readable description |
| `path` | string | Absolute path to corpus directory |
| `keywords` | array | Search keywords from config.yaml |

**Status Values:**
| Status | Meaning |
|--------|---------|
| `built` | Index exists and is current |
| `stale` | Index exists but source has changed |
| `placeholder` | config.yaml exists but index not built |

See `lib/corpus/patterns/discovery.md` for full algorithm.

---

## Discovery Algorithm

### 1. Scan Locations

```
FOR each location IN [user_level, repo_local, marketplace]:
  patterns = get_glob_patterns(location)
  FOR each pattern IN patterns:
    matches = glob(pattern)
    FOR each match IN matches:
      IF is_valid_corpus(match):
        corpora.append(parse_corpus(match))
```

### 2. Validate Corpus

A valid corpus has:
- `data/config.yaml` with `project_name` field
- Either `SKILL.md` (user-level) or `skills/navigate/SKILL.md` (plugin)

### 3. Determine Status

```
IF not exists(data/index.md):
  status = "placeholder"
ELSE IF index_sha != config_sha:
  status = "stale"
ELSE:
  status = "built"
```

### 4. Extract Metadata

From `data/config.yaml`:
- `project_name` → `name`
- `description` → `description`
- `keywords` → `keywords`

---

## Common Patterns

### List Available Corpora

```yaml
nodes:
  discover:
    type: action
    actions:
      - type: discover_installed_corpora
        store_as: computed.corpora
      - type: display_table
        title: "Installed Corpora"
        headers: ["Name", "Status", "Description"]
        rows: "${computed.corpora_table}"
```

### Check for Specific Corpus

```yaml
nodes:
  find_corpus:
    type: action
    actions:
      - type: discover_installed_corpora
        store_as: computed.corpora
      - type: compute
        expression: "computed.corpora.find(c => c.name == arguments)"
        store_as: computed.target_corpus
    on_success: check_found

  check_found:
    type: decision
    conditions:
      - condition:
          evaluate_expression: "computed.target_corpus != null"
        goto: use_corpus
      - goto: corpus_not_found
```

### Filter by Status

```yaml
- type: discover_installed_corpora
  store_as: computed.all_corpora

- type: compute
  expression: "computed.all_corpora.filter(c => c.status == 'stale')"
  store_as: computed.stale_corpora
```

---

## Related Documentation

- **Parent:** [README.md](README.md) - Extension overview
- **Core consequences:** [../core/](../core/) - Fundamental workflow operations
- **Discovery patterns:** `lib/corpus/patterns/discovery.md` - Full algorithm
- **Status patterns:** `lib/corpus/patterns/status.md` - Freshness checking
