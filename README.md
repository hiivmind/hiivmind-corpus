# hiivmind-corpus

A Claude Code plugin for building persistent, curated documentation indexes with semantic search. One plugin creates, maintains, and queries documentation corpora from any source — git repos, local files, web pages, Obsidian vaults, PDFs, and more.

**Quick links:** [Using a Corpus](#using-a-corpus) | [Building a Corpus](#building-a-corpus) | [Semantic Search](#semantic-search-rag) | [Published Corpora](#published-corpora)

## The Idea

Without structured indexing, Claude investigates libraries by relying on training data (outdated), web searching (hit-or-miss), or fetching URLs one at a time (no context). Every session rediscovers the same things.

A corpus solves this. You build a curated index once — collaboratively, around your actual use case — and Claude searches it across sessions. The index tracks where everything came from, how fresh it is, and uses semantic search to find relevant entries even when queries don't match exact keywords.

This follows the ["just in time" context pattern](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) from Anthropic: maintain lightweight identifiers, dynamically load content at runtime.

## Getting Started

```
/hiivmind-corpus
```

One command, natural language:

| You say... | What happens |
|---|---|
| *"Create a corpus for Polars"* | Scaffolds a new corpus, clones docs |
| *"What corpora do I have?"* | Discovers all installed corpora |
| *"How do lazy frames work?"* | Searches your corpora with semantic + keyword matching |
| *"Refresh my React corpus"* | Checks for upstream changes, updates stale entries |
| *"Add the TanStack Query docs"* | Extends an existing corpus with new sources |

## Installation

**From the command line:**

```bash
claude plugin add hiivmind/hiivmind-corpus
```

**From within a Claude Code session:**

```
/plugin marketplace add hiivmind/hiivmind-corpus
/plugin install hiivmind-corpus@hiivmind
```

Or use `/plugin` to browse and install interactively.

## Using a Corpus

Most users start here — someone else built the corpus, you just want to query it.

### 1. Register a corpus with your project

```
/hiivmind-corpus register github:hiivmind/hiivmind-corpus-polars
```

This adds the corpus to your project's registry (`.hiivmind/corpus/registry.yaml`). Register as many as you need — they're lightweight references, not copies.

### 2. Ask questions

Just ask naturally. Claude routes your question to the right corpus:

```
"How do I filter rows in Polars?"
"What's the difference between select and with_columns?"
"Show me lazy frame optimization techniques"
```

Or be explicit: `/hiivmind-corpus navigate polars "group by aggregations"`

### How navigation works

When you ask a question, the navigate skill:

1. **Routes to the right corpus** — matches your query against registered corpora using semantic similarity (if embeddings are cached) or keyword matching
2. **Finds relevant entries** — searches the corpus index using vector search with optional SQL filtering, boosted by concept graph relationships
3. **Fetches documentation** — retrieves the actual content from the source repo via `gh api`
4. **Presents the answer** — with source citations and related doc suggestions

For remote GitHub corpora, embeddings are automatically cached locally on first query (~5 seconds, then instant on subsequent queries).

### Check what you have

```
/hiivmind-corpus discover        # List all available corpora
/hiivmind-corpus status           # Check freshness and health
```

### Cross-corpus queries

With 2+ corpora registered, you can create **bridges** — links between related concepts across corpora:

```
/hiivmind-corpus bridge           # Detect and create cross-corpus links
```

Navigate then uses bridges and aliases to route queries that span multiple documentation sets. Search for "lazy evaluation" and it finds relevant entries in both Polars and Ibis.

---

## Building a Corpus

If you want to create a new corpus from scratch — for a library, framework, or internal project.

### Quick start

```
/hiivmind-corpus init             # Scaffold from a GitHub repo
/hiivmind-corpus add-source       # Add git repos, local files, web pages, PDFs
/hiivmind-corpus build            # Scan sources, build index collaboratively
```

The build process is a conversation — Claude scans the docs and you guide what matters: "I care about data modeling and ETL, skip the deployment stuff." That curation persists across sessions.

### After building

```
/hiivmind-corpus enhance          # Deepen coverage on specific topics
/hiivmind-corpus refresh          # Sync with upstream changes
/hiivmind-corpus graph add-concept  # Add zettelkasten concept clusters
```

---

## What a Corpus Looks Like

Each corpus is a data-only repository — just files, no server, no database:

```
hiivmind-corpus-{project}/
├── config.yaml                # Source definitions + keywords
├── index.yaml                 # Structured index (entries with summaries, tags, concepts)
├── index.md                   # Human-readable index (rendered from index.yaml)
├── graph.yaml                 # Concept graph — zettelkasten relationships (optional)
├── index-embeddings.lance/    # Semantic search embeddings (committed, not gitignored)
├── render-index.sh            # Deterministic index.yaml → index.md renderer
├── .source/                   # Git clones (gitignored)
├── .cache/                    # Web/llms-txt cached content (gitignored)
└── uploads/                   # Local document sources
```

The index is the product. Everything else supports building and maintaining it.

## Three Layers

The corpus architecture is a value-add pipeline — each layer builds on the previous:

```
Layer 1: INDEX (foundation)
  source files → index.yaml (entries with title, summary, tags, keywords, concepts)
  → index.md (rendered for humans)

Layer 2a: GRAPH (zettelkasten)          Layer 2b: RAG (semantic search)
  Concept definitions + relationships    Vector embeddings of entry metadata
  References entries by concept ID       Enriched by concept membership
  Pure relationship store                Entries embed: title|summary|tags|concepts

         ↕ mutual enrichment ↕
  Graph candidate detection uses RAG similarity
  RAG graph-boost uses graph relationships
  Bridge detection queries per-corpus RAG
```

**Layer 1 (index.yaml)** is always built. Layers 2a and 2b are optional — they add value for larger corpora and cross-corpus scenarios.

## Skills

### Build & Maintain

| Skill | Purpose |
|---|---|
| **init** | Scaffold a new corpus from a GitHub repo URL or local project |
| **add-source** | Add git repos, local files, web pages, PDFs, Obsidian vaults, llms.txt |
| **build** | Scan sources, build index.yaml collaboratively with user, generate embeddings |
| **enhance** | Deepen coverage on specific topics within an existing index |
| **refresh** | Compare against upstream commits, flag stale entries, re-embed |

### Query & Discover

| Skill | Purpose |
|---|---|
| **navigate** | Search across corpora — semantic pre-filter, graph-boost, reranking |
| **discover** | Find all installed/registered corpora and their status |
| **register** | Connect a corpus to the current project via registry.yaml |
| **status** | Check corpus health — freshness, embedding status, upstream changes |

### Concepts & Relationships

| Skill | Purpose |
|---|---|
| **graph** | View, validate, and edit concept graphs (graph.yaml) |
| **bridge** | Create cross-corpus concept bridges and query-routing aliases |

### Lifecycle

```
init → add-source → build → refresh/enhance (as needed)
                       ↓
              graph (concepts) ←→ embeddings (RAG)
                       ↓
         register → navigate (query) → bridge (cross-corpus)
```

## Source Types

| Type | Storage | Example |
|---|---|---|
| **git** | `.source/{source_id}/` | Library docs, framework APIs |
| **local** | `uploads/{source_id}/` | Team standards, internal docs |
| **web** | `.cache/web/{source_id}/` | Blog posts, articles |
| **llms-txt** | `.cache/llms-txt/{source_id}/` | Sites with llms.txt manifests |
| **generated-docs** | `.source/{source_id}/` + web | Hybrid git+web (e.g., docs built from source) |
| **pdf** | `uploads/{source_id}/` | PDF books, split into chapters |
| **obsidian** | `.source/{source_id}/` | Obsidian vaults with wikilinks and tags |
| **self** | (current repo) | Embedded corpus — index the repo's own docs |

## Semantic Search (RAG)

Corpora can include **entry-level semantic embeddings** for retrieval that goes beyond keyword matching.

**How it works:**
- During `build`, entries are embedded using [fastembed](https://github.com/qdrant/fastembed) with `BAAI/bge-small-en-v1.5` (ONNX, no PyTorch, ~120MB)
- Embeddings are stored in [Lance format](https://lancedb.com/) — flat files, no server, committed to the repo
- At query time, `navigate` searches by cosine similarity with optional SQL predicates for hybrid search (vector + keyword)
- An FTS index on metadata enables full-text keyword matching alongside semantic search
- Optional reranking with CrossEncoder for better precision on ambiguous queries

**What gets embedded:**
```
"passage: {title} | {summary} | {tags} | {concepts}"
```

Concept labels in the embedding text mean searching for "lazy evaluation" finds entries assigned to that concept even if those words don't appear in the title or summary. The zettelkasten structure directly improves RAG recall.

**Remote corpora:** For GitHub-hosted corpora, navigate automatically sparse-clones the Lance directory to a local cache (`.hiivmind/corpus/cache/`) on first query, with TTL-based freshness tracking.

**Opt-in:** Embeddings are suggested during build when `entry_count > 150` or the corpus has tiered indexes. Below that threshold, the LLM scanning the full index directly is effective enough.

**Dependencies:** `pip install fastembed lancedb pyyaml` (~260MB). If not installed, navigate falls back to keyword/yq pre-filtering — embeddings are an enhancement, not a requirement.

## Concept Graphs

Each corpus can have a **concept graph** (`graph.yaml`) — a zettelkasten-style knowledge structure:

```yaml
schema_version: 2
concepts:
  lazy-evaluation:
    label: "Lazy Evaluation"
    description: "Deferred query execution for optimization"
    tags: [performance, lazy]
  query-optimization:
    label: "Query Optimization"
    description: "Techniques for faster query execution"
    tags: [performance, indexing]
relationships:
  - from: lazy-evaluation
    to: query-optimization
    type: depends-on
    origin: manual
```

Concept membership is bidirectional: entries in `index.yaml` declare their concepts via a `concepts[]` field, and graph.yaml defines concept definitions and relationships. The graph skill lets you add concepts, add relationships (with embedding-powered candidate detection), and validate the graph.

## Cross-Corpus Bridges

Projects with 2+ registered corpora can create **bridges** — links between concepts in different corpora:

```yaml
# .hiivmind/corpus/registry-graph.yaml
bridges:
  - concept_a: "polars:lazy-evaluation"
    concept_b: "ibis:deferred-execution"
    type: see-also
    note: "Both implement deferred query execution"
aliases:
  "lazy evaluation":
    - corpus: polars
      concept: lazy-evaluation
    - corpus: ibis
      concept: deferred-execution
```

Bridge candidate detection queries each corpus's embeddings to find semantically similar concepts across corpora — even when they use different terminology.

## Per-Project Registry

Projects register which corpora they use:

```yaml
# .hiivmind/corpus/registry.yaml
corpora:
  - id: polars
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-polars
      ref: main
  - id: flyio
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main
```

Navigate uses the registry to search across all registered corpora and route queries to the right one.

## Dependencies

| Tool | Required | Purpose |
|---|---|---|
| **git** | Yes | Clone source repos, track commits |
| **gh** (GitHub CLI) | Recommended | Fetch content from GitHub repos (preferred over raw URLs) |
| **yq** 4.0+ | Recommended | Parse YAML config files (grep fallback available) |
| **fastembed + lancedb** | Optional | Semantic search embeddings (~260MB pip install) |
| **pyyaml** | Optional | YAML parsing in embedding scripts |

## Design Principles

- **Human-curated indexes** — You decide what matters, not an algorithm
- **Collaborative building** — The build process is a conversation, not a batch job
- **Layered value-add** — Index first, then optionally concepts and embeddings
- **Graceful degradation** — Works without embeddings, without graphs, without yq
- **Portable** — Corpora are just files. Commit, diff, review, share with your team
- **Known freshness** — Commit SHA tracking tells you exactly how old your sources are
- **Works without local clone** — Falls back to `gh api` for remote content fetching

## Published Corpora

| Corpus | Source |
|---|---|
| [hiivmind-corpus-polars](https://github.com/hiivmind/hiivmind-corpus-data) | Polars documentation |
| [hiivmind-corpus-ibis](https://github.com/hiivmind/hiivmind-corpus-data) | Ibis documentation |
| [hiivmind-corpus-narwhals](https://github.com/hiivmind/hiivmind-corpus-data) | Narwhals documentation |
| [hiivmind-corpus-substrait](https://github.com/hiivmind/hiivmind-corpus-data) | Substrait specification |
| [hiivmind-corpus-flyio](https://github.com/hiivmind/hiivmind-corpus-flyio) | Fly.io platform docs |
| [hiivmind-corpus-obsidian](https://github.com/hiivmind/hiivmind-corpus-obsidian) | Obsidian help docs |
| [hiivmind-corpus-lancedb](https://github.com/hiivmind/hiivmind-corpus-lancedb) | LanceDB documentation |
| [hiivmind-corpus-claude-agent-sdk](https://github.com/hiivmind/hiivmind-corpus-claude) | Claude Agent SDK |

Register any of these with:
```
/hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

## License

MIT
