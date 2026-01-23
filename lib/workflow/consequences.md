# Workflow Consequences

Consequences are operations that mutate state or perform actions. Used in:
- **Action nodes** - Execute operations and store results
- **User prompt responses** - Apply changes before routing

All consequences either succeed or fail. Failures trigger `on_failure` routing.

---

## State Mutation Consequences

### set_flag

Set a boolean flag.

```yaml
- type: set_flag
  flag: config_found
  value: true
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `flag` | string | Yes | Flag name |
| `value` | boolean | Yes | Value to set |

**Effect:**
```
state.flags[flag] = value
```

---

### set_state

Set any state field.

```yaml
- type: set_state
  field: source_type
  value: git
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `field` | string | Yes | Field path (dot notation for nested) |
| `value` | any | Yes | Value to set (can use ${} interpolation) |

**Effect:**
```
set_state_value(field, value)
```

**Examples:**
```yaml
# Simple field
- type: set_state
  field: source_type
  value: git

# Nested field
- type: set_state
  field: computed.manifest.title
  value: "${fetch_result.title}"

# From interpolation
- type: set_state
  field: source_id
  value: "${computed.derived_id}"
```

---

### append_state

Append value to array field.

```yaml
- type: append_state
  field: computed.discovered_urls
  value:
    path: "/api/users"
    title: "User API"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `field` | string | Yes | Array field path |
| `value` | any | Yes | Value to append |

**Effect:**
```
get_state_value(field).push(value)
```

---

### clear_state

Reset field to null/empty.

```yaml
- type: clear_state
  field: computed.errors
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `field` | string | Yes | Field to clear |

**Effect:**
```
set_state_value(field, null)
```

---

### merge_state

Merge object into state field.

```yaml
- type: merge_state
  field: computed.source_config
  value:
    repo_owner: "${computed.owner}"
    repo_name: "${computed.name}"
    branch: main
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `field` | string | Yes | Object field to merge into |
| `value` | object | Yes | Object to merge |

**Effect:**
```
Object.assign(get_state_value(field), value)
```

---

## Evaluation Consequences

### evaluate

Evaluate expression and set flag based on result.

```yaml
- type: evaluate
  expression: "len(config.sources) == 0"
  set_flag: is_first_source
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expression` | string | Yes | Boolean expression |
| `set_flag` | string | Yes | Flag to set with result |

**Effect:**
```
state.flags[set_flag] = eval(expression)
```

**Expression syntax:** Same as `evaluate_expression` precondition.

---

### compute

Run expression and store result.

```yaml
- type: compute
  expression: "source_url.split('/').pop()"
  store_as: computed.repo_name
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expression` | string | Yes | Expression to evaluate |
| `store_as` | string | Yes | State field to store result |

**Effect:**
```
set_state_value(store_as, eval(expression))
```

---

## File System Consequences

### read_config

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

### read_file

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

### write_file

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

---

### create_directory

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

### delete_file

Delete file if exists.

```yaml
- type: delete_file
  path: ".cache/web/${source_id}/${computed.filename}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | File to delete |

---

## Config Modification Consequences

### write_config_entry

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

---

### add_source

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

---

### update_source

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

---

## Git Consequences

### clone_repo

Clone git repository.

```yaml
- type: clone_repo
  url: "${source_url}"
  dest: ".source/${computed.source_id}"
  branch: "${computed.branch}"
  depth: 1
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | Repository URL |
| `dest` | string | Yes | Destination path |
| `branch` | string | No | Branch to clone (default: default branch) |
| `depth` | number | No | Shallow clone depth (default: 1) |

**Effect:**
```bash
git clone --depth {depth} --branch {branch} {url} {dest}
```

---

### get_sha

Get HEAD commit SHA from repo.

```yaml
- type: get_sha
  repo_path: ".source/${computed.source_id}"
  store_as: computed.sha
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_path` | string | Yes | Path to git repo |
| `store_as` | string | Yes | State field for SHA |

**Effect:**
```bash
sha=$(git -C {repo_path} rev-parse HEAD)
state.computed[store_as] = sha
```

---

### git_pull

Pull latest changes.

```yaml
- type: git_pull
  repo_path: ".source/${computed.source_id}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_path` | string | Yes | Path to git repo |

**Effect:**
```bash
git -C {repo_path} pull --ff-only
```

---

### git_fetch

Fetch remote refs.

```yaml
- type: git_fetch
  repo_path: ".source/${computed.source_id}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo_path` | string | Yes | Path to git repo |

**Effect:**
```bash
git -C {repo_path} fetch
```

---

## Web Consequences

### web_fetch

Fetch URL content.

```yaml
- type: web_fetch
  url: "${source_url}/llms.txt"
  store_as: computed.manifest_check
  allow_failure: true
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to fetch |
| `store_as` | string | Yes | State field for result |
| `allow_failure` | boolean | No | If true, 4xx/5xx doesn't fail action |
| `prompt` | string | No | Prompt for WebFetch tool |

**Effect:**
```
result = WebFetch(url, prompt)
state.computed[store_as] = {
  status: result.status,
  content: result.content,
  url: url
}
```

**Result structure:**
```yaml
computed.manifest_check:
  status: 200          # HTTP status code
  content: "..."       # Response body
  url: "https://..."   # Requested URL
