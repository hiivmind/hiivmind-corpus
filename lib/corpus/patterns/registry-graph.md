# Pattern: Project-Level Registry Graph (registry-graph.yaml)

## Purpose

Define the strict schema for `registry-graph.yaml` — a project-level cross-corpus concept overlay stored in `.hiivmind/corpus/`. Maps relationships between concepts that exist in different corpora and provides query-routing aliases.

This file is always manually curated (via the `bridge` skill). It is project-specific — the same corpus may participate in different bridges depending on the project.

## When to Use

- During `bridge` skill — create and manage cross-corpus concept links
- During `navigate` skill — check for cross-corpus bridges and aliases (tier 4 retrieval)
- When a project has 2+ corpora with `graph.yaml` files

## Location

```
{project_root}/.hiivmind/corpus/registry-graph.yaml
```

Alongside the existing `registry.yaml` (which tracks corpus locations and access).

---

### Schema Definition (Strict)

```yaml
schema_version: 1

# Bridges: cross-corpus concept relationships
# Each bridge links a concept in one corpus to a concept in another
bridges:
  - concept_a: "{corpus_name}:{concept-id}"    # Required. Namespaced concept reference.
    concept_b: "{corpus_name}:{concept-id}"    # Required. Namespaced concept reference.
    type: "{relationship-type}"                 # Required. Same vocabulary as graph.yaml.
    note: "{why these are related}"             # Optional. Human-readable justification.

# Aliases: query-routing hints
# When a query matches an alias key, check the listed corpora/concepts
aliases:
  "{search term}":                              # Key: natural language term users might search for
    - corpus: "{corpus_name}"                   # Which corpus to check
      concept: "{concept-id}"                   # Which concept in that corpus
    - corpus: "{corpus_name}"
      concept: "{concept-id}"

# Metadata
meta:
  updated_at: "{ISO-8601 timestamp}"            # Required. Last update time.
  bridge_count: {integer}                       # Required. Number of bridges.
  corpora_linked: ["{corpus_name}"]             # Required. All corpora referenced.
```

---

### Namespaced Reference Format

Cross-corpus references use `{corpus_name}:{concept-id}`:

- `corpus_name` matches the `corpus.name` field in the target corpus's `config.yaml`
- `concept-id` matches a key in the target corpus's `graph.yaml` `concepts:` section
- Example: `polars:query-optimization` → concept `query-optimization` in the `polars` corpus

---

### Validation Rules

The `bridge validate` subcommand checks:

1. **Schema compliance** — all required fields present, correct types
2. **Corpus resolution** — each `corpus_name` resolves to an installed corpus via `registry.yaml`
3. **Concept resolution** — each `concept-id` exists in the referenced corpus's `graph.yaml`
4. **Dangling references** — flag bridges where one side's corpus is not installed (warning, not error — corpus may have been removed)
5. **Relationship type vocabulary** — same controlled types as graph.yaml
6. **Alias targets** — each alias target resolves to a valid corpus + concept

---

### Bridge Candidate Detection

**Algorithm (used by bridge skill):**

1. Load all installed corpora from `registry.yaml`
2. For each corpus, load its `graph.yaml` (skip corpora without one)
3. Collect all concept labels and tags across all corpora
4. Identify candidates:
   a. **Label similarity** — concepts with similar labels across corpora (fuzzy match)
   b. **Tag overlap** — concepts sharing tags across corpora
   c. **Keyword overlap** — corpus keywords that appear in another corpus's concept labels
5. Present candidates to user for confirmation

---

### Graceful Degradation

- **File does not exist:** Navigate skips tier 4. No cross-corpus suggestions.
- **Dangling corpus reference:** Skip that bridge silently. Log warning.
- **Dangling concept reference:** Skip that bridge silently. Log warning.
- **No graph.yaml in referenced corpus:** Skip. Bridge only works between corpora that have graphs.

---

## Related Patterns

- [graph.md](graph.md) — Per-corpus graph that bridges reference into
- [registry-loading.md](registry-loading.md) — How registry.yaml is loaded
- [corpus-routing.md](corpus-routing.md) — Query routing that aliases enhance
