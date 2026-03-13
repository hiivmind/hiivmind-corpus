---
name: hiivmind-corpus-graph
description: >
  View, validate, and edit a corpus concept graph (graph.yaml).
  Triggers: "graph", "show graph", "validate graph", "concept graph",
  "view concepts", "graph.yaml", "show relationships", "add concept",
  "add relationship".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
---

# Corpus Concept Graph

View, validate, and edit the concept graph (`graph.yaml`) for a corpus.

## Precondition

A corpus must exist with a `graph.yaml` file. If no graph exists, inform the user:
"This corpus does not have a concept graph yet. Run `build` with extraction enabled to generate one, or use `add-concept` to create one manually."

---

## Phase 1: Locate Graph

**Inputs:** Corpus path (from user or auto-detected)

**Procedure:**

1. Locate the corpus using discovery patterns
2. Check for `graph.yaml` alongside `index.md`
3. Load and parse the graph

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/discovery.md`
**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md`

---

## Phase 2: Execute Subcommand

Determine which subcommand to run based on user intent:

### show

Display a human-readable summary of the concept graph.

**Procedure:**

1. List all concepts with: label, entry count, tags
2. List all relationships with: from → to (type), origin
3. Show meta: generated_at, total counts
4. Format as a readable table or structured list

**Output example:**

```
Concepts (8):
  family-activities    — 5 entries, tags: [family]
  recipes              — 3 entries
  work-projects        — 3 entries, tags: [project]
  ...

Relationships (5):
  family-activities → recipes (includes) [wikilink]
  work-projects → budget-review (see-also) [manual]
  ...

Generated: 2026-03-13T00:00:00Z | 24 entries | 8 concepts | 5 relationships
```

### validate

Check graph.yaml for issues.

**Procedure:**

1. Load `graph.yaml` and `index.md`
2. Run all validation rules from `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` § Validation Rules
3. Report: errors (must fix), warnings (should review)
4. If clean: "Graph validates OK — N concepts, M relationships, no issues."

### add-concept (deferred — vertical slice excludes this)

### add-relationship (deferred — vertical slice excludes this)

---

## Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| No corpus found | "Could not locate a corpus. Specify the path or run from a corpus directory." | Ask user for path |
| No graph.yaml | "This corpus has no concept graph. Generate one with `build` (extraction enabled)." | Suggest build |
| Invalid YAML | "graph.yaml has syntax errors: {details}" | Show error location |
| Schema violation | "graph.yaml schema issue: {details}" | Show specific field |

---

## Pattern Documentation

- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` — Graph schema, validation rules, concept ID conventions
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/discovery.md` — Corpus location discovery
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md` — Config.yaml parsing

## Related Skills

- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md` — Generates graph.yaml during build
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-navigate/SKILL.md` — Uses graph.yaml for enriched retrieval
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus graph overlay
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md` — Can add entries to concepts
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md` — Updates auto-extracted relationships
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md` — Configures extraction
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md` — Initializes corpus
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md` — Finds installed corpora
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-register/SKILL.md` — Registers corpus to project
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-status/SKILL.md` — Reports corpus health
