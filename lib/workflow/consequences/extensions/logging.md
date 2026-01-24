# Logging Consequences

Consequences for workflow execution logging, audit trails, and CI output.

---

## init_log

Initialize log structure for current workflow execution.

```yaml
- type: init_log
  store_as: computed.log
  metadata:
    workflow_version: "${workflow_version}"
    corpus_name: "${config.corpus.name}"
    corpus_path: "${PWD}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `store_as` | string | Yes | State field to store log object |
| `metadata` | object | No | Additional metadata to include |

**Effect:**
```
timestamp = ISO8601_now()
state.computed[store_as] = {
  metadata: {
    workflow_version: interpolate(metadata.workflow_version),
    corpus_name: interpolate(metadata.corpus_name),
    corpus_path: interpolate(metadata.corpus_path),
    ...metadata
  },
  parameters: {
    auto_approve: state.flags.auto_approve,
    status_only: state.flags.status_only,
    log_format: state.flags.log_format || "yaml",
    ci_output: state.flags.ci_output || "none"
  },
  execution: {
    start_time: timestamp,
    end_time: null,
    duration_seconds: null,
    mode: null,
    outcome: "in_progress",
    ending_node: null
  },
  sources: {
    checked: 0,
    updated: 0,
    details: []
  },
  changes: [],
  index_updates: {
    files_modified: [],
    entries_added: 0,
    entries_removed: 0,
    keywords_preserved: false
  },
  node_history: [],
  errors: [],
  warnings: [],
  summary: null
}
```

---

## log_node

Record node execution in the log history.

```yaml
- type: log_node
  node: "${current_node}"
  outcome: "success"
  details: {}
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `node` | string | Yes | Node name that was executed |
| `outcome` | string | Yes | Result: "success", "branch:{value}", "response:{id}" |
| `details` | object | No | Additional context for this node |

**Effect:**
```
state.computed.log.node_history.push({
  node: interpolate(node),
  timestamp: ISO8601_now(),
  outcome: interpolate(outcome),
  details: interpolate(details) || {}
})
```

**Outcome formats:**
- `"success"` - Action node completed successfully
- `"failure"` - Action node failed
- `"branch:true"` / `"branch:false"` - Conditional node result
- `"response:status"` - User selected "status" option
- `"response:update"` - User selected "update" option
- `"response:other"` - User provided custom input

---

## log_source_status

Log the status check result for a source.

```yaml
- type: log_source_status
  source_id: "${current_source.id}"
  type: "${current_source.type}"
  status: "${computed.status}"
  indexed_sha: "${current_source.last_commit_sha}"
  upstream_sha: "${computed.upstream_sha}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source_id` | string | Yes | Source identifier |
| `type` | string | Yes | Source type (git, local, web, etc.) |
| `status` | string | Yes | Status result (current, stale, unknown) |
| `indexed_sha` | string | No | SHA/hash stored in config |
| `upstream_sha` | string | No | Current upstream SHA/hash |
| `indexed_hash` | string | No | Alternative for hash-based sources |
| `current_hash` | string | No | Current hash for hash-based sources |
| `commits_behind` | number | No | Number of commits behind upstream |
| `action` | string | No | Action taken (skipped, updated, etc.) |

**Effect:**
```
state.computed.log.sources.checked += 1
state.computed.log.sources.details.push({
  source_id: interpolate(source_id),
  type: interpolate(type),
  status: interpolate(status),
  indexed_sha: interpolate(indexed_sha),
  upstream_sha: interpolate(upstream_sha),
  indexed_hash: interpolate(indexed_hash),
  current_hash: interpolate(current_hash),
  commits_behind: interpolate(commits_behind),
  action: interpolate(action) || "pending"
})
```

---

## log_source_changes

Log file changes for a source after update.

```yaml
- type: log_source_changes
  source_id: "${current_source.id}"
  changes: "${computed.file_changes}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source_id` | string | Yes | Source identifier |
| `changes` | object/array | Yes | File changes object |

**Effect:**
```
# Mark source as updated
source_detail = state.computed.log.sources.details.find(s => s.source_id == source_id)
if (source_detail) {
  source_detail.action = "updated"
  source_detail.new_sha = state.computed.new_sha
  state.computed.log.sources.updated += 1
}

# Record changes
state.computed.log.changes.push({
  source_id: interpolate(source_id),
  added_files: changes.added || [],
  modified_files: changes.modified || [],
  deleted_files: changes.deleted || []
})
```

**Changes object format:**
```yaml
changes:
  added:
    - "docs/guides/new-feature.md"
  modified:
    - "docs/reference/expressions.md"
  deleted: []
```

---

## log_index_update

Log index file updates.

```yaml
- type: log_index_update
  files: "${computed.index_files_modified}"
  entries_added: "${computed.entries_added}"
  entries_removed: "${computed.entries_removed}"
  keywords_preserved: true
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `files` | array | Yes | List of index files modified |
| `entries_added` | number | No | Number of entries added (default: 0) |
| `entries_removed` | number | No | Number of entries removed (default: 0) |
| `keywords_preserved` | boolean | No | Whether keywords were preserved (default: false) |

**Effect:**
```
state.computed.log.index_updates = {
  files_modified: interpolate(files) || [],
  entries_added: interpolate(entries_added) || 0,
  entries_removed: interpolate(entries_removed) || 0,
  keywords_preserved: interpolate(keywords_preserved) || false
}
```

---

## log_warning

Add a warning message to the log.

```yaml
- type: log_warning
  message: "Web source 'blog' cache is 14 days old"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | Yes | Warning message |

**Effect:**
```
state.computed.log.warnings.push(interpolate(message))
```

