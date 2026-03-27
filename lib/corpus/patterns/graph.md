# Pattern: Per-Corpus Concept Graph (graph.yaml)

## Purpose

Define the strict schema for `graph.yaml` — a concept-centric relationship graph stored alongside `index.md` in each corpus. Concepts are knowledge graph nodes; entries are evidence; relationships are typed edges between concepts.

## When to Use

- During `build` skill — generate graph.yaml from extraction output
- During `refresh` skill — update auto-extracted relationships, preserve manual ones
- During `navigate` skill — enrich retrieval with concept membership and relationship traversal
- During `graph` skill — view, validate, and edit graph.yaml

---

### Schema Definition (Strict)

**Schema version 2** (current): Concepts define labels, descriptions, and tags only.
Entry membership is stored in index.yaml entries via `concepts[]` field (bidirectional link).
Schema version 1 (legacy) included `entries[]` and `entry_count` per concept — these are
migrated to index.yaml `concepts[]` on next build or graph edit.

```yaml
schema_version: 2

# Concepts: knowledge graph nodes
# Key: concept ID (slugified label — lowercase, hyphens, no spaces)
# Entry membership is in index.yaml — query with:
#   yq '.entries[] | select(.concepts[] == "{concept-id}")' index.yaml
concepts:
  {concept-id}:
    label: "{Human-Readable Label}"           # Required. Display name.
    description: "{One-line description}"      # Required. What this concept covers.
    tags: ["{tag1}", "{tag2}"]                 # Optional. From extracted #tags. Used for concept matching.

# Relationships: typed edges between concepts
relationships:
  - from: "{concept-id}"                       # Required. Source concept ID.
    to: "{concept-id}"                         # Required. Target concept ID.
    type: "{relationship-type}"                # Required. One of the controlled vocabulary.
    origin: "{origin-type}"                    # Required. How this relationship was discovered.
    evidence: "{source_id}:{path}"             # Optional. File that established this link. Null for manual.

# Metadata about graph state
meta:
  generated_at: "{ISO-8601 timestamp}"         # Required. When graph was last generated/updated.
  concept_count: {integer}                     # Required. Number of concepts.
  relationship_count: {integer}                # Required. Number of relationships.
```

---

### Concept ID Conventions

Concept IDs are slugified from the label:

**Algorithm:**

1. Take the label text
2. Convert to lowercase
3. Replace spaces with hyphens
4. Remove special characters (keep alphanumeric and hyphens)
5. Collapse multiple hyphens

**Examples:**

| Label | Concept ID |
|-------|------------|
| Family Activities | `family-activities` |
| Query Optimization | `query-optimization` |
| Q1 2022 Budget | `q1-2022-budget` |
| IT Cybersecurity | `it-cybersecurity` |

---

### Relationship Type Vocabulary (Controlled)

| Type | Meaning | Example |
|------|---------|---------|
| `includes` | Concept A contains or encompasses Concept B | family-activities → recipes |
| `depends-on` | Concept A requires understanding of Concept B | lazy-frames → query-optimization |
| `see-also` | Concepts are related but independent | work-projects → budget-review |
| `extends` | Concept A builds upon Concept B | advanced-queries → basic-queries |
| `contrast-with` | Concepts represent alternative approaches | lazy-evaluation → eager-evaluation |

---

### Origin Types

| Origin | Meaning | Refresh Behavior |
|--------|---------|-----------------|
| `wikilink` | Discovered from [[wikilink]] or [markdown](link) | Updated automatically on refresh |
| `tag` | Inferred from shared #tag co-occurrence | Updated automatically on refresh |
| `frontmatter` | Inferred from frontmatter metadata | Updated automatically on refresh |
| `manual` | Curated by human | Preserved on refresh — never overwritten |

---

### Graph Generation from Extraction Output

**Algorithm (used by build skill):**

1. **Collect extraction data** from all source-scanner reports
2. **Cluster entries into concepts:**
   a. Group by directory structure (e.g., `Family/Recipes/*.md` → `recipes` concept)
   b. Group by shared tags (e.g., all files tagged `#project` → `work-projects` concept)
   c. Group by wikilink hub pages (a file that links to many others defines a concept boundary)
3. **Propose concepts to user** — present clusters with suggested labels, ask for confirmation/renaming
4. **Generate relationships:**
   a. Wikilinks between entries in different concepts → relationship between those concepts
   b. Hub pages that link to entries across concepts → `includes` relationships
   c. Shared tags across concepts → `see-also` relationships
5. **Write graph.yaml** with `origin` tracking on each relationship

**Using bash (slugify helper):**

```bash
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//'
}
```

---

### Validation Rules

The `graph validate` subcommand checks:

1. **Schema compliance** — all required fields present, correct types, schema_version is 2
2. **Dangling concept references** — entries in index.yaml reference concept IDs that don't exist in graph.yaml (query: `yq '.entries[].concepts[]' index.yaml | sort -u` vs graph.yaml concept keys)
3. **Dangling relationships** — `from` and `to` reference defined concept IDs
4. **Orphan concepts** — concepts not referenced by any entry in index.yaml (warning, not error)
5. **Relationship type vocabulary** — only controlled types used
6. **Origin type vocabulary** — only defined origins used

---

### yq Query Patterns

```bash
# Find concepts by tag
yq '.concepts | to_entries[] | select(.value.tags[] == "performance") | .key' graph.yaml

# Find entries belonging to a concept (query index.yaml, not graph.yaml)
yq '.entries[] | select(.concepts[] == "lazy-evaluation") | {id, title}' index.yaml

# Find entries belonging to multiple concepts
yq '.entries[] | select(.concepts | length > 1) | {id, concepts}' index.yaml

# Follow relationships from a concept (1 hop)
yq '.relationships[] | select(.from == "query-optimization") | .to' graph.yaml

# Find manually curated relationships (preserved on refresh)
yq '.relationships[] | select(.origin == "manual")' graph.yaml
```

---

## Related Patterns

- [extraction.md](extraction.md) — Produces the data that feeds graph generation
- [registry-graph.md](registry-graph.md) — Project-level cross-corpus graph overlay
- [index-generation.md](index-generation.md) — Graph complements the flat index
- [scanning.md](scanning.md) — Source-scanner produces extraction data
