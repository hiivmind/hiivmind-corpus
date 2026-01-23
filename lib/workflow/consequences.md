# Workflow Consequences

Consequences are operations that mutate state or perform actions. Used in:
- **Action nodes** - Execute operations and store results
- **User prompt responses** - Apply changes before routing

All consequences either succeed or fail. Failures trigger `on_failure` routing.

---

## Modular Documentation

Consequences are organized into **core** (workflow engine) and **extension** (domain-specific) modules. See the [consequences/](consequences/) directory for detailed documentation.

### Core Consequences

Fundamental workflow operations intrinsic to any workflow engine:

| Domain | File | Consequence Types |
|--------|------|-------------------|
| Fundamental Operations | [consequences/core/workflow.md](consequences/core/workflow.md) | set_flag, set_state, append_state, clear_state, merge_state, evaluate, compute, display_message, display_table, create_checkpoint, rollback_checkpoint, spawn_agent, invoke_skill, invoke_pattern, set_timestamp, compute_hash |
| Intent Detection | [consequences/core/intent-detection.md](consequences/core/intent-detection.md) | evaluate_keywords, parse_intent_flags, match_3vl_rules, dynamic_route |
| Common Patterns | [consequences/core/shared.md](consequences/core/shared.md) | Interpolation, parameters, failure handling |

### Extension Consequences

Domain-specific operations for corpus management:

| Domain | File | Consequence Types |
|--------|------|-------------------|
| File System | [consequences/extensions/file-system.md](consequences/extensions/file-system.md) | read_config, read_file, write_file, create_directory, delete_file |
| Config | [consequences/extensions/config.md](consequences/extensions/config.md) | write_config_entry, add_source, update_source |
| Git | [consequences/extensions/git.md](consequences/extensions/git.md) | clone_repo, get_sha, git_pull, git_fetch |
| Web | [consequences/extensions/web.md](consequences/extensions/web.md) | web_fetch, cache_web_content |
| Discovery | [consequences/extensions/discovery.md](consequences/extensions/discovery.md) | discover_installed_corpora |

**Full index:** [consequences/README.md](consequences/README.md) - Taxonomy and quick reference

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
