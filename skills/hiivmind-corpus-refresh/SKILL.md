---
name: hiivmind-corpus-refresh
description: >
  This skill should be used when the user asks to "refresh corpus", "sync documentation",
  "update corpus index", "check for upstream changes", "corpus is stale", "docs are outdated",
  or mentions that documentation sources have changed. Triggers on "refresh my [corpus name] corpus",
  "sync corpus with upstream", "check if docs are current", "update from source repo", or
  "hiivmind-corpus refresh".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch, Task
---

# Refresh Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/workflow.yaml`

---

## Entry Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--auto-approve` | boolean | false | Skip all user prompts, use safe defaults for CI/automated runs |
| `--status-only` | boolean | false | Only check status, don't offer to update |
| `--no-log` | boolean | false | Skip writing log file |
| `--log-format` | string | "yaml" | Log format: yaml, json, or markdown |
| `--log-location` | string | "data/logs/" | Override log directory |
| `--ci-output` | string | "none" | CI output: github, plain, json, or none |
| `--log-gitignore` | boolean | false | Add log to .gitignore (not committed) |

Set via initial_state flags when invoking programmatically.

---

## Execution Instructions

### Phase 1: Initialize

1. **Load workflow.yaml** from this skill directory:
   Read: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/workflow.yaml`

2. **Check entry preconditions** (see `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`):
   - `config_exists`: Verify `data/config.yaml` exists

3. **Initialize runtime state**:
   ```yaml
   workflow_name: refresh
   workflow_version: "1.0.0"
   current_node: read_config
   previous_node: null
   history: []
   user_responses: {}
   phase: "validate"
   command_mode: null
   sources: []
   sources_to_update: []
   status_report: []
   current_source: null
   index_structure:
     is_tiered: false
     sub_indexes: []
   computed:
     source_count: 0
     all_changes: []
     affected_sections: []
     current_source_index: 0
     updated_sources: []
     log: null
     log_file_path: null
     timestamp_slug: null
   flags:
     config_found: false
     has_sources: false
     index_built: false
     is_multi_source: false
     is_tiered_index: false
     auto_approve: false
     status_only: false
     has_stale_sources: false
     all_sources_current: false
     no_log: false
     log_format: "yaml"
     log_location: "data/logs/"
     ci_output: "none"
     log_gitignore: false
   checkpoints: {}
   ```

---

### Phase 2: Execution Loop

Execute nodes until an ending is reached:

```
LOOP:
  1. Get current node from workflow.nodes[current_node]

  2. Check for ending:
     - IF current_node is in workflow.endings:
       - Display ending.message with ${} interpolation
       - IF ending.type == "error" AND ending.recovery:
         - Display recovery instructions
       - IF ending.type == "success" AND ending.summary:
         - Display summary fields
       - STOP

  3. Execute based on node.type:

     ACTION NODE:
     - FOR each action IN node.actions:
       - Execute action per ${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md
       - Store results in state.computed if store_as specified
     - IF all actions succeed:
       - Set current_node = node.on_success
     - ELSE:
       - Set current_node = node.on_failure
     - CONTINUE

     CONDITIONAL NODE:
     - Evaluate node.condition per ${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md
     - IF result == true:
       - Set current_node = node.branches.true
     - ELSE:
       - Set current_node = node.branches.false
     - CONTINUE

     USER_PROMPT NODE:
     - Build AskUserQuestion from node.prompt
     - Present via AskUserQuestion tool
     - Wait for user response
     - Find matching handler in node.on_response
     - Store response in state.user_responses[current_node]
     - Apply handler.consequence if present
     - Set current_node = handler.next_node
     - CONTINUE

     VALIDATION_GATE NODE:
     - Evaluate all validations
     - IF any fail: route to on_invalid
     - ELSE: route to on_valid
     - CONTINUE

     REFERENCE NODE:
     - Load document: Read ${CLAUDE_PLUGIN_ROOT}/{node.doc}
     - IF node.section: extract only that section
     - Execute with context available
     - Set current_node = node.next_node
     - CONTINUE

  4. Record in history and update position

UNTIL ending reached
```

---

## Parallel Agent Spawning

For multi-source corpora (2+ sources), the workflow spawns `source-scanner` agents in parallel for status checking.

**Agent invocation** (at `spawn_status_agents` node):
1. For each source in config.sources, create a Task tool call with `subagent_type="source-scanner"`
2. Include ALL Task calls in a single response message for parallel execution
3. Collect results and aggregate into `status_report`

**Agent definition:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

---

## Variable Interpolation

Replace `${...}` patterns in strings:

| Pattern | Resolution |
|---------|------------|
| `${config.corpus.name}` | Corpus name from config |
| `${sources}` | Array of source configurations |
| `${status_report}` | Array of per-source status results |
| `${sources_to_update}` | Sources selected for update |
| `${current_source}` | Currently processing source |
| `${computed.all_changes}` | Accumulated changes from all sources |
| `${computed.updated_sources}` | Successfully updated sources |
| `${index_structure.is_tiered}` | Boolean: uses tiered indexing |
| `${flags.auto_approve}` | Boolean: skip user prompts |
| `${flags.has_stale_sources}` | Boolean: some sources need updates |

**Resolution order:**
1. `state.computed.{path}`
2. `state.flags.{path}`
3. `state.user_responses.{path}`
4. `state.{path}`
5. `config.{path}`

---

## Workflow Graph Overview

```
read_config
    │
    ▼
check_has_sources ───── no sources? ──► error_no_sources
    │
    │ has sources
    ▼
check_index_exists ──── no index? ──► error_no_index
    │
    │ index exists
    ▼
check_index_built ───── placeholder? ──► error_index_placeholder
    │
    │ built
    ▼
detect_index_structure (check for tiered)
    │
    ▼
check_auto_approve ──── auto? ──► auto_set_update_mode
    │                              │
    │ interactive                  │
    ▼                              │
prompt_command_mode                │
    │                              │
    ├── status ──────┐             │
    │                │             │
    └── update ──────┼─────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                │
route_status    initialize_status    │
by_source_count for_update           │
    │                │                │
    ├─single─────────┼─single─────────┤
    │                │                │
    ▼                ▼                │
check_single_   check_single_        │
source_status   source_for_update    │
    │                │                │
    ├─multi──────────┼─multi──────────┤
    │                │                │
    ▼                ▼                │
spawn_status_   spawn_status_        │
agents          agents_for_update    │
    │                │                │
    └────────┬───────┘                │
             │                        │
             ▼                        │
    aggregate_status_results          │
             │                        │
             ▼                        │
    present_status_report             │
             │                        │
    ┌────────┴───────┐                │
    │ status mode    │ update mode    │
    ▼                ▼                │
suggest_update   route_to_update_    │
(if stale)       selection           │
    │                │                │
    └────────────────┼────────────────┘
                     │
                     ▼
           prompt_select_sources (or auto-select)
                     │
                     ▼
              start_update_loop
                     │
    ┌────────────────┴────────────────┐
    │ for each source:                │
    ├─► git: fetch, pull, get diff    │
    ├─► local: scan for changes       │
    ├─► web: prompt/auto refetch      │
    ├─► generated-docs: rediscover    │
    └─► llms-txt: diff manifests      │
                     │
                     ▼
            check_has_changes
                     │
        ┌────────────┴────────────┐
        │ no changes             │ changes
        ▼                        ▼
skip_index_update     route_index_update_by_structure
        │                        │
        │          ┌─────────────┼─────────────┐
        │          │ single      │ tiered      │
        │          ▼             ▼             │
        │   update_single   map_changes_to    │
        │   index           sub_indexes       │
        │          │             │             │
        │          │       update_sub_indexes │
        │          │             │             │
        │          └─────────────┼─────────────┘
        │                        │
        │                        ▼
        │              confirm_index_changes
        │                        │
        │                        ▼
        │                 save_index_files
        │                        │
        └────────────┬───────────┘
                     │
                     ▼
          update_config_metadata
                     │
                     ▼
            present_completion
                     │
                     ▼
                  success
```

---

## Source Type Handlers

| Source Type | Status Check | Update Action |
|-------------|--------------|---------------|
| **git** | `git ls-remote` SHA comparison | `git pull`, diff changes |
| **local** | File modification times | Scan for new/modified files |
| **web** | Cache age reporting | Re-fetch URLs (requires approval) |
| **generated-docs** | Source repo SHA comparison | Re-discover URLs from sitemap |
| **llms-txt** | Manifest hash comparison | Diff manifests, update structure |

---

## Auto-Approve Mode

When `flags.auto_approve: true`:

| User Prompt | Auto-Approve Default |
|-------------|---------------------|
| `prompt_command_mode` | "update" (not status) |
| `prompt_select_sources` | All stale sources |
| `prompt_web_refetch` | "yes" |
| `prompt_rediscover_urls` | "yes" |
| `prompt_affected_sections` | "all" |
| `prompt_confirm_changes` | "save" |
| `prompt_main_index_update` | "yes" |

Auto-approve mode:
- Never deletes files without backup
- Always preserves entry keywords
- Logs all actions for audit trail
- Exits with error (not silent) on failures

---

## Logging

Every refresh execution generates a detailed log file by default.

**Log location:** `data/logs/refresh-{YYYY-MM-DD-HHMMSS}.yaml`

### Log Contents

- **Metadata:** Workflow version, corpus name, execution path
- **Parameters:** auto_approve, status_only, log settings
- **Execution:** Start/end time, duration, mode, outcome
- **Sources:** Per-source status, SHAs, actions taken
- **Changes:** Added/modified/deleted files per source
- **Index updates:** Files modified, entries added/removed
- **Node history:** Full decision path with timestamps
- **Errors/Warnings:** Any issues encountered

### Log Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| yaml | `.yaml` | Default, human-readable |
| json | `.json` | Programmatic parsing |
| markdown | `.md` | Review and documentation |

### CI Output Formats

| Format | Description |
|--------|-------------|
| `github` | GitHub Actions annotations (`::group::`, `::notice::`, `::error::`) |
| `plain` | KEY=VALUE format for shell scripts |
| `json` | JSON object for programmatic parsing |
| `none` | No structured CI output (default) |

### Retention

Configure in corpus `config.yaml`:

```yaml
logging:
  retention:
    strategy: "count"   # none | days | count
    count: 20           # keep last 20 logs
```

### Git Integration

- **Default:** Logs are committed (in `data/logs/`)
- **Optional:** Use `--log-gitignore` to exclude from git

### Examples

```bash
# Normal interactive (logs to data/logs/)
/hiivmind-corpus-refresh

# CI with GitHub Actions output
/hiivmind-corpus-refresh --auto-approve --ci-output=github

# Status check with JSON output
/hiivmind-corpus-refresh --status-only --ci-output=json

# Skip logging entirely
/hiivmind-corpus-refresh --no-log
```

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/refresh-logging.md` for full schema.

---

## Keyword Preservation

When updating index entries, preserve any `Keywords:` lines:

```markdown
# Entry before update
- **Milestones REST** `rest:repos/milestones.md` - REST API for milestones
  Keywords: `milestones`, `POST`, `create`, `due_on`

# After path change (keywords preserved)
- **Milestones REST** `rest:repos/v2/milestones.md` - REST API for milestones
  Keywords: `milestones`, `POST`, `create`, `due_on`
```

All index update reference nodes receive `preserve_keywords: true` in context.

---

## Reference Documentation

- **Workflow Schema:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/schema.md`
- **Preconditions:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md` (modular: `consequences/`)
  - Core operations: `consequences/core/workflow.md`
  - Config operations: `consequences/extensions/config.md`
  - Git operations: `consequences/extensions/git.md`
  - Web operations: `consequences/extensions/web.md`
  - Logging operations: `consequences/extensions/logging.md`
- **Logging patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/refresh-logging.md`

---

## Pattern Documentation

Operations referenced by this workflow:

- **Status checking:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/status.md`
- **Source patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/` (git.md, local.md, web.md, generated-docs.md, llms-txt.md)
- **Index generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-generation.md`
- **Config parsing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md`

---

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Upgrade to latest: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus.md`

---

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md` - Parallel status checking and scanning for multi-source corpora
