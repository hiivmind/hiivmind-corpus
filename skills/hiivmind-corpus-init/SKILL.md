---
name: hiivmind-corpus-init
description: >
  This skill should be used when the user asks to "create a corpus", "initialize documentation",
  "set up docs for a library", "index this project's docs", "create documentation corpus",
  "scaffold corpus skill", or mentions wanting to create a new documentation corpus for any
  open source project. Also triggers on "new corpus", "corpus for [library name]", or
  "hiivmind-corpus init".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
---

# Init Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/workflow.yaml`

---

## Execution Instructions

### Phase 1: Initialize

1. **Load workflow.yaml** from this skill directory:
   Read: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/workflow.yaml`

2. **Check entry preconditions** (see `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`):
   - None for init (this skill creates the corpus)

3. **Initialize runtime state**:
   ```yaml
   workflow_name: init
   workflow_version: "1.0.0"
   current_node: detect_context
   previous_node: null
   history: []
   user_responses: {}
   computed: {}
   flags:
     is_git_repo: false
     has_marketplace: false
     has_corpus_plugins: false
     is_established_project: false
     user_wants_source: false
     start_empty: false
   checkpoints: {}
   phase: "detect"
   context_type: null
   destination_type: null
   corpus_name: null
   source_url: null
   keywords: []
   placeholders:
     plugin_name: null
     project_name: null
     project_display_name: null
     corpus_short_name: null
     keyword_list: null
     keywords_sentence: null
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
       - IF ending.delegate:
         - Inform user about delegation to next skill
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
| `${corpus_name}` | `state.corpus_name` |
| `${destination_type}` | `state.destination_type` |
| `${context_type}` | `state.context_type` |
| `${source_url}` | `state.source_url` |
| `${computed.skill_root}` | `state.computed.skill_root` |
| `${computed.plugin_root}` | `state.computed.plugin_root` |
| `${placeholders.plugin_name}` | `state.placeholders.plugin_name` |
| `${flags.is_git_repo}` | `state.flags.is_git_repo` |
| `${user_responses.node_name.id}` | Selected option id |
| `${user_responses.node_name.raw.text}` | Custom text input |

**Resolution order:**
1. `state.computed.{path}`
2. `state.flags.{path}`
3. `state.placeholders.{path}`
4. `state.user_responses.{path}`
5. `state.{path}`

---

## Workflow Graph Overview

```
detect_context
    │
    ▼
route_context ─────── has_marketplace? ─────┐
    │ no                                    │ yes
    ▼                                       ▼
check_has_corpus_plugins              confirm_context_c
    │                                       │
    ├─► yes ─► confirm_context_c            │
    │                                       │
    └─► no ─► check_established_project     │
              │                             │
              ├─► yes ─► confirm_context_a  │
              │              │              │
              │              ▼              │
              │         choose_dest_a       │
              │              │              │
              │         ┌────┴────┐         │
              │         │         │         │
              │    user-level  repo-local   │
              │         │         │         │
              │         └────┬────┘         │
              │              │              │
              └─► no ─► confirm_context_b   │
                             │              │
                             ▼              │
                        choose_dest_b       │
                             │              │
                    ┌────────┼────────┐     │
                    │        │        │     │
               user-level single  multi     │
                    │        │        │     │
                    └────────┴────────┘     │
                             │              │
                             └──────────────┴─────────────────────┐
                                                                  │
                                                                  ▼
                                                        collect_source_url
                                                                  │
                                                ┌─────────────────┼─────────────────┐
                                                │                 │                 │
                                           github URL         docs URL          start empty
                                                │                 │                 │
                                         collect_github_url  collect_docs_url      │
                                                │                 │                 │
                                                └────────┬────────┘                 │
                                                         │                          │
                                                  derive_corpus_name                │
                                                         │                          │
                                                  confirm_corpus_name  ◄────────────┤
                                                         │                          │
                                                         │     collect_corpus_name_manual
                                                         │                          │
                                                         └──────────┬───────────────┘
                                                                    │
                                                          compute_placeholders
                                                                    │
                                                              collect_keywords
                                                                    │
                                                           compute_skill_root
                                                                    │
                                            ┌───────────────────────┴───────────────────────┐
                                            │                                               │
                                    skill (user/repo-local)                          plugin types
                                            │                                               │
                                   compute_skill_path                            compute_plugin_path
                                            │                                               │
                                            │                    ┌──────────────────────────┤
                                            │                    │                          │
                                            │             single-corpus               multi-corpus
                                            │                    │                          │
                                            │          compute_single_corpus_path   compute_multi_corpus_path
                                            │                    │                          │
                                            └────────────────────┴────────────┬─────────────┘
                                                                              │
                                                              create_checkpoint_before_scaffold
                                                                              │
                                                              route_scaffold_by_destination
                                                                              │
                                            ┌─────────────────────────────────┴─────────────────────────────────┐
                                            │                       │                       │                   │
                                     skill scaffold           single-corpus          multi-corpus-new    multi-corpus-existing
                                            │                       │                       │                   │
                                   scaffold_skill_directories  scaffold_single_corpus  scaffold_multi_corpus_new  scaffold_multi_corpus_existing
                                            │                       │                       │                   │
                                   generate_skill_files       generate_single_corpus_files  generate_multi_corpus_new_files  generate_multi_corpus_existing_files
                                            │                       │                       │                   │
                                   verify_skill_structure     verify_single_corpus_structure  verify_multi_corpus_new_structure  verify_multi_corpus_existing_structure
                                            │                       │                       │                   │
                                            │                       │                       │       update_marketplace_registry
                                            │                       │                       │                   │
                                            └───────────────────────┴───────────────────────┴───────────────────┘
                                                                              │
                                                                  check_source_delegation
                                                                              │
                                                              ┌───────────────┴───────────────┐
                                                              │                               │
                                                        user_wants_source               start_empty
                                                              │                               │
                                                   prepare_add_source_delegation              │
                                                              │                               │
                                                       success_with_source            success_empty
                                                              │
                                                  (delegate to add-source)
```

---

## Context Detection Matrix

| Flags | Context | Destination Options |
|-------|---------|---------------------|
| `has_marketplace` OR `has_corpus_plugins` | C: Existing marketplace | multi-corpus-existing |
| `is_established_project` | A: Established project | user-level, repo-local |
| Neither | B: Fresh directory | user-level, single-corpus, multi-corpus-new |

---

## Reference Documentation

- **Workflow Schema:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/schema.md`
- **Preconditions:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/preconditions.md`
- **Consequences:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/consequences.md` (modular: `consequences/`)
  - Core operations: `consequences/core/workflow.md` (skill invocation, state, evaluation)
  - File operations: `consequences/extensions/file-system.md`
  - Config operations: `consequences/extensions/config.md`
- **Execution Model:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/execution.md`
- **State Structure:** `${CLAUDE_PLUGIN_ROOT}/lib/workflow/state.md`

---

## Pattern Documentation

Template generation operations referenced by this workflow:

- **Template generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/template-generation.md`
- **Template placeholders:** `${CLAUDE_PLUGIN_ROOT}/references/template-placeholders.md`
- **Marketplace templates:** `${CLAUDE_PLUGIN_ROOT}/references/marketplace-templates.md`

---

## Related Skills

- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build full index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- Discover corpora: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md`
