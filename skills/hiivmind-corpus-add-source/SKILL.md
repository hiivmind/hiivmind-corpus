---
name: hiivmind-corpus-add-source
description: >
  Add documentation source to corpus. Triggers: "add source", "add git repo",
  "include blog posts", "add local documents", "extend corpus with web pages",
  "add team docs", "add PDF to corpus", "import PDF book", "split PDF into chapters".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
---

# Add Source Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/workflow.yaml`

---

## Execution Instructions

### Phase 1: Initialize

1. **Load workflow.yaml** from this skill directory:
   Read: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/workflow.yaml`

2. **Check entry preconditions** (see `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`):
   - `config_exists`: Verify `data/config.yaml` exists
   - If ANY fails: display error message, suggest recovery skill, STOP

3. **Initialize runtime state**:
   ```yaml
   workflow_name: add-source
   workflow_version: "1.0.0"
   current_node: locate_corpus
   previous_node: null
   history: []
   user_responses: {}
   computed: {}
   flags:
     config_found: false
     manifest_detected: false
     is_first_source: false
     is_pdf: false
     pdf_splitter_available: false
     clone_succeeded: false
     user_wants_indexing: false
   checkpoints: {}
   phase: "locate"
   source_type: null
   source_url: null
   source_id: null
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
         - Suggest: "Try running: /{recovery}"
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

Replace `${...}` patterns in strings:

| Pattern | Resolution |
|---------|------------|
| `${source_type}` | `state.source_type` |
| `${computed.source_id}` | `state.computed.source_id` |
| `${flags.config_found}` | `state.flags.config_found` |
| `${user_responses.node_name.id}` | Selected option id |
| `${user_responses.node_name.raw.text}` | Custom text input |

**Resolution order:**
1. `state.computed.{path}`
2. `state.flags.{path}`
3. `state.user_responses.{path}`
4. `state.{path}`

---

## Workflow Graph Overview

```
locate_corpus
    │
    ▼
check_url_provided ──── source_url provided? ────┐
    │ no                                         │ yes
    ▼                                            ▼
ask_source_input                           detect_pdf
    │                                            │
    ├─► git ──────► collect_git_url             │
    ├─► local ────► collect_local_info          │
    ├─► web ──────► collect_web_info            │
    ├─► llms_txt ─► collect_llms_txt_url        │
    └─► other ────► handle_url_input ───────────┘
                                                 │
                          ┌──────────────────────┴─────────────────────┐
                          │                                            │
                     is_pdf?                                try_llms_txt_detection
                          │                                            │
                    ┌─────┴─────┐                            ┌─────────┴─────────┐
                    │           │                            │                   │
              check_pymupdf  continue                  manifest found?       not found
                    │                                        │                   │
               ┌────┴────┐                         present_manifest_option  ask_source_type_for_url
               │         │                                   │                   │
         available   missing                        ┌────────┴────────┐          │
               │         │                          │                 │          │
        ask_pdf_split  offer                   use_llms           other          │
               │      single                        │                 │          │
               │         │                collect_llms_txt_details    └──────────┤
               ▼         │                          │                            │
      (split or single)  │                          │                            │
               │         │                          │                            │
               └─────────┴──────────────────────────┴────────────────────────────┤
                                                                                 │
                                                                    ┌────────────┴────────────┐
                                                                    │                         │
                                                              git branch/docs           web/llms/generated
                                                                    │                         │
                                                            validate_git_source               │
                                                                    │                         │
                                                            execute_git_clone                 │
                                                                    │                         │
                                                            research_git_source               │
                                                                    │                         │
                                                            add_source_to_config              │
                                                                    │                         │
                                                                    └─────────┬───────────────┘
                                                                              │
                                                                    check_first_source_navigate
                                                                              │
                                                                    ┌─────────┴─────────┐
                                                                    │                   │
                                                              is_first?            not first
                                                                    │                   │
                                                        update_navigate_examples        │
                                                                    │                   │
                                                                    └─────────┬─────────┘
                                                                              │
                                                                        ask_index_now
                                                                              │
                                                                    ┌─────────┴─────────┐
                                                                    │                   │
                                                                   yes                 no
                                                                    │                   │
                                                            suggest_build_skill         │
                                                                    │                   │
                                                                    └─────────┬─────────┘
                                                                              │
                                                                           success
```

---

## Reference Documentation

- **Workflow Schema:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/schema.md`
- **Preconditions:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md` (modular: `consequences/`)
  - Core operations: `consequences/core/workflow.md`
  - Git operations: `consequences/extensions/git.md`
  - Config operations: `consequences/extensions/config.md`
  - File operations: `consequences/extensions/file-system.md`
  - Web operations: `consequences/extensions/web.md`
- **Execution Model:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/execution.md`
- **State Structure:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/state.md`

---

## Pattern Documentation

Source-specific operations referenced by this workflow:

- **Git sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/git.md`
- **Local sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/local.md`
- **Web sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/web.md`
- **llms-txt sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/llms-txt.md`
- **Generated docs:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/generated-docs.md`
- **PDF processing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/pdf.md`
- **Shared patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/shared.md`

---

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Build full index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
