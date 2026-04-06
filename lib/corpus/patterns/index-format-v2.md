# Pattern: index-format-v2 — index.yaml Strict Schema

## Purpose

`index.yaml` replaces LLM-generated prose (`index.md`) as the source of truth for corpus entry metadata. It is a structured, machine-queryable file optimized for deterministic pre-filtering via `yq`. The LLM no longer reads unstructured prose to find relevant files — instead, `yq` filters candidates by tags, keywords, category, and summary regex before the LLM applies semantic judgment.

`index.yaml` is written by the source-scanner agent during `build` and updated differentially during `refresh` and CI. It is the authoritative record of what the corpus contains and the metadata needed to answer navigate queries efficiently.

## When to Use

| Skill / Workflow | Role of index.yaml |
|------------------|--------------------|
| `hiivmind-corpus build` | Written by source-scanner agent; rendered into index.md as final step |
| `hiivmind-corpus refresh` | Differentially updated — stale flags set, new entries added, deleted entries removed, then re-rendered |
| `hiivmind-corpus navigate` | Read for yq pre-filtering before LLM semantic judgment; freshness check compares config.yaml SHA |
| CI refresh workflow | Structurally updated without LLM (SHA diff, stale flagging); triggers external agent for LLM re-scan |

## Relationship to index.md

`index.md` is a **render artifact** produced deterministically from `index.yaml`. It is never hand-edited and never LLM-generated at render time. The same `index.yaml` always produces the same `index.md`, regardless of which agent executes the render.

- `index.yaml` — source of truth, machine-queryable, written/updated by build/refresh
- `index.md` — rendered output, human-readable, regenerated whenever `index.yaml` changes

Navigate checks for `index.yaml` first (v2 flow with yq pre-filtering). If absent, it falls back to `index.md` prose scanning (v1 behavior). Existing corpora with only `index.md` continue to work unchanged.

## Relationship to config.yaml

Source metadata — repository URL, branch, SHA tracking (`last_commit_sha`), timestamps (`last_indexed_at`), and source coordinates — lives in `config.yaml`. It is **not duplicated** in `index.yaml`.

- Navigate reads `config.yaml` for freshness checks (indexed SHA vs live repo SHA)
- CI reads `config.yaml` for source coordinates (repo, branch) to compute file diffs
- `index.yaml` entries reference their source via the `source` field (source ID), which joins to `config.yaml`

## Schema Definition (Strict)

```yaml
entries:
  - id: "polars:user-guide/expressions/basic-operations.md"
    source: polars
    path: "user-guide/expressions/basic-operations.md"
    title: "Basic Operations"
    summary: "Arithmetic, comparisons, Boolean operations, counting unique values"
    tags: [expressions, arithmetic, comparisons, boolean]
    keywords: [add, subtract, multiply, divide, filter, unique, n_unique]
    concepts: [data-transformation, expressions]
    category: reference
    content_type: markdown
    size: standard
    grep_hint: null
    headings:
      - anchor: "arithmetic"
        title: "Arithmetic Operations"
      - anchor: "comparisons"
        title: "Comparison Operators"
    links_to:
      - "polars:user-guide/expressions/casting.md"
    links_from:
      - "polars:user-guide/getting-started.md"
    frontmatter: {}
    stale: false
    stale_since: null
    last_indexed: "2026-03-13T10:00:00Z"

meta:
  generated_at: "2026-03-13T10:00:00Z"
  entry_count: 119
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Canonical identifier: `{source_id}:{path}`. Join key to graph.yaml |
| `source` | string | yes | Source ID from config.yaml |
| `path` | string | yes | Relative path within source |
| `title` | string | yes | Human-readable title — from frontmatter `title`, first heading, or filename |
| `summary` | string | yes | 1-2 sentence description of content. LLM-generated during build |
| `tags` | string[] | yes | Curated search facets — from frontmatter tags, LLM-assigned, or extraction. Controlled vocabulary where possible |
| `keywords` | string[] | yes | Auto-extracted significant terms from content body. Broader than tags — includes function names, API terms, domain-specific identifiers |
| `concepts` | string[] | no | Concept IDs this entry belongs to (keys from graph.yaml). Populated by build Phase 5b or graph add-concept. Empty list if not yet mapped. Enriches embedding text for RAG retrieval. |
| `category` | enum | yes | Coarse classifier. Values: `reference`, `tutorial`, `guide`, `api`, `config`, `navigation`, `journal`, `unknown` (CI placeholder — replaced on LLM re-scan) |
| `content_type` | enum | yes | File format. Values: `markdown`, `yaml`, `json`, `text`, `rst` |
| `size` | enum | yes | `standard` or `large`. Large = file exceeds 1000 lines |
| `grep_hint` | string | no | For large files: suggested grep/search command with `FILE` placeholder, e.g. `grep -n "^## " FILE`. Null for standard files |
| `headings` | object[] | no | Sub-file anchors with `anchor` (slugified) and `title` fields |
| `links_to` | string[] | no | Outbound links — entry IDs this file references. From extraction |
| `links_from` | string[] | no | Inbound links — entry IDs that reference this file. Populated during full build by cross-referencing all entries' `links_to`. **Not updated by CI differential refresh** — requires full LLM-powered build to recompute cross-references accurately |
| `frontmatter` | object | no | Preserved original YAML frontmatter from source file — all keys by default. Corpus authors can configure exclusions in `config.yaml` extraction settings. Pass-through for domain-specific queries |
| `stale` | boolean | yes | CI flag: content changed since last LLM-powered scan. Default: false |
| `stale_since` | datetime | no | When the entry was marked stale. Null if not stale |
| `last_indexed` | datetime | yes | When this entry was last scanned by the source-scanner agent |

## Section Entries (Tier 2)

When a source has `sections.enabled: true`, the source-scanner generates sub-entries
for heading-bounded sections within large or structured documents. Section entries
live in the same `entries` list as file-level entries.

### Additional Fields for Section Entries

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent` | string | yes (sections) | ID of the parent file entry |
| `tier` | enum | yes (sections) | Always `section` for section entries. File entries omit this field or use `file` |
| `anchor` | string | yes (sections) | Slugified heading text (URL fragment) |
| `heading_level` | integer | yes (sections) | Heading level (2-6). Level 1 is typically the page title |
| `line_range` | integer[2] | yes (sections) | `[start_line, end_line]` — 1-indexed, inclusive |

