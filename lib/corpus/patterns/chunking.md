# Pattern: Deep Chunking

## Purpose

Deep chunking splits documents into ~900-token content chunks and embeds the actual
text (not metadata summaries) into a separate `chunks-embeddings.lance/` file. This
enables LanceDB native hybrid search (FTS + vector + RRF) for precise retrieval in
unstructured content where file-level or section-level indexing is too coarse.

## When to Use

Recommended for:
- Meeting transcripts (no heading structure, buried insights)
- Diary notes, journal entries
- Blog posts, articles
- Obsidian vaults with long unstructured notes
- Any content where relevant information could be anywhere in a file

Not the right tool for:
- Well-structured reference documentation (use section indexing instead)
- Small files that fit in a single context window

## Source Configuration

```yaml
sources:
  - id: meeting-notes
    type: local
    path: ~/notes/meetings/
    chunking:
      enabled: true
      strategy: transcript
      target_tokens: 900      # optional, strategy default used if omitted
      overlap_tokens: 100     # optional, strategy default used if omitted
```

### Strategies

| Strategy | Best For | Boundary Scoring | Default Target | Default Overlap |
|----------|---------|-----------------|----------------|-----------------|
| `markdown` | Markdown docs with headings | Headings (100), blank lines (20), list items (10) | 900 | 100 |
| `transcript` | Meeting notes, conversations | Speaker turns (80), timestamps (50), blank lines (20) | 900 | 100 |
| `code` | Source code files | Function/class boundaries (100), blank lines (20) | 600 | 50 |
| `paragraph` | Plain text, prose | Double newlines (50), single newlines (10) | 900 | 100 |

## Chunk Generation

### CLI

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/chunk.py <file> \
  --strategy <strategy> \
  --target-tokens <n> \
  --overlap-tokens <n> \
  --json
```

Output: JSON array of chunks with `text`, `line_range`, `chunk_index`, `overlap_prev`.

### Build Integration

During build Phase 5d, for each source with `chunking.enabled: true`:

1. Source-scanner runs chunk.py on each file
2. Annotates each chunk with `id`, `parent`, `source`, `path` fields
3. Aggregates all chunks into a single JSON file
4. embed.py `--mode chunks` embeds into `chunks-embeddings.lance/`

### Chunk ID Format

`{source_id}:{path}#chunk-{n}` — e.g., `notes:2026-03-15-standup.md#chunk-3`

## Embedding

Chunks embed the actual `chunk_text` content — NOT metadata summaries. This is the
key difference from file/section-level embeddings.

No `passage:` prefix is used for chunk embeddings (raw content embedding).

### Lance Schema

Table name: `chunks` (in `chunks-embeddings.lance/`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | `{source_id}:{path}#chunk-{n}` |
| `parent` | string | `{source_id}:{path}` — parent file ID |
| `source` | string | Source ID |
| `path` | string | Relative file path |
| `chunk_index` | int | Sequential within parent |
| `chunk_text` | string | Actual content (embedded AND FTS-indexed) |
| `vector` | vector[384] | Content embedding |
| `line_range` | int[2] | [start, end] lines in source file |
| `overlap_prev` | bool | Whether this chunk overlaps with previous |
| `updated_at` | string | ISO-8601 timestamp |

### Indexes

- FTS index on `chunk_text` — enables LanceDB hybrid search
- Vector index (IVF_PQ) if chunk count > 500

## Hybrid Search

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/search.py chunks-embeddings.lance/ "query" \
  --table chunks --hybrid --text-column chunk_text --top-k 15 --json
```

This uses LanceDB native hybrid search: FTS on `chunk_text` + vector similarity + RRF fusion.

## Query Expansion

When `chunks-embeddings.lance/` exists, the navigate skill generates 2 variant queries:
- Lexical variant (keyword reformulation)
- Conceptual variant (synonym/concept expansion)

Original query is weighted 2x. Only applied to chunk search, not metadata search.

## Distribution

`chunks-embeddings.lance/` is committed to the corpus repo alongside `index-embeddings.lance/`.
Larger (10-100MB) since it stores actual text. Only present when at least one source has chunking enabled.

## Related Patterns

- [section-indexing.md](section-indexing.md) — Section-level indexing (complementary)
- [embeddings.md](embeddings.md) — Embedding pipeline and LanceDB patterns
- [index-format-v2.md](index-format-v2.md) — Index schema
