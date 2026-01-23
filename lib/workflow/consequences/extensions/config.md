# Config Modification Consequences

Consequences for modifying corpus config.yaml files.

---

## write_config_entry

Update specific field in config.yaml.

```yaml
- type: write_config_entry
  path: "sources[0].last_commit_sha"
  value: "${computed.new_sha}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | YAML path (yq-style) |
| `value` | any | Yes | Value to set |

**Effect:**
```
# Using yq
yq -i '{path} = {value}' data/config.yaml
```

**Path syntax examples:**
```yaml
# Top-level field
path: "project_name"

# Nested field
path: "metadata.version"

# Array element
path: "sources[0].branch"

# Array element by property
path: "sources[] | select(.id == \"main\").last_commit_sha"
```

---

## add_source

Add source entry to config.yaml.

```yaml
- type: add_source
  spec:
    id: "${computed.source_id}"
    type: git
    repo_url: "${source_url}"
    repo_owner: "${computed.owner}"
    repo_name: "${computed.name}"
    branch: main
    docs_root: "docs"
    last_commit_sha: "${computed.sha}"
    last_indexed_at: null
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `spec` | object | Yes | Source configuration object |

**Effect:**
```
config.sources.push(spec)
write_yaml(config, "data/config.yaml")
```

**Source spec fields by type:**

Git source:
```yaml
spec:
  id: "main"
  type: git
  repo_url: "https://github.com/org/repo"
  repo_owner: "org"
  repo_name: "repo"
  branch: "main"
  docs_root: "docs"
  last_commit_sha: "abc123"
  last_indexed_at: null
```

Local source:
```yaml
spec:
  id: "uploads"
  type: local
  path: "data/uploads"
  last_indexed_at: null
```

Web source:
```yaml
spec:
  id: "api-docs"
  type: web
  base_url: "https://docs.example.com"
  urls:
    - "/api/overview"
    - "/api/endpoints"
  last_indexed_at: null
```

---

## update_source

Update existing source in config.yaml.

```yaml
- type: update_source
  id: "${computed.source_id}"
  fields:
    last_commit_sha: "${computed.new_sha}"
    last_indexed_at: "${computed.timestamp}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | Yes | Source identifier |
| `fields` | object | Yes | Fields to update |

**Effect:**
```
source = config.sources.find(s => s.id == id)
Object.assign(source, fields)
write_yaml(config, "data/config.yaml")
```

**Common update patterns:**

After refresh:
```yaml
- type: update_source
  id: "main"
  fields:
    last_commit_sha: "${computed.new_sha}"
    last_indexed_at: "${computed.timestamp}"
```

Change branch:
```yaml
- type: update_source
  id: "main"
  fields:
    branch: "develop"
```

---

## Related Documentation

- **Parent:** [README.md](README.md) - Extension overview
- **Core consequences:** [../core/](../core/) - Fundamental workflow operations
- **File operations:** [file-system.md](file-system.md) - read_config, read_file
- **Config patterns:** `lib/corpus/patterns/config-parsing.md` - Tool-agnostic config access
