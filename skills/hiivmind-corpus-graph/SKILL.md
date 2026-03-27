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

### add-concept

Add a new concept to graph.yaml with semi-automated entry suggestion.

**Invocation:** `graph add-concept "Concept Label"` or interactive (no args → prompt for label)

**Procedure:**

1. **Slugify label** to concept ID per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` § Concept ID Conventions:
   ```bash
   slugify() {
     echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//'
   }
   ```
2. **Check for duplicates** — if concept ID already exists in graph.yaml, error:
   "Concept '{id}' already exists. Use a different name or edit the existing concept."
3. **Scan index for matching entries:**
   - Extract 2-4 search terms from the concept label
   - **v2 (index.yaml):** yq pre-filter on tags, keywords, summary fields. If yq unavailable, read index.yaml directly and use LLM judgment.
     ```bash
     yq '.entries[] | select(
       (.tags[] | test("term1|term2"; "i")) or
       (.keywords[] | test("term1|term2"; "i")) or
       (.summary | test("term1.*term2|term2.*term1"; "i"))
     ) | {id, title, summary, tags}' index.yaml
     ```
   - **v1 (index.md):** grep for search terms + LLM semantic judgment
   - Present top 10-15 candidates ranked by relevance
4. **User selects entries** — present numbered list, user confirms/deselects
5. **Suggest tags** — based on selected entries' metadata (if available from index.yaml)
6. **Suggest description** — one-line summary based on selected entries' summaries
7. **Write concept to graph.yaml** (v2 schema — no entry lists):
   ```yaml
   {concept-id}:
     label: "{User-Provided Label}"
     description: "{description}"
     tags: ["{tag1}", "{tag2}"]
   ```
8. **Update index.yaml entries with concept reference:**
   For each selected entry, update its `concepts` array in index.yaml:
   - Read index.yaml
   - Find entry by ID
   - Append `"{concept-id}"` to entry's `concepts` list (create list if missing)
   - Save index.yaml
   - Re-run embed.py if `index-embeddings.lance/` exists (incremental update)
   Display: "Updated {n} entries in index.yaml with concept '{concept-id}'"
9. **Update meta** — increment `concept_count`, set `generated_at` to current ISO-8601 timestamp

**Empty graph bootstrap:** If `graph.yaml` doesn't exist, create a new one:

```yaml
schema_version: 2

concepts:
  {concept-id}:
    label: "{label}"
    description: "{description}"
    tags: []

relationships: []

meta:
  generated_at: "{ISO-8601}"
  concept_count: 1
  relationship_count: 0
```

**graph.yaml v1 compatibility:** If existing `graph.yaml` has `schema_version: 1` (concepts with `entries[]` lists), migrate on edit: move entry lists to index.yaml `concepts[]`, remove `entries` and `entry_count` from graph.yaml, set `schema_version: 2`.

**Output:** "Added concept '{label}' with {n} entries to graph.yaml and index.yaml"

### add-relationship

Add a typed relationship between two existing concepts. Supports explicit (args) and interactive (no args) modes.

**Explicit invocation:** `graph add-relationship "{from-concept}" "{to-concept}" {type}`

**Procedure (explicit):**

1. **Validate concept IDs** — both `from` and `to` must exist in graph.yaml. If not:
   "Concept '{id}' not found. Available concepts: {list}"
2. **Validate relationship type** — must be one of the controlled vocabulary:
   `includes`, `depends-on`, `see-also`, `extends`, `contrast-with`
   (see `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` § Relationship Type Vocabulary)
3. **Check for duplicates** — same from/to/type triple already exists:
   "Relationship '{from}' → '{to}' ({type}) already exists."
4. **Optionally ask for evidence** — an entry path that demonstrates the link (can be null)
5. **Write relationship to graph.yaml:**
   ```yaml
   - from: "{from-concept}"
     to: "{to-concept}"
     type: "{type}"
     origin: "manual"
     evidence: null
   ```
6. **Update meta** — increment `relationship_count`, set `generated_at`

**Interactive invocation** (no args):

1. Load graph.yaml, list all concepts
2. Analyze concept pairs for relationship candidates:
   - **Tag overlap:** Concepts sharing 2+ tags → strong candidate
   - **Entry cross-references:** If entries in concept A link to entries in concept B
   - **Label/description keyword similarity:** Fuzzy match on descriptions
   - **Embedding similarity** (if `index-embeddings.lance/` exists and fastembed available): For each concept, query `index-embeddings.lance/` with the concept's label+description. Concepts with entries that are semantically similar (score > 0.7) but not yet linked are relationship candidates.
3. Present candidates:
   ```
   These concept pairs look related — confirm or skip each:

   1. query-optimization → lazy-frames
      Reason: shared tags [performance, optimization]
      Suggested type: depends-on
      [Confirm / Change type / Skip]

   2. data-types → serialization
      Reason: entries cross-reference each other
      Suggested type: see-also
      [Confirm / Change type / Skip]
   ```
4. For each confirmed pair, write relationship with `origin: "manual"`
5. Summary: "Added {n} relationships to graph.yaml"

**Note:** All relationships added by this subcommand use `origin: "manual"`, which means refresh will preserve them (never overwritten by auto-extraction).

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
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md` — Embedding-based similarity for relationship candidates

## Related Skills

- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md` — Generates graph.yaml during build
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-navigate/SKILL.md` — Uses graph.yaml for enriched retrieval
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md` — Can add entries to concepts
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md` — Updates auto-extracted relationships
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md` — Configures extraction
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md` — Initializes corpus
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md` — Finds installed corpora
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-register/SKILL.md` — Registers corpus to project
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-status/SKILL.md` — Reports corpus health
