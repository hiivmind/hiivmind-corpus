---
description: Unified entry point for all corpus operations - describe what you need in natural language
argument-hint: Describe your goal (e.g., "index React docs", "refresh my polars corpus", or just a corpus name)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "TodoWrite", "AskUserQuestion", "Skill", "Task", "WebFetch"]
---

# Corpus Gateway Workflow

Execute this workflow deterministically. State persists in conversation context across turns.

> **Workflow Definition:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/workflow.yaml`
> **Blueprint Library:** `hiivmind/hiivmind-blueprint-lib@v2.0.0`

---

## Execution Reference

| Resource | Location |
|----------|----------|
| Workflow Definition | `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/workflow.yaml` |
| Intent Mapping | `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml` |
| Core loop | [traversal.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/traversal.yaml) |
| State | [state.yaml](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/state.yaml) |
| Execution Model | [execution/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/) |
| Type Definitions | [hiivmind-blueprint-lib@v2.0.0](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0) |
| Consequences (core) | [consequences/core/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/consequences/core/) |
| Consequences (extensions) | [consequences/extensions/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/consequences/extensions/) |
| Preconditions | [preconditions/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/preconditions/) |

---

## Usage

Describe your goal in natural language:

- "index the polars documentation" → Creates new corpus
- "what is lazy evaluation?" → Navigates installed corpora
- "is my polars corpus up to date?" → Checks freshness
- "more detail on authentication" → Enhances topic coverage

---

## Quick Examples

| Input | Result |
|-------|--------|
| `/hiivmind-corpus` | Show interactive menu |
| `/hiivmind-corpus polars lazy evaluation` | Navigate polars corpus |
| `/hiivmind-corpus create react docs` | Initialize new corpus |
| `/hiivmind-corpus refresh polars` | Check for upstream changes |
| `/hiivmind-corpus enhance polars lazy api` | Deepen coverage on topic |
| `/hiivmind-corpus list` | List installed corpora |

---

## Context Types

| Context | Detection | Valid Operations |
|---------|-----------|------------------|
| corpus-dir | `data/config.yaml` exists | add-source, build, enhance, refresh, upgrade, navigate |
| marketplace | `.claude-plugin/marketplace.json` exists | init (add), batch refresh, batch upgrade |
| fresh | Neither of above | init |

---

## Intent Detection

The gateway uses 3-Valued Logic (3VL) for compound intent handling. This allows inputs like "help me initialize" to correctly route to init rather than help.

**Intent Mapping:** `${CLAUDE_PLUGIN_ROOT}/commands/hiivmind-corpus/intent-mapping.yaml`

This file defines:
- **11 intent flags** - Keywords that detect user intents
- **19 intent rules** - Flag combinations mapped to actions with priorities

For 3VL semantics and algorithms, see [hiivmind-blueprint-lib](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0).

---

## Reference Documentation

| Resource | Location |
|----------|----------|
| Type Definitions | [hiivmind-blueprint-lib@v2.0.0](https://github.com/hiivmind/hiivmind-blueprint-lib/tree/v2.0.0) |
| Execution Model | [execution/](https://raw.githubusercontent.com/hiivmind/hiivmind-blueprint-lib/v2.0.0/execution/) |
| Discovery Pattern | `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/discovery.md` |
| Config Parsing | `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md` |

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
