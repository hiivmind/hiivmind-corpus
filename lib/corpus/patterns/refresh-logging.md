# Refresh Logging Patterns

Patterns for logging, audit trails, and CI output during corpus refresh operations.

---

## Overview

The refresh workflow produces detailed execution logs that:
- Provide audit trails for automated/CI runs
- Support debugging with full decision history
- Enable CI/CD integration with structured output
- Track changes across refresh operations

---

## Log File Location

**Default:** `data/logs/`

**Filename format:** `refresh-{YYYY-MM-DD}-{HHMMSS}.{ext}`

**Extensions:**
- `.yaml` - YAML format (default)
- `.json` - JSON format
- `.md` - Markdown format

**Examples:**
- `refresh-2025-01-24-103045.yaml`
- `refresh-2025-01-24-140000.json`
- `refresh-2025-01-24-161532.md`

---

## Log Schema (YAML)

```yaml
# Refresh Log
# Generated: 2025-01-24T10:30:00.000Z

metadata:
  workflow_version: "1.0.0"
  corpus_name: "hiivmind-corpus-polars"
  corpus_path: "/home/user/.claude/skills/hiivmind-corpus-polars"

parameters:
  auto_approve: false
  status_only: false
  log_format: "yaml"
  ci_output: "github"

execution:
  start_time: "2025-01-24T10:30:00.000Z"
  end_time: "2025-01-24T10:30:45.000Z"
  duration_seconds: 45
  mode: "update"
  outcome: "success"
  ending_node: "success"

sources:
  checked: 3
  updated: 2
  details:
    - source_id: "polars"
      type: "git"
      status: "stale"
      indexed_sha: "abc123def456..."
      upstream_sha: "789xyz012..."
      commits_behind: 15
      action: "updated"
      new_sha: "789xyz012..."

    - source_id: "team-docs"
      type: "local"
      status: "current"
      action: "skipped"

    - source_id: "blog"
      type: "web"
      status: "cache_check"
      action: "refetched"

changes:
  - source_id: "polars"
    added_files:
      - "docs/guides/new-feature.md"
      - "docs/guides/migration-v1.md"
    modified_files:
      - "docs/reference/expressions.md"
      - "docs/reference/api.md"
    deleted_files:
      - "docs/deprecated/old-api.md"

index_updates:
  files_modified:
    - "data/index.md"
    - "data/index-reference.md"
  entries_added: 3
  entries_removed: 1
  keywords_preserved: true

node_history:
  - node: "read_config"
    timestamp: "2025-01-24T10:30:00.100Z"
    outcome: "success"

  - node: "check_has_sources"
    timestamp: "2025-01-24T10:30:00.150Z"
    outcome: "branch:true"

  - node: "prompt_command_mode"
    timestamp: "2025-01-24T10:30:02.000Z"
    outcome: "response:update"
    details:
      user_selection: "update"

  - node: "spawn_status_agents"
    timestamp: "2025-01-24T10:30:03.000Z"
    outcome: "success"
    details:
      agents_spawned: 3

  - node: "update_git_source"
    timestamp: "2025-01-24T10:30:15.000Z"
    outcome: "success"
    details:
      source_id: "polars"
      commits_pulled: 15

errors: []

warnings:
  - "Web source 'blog' cache is 14 days old"
  - "Local source 'team-docs' has no last_indexed_at timestamp"

summary: "Updated polars (15 commits), refetched blog. Index: +3/-1 entries."
```

---

## Field Reference

### metadata

| Field | Type | Description |
|-------|------|-------------|
| `workflow_version` | string | Version of refresh workflow |
| `corpus_name` | string | Name from config.yaml |
| `corpus_path` | string | Absolute path to corpus root |

### parameters

| Field | Type | Description |
|-------|------|-------------|
| `auto_approve` | boolean | Whether auto-approve mode was enabled |
| `status_only` | boolean | Whether status-only mode was requested |
| `log_format` | string | Log file format (yaml/json/markdown) |
| `ci_output` | string | CI output format (github/plain/json/none) |

### execution

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | string | ISO 8601 timestamp of workflow start |
| `end_time` | string | ISO 8601 timestamp of workflow end |
| `duration_seconds` | number | Total execution time in seconds |
| `mode` | string | Execution mode ("status" or "update") |
| `outcome` | string | Final outcome ("success", "partial", "error") |
| `ending_node` | string | Name of ending node reached |

### sources

| Field | Type | Description |
|-------|------|-------------|
| `checked` | number | Total sources checked |
| `updated` | number | Sources that were updated |
| `details` | array | Per-source status objects |