```

---

### cache_web_content

Save fetched content to cache file.

```yaml
- type: cache_web_content
  from: computed.fetch_result
  dest: ".cache/web/${source_id}/${computed.slug}.md"
  store_path_as: computed.cached_file
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from` | string | Yes | State field with fetch result |
| `dest` | string | Yes | Destination file path |
| `store_path_as` | string | No | State field to store path |

**Effect:**
```
content = get_state_value(from).content
write_file(dest, content)
if (store_path_as) set_state_value(store_path_as, dest)
```

---

## User Interaction Consequences

### display_message

Show message to user (informational).

```yaml
- type: display_message
  message: |
    Found ${computed.file_count} documentation files in source.
    Ready to proceed with indexing.
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | Yes | Message with ${} interpolation |

**Effect:**
Display message to user. No state changes.

---

### display_table

Show tabular data to user.

```yaml
- type: display_table
  title: "Discovered Sources"
  headers: ["ID", "Type", "Location"]
  rows: "${computed.sources_table}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | No | Table title |
| `headers` | array | Yes | Column headers |
| `rows` | string/array | Yes | Row data (state ref or literal) |

---

## Reference Consequences

### invoke_pattern

Execute a pattern document section.

```yaml
- type: invoke_pattern
  path: "lib/corpus/patterns/sources/git.md"
  section: "Clone Repository"
  context:
    repo_url: "${source_url}"
    source_id: "${computed.source_id}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Pattern document path |
| `section` | string | No | Specific section to execute |
| `context` | object | No | Variables available in pattern |

**Effect:**
1. Load document at path
2. If section specified, extract that section
3. Execute instructions with context variables
4. Return any outputs to workflow

---

## Control Flow Consequences

### create_checkpoint

Save state snapshot for potential rollback.

```yaml
- type: create_checkpoint
  name: "before_clone"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Checkpoint identifier |

**Effect:**
```
state.checkpoints[name] = deep_copy(state)
```

---

### rollback_checkpoint

Restore state from checkpoint.

```yaml
- type: rollback_checkpoint
  name: "before_clone"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Checkpoint to restore |

**Effect:**
```
state = state.checkpoints[name]
```

---

### spawn_agent

Launch a Task agent for parallel work.

```yaml
- type: spawn_agent
  subagent_type: "source-scanner"
  prompt: "Scan source ${source_id} for documentation structure"
  store_as: computed.scan_results.${source_id}
  run_in_background: true
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subagent_type` | string | Yes | Agent type |
| `prompt` | string | Yes | Task prompt |
| `store_as` | string | Yes | State field for result |
| `run_in_background` | boolean | No | Async execution |

---

## Timestamp Consequences

### set_timestamp

Set current ISO timestamp.

```yaml
- type: set_timestamp
  store_as: computed.indexed_at
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `store_as` | string | Yes | State field for timestamp |

**Effect:**
```
state.computed[store_as] = new Date().toISOString()
```

---

## Hash Consequences

### compute_hash

Compute SHA-256 hash of content.

```yaml
- type: compute_hash
  from: computed.manifest_content
  store_as: computed.manifest_hash
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `from` | string | Yes | State field with content |
| `store_as` | string | Yes | State field for hash |

**Effect:**
```
hash = sha256(get_state_value(from))
set_state_value(store_as, "sha256:" + hash)
```

---

## Skill Invocation Consequences

### invoke_skill

Invoke another skill and wait for completion.

```yaml
- type: invoke_skill
  skill: "hiivmind-corpus-init"
  args: "${source_url}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill` | string | Yes | Skill name (without plugin prefix) |
| `args` | string | No | Arguments to pass to the skill |

**Effect:**
```
Invoke the Skill tool:
  Skill: {skill}
  Args: {args}
```

The invoked skill takes over the conversation. This consequence is typically the last action before reaching a success ending.

---

### evaluate_keywords

Match user input against keyword sets to detect intent.

```yaml
- type: evaluate_keywords
  input: "${arguments}"
  keyword_sets:
    init:
      - "create"
      - "new"
      - "index"
    refresh:
      - "update"
      - "sync"
      - "check"
  store_as: computed.detected_intent
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `input` | string | Yes | User input to match against |
| `keyword_sets` | object | Yes | Map of intent names to keyword arrays |
| `store_as` | string | Yes | State field for matched intent |

**Effect:**
```
FOR each keyword_set IN keyword_sets:
  FOR each keyword IN keyword_set.keywords:
    IF input.toLowerCase().includes(keyword.toLowerCase()):
      set_state_value(store_as, keyword_set.name)
      RETURN success
set_state_value(store_as, null)
RETURN success
```

Matches the **first** keyword set that contains a phrase found in the input (case-insensitive). Returns null if no match found.

---

### discover_installed_corpora

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

See `lib/corpus/patterns/discovery.md` for full algorithm.

---

## Consequence Execution

Consequences in an action node execute **sequentially**:

```yaml
actions:
  - type: read_config        # 1. Execute first
    store_as: config
  - type: set_flag           # 2. Execute second (uses config)
    flag: config_found
    value: true
  - type: evaluate           # 3. Execute third (uses config)
    expression: "len(config.sources) == 0"
    set_flag: is_first_source
```

**On failure:**
- If any consequence fails, remaining consequences are skipped
- Action node routes to `on_failure`
- State mutations from failed action may be partial (use checkpoints)

---

## Related Documentation

- **Schema:** `lib/workflow/schema.md` - Workflow YAML structure
- **Preconditions:** `lib/workflow/preconditions.md` - Boolean evaluations
- **Execution:** `lib/workflow/execution.md` - Turn loop
- **State:** `lib/workflow/state.md` - Runtime state structure
