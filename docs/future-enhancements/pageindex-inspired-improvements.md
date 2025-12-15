# PageIndex-Inspired Improvements

> **Context:** Analysis of [PageIndex](https://github.com/VectifyAI/PageIndex) revealed architectural patterns that could enhance hiivmind-corpus while preserving our zero-infrastructure, human-curated philosophy.

## Overview

| Proposal | Effort | Value | Philosophy Fit |
|----------|--------|-------|----------------|
| 1. Hierarchical tree index format | Medium | High | Extends current approach |
| 2. Node summaries | Low | Medium | Optional enhancement |
| 3. Reasoning transparency | Low | High | Debugging + trust |
| 4. PDF source type | Medium | High | Broader coverage |
| 5. OpenAPI/GraphQL indexing | Medium | High | API-focused corpora |
| 6. PageIndex integration | Low | Medium | Best of both worlds |

---

## Proposal 1: Hierarchical Tree Index Format

### The Problem

Our current index format is flat:

```markdown
## Query Optimization
*Improving query performance*

- **EXPLAIN** `polars:sql-reference/explain.md` - Analyze query plans
- **Profiling** `polars:operations/profiling.md` - Identify bottlenecks
- **Settings** `polars:sql-reference/settings.md#performance` - Runtime tuning
```

This works well for shallow documentation (2-3 levels), but struggles with:
- Deeply nested API documentation (REST endpoints, GraphQL schemas)
- Large technical manuals with 5+ levels of hierarchy
- Documents where navigation path matters (legal, compliance)

### The Solution: Optional Tree Format

Support an alternative **YAML tree format** for corpora that need deep hierarchy:

```yaml
# data/index.yaml (alternative to index.md)
schema: tree-v1
project: github-api

sections:
  - title: REST API
    summary: CRUD operations via HTTP endpoints
    children:
      - title: Repositories
        summary: Repository management endpoints
        children:
          - title: Create Repository
            path: rest:repos/create.md
            summary: POST /user/repos - Create a new repository
            keywords: [repos, POST, create, name, private]
          - title: Get Repository
            path: rest:repos/get.md
            summary: GET /repos/{owner}/{repo}
            keywords: [repos, GET, owner, repo]
          - title: Branch Protection
            summary: Manage branch protection rules
            children:
              - title: Get Protection
                path: rest:repos/branches/protection.md#get
                summary: GET branch protection settings
                keywords: [branches, protection, GET, required_reviews]
              - title: Update Protection
                path: rest:repos/branches/protection.md#update
                summary: PUT branch protection settings
                keywords: [branches, protection, PUT, enforce_admins]
```

### Navigation Behavior

When using tree format, the navigate skill reasons through the hierarchy:

```markdown
### Tree Navigation (for index.yaml)

1. **Read tree structure** from `data/index.yaml`
2. **Present top-level sections** to understand scope
3. **Reason through hierarchy** based on user question:

   Question: "How do I require reviews on a branch?"

   Reasoning:
   > Looking for "reviews" + "branch"
   > → REST API (likely HTTP operation)
   > → Repositories (branches are part of repos)
   > → Branch Protection (matches "branch")
   > → Update Protection (has keyword "required_reviews")
   > → Found: `rest:repos/branches/protection.md#update`

4. **Fetch content** using path
5. **Cite reasoning path** in response
```

### When to Use Tree vs Flat

| Corpus Type | Recommended Format |
|-------------|-------------------|
| Library docs (Polars, React) | Flat (index.md) |
| API references (REST, GraphQL) | Tree (index.yaml) |
| Technical manuals (>100 pages) | Tree (index.yaml) |
| Mixed sources (git + web + local) | Flat (index.md) |
| Operational corpora (routing guides) | Flat with keywords |

### Coexistence

Both formats can coexist:
- `data/index.md` - flat format (current default)
- `data/index.yaml` - tree format (optional)

If both exist, prefer tree for navigation but support both.

### Build Skill Update

Add tree format support to `hiivmind-corpus-build`:

```markdown
### Step 2: Choose Index Format

"This corpus has deep hierarchy (5+ levels detected). Would you like to use:
1. **Flat format** (index.md) - Simple, works for most cases
2. **Tree format** (index.yaml) - Better for deep navigation, shows reasoning path"

For API documentation or technical manuals, tree format is recommended.
```

### Schema Definition

```yaml
# Tree index schema
schema: tree-v1
project: string           # Project name
display_name: string      # Human-readable name

sections:                 # Top-level array
  - title: string         # Section heading
    summary: string       # Brief description (optional but recommended)
    path: string          # source:relative/path.md (leaf nodes only)
    keywords: [string]    # Entry-level keywords (optional)
    children: [section]   # Nested sections (recursive)
```

### Implementation Checklist

- [ ] Define tree index schema (`schemas/tree-index.yaml`)
- [ ] Update `hiivmind-corpus-build` to support tree format
- [ ] Update navigate template with tree reasoning logic
- [ ] Update `hiivmind-corpus-enhance` to handle tree modifications
- [ ] Update `hiivmind-corpus-refresh` to preserve tree structure
- [ ] Add format detection to discover skill

---

## Proposal 2: Node Summaries

### The Problem

Our current entries have brief descriptions:

```markdown
- **EXPLAIN** `polars:sql-reference/explain.md` - Analyze query plans
```

For routing decisions, especially with keywords, a richer summary helps the LLM understand *what's in the document* without fetching it.

### The Solution: Optional Summary Field

Add an optional multi-line summary:

```markdown
- **EXPLAIN** `polars:sql-reference/explain.md` - Analyze query plans
  Summary: Shows the logical and physical query plan. Use EXPLAIN ANALYZE
  for actual execution statistics. Covers lazy frame optimization, predicate
  pushdown visibility, and projection pruning.
  Keywords: `explain`, `analyze`, `query plan`, `optimization`
```

Or in tree format:

```yaml
- title: EXPLAIN
  path: polars:sql-reference/explain.md
  summary: |
    Shows the logical and physical query plan. Use EXPLAIN ANALYZE
    for actual execution statistics. Covers lazy frame optimization,
    predicate pushdown visibility, and projection pruning.
  keywords: [explain, analyze, query plan, optimization]
```

### When Summaries Help

| Situation | Benefit |
|-----------|---------|
| Multiple similar entries | Disambiguation without fetching |
| Large source files | Know what's inside before reading |
| Routing decisions | Better keyword + summary matching |
| Tiered indexes | Section summaries guide navigation |

### Generation Options

1. **Human-written** (current) - Most accurate, requires time
2. **LLM-assisted during build** - "Generate a 2-sentence summary of this file"
3. **Hybrid** - LLM drafts, human edits

### Build Skill Update

Add summary generation option:

```markdown
### Step 5: Enhance Entries (Optional)

"Would you like me to generate summaries for entries? This helps with:
- Better routing decisions
- Disambiguation between similar entries
- Understanding content without fetching

Options:
1. **No summaries** - Keep entries brief (default)
2. **Section summaries** - Summarize each section heading
3. **Entry summaries** - Summarize each individual entry"
```

### Implementation Checklist

- [ ] Update index format to support `Summary:` lines
- [ ] Update tree schema with summary field
- [ ] Add summary generation option to build skill
- [ ] Update navigate skills to use summaries for routing
- [ ] Document summary best practices

---

## Proposal 3: Reasoning Transparency

### The Problem

When navigate returns an answer, the user doesn't see *why* that source was chosen. This makes debugging difficult and reduces trust.

### The Solution: Optional Reasoning Output

PageIndex includes a "thinking" field in its output. We can adopt this pattern:

```markdown
### Reasoning Transparency (Optional)

If the user requests reasoning or if routing was ambiguous, show the decision path:

**User question:** "How do I filter nulls in a lazy frame?"

**Reasoning:**
> 1. Extracted terms: `filter`, `nulls`, `lazy frame`
> 2. Searched index for matches:
>    - "Lazy Operations" section matches `lazy`
>    - "Null Handling" entry matches `nulls`, `filter`
>    - Keywords `drop_nulls`, `fill_null` found
> 3. Selected: `polars:user-guide/expressions/null.md`
> 4. Fetching content...

**Answer:** [actual answer with citation]
```

### Triggering Reasoning Output

| Trigger | Behavior |
|---------|----------|
| User says "show your reasoning" | Always show |
| User says "why did you pick that?" | Show for current answer |
| Ambiguous routing (multiple matches) | Auto-show to explain choice |
| Debug mode in config | Always show |

### Navigate Skill Update

Add to `hiivmind-corpus-navigate` template:

```markdown
## Reasoning Output

When reasoning transparency is requested or helpful:

1. **Show search process:**
   - Terms extracted from question
   - Index sections/entries searched
   - Keyword matches found

2. **Show routing decision:**
   - If single match: "Direct match found"
   - If multiple matches: "Chose X because [reason]"
   - If no match: "No direct match, exploring [related sections]"

3. **Show fetch decision:**
   - Why this file was selected
   - If using `⚡ GREP`: What pattern was searched

Format as a blockquote before the answer:
> **Reasoning:** [decision path]
```

### Implementation Checklist

- [ ] Add reasoning output section to navigate template
- [ ] Define triggers for auto-showing reasoning
- [ ] Update global navigate with reasoning for corpus routing
- [ ] Add `show_reasoning` config option

---

## Proposal 4: PDF Source Type

### The Problem

Many valuable documentation sources are PDFs:
- Technical specifications
- Research papers
- Government/regulatory documents
- Vendor documentation

Currently, users must manually extract and convert these.

### The Solution: Native PDF Source Type

Add `type: pdf` to source configuration:

```yaml
sources:
  - id: spec
    type: pdf
    path: data/uploads/spec/technical-spec-v2.pdf
    # Or remote:
    url: https://example.com/docs/specification.pdf

    # PDF-specific options
    extract_toc: true          # Use PDF's table of contents
    page_range: [1, 50]        # Optional: limit pages
    ocr_fallback: false        # Use OCR for scanned PDFs
```

### Index Generation for PDFs

When building index for PDF sources:

1. **Extract structure** from PDF outline/TOC
2. **Create page-based entries:**

```markdown
## Technical Specification

### Architecture (Pages 5-12)
- **System Overview** `spec:pages/5-7` - High-level architecture diagram and components
  Summary: Three-tier architecture with message queue. Covers scalability requirements.

- **Data Flow** `spec:pages/8-12` - Request/response patterns
  Summary: Synchronous API calls, async event processing, caching strategy.

### API Reference (Pages 13-45)
- **Authentication** `spec:pages/13-18` - OAuth2 and API keys
- **Endpoints** `spec:pages/19-45` ⚡ GREP - Full endpoint documentation
```

### Path Format for PDFs

```
{source_id}:pages/{start}-{end}
{source_id}:pages/{page}
{source_id}:pages/{page}#section-anchor
```

### Retrieval Behavior

When fetching PDF content:

1. **If local PDF exists:** Extract text from specified pages
2. **If remote URL:** Download, cache, then extract
3. **For `⚡ GREP` entries:** Search extracted text

### PDF Processing Options

| Option | Default | Purpose |
|--------|---------|---------|
| `extract_toc` | true | Use PDF's built-in outline |
| `page_range` | all | Limit to specific pages |
| `ocr_fallback` | false | OCR for scanned documents |
| `preserve_tables` | true | Maintain table structure |
| `image_extraction` | false | Extract embedded images |

### Integration with PageIndex

For complex PDFs, offer PageIndex integration:

```yaml
sources:
  - id: manual
    type: pdf
    path: data/uploads/manual.pdf
    processor: pageindex        # Use PageIndex for tree extraction
    pageindex_options:
      max_pages_per_node: 10
      add_summaries: true
```

This leverages PageIndex's PDF processing strength while maintaining our corpus structure.

### Implementation Checklist

- [ ] Add PDF source type to config schema
- [ ] Implement PDF text extraction (PyMuPDF or similar)
- [ ] Add page-range path format support
- [ ] Update build skill with PDF structure detection
- [ ] Add optional PageIndex integration
- [ ] Document PDF source best practices

---

## Proposal 5: OpenAPI/GraphQL Auto-Indexing

### The Problem

API documentation often lives in structured formats:
- OpenAPI/Swagger specs (YAML/JSON)
- GraphQL schemas
- AsyncAPI specs

These are highly structured but too large to read entirely. Our `⚡ GREP` marker helps, but we could do better.

### The Solution: Schema-Aware Indexing

Automatically generate index entries from API schemas:

```yaml
sources:
  - id: api
    type: openapi
    path: .source/api/openapi.yaml
    # Or:
    url: https://api.example.com/openapi.json

    index_options:
      group_by: tag              # Group endpoints by OpenAPI tags
      include_schemas: true      # Index schema definitions
      include_examples: true     # Index request/response examples
```

### Generated Index (OpenAPI)

From an OpenAPI spec, auto-generate:

```markdown
## API Reference
*Auto-generated from openapi.yaml*

### Users (tag)
- **List Users** `api:openapi.yaml` ⚡ GREP `GET /users`
  Summary: Paginated list of users. Supports filtering by role, status.
  Keywords: `users`, `GET`, `list`, `pagination`, `filter`

- **Create User** `api:openapi.yaml` ⚡ GREP `POST /users`
  Summary: Create new user account. Requires admin role.
  Keywords: `users`, `POST`, `create`, `email`, `role`

- **Get User** `api:openapi.yaml` ⚡ GREP `GET /users/{id}`
  Summary: Retrieve user by ID. Includes profile and settings.
  Keywords: `users`, `GET`, `id`, `profile`

### Schemas
- **User** `api:openapi.yaml` ⚡ GREP `components/schemas/User`
  Summary: User object with id, email, role, created_at fields.
  Keywords: `User`, `schema`, `id`, `email`, `role`
```

### Generated Index (GraphQL)

From a GraphQL schema:

```markdown
## GraphQL API
*Auto-generated from schema.graphql*

### Queries
- **user** `schema:schema.graphql` ⚡ GREP `type Query` → `user`
  Summary: Query single user by ID. Returns User type.
  Keywords: `user`, `query`, `id`, `User`

- **users** `schema:schema.graphql` ⚡ GREP `type Query` → `users`
  Summary: Query paginated users with filters.
  Keywords: `users`, `query`, `filter`, `pagination`

### Mutations
- **createUser** `schema:schema.graphql` ⚡ GREP `type Mutation` → `createUser`
  Summary: Create new user. Input: CreateUserInput.
  Keywords: `createUser`, `mutation`, `CreateUserInput`

### Types
- **User** `schema:schema.graphql` ⚡ GREP `type User`
  Summary: User type with id, email, posts, comments fields.
  Keywords: `User`, `type`, `id`, `email`, `posts`
```

### Build Skill Integration

When adding an OpenAPI/GraphQL source:

```markdown
### API Schema Detected

"I found an OpenAPI 3.0 specification with:
- 45 endpoints across 8 tags
- 23 schema definitions
- 12 security schemes

Would you like me to:
1. **Auto-generate full index** - Create entries for all endpoints and schemas
2. **Selective indexing** - Choose which tags/schemas to include
3. **Manual indexing** - I'll note the schema exists, you curate entries"

For operational corpora with routing guides, auto-generation with keywords
is recommended.
```

### Schema-Specific GREP Patterns

Enhance `⚡ GREP` with schema-aware patterns:

| Schema Type | GREP Pattern |
|-------------|--------------|
| OpenAPI endpoint | `paths:./users:.get:` |
| OpenAPI schema | `components:.schemas:.User:` |
| GraphQL type | `^type User \{` |
| GraphQL query | `^type Query \{[^}]*user` |
| GraphQL mutation | `^type Mutation \{[^}]*createUser` |

### Implementation Checklist

- [ ] Add `openapi` source type with YAML/JSON parsing
- [ ] Add `graphql` source type with schema parsing
- [ ] Implement auto-index generation from schemas
- [ ] Add schema-aware GREP patterns
- [ ] Update build skill with schema detection
- [ ] Support selective indexing (by tag, type, etc.)
- [ ] Generate keywords from operation names and parameters

---

## Proposal 6: PageIndex Integration

### The Problem

Some documents benefit from PageIndex's automated tree extraction, especially:
- Complex PDFs without clear structure
- Documents where page-level navigation matters
- Ad-hoc documents not worth manually indexing

### The Solution: PageIndex as a Processor

Allow PageIndex to pre-process documents, then import the result:

```yaml
sources:
  - id: report
    type: pageindex
    path: data/uploads/annual-report.pdf

    pageindex_options:
      model: gpt-4o
      max_pages_per_node: 10
      add_summaries: true

    # Import PageIndex's tree into our index
    import_mode: tree           # or 'flat' to flatten
```

### Workflow

```
PDF Document
    ↓
PageIndex (automated tree extraction)
    ↓
JSON tree with summaries
    ↓
Import into hiivmind-corpus
    ↓
Human curation (optional)
    ↓
Final corpus index
```

### Integration Benefits

| PageIndex Strength | hiivmind-corpus Addition |
|--------------------|--------------------------|
| Automated structure extraction | Human curation layer |
| Single-document focus | Multi-source corpora |
| JSON tree format | Markdown or YAML index |
| Requires Python + API | Zero infrastructure (post-import) |

### Build Skill Integration

```markdown
### PageIndex Import

"Would you like to use PageIndex to pre-process this document?

PageIndex will:
- Extract hierarchical structure automatically
- Generate summaries for each section
- Create page-level references

You can then:
- Review and curate the generated index
- Add keywords for operational use
- Merge with other sources in this corpus

Note: Requires PageIndex API access (pageindex.ai)"
```

### Import Modes

| Mode | Result |
|------|--------|
| `tree` | Import PageIndex tree as index.yaml |
| `flat` | Flatten tree into index.md entries |
| `hybrid` | Top 2 levels as sections, rest as entries |

### Implementation Checklist

- [ ] Add `pageindex` source type
- [ ] Implement PageIndex API integration (optional dependency)
- [ ] Create tree-to-corpus import logic
- [ ] Add import mode options
- [ ] Document PageIndex integration workflow

---

## Cross-Proposal Dependencies

```
                    ┌──────────────────┐
                    │ 1. Tree Format   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ 2. Summaries│  │ 4. PDF Type │  │ 6. PageIndex│
    └─────────────┘  └──────┬──────┘  └──────┬──────┘
                            │                │
                            └────────┬───────┘
                                     │
                                     ▼
                          ┌─────────────────┐
                          │ 5. API Indexing │
                          └─────────────────┘
                                     │
                                     ▼
                          ┌─────────────────┐
                          │ 3. Reasoning    │
                          └─────────────────┘
```

**Recommended implementation order:**
1. **Reasoning Transparency** (standalone, low effort, high value)
2. **Node Summaries** (standalone, enhances all other features)
3. **Tree Format** (foundation for PDF and PageIndex)
4. **OpenAPI/GraphQL Indexing** (high value for API corpora)
5. **PDF Source Type** (benefits from tree format)
6. **PageIndex Integration** (builds on all above)

---

## Summary

| Proposal | What It Adds | Preserves |
|----------|--------------|-----------|
| Tree Format | Deep hierarchy navigation | Human curation |
| Summaries | Richer routing decisions | Zero infrastructure |
| Reasoning | Transparency + debugging | Simple lookup model |
| PDF Sources | Broader document coverage | File-based state |
| API Indexing | Structured API corpora | Collaborative building |
| PageIndex | Automated extraction option | Final curation step |

All proposals maintain the core philosophy:
- **Zero infrastructure** (files + git)
- **Human curation** (quality over automation)
- **Per-session discovery** (no stale state)
- **Collaborative building** (fast setup)

They extend hiivmind-corpus to handle more document types and deeper hierarchies while keeping the system simple and portable.
