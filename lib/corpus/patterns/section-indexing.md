# Pattern: Section-Level Indexing

## Purpose

Section-level indexing promotes heading-bounded sections within large structured
documents into first-class index entries with their own metadata and embeddings.
This enables retrieval at the section level instead of requiring the LLM to navigate
entire large files.

## When to Use

Recommended when a source has:
- Files exceeding 1000 lines (already flagged as `size: large`)
- Consistent heading structure (h2+ headings present and meaningful)
- Structured documentation (reference, guides, tutorials)

Not recommended for:
- Unstructured content (meeting transcripts, diary notes) — use deep chunking instead
- Files with inconsistent or missing headings

## Source Configuration

```yaml
sources:
  - id: polars-docs
    type: git
    repo: pola-rs/polars
    docs_root: docs/
    sections:
      enabled: true
      min_level: 2         # Only h2+ become entries (default: 2)
      min_content_lines: 5 # Skip trivially short sections (default: 5)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | false | Enable section-level indexing for this source |
| `min_level` | 2 | Minimum heading level to promote (1=h1, 2=h2, etc.) |
| `min_content_lines` | 5 | Minimum lines of content under a heading to create an entry |

## Source-Scanner Behavior

When `sections.enabled: true` is present in the source config passed to the
source-scanner, the scanner generates additional section entries for each
qualifying heading in each file.

### Section entry generation

For each file with headings:

1. Parse heading structure (already extracted for the `headings` field)
2. For each heading at `min_level` or deeper:
   a. Calculate content boundaries: from this heading to the next heading of equal or higher level (or end of file)
   b. Count content lines (excluding blank lines)
   c. If content lines < `min_content_lines`: skip
   d. Generate metadata: title (heading text), summary, tags, keywords
   e. Set `line_range` to `[heading_line, last_content_line]`
   f. Set `anchor` to slugified heading text
   g. Set `parent` to the file entry ID
   h. Set `tier: section`

### Heading consistency detection

The source-scanner should assess heading consistency during the initial file
sampling phase (step 4 in its process). Report in the scan output:

```yaml
heading_consistency: high|mixed|low
heading_consistency_note: "Consistent h2 sections across 90% of files"
```

This informs the build skill's indexing depth recommendation.

## Relationship to Deep Chunking

Section indexing and deep chunking are independent. A source can have both:
- Sections capture the semantic structure (meaningful headings with summaries)
- Chunks capture content for retrieval (FTS + vector search on actual text)

For sources with both enabled, section entries go into `index-embeddings.lance/`
(metadata embeddings) and chunks go into `chunks-embeddings.lance/` (content embeddings).

## Related Patterns

- [index-format-v2.md](index-format-v2.md) — Full schema including section fields
- [embeddings.md](embeddings.md) — Embedding pipeline (section entries use existing pipeline)
- [chunking.md](chunking.md) — Deep chunking (complementary feature)
