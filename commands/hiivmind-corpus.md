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
     intent_flags: {}            # 3VL flag values (T/F/U)
     intent_matches: null        # 3VL rule matching results
     matched_action: null        # Action from winning rule
     extracted_project: null
     extracted_corpus: null
   flags:
     has_arguments: false
     in_corpus_dir: false
     in_marketplace: false
     has_installed_corpora: false
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

## Variable Interpolation

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/variables.md`

This workflow uses standard variable interpolation for `${...}` patterns. Common variables used in this workflow:
- `${arguments}`, `${intent}`, `${target_corpus}`, `${source_url}`
- `${computed.*}` - Derived values (context_type, available_corpora, intent_flags)
- `${flags.*}` - Boolean state flags
- `${user_responses.*}` - User prompt responses

---

## 3VL Intent Detection

The gateway uses 3-Valued Logic (3VL) for compound intent handling. This allows inputs like "help me initialize" to correctly route to init rather than help.

**Framework Documentation:**
- **Semantics & Scoring:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/framework.md`
- **Algorithms:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/execution.md`
- **Variables:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/variables.md`

**Intent Mapping:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml`

---

## Skill Invocation

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences/core/workflow.md` § invoke_skill

This workflow delegates to corpus skills (init, build, refresh, etc.) using the `invoke_skill` consequence. The invoked skill takes over the conversation.

---

## Corpus Discovery

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences/extensions/discovery.md` § discover_installed_corpora

This workflow discovers installed corpora using the `discover_installed_corpora` consequence. For the full discovery algorithm, see `lib/corpus/patterns/discovery.md`.

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
    └─► has args ──► parse_intent_flags ──► match_intent_rules
                                                    │
                          ┌─────────────────────────┴─────────────────────────┐
                          │                                                   │
                    clear_winner                                        ambiguous
                          │                                                   │
                          ▼                                                   ▼
                 execute_matched_action                         show_disambiguation_menu
                          │                                                   │
          ┌───────────────┼───────────────┬─────────────┐                     │
          │               │               │             │                     │
          ▼               ▼               ▼             ▼                     │
    extract_project  detect_context  discover_corpora  ...                    │
          │               │               │             │                     │
          ▼               ▼               ▼             ▼                     │
    delegate_init   delegate_*      delegate_navigate  ...◄──────────────────┘
```

---

## Intent Configuration

Intent flags and rules are defined externally for maintainability.

**See:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml`

This file defines:
- **11 intent flags** - Keywords that detect user intents
- **19 intent rules** - Flag combinations mapped to actions with priorities

For 3VL semantics (scoring, priorities, winner determination), see the framework documentation referenced above.

---

## Context Types

| Context | Detection | Valid Operations |
|---------|-----------|------------------|
| corpus-dir | `data/config.yaml` exists | add-source, build, enhance, refresh, upgrade, navigate |
| marketplace | `.claude-plugin/marketplace.json` exists | init (add), batch refresh, batch upgrade |
| fresh | Neither of above | init |

---

## Reference Documentation

### Workflow Framework
- **Workflow Schema:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/schema.md`
- **Preconditions:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md` (modular: `consequences/`)
  - Core operations: `consequences/core/workflow.md` (state, evaluation, skill invocation)
  - Intent detection: `consequences/core/intent-detection.md`
  - Discovery: `consequences/extensions/discovery.md`
- **Execution Model:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/execution.md`
- **State Structure:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/state.md`

### Intent Detection
- **3VL Framework:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/framework.md`
- **Execution Algorithms:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/execution.md`
- **Variable Interpolation:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/variables.md`

---

## Related Skills

### Build Skills (Create/Maintain Corpora)

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-init` | Create new corpus scaffold |
| `hiivmind-corpus-add-source` | Add documentation sources |
| `hiivmind-corpus-build` | Build/rebuild the index |
| `hiivmind-corpus-enhance` | Deepen coverage on topics |
| `hiivmind-corpus-refresh` | Sync with upstream changes |
| `hiivmind-corpus-upgrade` | Apply latest templates |

### Read Skills (Query/Navigate Corpora)

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-navigate` | Search and retrieve documentation |
| `hiivmind-corpus-register` | Add corpus to project registry |
| `hiivmind-corpus-status` | Check corpus health/freshness |

### Shared Skills

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-discover` | Find available corpora (registry + plugins) |
| `hiivmind-corpus-awareness` | Add to CLAUDE.md |