**Source detail object:**

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | string | Source identifier |
| `type` | string | Source type (git, local, web, etc.) |
| `status` | string | Status result (current, stale, unknown) |
| `indexed_sha` | string | SHA from config (git sources) |
| `upstream_sha` | string | Current upstream SHA (git sources) |
| `indexed_hash` | string | Hash from config (hash-based sources) |
| `current_hash` | string | Current hash (hash-based sources) |
| `commits_behind` | number | Commits behind upstream (git sources) |
| `action` | string | Action taken (skipped, updated, refetched) |
| `new_sha` | string | New SHA after update (git sources) |

### changes

Array of change objects per source:

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | string | Source identifier |
| `added_files` | array | Files added since last index |
| `modified_files` | array | Files modified since last index |
| `deleted_files` | array | Files deleted since last index |

### index_updates

| Field | Type | Description |
|-------|------|-------------|
| `files_modified` | array | Index files that were modified |
| `entries_added` | number | Entries added to index |
| `entries_removed` | number | Entries removed from index |
| `keywords_preserved` | boolean | Whether entry keywords were preserved |

### node_history

Array of node execution records:

| Field | Type | Description |
|-------|------|-------------|
| `node` | string | Node name |
| `timestamp` | string | ISO 8601 execution timestamp |
| `outcome` | string | Result (success, failure, branch:*, response:*) |
| `details` | object | Optional additional context |

### errors / warnings

- `errors`: Array of error objects with `message`, `details`, `timestamp`
- `warnings`: Array of warning message strings

---

## JSON Format

Same structure as YAML, serialized as JSON:

```json
{
  "metadata": {
    "workflow_version": "1.0.0",
    "corpus_name": "hiivmind-corpus-polars",
    "corpus_path": "/home/user/.claude/skills/hiivmind-corpus-polars"
  },
  "parameters": {
    "auto_approve": false,
    "status_only": false,
    "log_format": "json",
    "ci_output": "none"
  },
  "execution": {
    "start_time": "2025-01-24T10:30:00.000Z",
    "end_time": "2025-01-24T10:30:45.000Z",
    "duration_seconds": 45,
    "mode": "update",
    "outcome": "success",
    "ending_node": "success"
  },
  "sources": {
    "checked": 3,
    "updated": 2,
    "details": [...]
  },
  "changes": [...],
  "index_updates": {...},
  "node_history": [...],
  "errors": [],
  "warnings": [...],
  "summary": "Updated polars (15 commits). Index: +3/-1 entries."
}
```

---

## Markdown Format

Human-readable format for review:

```markdown
# Refresh Log: 2025-01-24 10:30:45

## Summary

| Field | Value |
|-------|-------|
| Corpus | hiivmind-corpus-polars |
| Mode | update |
| Outcome | success |
| Duration | 45s |
| Sources Checked | 3 |
| Sources Updated | 2 |

---

## Sources

### polars (git)

| Field | Value |
|-------|-------|
| Status | stale → updated |
| Indexed SHA | abc123def456... |
| Upstream SHA | 789xyz012... |
| Commits Behind | 15 |

**Changes:**
- **Added:** docs/guides/new-feature.md, docs/guides/migration-v1.md
- **Modified:** docs/reference/expressions.md, docs/reference/api.md
- **Deleted:** docs/deprecated/old-api.md

### team-docs (local)

| Field | Value |
|-------|-------|
| Status | current (skipped) |

### blog (web)

| Field | Value |
|-------|-------|
| Status | cache refreshed |

---

## Index Updates

- **Files:** data/index.md, data/index-reference.md
- **Entries Added:** 3
- **Entries Removed:** 1
- **Keywords Preserved:** Yes

---

## Warnings

- Web source 'blog' cache is 14 days old
- Local source 'team-docs' has no last_indexed_at timestamp

---

## Execution Path

| # | Node | Time | Outcome |
|---|------|------|---------|
| 1 | read_config | 10:30:00.100 | success |
| 2 | check_has_sources | 10:30:00.150 | branch:true |
| 3 | prompt_command_mode | 10:30:02.000 | response:update |
| 4 | spawn_status_agents | 10:30:03.000 | success |
| 5 | update_git_source | 10:30:15.000 | success |
| ... | ... | ... | ... |

---

*Generated by hiivmind-corpus-refresh v1.0.0*
```

---

## Config Schema: Logging Section

Add optional `logging` section to corpus `config.yaml`:

```yaml
# config.yaml

corpus:
  name: "hiivmind-corpus-polars"
  version: "1.0.0"

sources:
  - id: "polars"
    type: git
    # ...

# Optional logging configuration
logging:
  # Retention policy (default: none - keep all logs)
  retention:
    strategy: "none"    # none | days | count
    days: 30            # if strategy: days, keep logs from last N days
    count: 20           # if strategy: count, keep last N log files

  # Default log settings (can be overridden by CLI flags)
  defaults:
    format: "yaml"      # yaml | json | markdown
    location: "data/logs/"
    ci_output: "none"   # github | plain | json | none
    gitignore: false    # true to add logs to .gitignore
```

### Retention Strategies

| Strategy | Description | Parameters |
|----------|-------------|------------|
| `none` | Keep all logs forever (default) | - |
| `days` | Keep logs from last N days | `days: 30` |
| `count` | Keep last N log files | `count: 20` |

### CI Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `github` | GitHub Actions annotations | GitHub Actions CI |
| `plain` | KEY=VALUE format | Shell scripts, generic CI |
| `json` | JSON object | Programmatic parsing |
| `none` | No structured output | Interactive use |

---

## Entry Parameters

Parameters passed to refresh workflow:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--no-log` | boolean | false | Skip writing log file |
| `--log-format` | string | "yaml" | Log format: yaml, json, markdown |
| `--log-location` | string | "data/logs/" | Override log directory |
| `--ci-output` | string | "none" | CI output: github, plain, json, none |
| `--log-gitignore` | boolean | false | Add log to .gitignore |

### CLI Examples

```bash
# Normal interactive refresh (logs to data/logs/)
/hiivmind-corpus-refresh

# CI mode with GitHub Actions output
/hiivmind-corpus-refresh --auto-approve --ci-output=github

# Status check only, JSON output for parsing
/hiivmind-corpus-refresh --status-only --ci-output=json

# Refresh without writing log file
/hiivmind-corpus-refresh --no-log

# Custom log location
/hiivmind-corpus-refresh --log-location=.logs/

# Keep logs out of git
/hiivmind-corpus-refresh --log-gitignore
```

---

## Git Integration

### Default Behavior: Logs Are Committed

By default, `data/logs/` is committed to git:
- Provides audit trail across team members
- Enables debugging historical issues
- Tracks refresh frequency

### Optional: Gitignore Logs

To exclude logs from git:

1. **Per-run:** Use `--log-gitignore` flag
2. **Config:** Set `logging.defaults.gitignore: true`
3. **Manual:** Add to `.gitignore`:

```gitignore
# Refresh logs (optional - keep if audit trail desired)
data/logs/
```

---

## CI/CD Integration Examples

### GitHub Actions

```yaml
# .github/workflows/refresh-corpus.yml
name: Refresh Corpus

on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am
  workflow_dispatch:

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Refresh corpus
        run: |
          claude-code /hiivmind-corpus-refresh \
            --auto-approve \
            --ci-output=github

      - name: Commit changes
        if: success()
        run: |
          git add data/
          git diff --staged --quiet || git commit -m "Refresh corpus index"
          git push
```

### Plain CI (Shell Script)

```bash
#!/bin/bash
set -e

# Run refresh and capture output
output=$(claude-code /hiivmind-corpus-refresh \
  --auto-approve \
  --ci-output=plain)

# Parse output
eval "$output"

echo "Outcome: $REFRESH_OUTCOME"
echo "Sources updated: $REFRESH_SOURCES_UPDATED"
echo "Log file: $REFRESH_LOG"

if [ "$REFRESH_OUTCOME" != "success" ]; then
  exit 1
fi
```

### JSON Parsing

```python
import json
import subprocess

result = subprocess.run(
    ["claude-code", "/hiivmind-corpus-refresh",
     "--auto-approve", "--ci-output=json"],
    capture_output=True, text=True
)

data = json.loads(result.stdout.split('\n')[-1])  # Last line is JSON

if data["outcome"] == "success":
    print(f"Updated {data['sources_updated']} sources")
else:
    print(f"Refresh failed, see: {data['log_file']}")
```

---

## Related Documentation

- **Logging consequences:** `lib/workflow/consequences/extensions/logging.md`
- **Refresh workflow:** `skills/hiivmind-corpus-refresh/workflow.yaml`
- **Refresh skill:** `skills/hiivmind-corpus-refresh/SKILL.md`
- **Status patterns:** `lib/corpus/patterns/status.md`
- **Config parsing:** `lib/corpus/patterns/config-parsing.md`
