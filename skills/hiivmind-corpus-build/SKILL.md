---
name: hiivmind-corpus-build
description: >
  This skill should be used when the user asks to "build corpus index", "create index from docs",
  "analyze documentation", "populate corpus index", or needs to build the initial index for a
  corpus that was just initialized. Triggers on "build my corpus", "index the documentation",
  "create the index.md", "finish setting up corpus", "hiivmind-corpus build", or when a corpus
  has placeholder index.md that says "Run hiivmind-corpus-build".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch, Task
---

# Build Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/workflow.yaml`
> **Blueprint Library:** `hiivmind/hiivmind-blueprint-lib@v2.0.0`

---

## Execution Reference

| Resource | Location |
|----------|----------|
| Workflow Definition | `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/workflow.yaml` |
| Type Definitions | [hiivmind-blueprint-lib@v2.0.0](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0) |
| Consequences (core) | [consequences/core/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/consequences/core/) |
| Consequences (extensions) | [consequences/extensions/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/consequences/extensions/) |
| Preconditions | [preconditions/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/preconditions/) |

---

## Execution Instructions

### Phase 1: Initialize

1. **Load workflow.yaml** from this skill directory:
   Read: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/workflow.yaml`

2. **Check entry preconditions** (see blueprint-lib `preconditions/`):
   - `config_exists`: Verify `config.yaml` exists

3. **Initialize runtime state**:
   ```yaml
   workflow_name: build
   workflow_version: "2.0.0"
   current_node: read_config
   previous_node: null
   history: []
   user_responses: {}
   computed: {}
   phase: "prepare"
   sources: []
   scan_results: {}
   user_preferences:
     use_case: null
     priority_sources: []
     skip_sections: []
     organization: null
   segmentation:
     strategy: null
     sections: []
   index:
     content: null
     sub_indexes: []
   flags:
     config_found: false
     is_multi_source: false
     is_large_corpus: false
     needs_segmentation: false
     user_satisfied: false
     sources_prepared: false
     scan_completed: false
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
       - Execute action per blueprint-lib consequence definitions
       - Store results in state.computed if store_as specified
     - IF all actions succeed:
       - Set current_node = node.on_success
     - ELSE:
       - Set current_node = node.on_failure
     - CONTINUE

     CONDITIONAL NODE:
     - Evaluate node.condition per blueprint-lib precondition definitions
     - IF result == true:
       - Set current_node = node.branches.true
     - ELSE:
       - Set current_node = node.branches.false
     - CONTINUE

     USER_PROMPT NODE:
     - Build AskUserQuestion from node.prompt:
       '```json
       {
         "questions": [{
           "question": "[interpolated node.prompt.question]",
           "header": "[node.prompt.header]",
           "multiSelect": false,
           "options": [map node.prompt.options to {label, description}]
         }]
       }
       ```'
     - Present via AskUserQuestion tool
     - Wait for user response
     - Find matching handler in node.on_response:
       - If user selected an option: use that option's id
       - If user typed custom text: use "other"
     - Store response in state.user_responses[current_node]
     - Apply handler.consequence if present (execute each consequence)
     - Set current_node = handler.next_node
     - CONTINUE

     VALIDATION_GATE NODE:
     - FOR each validation IN node.validations:
       - Evaluate validation (precondition with error_message)
       - IF fails: collect validation.error_message
     - IF any validations failed:
       - Store errors in state.computed.validation_errors
       - Set current_node = node.on_invalid
     - ELSE:
       - Set current_node = node.on_valid
     - CONTINUE

     REFERENCE NODE:
     - Load document: Read ${CLAUDE_PLUGIN_ROOT}/{node.doc}
     - IF node.section: extract only that section
     - Build context object from node.context with ${} interpolation
     - Execute the document section with context available
     - Set current_node = node.next_node
     - CONTINUE

  4. Record in history:
     '```yaml
     history.append({
       node: previous_node_name,
       outcome: { success: true/false, branch: "true"/"false", response: "id" },
       timestamp: now()
     })
     ```'

  5. Update position:
     - previous_node = current_node (before update)
     - current_node = next_node (from step 3)

UNTIL ending reached
```

---

## Parallel Agent Spawning

For multi-source corpora (2+ sources), the workflow spawns `source-scanner` agents in parallel.

**Agent invocation** (at `spawn_scanner_agents` node):
1. For each source in config.sources, create a Task tool call with `subagent_type="source-scanner"`
2. Include ALL Task calls in a single response message for parallel execution
3. Collect results and aggregate into `scan_results`

