# Embedding Patterns

Optional semantic search layer for corpus retrieval. Generates entry-level embeddings
(title + summary + tags) using fastembed with BAAI/bge-small-en-v1.5 (384 dimensions)
and stores them in Lance format for hybrid vector + SQL search.

## Dependencies

- `fastembed` — ONNX-based embedding library (no PyTorch)
- `lancedb` — Lance vector database (flat files, no server)
- `pyyaml` — YAML parsing for index.yaml and concepts files
- `pyarrow` — Columnar data (transitive dependency of lancedb)
- Model: `BAAI/bge-small-en-v1.5` (~45MB, auto-downloaded on first use)

Install: `pip install fastembed lancedb pyyaml` (~260MB total)

## Dependency Detection

Detection via `detect.py`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py
```

| Output | Exit | Meaning |
|--------|------|---------|
| `ready` | 0 | fastembed + lancedb installed, model downloaded |
| `no-model` | 0 | Installed, model needs ~45MB download on first use |
| `not-installed` | 1 | fastembed or lancedb not available |

**Install prompt** (when heuristic recommends embeddings):
> "Enable semantic search? Requires: `pip install fastembed lancedb pyyaml` (~260MB)"

**Model download note** (when detect.py reports "no-model"):
> "Downloading embedding model (~45MB, one-time)..."

## Heuristic for Opt-in

Prompt user to enable embeddings when:
- `entry_count > 150`
- Corpus has tiered indexes (index-*.md sub-indexes exist)

The multi-corpus condition is evaluated by the bridge skill, not at build time.

When heuristic conditions are not met: skip silently — no prompt.

## Data Model

Each Lance dataset uses a fixed table name `embeddings` with this schema:

| Column | Type | Description |
|---|---|---|
| `id` | string | Entry ID (e.g., `polars:user-guide/expressions.md`) |
| `source` | string | Source ID from index.yaml entry's `source` field |
| `title` | string | Entry title |
| `tags` | list[string] | Entry tags |
| `concepts` | list[string] | Concept IDs from index.yaml entry's `concepts` field |
| `metadata_text` | string | Concatenated text that was embedded |
| `vector` | vector[384] | Dense embedding (bge-small-en-v1.5) |
| `updated_at` | string | ISO-8601 timestamp when embedding was generated |

Model metadata is stored in a `_meta` Lance table within the same database (key-value pairs):

```
model       = BAAI/bge-small-en-v1.5
dimensions  = 384
generated_at = 2026-03-27T10:00:00Z
entry_count = 312
```

## Embedding Strategy

Uses asymmetric retrieval with `passage:`/`query:` prefixes. bge-small is trained
to distinguish between document text and query text:

**Indexing (passage):**
- `"passage: {title} | {summary} | {', '.join(tags)} | {', '.join(concepts)}"`
- Concept IDs in the embedding text mean searching for "lazy evaluation" finds entries
  assigned to that concept even if those words don't appear in the title or summary.

**Querying (query):**
- `"query: {user_query}"`

## Embedding Generation

### Per-corpus: index-embeddings.lance/

Generate entry embeddings from index.yaml:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/
```

Stored alongside index.yaml in the corpus root. **MUST be committed to the repo** — this is a
distributable artifact, not a cache. Consumers get pre-computed embeddings without needing
fastembed installed. Do NOT add to .gitignore. Treat it the same as index.yaml and index.md.

### Cross-corpus routing

Cross-corpus routing does not require a separate embedding dataset. Navigate Phase 2
searches each registered corpus's `index-embeddings.lance/` directly and compares top
scores to select the best corpus. See navigate skill Phase 2 for details.

For bridge candidate detection, the bridge skill queries each corpus's embeddings directly
and reads the `concepts` column from results to identify cross-corpus concept relationships.

### Incremental updates

embed.py uses Lance merge-insert (upsert by `id`). On subsequent runs:
- Updates entries where content changed
- Adds new entries
- Use `--force` to rebuild entirely (e.g., after model change)

### Indexes

embed.py automatically creates:
- **FTS index** on `metadata_text` — enables hybrid search (vector + keyword) via `--where` or native FTS queries
- **Vector index** (IVF_PQ) for corpora with >500 entries — faster ANN search vs brute-force scan

Both indexes are created inside the Lance dataset directory. No extra files.

## Querying Embeddings

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/search.py index-embeddings.lance/ "user query" --top-k 15 --json
```

Output: `[{"id": "polars:expressions.md", "score": 0.8432}, ...]`

### Reranking

For better precision on ambiguous queries, use `--rerank`:

```bash
python3 search.py index-embeddings.lance/ "query" --top-k 15 --rerank --json
```

Uses CrossEncoderReranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`, ~100MB, downloads on first use).
Slower but more precise — re-scores results using cross-attention between query and document.

**When to use `--rerank`:**
- Query is ambiguous or broad (e.g., "how do I use this?")
- Top 3 result scores are within 0.05 of each other (low differentiation)
- User explicitly asks for more relevant results

**When NOT to use `--rerank`:**
- Query has specific keywords (e.g., "LazyFrame predicate pushdown")
- Top result score > 0.8 (high confidence)
- Cross-corpus routing (Phase 2) — speed matters more than precision

### Column selection

Return extra columns in JSON output with `--select` (requires `--json`):

```bash
python3 search.py index-embeddings.lance/ "query" --select "concepts,title" --json
```

Output: `[{"id": "...", "score": 0.84, "concepts": ["lazy-evaluation"], "title": "Lazy Frames"}]`

`--select` is silently ignored in plain text output mode.

### Hybrid Search

Lance composes vector search with SQL predicates in a single query. Use `--where`:

```bash
# Semantic + tag filter
python3 search.py index-embeddings.lance/ "optimize queries" --top-k 10 \
  --where "array_has_any(tags, ['performance'])" --json

# Semantic + title filter
python3 search.py index-embeddings.lance/ "lazy evaluation" --top-k 10 \
  --where "title LIKE '%lazy%'" --json

# Pure semantic (no --where)
python3 search.py index-embeddings.lance/ "how to speed up queries" --top-k 15 --json
```

This replaces the need for a separate BM25 keyword index. Exact-match needs (API names,
config keys, version strings) are handled by SQL predicates on text columns.

## Staleness Detection

Compare `generated_at` in `_meta.json` vs `meta.generated_at` in index.yaml:
- If index.yaml is newer: embeddings are stale
- Stale embeddings are still usable (stale > none) — note in output

At navigate time: use stale embeddings, include note "Embeddings may be outdated"

## Graph-Boost

When navigate Phase 4a returns embedding results and graph.yaml exists:

1. For each result entry, read `concepts[]` from the Lance result row (concepts column)
2. If that concept has relationships to other concepts:
   - Entries in related concepts get +0.05 score boost
   - Once per entry (regardless of number of connecting relationships)
   - Capped at 1.0
   - No duplicate entries — boost only applies to entries not already in results
3. Re-sort by boosted scores

## Graceful Degradation

| Condition | Behavior |
|---|---|
| No index-embeddings.lance/ | Existing keyword/yq approach (no change) |
| No fastembed/lancedb installed | Skip embedding search and cross-corpus routing, fall back to keywords |
| Stale embeddings | Use them, note in output |
| Model mismatch (exit code 4) | Skip embedding search, fall back to keywords |

## Exit Codes (all scripts)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Dependencies not installed |
| 2 | File/dataset not found or invalid input |
| 3 | Other error |
| 4 | Model mismatch |
