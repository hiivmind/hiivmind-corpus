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
| `${computed.intent_flags}` | `state.computed.intent_flags` (3VL values) |
| `${computed.intent_matches}` | `state.computed.intent_matches` (rule results) |
| `${computed.matched_action}` | `state.computed.matched_action` |
| `${flags.has_arguments}` | `state.flags.has_arguments` |
| `${user_responses.node_name.id}` | Selected option id |
| `${user_responses.node_name.raw.text}` | Custom text input |

**Resolution order:**
1. `state.computed.{path}`
2. `state.flags.{path}`
3. `state.user_responses.{path}`
4. `state.{path}`

---

## 3VL Intent Detection

The gateway uses 3-Valued Logic (3VL) for compound intent handling. This allows inputs like "help me initialize" to correctly route to init rather than help.

**Framework Documentation:**
- **Semantics & Scoring:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/framework.md`
- **Algorithms:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/execution.md`
- **Variables:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/variables.md`

**Intent Mapping:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml`

### Quick Reference

| Value | Meaning |
|-------|---------|
| `T` | True - positive keyword matched |
| `F` | False - negative keyword matched |
| `U` | Unknown - no keywords matched |

**Scoring:** T+T or F+F = +2, soft matches = +1, U+U = 0, T+F or F+T = EXCLUDED

**Winner:** Clear winner needs top score >= second + 2, otherwise disambiguation menu

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

## Intent Flags and Rules

Intent flags and rules are defined in a separate configuration file for maintainability.

**Configuration:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml`

### Flags Overview

11 intent flags detect different user intents:
- **Creation:** has_init, has_add_source, has_build
- **Navigation:** has_query, has_list, has_show
- **Maintenance:** has_refresh, has_enhance, has_upgrade
- **Other:** has_help, has_awareness

### Rules Overview

19 intent rules map flag combinations to actions, organized by priority:
- **100:** Pure help (all others false)
- **95:** Pure listing
- **90:** Single intents (init, build, refresh, etc.)
- **85:** Query/navigate with qualifiers
- **80:** Help + X combinations
- **70:** Multi-step intents (init + build)
- **10:** Empty input fallback

See `intent-mapping.yaml` for the complete definitions.

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
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md`
- **Execution Model:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/execution.md`
- **State Structure:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/state.md`

### Intent Detection
- **3VL Framework:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/framework.md`
- **Execution Algorithms:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/execution.md`
- **Variable Interpolation:** `${CLAUDE_PLUGIN_ROOT}/lib/intent_detection/variables.md`

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
