# File System Consequences

Consequences for reading and writing files.

---

## read_config

Read and parse corpus config.yaml.

```yaml
- type: read_config
  store_as: config
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `store_as` | string | Yes | State field to store parsed config |

**Effect:**
```
state.computed[store_as] = parse_yaml(read_file("data/config.yaml"))
```

**Failure:** If file doesn't exist or YAML is invalid.

---

## read_file

Read arbitrary file content.

```yaml
- type: read_file
  path: "data/index.md"
  store_as: computed.index_content
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | File path |
| `store_as` | string | Yes | State field for content |

**Effect:**
```
state.computed[store_as] = read_file(path)
```

---

## write_file

Write content to file.

```yaml
- type: write_file
  path: "data/uploads/${computed.source_id}/README.md"
  content: "# ${computed.source_id}\n\nUpload documents here."
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | File path |
| `content` | string | Yes | Content to write |

**Effect:**
```
write_file(path, content)
```

**Notes:**
- Creates parent directories if needed
- Overwrites existing content

---

## create_directory

Create directory (including parents).

```yaml
- type: create_directory
  path: "data/uploads/${computed.source_id}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Directory path |

**Effect:**
```bash
mkdir -p {path}
```

---

## delete_file

Delete file if exists.

```yaml
- type: delete_file
  path: ".cache/web/${source_id}/${computed.filename}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | File to delete |

**Notes:**
- No error if file doesn't exist
- Does not delete directories

---

## Related Documentation

- **Parent:** [README.md](README.md) - Extension overview
- **Core consequences:** [../core/](../core/) - Fundamental workflow operations
- **Shared patterns:** [../core/shared.md](../core/shared.md) - Path interpolation
- **Config operations:** [config.md](config.md) - Config.yaml modifications
