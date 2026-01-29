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

Execute this workflow deterministically. State persists in conversation context.

> **Workflow:** `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/workflow.yaml`

---

## Workflow Graph Overview

```
read_config → check_sources → check_index → detect_structure
    │
    ▼
route_mode ─► status: check sources → present report
    │
    └─► update: select sources → update loop → apply changes → success
```

---

## Execution Reference

Execution semantics from [hiivmind-blueprint-lib](https://github.com/hiivmind/hiivmind-blueprint-lib) (version: v2.0.0):

| Semantic | Source |
|----------|--------|
| Core loop | [traversal.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/traversal.yaml) |
| State | [state.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/state.yaml) |
| Consequences | [consequence-dispatch.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/consequence-dispatch.yaml) |
| Preconditions | [precondition-dispatch.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/precondition-dispatch.yaml) |

---

## Reference Documentation

- **Type Definitions:** [hiivmind-blueprint-lib](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0)
- **Corpus Patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/`

---

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Upgrade corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md`
- Navigate: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-navigate/SKILL.md`

---

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`