### Section Entry ID Format

`{parent_id}#{anchor}` — e.g., `polars:expressions.md#window-functions`

### Example

```yaml
entries:
  # File-level entry (unchanged)
  - id: "polars:expressions.md"
    source: polars
    path: "expressions.md"
    title: "Expressions"
    summary: "Overview of Polars expression system"
    tags: [expressions, core]
    keywords: [col, lit, when, then]
    concepts: [expressions]
    category: reference
    content_type: markdown
    size: large
    grep_hint: "grep -n '^## ' FILE"
    headings:
      - anchor: "window-functions"
        title: "Window Functions"
      - anchor: "aggregations"
        title: "Aggregations"
    links_to: []
    links_from: []
    frontmatter: {}
    stale: false
    stale_since: null
    last_indexed: "2026-04-05T10:00:00Z"

  # Section entry (new)
  - id: "polars:expressions.md#window-functions"
    parent: "polars:expressions.md"
    tier: section
    source: polars
    path: "expressions.md"
    anchor: "window-functions"
    title: "Window Functions"
    summary: "How to use over() for window expressions in Polars"
    tags: [window, aggregation, over]
    keywords: [partition_by, order_by, rolling]
    concepts: ["window-expressions"]
    category: reference
    content_type: markdown
    heading_level: 2
    line_range: [145, 210]
    stale: false
    stale_since: null
    last_indexed: "2026-04-05T10:00:00Z"
```

### Embedding

Section entries use the same metadata-embedding pattern as file entries:
`"passage: {title} | {summary} | {', '.join(tags)} | {', '.join(concepts)}"`

They are embedded into the existing `index-embeddings.lance/` alongside file entries.
The `tier` field in index.yaml (not in Lance) lets the navigate skill distinguish them.

## Meta Section

| Field | Type | Description |
|-------|------|-------------|
| `meta.generated_at` | datetime | When the index was last written |
| `meta.entry_count` | integer | Total entries in the index |

Source-level tracking (SHA, timestamps, repo coordinates) remains in `config.yaml` where it already exists. No duplication.

## yq Query Patterns

```bash
# Tag search
yq '.entries[] | select(.tags[] == "expressions")' index.yaml

# Keyword search
yq '.entries[] | select(.keywords[] | test("filter"))' index.yaml

# Category filter
yq '.entries[] | select(.category == "reference")' index.yaml

# Summary regex
yq '.entries[] | select(.summary | test("arithmetic|comparisons"; "i"))' index.yaml

# Combined: tag + category
yq '.entries[] | select((.tags[] == "expressions") and .category == "reference")' index.yaml

# Heading search
yq '.entries[] | select(.headings[].title | test("Arithmetic"; "i"))' index.yaml

# Forward link traversal
yq '.entries[] | select(.links_to[] | test("casting"))' index.yaml

# Backlink discovery
yq '.entries[] | select(.links_from[] | test("getting-started"))' index.yaml

# Find stale entries
yq '.entries[] | select(.stale == true)' index.yaml

# Count entries per category
yq '.entries | group_by(.category) | .[] | {(.[0].category): length}' index.yaml
```

## Related Patterns

- [index-rendering.md](index-rendering.md) — Deterministic render algorithm: index.yaml → index.md
- [freshness.md](freshness.md) — SHA-gated freshness check and stale flagging algorithm
- [index-generation.md](index-generation.md) — Source-scanner output, build flow, and relationship to legacy format
- [graph.md](graph.md) — graph.yaml schema; concepts link to entry IDs, which are the join key from index.yaml
- [config-parsing.md](config-parsing.md) — config.yaml structure; source coordinates and SHA tracking used by navigate and CI
