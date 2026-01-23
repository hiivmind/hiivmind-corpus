---
description: Unified entry point for all corpus operations - describe what you need in natural language
argument-hint: Describe your goal (e.g., "index React docs", "refresh my polars corpus", or just a corpus name)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "TodoWrite", "AskUserQuestion", "Skill", "Task", "WebFetch"]
---

# Corpus Gateway Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/workflow.yaml`

---

## Execution Instructions

### Phase 1: Initialize

1. **Load workflow.yaml** from this command directory:
   Read: `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/workflow.yaml`

2. **Check entry preconditions**:
   - None for gateway (always available)

3. **Initialize runtime state**:
   ```yaml
   workflow_name: hiivmind-corpus-gateway
   workflow_version: "1.0.0"
   current_node: check_arguments
   previous_node: null
   history: []
   user_responses: {}
   computed:
     context_type: null
     available_corpora: []
     selected_corpus: null
     detected_intent: null
     extracted_project: null
     extracted_corpus: null
   flags:
     has_arguments: false
     in_corpus_dir: false
     in_marketplace: false
     has_installed_corpora: false
     is_compound_intent: false
     corpora_discovered: false
   checkpoints: {}
   phase: "detect"
   intent: null
   target_corpus: null
   target_topic: null
   source_url: null
   arguments: "${ARGUMENTS}"
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
     - Build AskUserQuestion from node.prompt:
       ```json
       {
         "questions": [{
           "question": "[interpolated node.prompt.question]",
           "header": "[node.prompt.header]",
           "multiSelect": false,
           "options": [map node.prompt.options to {label, description}]
         }]
       }
       ```
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
     ```yaml
     history.append({
       node: previous_node_name,
       outcome: { success: true/false, branch: "true"/"false", response: "id" },
       timestamp: now()
     })
     ```

  5. Update position:
     - previous_node = current_node (before update)
     - current_node = next_node (from step 3)

UNTIL ending reached
```

---

## Variable Interpolation

Replace `${...}` patterns in strings:

| Pattern | Resolution |
|---------|------------|
| `${ARGUMENTS}` | Command-line arguments passed to gateway |
| `${arguments}` | `state.arguments` |
| `${intent}` | `state.intent` |
| `${target_corpus}` | `state.target_corpus` |
| `${target_topic}` | `state.target_topic` |
| `${source_url}` | `state.source_url` |
| `${computed.context_type}` | `state.computed.context_type` |
| `${computed.available_corpora}` | `state.computed.available_corpora` |
| `${computed.selected_corpus}` | `state.computed.selected_corpus` |
| `${computed.detected_intent}` | `state.computed.detected_intent` |
| `${flags.has_arguments}` | `state.flags.has_arguments` |
| `${user_responses.node_name.id}` | Selected option id |
| `${user_responses.node_name.raw.text}` | Custom text input |

**Resolution order:**
1. `state.computed.{path}`
2. `state.flags.{path}`
3. `state.user_responses.{path}`
4. `state.{path}`

---

## Keyword Detection

The `evaluate_keywords` consequence type is used to match user input against keyword sets. Match the **first** keyword set that contains a phrase found in the input (case-insensitive).

**Algorithm:**
```
FOR each keyword_set IN keyword_sets:
  FOR each keyword IN keyword_set.keywords:
    IF input.toLowerCase().includes(keyword.toLowerCase()):
      RETURN keyword_set.name
RETURN null
```

---

## Skill Invocation

The `invoke_skill` consequence type delegates to another skill:

**Effect:**
1. Display context summary to user
2. Invoke the Skill tool with the skill name
3. Pass any arguments to the skill
4. The skill takes over the conversation

**Example:**
```yaml
- type: invoke_skill
  skill: "hiivmind-corpus-init"
  args: "${source_url}"
```

Translates to Skill tool invocation:
```
Skill: hiivmind-corpus-init
Args: [source_url value]
```

---

## Corpus Discovery

The `discover_installed_corpora` consequence type scans for installed corpora:

**Locations to scan:**
1. User-level: `~/.claude/skills/hiivmind-corpus-*`
2. Repo-local: `.claude-plugin/skills/hiivmind-corpus-*`
3. Marketplace plugins: `*/hiivmind-corpus-*/.claude-plugin/plugin.json`

**Returns array of:**
```yaml
- name: "polars"
  status: "built"        # built | stale | placeholder
  description: "Polars DataFrame documentation"
  path: "/path/to/corpus"
  keywords: ["polars", "dataframe"]
```

See `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/discovery.md` for full algorithm.

---

## Workflow Graph Overview

```
start
    │
    ▼
check_arguments
    │
    ├─► empty ──────► show_main_menu ──────► route_menu_selection
    │                                              │
    │                                              ├─► navigate → discover_corpora → select_corpus → delegate_navigate
    │                                              ├─► create → delegate_init
    │                                              ├─► manage → discover_corpora → select_corpus → show_action_menu
    │                                              ├─► list → delegate_discover
    │                                              └─► help → display_help
    │
    └─► has args ──► detect_intent
                          │
                          ├─► init keywords ────► extract_project ──► delegate_init
                          ├─► add-source keywords ─► detect_context → delegate_add_source
                          ├─► build keywords ───► detect_context → delegate_build
                          ├─► navigate keywords ─► discover_corpora → delegate_navigate
                          ├─► refresh keywords ──► extract_corpus → delegate_refresh
                          ├─► enhance keywords ──► extract_topic → delegate_enhance
                          ├─► upgrade keywords ──► extract_corpus → delegate_upgrade
                          ├─► discover keywords ─► delegate_discover
                          ├─► awareness keywords ► delegate_awareness
                          ├─► help keywords ────► display_help
                          └─► ambiguous ────────► ask_clarification
```

---

## Intent Keywords

| Intent | Keywords |
|--------|----------|
| init | create, new, index, set up, scaffold, initialize, start corpus |
| add_source | add, include, import, fetch, clone, source, extend with, also index |
| build | build, analyze, scan, create index, finish setup, index now |
| navigate | navigate, find, search, look up, what does, how do, explain, show me, where is |
| refresh | update, refresh, sync, check, upstream, stale, status, is up to date, current, behind |
| enhance | expand, deepen, more detail, enhance, elaborate, deeper coverage, add depth |
| upgrade | upgrade, migrate, latest, standards, template, modernize, update structure |
| discover | list, show, available, installed, discover, what corpora, which corpora |
| awareness | awareness, configure claude, setup claude, capabilities, tour, what can, claude.md, teach claude |
| help | help, commands, ?, usage, guide |

---

## Context Types

| Context | Detection | Valid Operations |
|---------|-----------|------------------|
| corpus-dir | `data/config.yaml` exists | add-source, build, enhance, refresh, upgrade, navigate |
| marketplace | `.claude-plugin/marketplace.json` exists | init (add), batch refresh, batch upgrade |
| fresh | Neither of above | init |

---

## Reference Documentation

- **Workflow Schema:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/schema.md`
- **Preconditions:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md`
- **Execution Model:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/execution.md`
- **State Structure:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/state.md`

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-init` | Create new corpus scaffold |
| `hiivmind-corpus-add-source` | Add documentation sources |
| `hiivmind-corpus-build` | Build/rebuild the index |
| `hiivmind-corpus-enhance` | Deepen coverage on topics |
| `hiivmind-corpus-refresh` | Sync with upstream changes |
| `hiivmind-corpus-upgrade` | Apply latest templates |
| `hiivmind-corpus-discover` | Find installed corpora |
| `hiivmind-corpus-awareness` | Add to CLAUDE.md |
| `hiivmind-corpus-navigate` | Query across corpora |