**Prompt template:**
```
Scan source '{source_id}' (type: {type}) at corpus path '{corpus_path}'.

Source config:
- ID: {id}
- Type: {type}
- Repo URL: {repo_url}
- Docs root: {docs_root}
- Branch: {branch}

Return YAML with:
- source_id, type, status
- file_count: total doc files
- sections: array with name, path, file_count
- large_files: files over 1000 lines
- framework: detected doc framework
- frontmatter_type: yaml|toml|none
- notes: observations
```

**Agent definition:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

---

## Variable Interpolation

Replace `${...}` patterns in strings:

| Pattern | Resolution |
|---------|------------|
| `${config.corpus.name}` | Corpus name from config |
| `${sources}` | Array of source configurations |
| `${scan_results}` | Object of scan results by source ID |
| `${computed.total_files}` | Total file count across sources |
| `${segmentation.strategy}` | Selected segmentation strategy |
| `${user_preferences.organization}` | User's organization preference |
| `${index.content}` | Generated index markdown content |
| `${flags.is_multi_source}` | Boolean: more than 1 source |
| `${flags.is_large_corpus}` | Boolean: 500+ total files |

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
count_sources
    │
    ▼
check_has_sources ─── no sources? ──► error_no_sources
    │
    │ has sources
    ▼
prepare_sources_start
    │
    ▼
[LOOP: prepare each source by type]
    │
    ├─► git: verify clone exists or clone repo
    ├─► local: verify uploads directory has files
    ├─► web: verify cache exists
    └─► llms-txt: verify cache exists
    │
    ▼
sources_prepared_complete
    │
    ▼
route_scanning ─────── multi-source? ─────┐
    │ single                              │ yes
    ▼                                     ▼
scan_single_source               spawn_scanner_agents
    │                                     │
    ▼                                     ▼
store_single_scan_result         aggregate_scan_results
    │                                     │
    └─────────────┬───────────────────────┘
                  │
                  ▼
          present_scan_summary
                  │
                  ▼
          check_corpus_size ─── >= 500 files? ──► present_segmentation_options
                  │                                       │
                  │ < 500                                 │
                  ▼                                       │
          check_moderate_corpus ─► suggest_segmentation   │
                  │                       │               │
                  │ < 200                 └───────────────┤
                  ▼                                       │
            ask_use_case ◄────────────────────────────────┘
                  │
                  ▼
      [if multi-source: ask_source_priorities]
                  │
                  ▼
            ask_organization
                  │
                  ▼
            ask_skip_sections
                  │
                  ▼
         generate_index_draft
                  │
                  ▼
         show_draft_to_user
                  │
          ┌───────┴───────┐
          │               │
      satisfied       refine
          │               │
          │       ┌───────┴───────┐
          │       │       │       │
          │    expand  reorg   add_docs
          │       │       │       │
          │       └───────┼───────┘
          │               │
          │       ◄───────┘ (loop back to show_draft)
          │
          ▼
    save_index_file
          │
          ▼
    [if tiered: save_sub_indexes]
          │
          ▼
    update_config_metadata
          │
          ▼
    update_per_source_metadata
          │
          ▼
    present_completion
          │
          ▼
        success
```

---

## Index Path Format

All file paths in the index use the format: `{source_id}:{relative_path}`

| Source Type | Path Format | Example |
|-------------|-------------|---------|
| git | `{source_id}:{relative_path}` | `react:reference/hooks.md` |
| local | `local:{source_id}/{filename}` | `local:team-standards/guidelines.md` |
| web | `web:{source_id}/{cached_file}` | `web:kent-blog/article.md` |
| llms-txt | `llms-txt:{source_id}/{path}` | `llms-txt:claude-code/skills.md` |

---

## Segmentation Strategies

| Strategy | When Used | Output Files |
|----------|-----------|--------------|
| `single` | < 500 files, or user preference | `data/index.md` only |
| `tiered` | >= 500 files (recommended) | `data/index.md` + `data/index-{section}.md` |
| `by-section` | Large but curated | `data/index.md` (top 20-30% only) |
| `by-source` | Multi-source, organized by source | `data/index.md` + `data/index-{source}.md` |

---

## Reference Documentation

### Blueprint Library (Remote)
- **Type Definitions:** [hiivmind-blueprint-lib@v2.0.0](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0)
- **Consequences:** `consequences/core/` (state, evaluation, logging) + `consequences/extensions/` (file, git, web)
- **Preconditions:** `preconditions/` (filesystem, state checks)
- **Execution Model:** `execution/` (traversal, state management)

### Corpus Patterns (Local)
- **Parallel Scanning:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/parallel-scanning.md`
- **Index Generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-generation.md`

---

## Pattern Documentation

Operations referenced by this workflow:

- **Source patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/` (git.md, local.md, web.md)
- **Scanning:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/scanning.md`
- **Index generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-generation.md`
- **Config parsing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md`

---

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Discover corpora: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md`

---

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md` - Parallel scanning for multi-source corpora