---

## log_error

Add an error to the log.

```yaml
- type: log_error
  message: "Failed to fetch upstream SHA for source 'main'"
  details: "${computed.error_details}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | Yes | Error message |
| `details` | any | No | Additional error details |

**Effect:**
```
state.computed.log.errors.push({
  message: interpolate(message),
  details: interpolate(details),
  timestamp: ISO8601_now()
})
```

---

## finalize_log

Complete log with timing and outcome information.

```yaml
- type: finalize_log
  outcome: "success"
  ending_node: "success"
  summary: "Updated polars (15 commits). Index: +1 entry."
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outcome` | string | Yes | Final outcome: "success", "partial", "error" |
| `ending_node` | string | Yes | Name of ending node reached |
| `summary` | string | No | Human-readable summary |

**Effect:**
```
end_time = ISO8601_now()
start_time = parse_time(state.computed.log.execution.start_time)
duration = (end_time - start_time) / 1000  # seconds

state.computed.log.execution.end_time = end_time
state.computed.log.execution.duration_seconds = duration
state.computed.log.execution.mode = state.command_mode
state.computed.log.execution.outcome = interpolate(outcome)
state.computed.log.execution.ending_node = interpolate(ending_node)
state.computed.log.summary = interpolate(summary)
```

---

## write_log

Write finalized log to file.

```yaml
- type: write_log
  format: "${flags.log_format || 'yaml'}"
  location: "${flags.log_location || 'data/logs/'}"
  filename: "refresh-${computed.timestamp_slug}.yaml"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `format` | string | No | Output format: "yaml", "json", "markdown" (default: "yaml") |
| `location` | string | No | Log directory (default: "data/logs/") |
| `filename` | string | No | Override filename (default: auto-generated) |

**Effect:**
```
format = interpolate(format) || "yaml"
location = interpolate(location) || "data/logs/"
timestamp_slug = format_timestamp(now(), "YYYY-MM-DD-HHmmss")

# Create directory if needed
mkdir -p {location}

# Generate filename
filename = interpolate(filename) || "refresh-{timestamp_slug}.{ext}"
ext = format == "markdown" ? "md" : format

# Format log content
if format == "yaml":
  content = yaml_serialize(state.computed.log)
elif format == "json":
  content = json_serialize(state.computed.log)
elif format == "markdown":
  content = markdown_format(state.computed.log)

# Write file
write_file("{location}/{filename}", content)

# Store path for CI output
state.computed.log_file_path = "{location}/{filename}"
```

**Filename format:** `refresh-{YYYY-MM-DD}-{HHMMSS}.{ext}`

Example: `refresh-2025-01-24-103045.yaml`

---

## apply_log_retention

Apply retention policy to clean up old logs.

```yaml
- type: apply_log_retention
  strategy: "${config.logging.retention.strategy || 'none'}"
  days: "${config.logging.retention.days}"
  count: "${config.logging.retention.count}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `strategy` | string | Yes | Retention strategy: "none", "days", "count" |
| `days` | number | No | Keep logs from last N days (if strategy: days) |
| `count` | number | No | Keep last N log files (if strategy: count) |
| `location` | string | No | Log directory (default: "data/logs/") |

**Effect:**
```
strategy = interpolate(strategy)
location = interpolate(location) || "data/logs/"

if strategy == "none":
  return  # No cleanup

# Get all refresh log files
log_files = glob("{location}/refresh-*.{yaml,json,md}")
log_files = sort_by_date_desc(log_files)

if strategy == "days":
  days = interpolate(days)
  cutoff = now() - days * 24 * 60 * 60 * 1000
  for file in log_files:
    if file.mtime < cutoff:
      delete_file(file)

elif strategy == "count":
  count = interpolate(count)
  if len(log_files) > count:
    for file in log_files[count:]:
      delete_file(file)
```

---

## output_ci_summary

Output CI-formatted summary for automated environments.

```yaml
- type: output_ci_summary
  format: "${flags.ci_output || 'none'}"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `format` | string | Yes | Output format: "github", "plain", "json", "none" |

**Effect:**

### GitHub Actions (`format: "github"`)

```
::group::Refresh Summary
Corpus: {corpus_name}
Mode: {mode}
Sources: {checked} checked, {updated} updated
Outcome: {outcome}
Duration: {duration}s
::endgroup::

::notice file=data/index.md::Index updated with {entries_added} new entry
::notice file=data/config.yaml::Source SHAs updated
```

For errors:
```
::error file=data/config.yaml::Failed to parse config
```

For warnings:
```
::warning::Web source 'blog' cache is 14 days old
```

### Plain Text (`format: "plain"`)

```
REFRESH_OUTCOME=success
REFRESH_MODE=update
REFRESH_SOURCES_CHECKED=3
REFRESH_SOURCES_UPDATED=2
REFRESH_DURATION=45
REFRESH_LOG=data/logs/refresh-2025-01-24-103000.yaml
```

### JSON (`format: "json"`)

```json
{
  "outcome": "success",
  "mode": "update",
  "sources_checked": 3,
  "sources_updated": 2,
  "duration_seconds": 45,
  "log_file": "data/logs/refresh-2025-01-24-103000.yaml"
}
```

### None (`format: "none"`)

No CI output produced. Normal display_message output only.

---

## Related Documentation

- **Parent:** [README.md](README.md) - Extension overview
- **Core consequences:** [../core/](../core/) - Fundamental workflow operations
- **Logging patterns:** `lib/corpus/patterns/refresh-logging.md` - Schema and format details
- **File operations:** [file-system.md](file-system.md) - write_file, create_directory
