# Pattern: PDF-to-Markdown Extraction

PDF documents are extracted to markdown with YAML frontmatter and wikilinks via a three-stage pipeline. The output files become a `local` source.

## When to Use

- User provides a `.pdf` file (book, manual, technical spec)
- PDF has structured content with chapters, sections, code examples
- Content will benefit from being Grep-searchable with metadata

## Pipeline Overview

```
Stage 1: LLM Inspection
    Source PDF → extraction-profile.yaml

Stage 2: LLM writes bespoke extraction script
    extraction-profile.yaml + pdf_utils.py → tools/extract_{source}.py
    tools/extract_{source}.py + Source PDF → *.md files with frontmatter

Stage 3: LLM Cleanup (optional)
    Spot-check generated markdown, fix edge cases
```

## Stage 1: LLM Inspection

Read sample pages from the source PDF to discover formatting patterns. Produce an extraction profile YAML file.

**What to discover:**

| Pattern | How to Find |
|---------|-------------|
| Font → heading mapping | Compare font sizes across chapter titles, section headers, body text |
| Code block detection | Identify monospace font name and size |
| Callout conventions | Look for Note/Tip/Caution formatting (bold keyword, boxed, indented) |
| Cross-reference patterns | Find "Chapter N", "page NNN", "see X on page Y" text |
| Table styles | Check if pymupdf native table extraction works |
| Running headers/footers | Identify repeated text at page margins |
| Chapter boundaries | Check for TOC bookmarks; if absent, identify chapter-start font patterns |
| Book structure | Identify parts, chapters, appendixes; note which sections to skip |
| Significant diagrams | Note page number and write description (image extraction deferred) |

**Output:** `tools/extraction-profile-{source_id}.yaml`

**See:** `pdf-extraction-profile.md` for the full profile schema.

## Stage 2: Bespoke Extraction Script

The LLM writes a Python script specific to this source document. The script imports
building blocks from `lib/corpus/tools/pdf_utils.py` and hardcodes document-specific
configuration from the extraction profile.

**Building blocks library:** `lib/corpus/tools/pdf_utils.py`

**Requirements:** `pip install pymupdf`

**Key building blocks:**

```python
from lib.corpus.tools.pdf_utils import (
    # Document analysis
    open_pdf, get_toc, get_page_count,
    # Text extraction
    extract_text_blocks, strip_headers_footers,
    # Chapter detection
    detect_chapters_from_toc, detect_chapters_from_fonts,
    # Markdown emission
    emit_heading, emit_code_block, emit_table, emit_callout, emit_frontmatter,
    # Cross-references
    find_cross_references, resolve_cross_ref, make_wikilink,
    # File output
    write_chapter_markdown, sanitize_filename,
)
```

**Script characteristics:**
- Lives in the corpus: `tools/extract_{source}.py`
- Hardcodes document-specific config (fonts, patterns, skip ranges)
- Runs once to produce markdown files
- Disposable — modify and re-run if extraction needs tweaking

**Output structure:**
```
uploads/{source_id}/
├── {source}.pdf          # Original full PDF (authoritative copy)
├── 01_Introduction.md
├── 02_Getting_Started.md
├── 03_Core_Concepts.md
└── ...
```

## Stage 3: LLM Cleanup (Optional)

Spot-check generated markdown for:
- Misidentified code blocks
- Broken table formatting
- Unresolved cross-references
- Diagram descriptions that need enrichment

## Output Format

Each markdown file has YAML frontmatter:

```yaml
---
source_document: "Full Book Title"
source_id: "source-id"
original_pdf: "source.pdf"
chapter_number: 3
chapter_title: "Chapter Title"
part: "Part Name"
page_range: "27-44"
headings:
  - "Section 1"
  - "Section 2"
tags:
  - tag1
  - tag2
links_to:
  - target: "other_chapter_filename"
    context: "Chapter N, Title"
---
```

**Wikilink conventions:**
- Same book: `[[16_Scopes_of_Macro_Variables|Scopes of Macro Variables]]`
- Cross book: `[[source-id:filename|Display Text]]`

## Hybrid Extraction with pymupdf4llm

For PDFs with complex table layouts (especially standalone chapter PDFs), a hybrid approach combines pymupdf4llm's layout analysis with font-based text classification.

### When to Use

- PDF has many tables with complex structures (multi-section, merged cells)
- PDF is a standalone chapter (not a monolithic book needing chapter splitting)
- Content mixes regular text, code blocks, and tabular output

### Approach

1. **pymupdf4llm for layout regions:** `pymupdf4llm.to_json(path, pages=...)` returns classified page boxes (`boxclass`: table, text, caption, section-header, page-header) with table cell extraction
2. **Font-based classification for text:** Use `extract_text_blocks()` from pdf_utils for text regions — font name and size identify headings, code blocks, body text, and output
3. **Table post-processing pipeline:** Process pymupdf4llm table data through the pdf_utils pipeline

### Table Processing Pipeline

```
table_data["extract"]
    -> split_subtables()              # Split on empty rows
    -> merge_continuation_rows()      # Merge wrapped text
    -> expand_newline_cells()         # Expand \n-packed cells
    -> merge_continuation_rows()      # Merge again after expansion
    -> strip_empty_columns()          # Remove empty columns
    -> quality check                  # Fall back to code block if sparse/wide
    -> emit_table() or emit_code_block()
```

Or use `emit_layout_table(table_data)` which orchestrates the full pipeline.

### TeX Math Font Decoding

PDFs generated by pdflatex with MathTime2 or Computer Modern math fonts extract garbled characters through pymupdf (e.g., alpha as ogonek, beta as caron, = as D). Use `tex_math_map.py`:

```python
from lib.corpus.tools.tex_math_map import decode_math_text, is_math_font

# In your line_text() function, decode math font spans:
if is_math_font(span.font):
    text = decode_math_text(text, span.font)
```

This provides character-level Unicode mapping. Does not reconstruct LaTeX structure (fractions, subscripts). For full LaTeX reconstruction, consider targeted OCR on math regions (future enhancement).

### Optional Dependency

```bash
uv pip install pymupdf4llm
```

Not required for basic pdf_utils usage. Only needed when extraction scripts use the hybrid approach.

```python
import pymupdf4llm
layout_data = json.loads(pymupdf4llm.to_json(str(pdf_path), pages=content_pages))
```

## Integration with Add-Source Workflow

When the add-source skill detects a PDF file:

1. **Check file size** — small PDFs (< 20 pages) can be added directly as a local source
2. **Run LLM inspection** — read sample pages, produce extraction profile
3. **Write bespoke script** — LLM composes extraction script using pdf_utils building blocks
4. **Execute extraction** — run the script to produce markdown files
5. **Configure as local source** — add source entry to config.yaml referencing `.md` files
6. **Build index** — frontmatter tags and headings feed into index generation

## Deferred Features

- **Image extraction:** Currently description-only. Future enhancement to extract images
  as files and generate alt-text descriptions. Track in the extraction profile under
  `images.handling: "description_only"`.

## Related Patterns

- `local.md` — Where output markdown files are stored
- `pdf-extraction-profile.md` — Extraction profile schema
- `../scanning.md` — File discovery after extraction
- `shared.md` — Path utilities
