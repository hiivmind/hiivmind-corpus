# Embedding Patterns

Optional semantic search layer for corpus retrieval. Generates entry-level embeddings
(title + summary + keywords) using fastembed with all-MiniLM-L6-v2 (384 dimensions).

## Dependencies

- `fastembed` — ONNX-based embedding library (~120MB install)
- `pyyaml` — YAML parsing for index.yaml and concepts files
- Model: `all-MiniLM-L6-v2` (~80MB, auto-downloaded on first use)

Install: `pip install fastembed pyyaml`

## Dependency Detection

fastembed is the sole embedding dependency. Detection via `detect.py`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py
```

| Output | Exit | Meaning |
|--------|------|---------|
| `ready` | 0 | fastembed installed, model downloaded |
| `no-model` | 0 | fastembed installed, model needs ~80MB download on first use |
| `not-installed` | 1 | fastembed not available |

**Install prompt** (when heuristic recommends embeddings):
> "Enable semantic search? Requires: `pip install fastembed pyyaml` (~120MB)"

**Model download note** (when detect.py reports "no-model"):
> "Downloading embedding model (~80MB, one-time)..."

## Heuristic for Opt-in

Prompt user to enable embeddings when:
- `entry_count > 150`
- Corpus has tiered indexes (index-*.md sub-indexes exist)

The multi-corpus condition is evaluated by the bridge skill, not at build time.

When heuristic conditions are not met: skip silently — no prompt.

## Embedding Generation

### Per-corpus: embeddings.db

Generate entry embeddings from index.yaml:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml embeddings.db
```

Text per entry: `"{title} - {summary} {keywords.join(', ')}"`

Stored alongside index.yaml in the corpus root. **Committed to repo** — enables remote
consumers to benefit from pre-computed embeddings.

### Cross-corpus: registry-embeddings.db

Generate concept embeddings from all registered corpora's graph.yaml files:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py --mode concepts concepts.yaml .hiivmind/corpus/registry-embeddings.db
```

Text per concept: `"{label} - {description} {tags.join(', ')}"`
ID format: `{corpus_id}:{concept-id}`

Stored at `.hiivmind/corpus/registry-embeddings.db`. **Not committed** — project-local,
must be gitignored.

### Concepts YAML schema (for --mode concepts)

```yaml
concepts:
  - id: "polars:lazy-evaluation"
    label: "Lazy Evaluation"
    description: "Deferred query execution for optimization"
    tags: [performance, lazy, optimization]
```

### Incremental updates

embed.py tracks content via sha256 text hashes. On subsequent runs:
- Only re-embeds entries where text changed (hash mismatch)
- Removes entries no longer in input
- Updates metadata timestamps

Use `--force` to re-embed everything (e.g., after model change).

## Querying Embeddings

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/search.py embeddings.db "user query" --top-k 15 --json
```

Output: `[{"id": "polars:expressions.md", "score": 0.8432}, ...]`

Requires fastembed at query time (must embed the query string).

## Staleness Detection

Compare `meta.generated_at` in embeddings.db vs `meta.generated_at` in index.yaml:
- If index.yaml is newer: embeddings are stale
- Stale embeddings are still usable (stale > none) — note in output

At navigate time: use stale embeddings, include note "Embeddings may be outdated"

## Graph-Boost

When navigate Phase 4a returns embedding results and graph.yaml exists:

1. For each result entry, check if it belongs to a concept in graph.yaml
2. If that concept has relationships to other concepts:
   - Entries in related concepts get +0.05 score boost
   - Once per entry (regardless of number of connecting relationships)
   - Capped at 1.0
   - No duplicate entries — boost only applies to entries not already in results
3. Re-sort by boosted scores

## Graceful Degradation

| Condition | Behavior |
|---|---|
| No embeddings.db | Existing keyword/yq approach (no change) |
| No fastembed installed but embeddings.db exists | Skip embedding search, fall back to keywords |
| Stale embeddings | Use them, note in output |
| No registry-embeddings.db | Skip cross-corpus routing, use keyword scoring |
| Model mismatch (exit code 4) | Skip embedding search, fall back to keywords |

## Exit Codes (all scripts)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | fastembed not installed |
| 2 | File not found / invalid input |
| 3 | Other error |
| 4 | Model mismatch |
