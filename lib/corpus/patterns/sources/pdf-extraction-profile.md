# Pattern: PDF Extraction Profile

An extraction profile is a YAML file produced during Stage 1 of the PDF extraction pipeline. It captures document-specific formatting patterns that the bespoke extraction script (Stage 2) uses to correctly identify headings, code blocks, callouts, cross-references, and structure. Each source PDF gets its own profile.

**Profile location:** `tools/extraction-profile-{source_id}.yaml`

**See also:** `pdf.md` — Full pipeline overview.

---

## Extraction Profile Schema

The complete schema with field-by-field documentation:

```yaml
source:
  filename: "{original}.pdf"      # Original PDF filename (basename only)
  title: "Full Book Title"        # Full title as printed on cover/TOC
  edition: N                      # Edition number (integer); omit if not applicable
  publisher: "Publisher Name"     # Publisher name (e.g. "SAS Institute", "O'Reilly")
  total_pages: N                  # Total page count from PDF metadata or last page

structure:
  parts:
    - name: "Part Name"           # Part/section grouping (e.g. "Part 1: Foundations")
      page_range: "start-end"     # Inclusive PDF page numbers (1-based)
      skip: false                 # true to exclude from extraction (front matter, index, etc.)
  chapter_detection:
    method: "toc_bookmarks"       # Primary detection method (see below)
    fallback: "font_analysis"     # Fallback if primary fails

# chapter_detection.method values:
#   toc_bookmarks  — Use PDF bookmark tree (most reliable when present)
#   font_analysis  — Identify chapter-start pages by heading font size spike
#   text_pattern   — Match regex against first line of each page

fonts:
  headings:
    h1: { font: "FontName-Bold", size_min: 24, color: "#hex" }
    # font:     Exact font name as returned by pymupdf span["font"]
    # size_min: Minimum point size to qualify as this heading level
    # color:    Optional hex color filter (useful when size alone is ambiguous)
    h2: { font: "FontName-Bold", size_min: 16 }
    h3: { font: "FontName-Bold", size_min: 12 }
  body: { font: "FontName", size: 10 }   # Dominant body text font and size
  code: { font: "MonoFontName", size: 9 } # Monospace font used for code examples

headers_footers:
  header_pattern: "regex"         # Regex matching running header text (e.g. "^Chapter \\d+")
  footer_pattern: "regex"         # Regex matching running footer text (e.g. "^\\d+$" for page nums)
  header_zones: { top: 50 }       # Strip blocks whose top edge is within N points of page top
  footer_zones: { bottom: 40 }    # Strip blocks whose bottom edge is within N points of page bottom

callouts:
  note: { trigger: "^Note:", style: "indented_bold_keyword" }
  # trigger: Regex matched against the first text span of the block
  # style values:
  #   indented_bold_keyword  — Bold keyword at start, rest of block indented
  #   boxed_bold_keyword     — Block appears in a visible box/border
  #   shaded_background      — Block has a filled background color
  tip: { trigger: "^TIP", style: "boxed_bold_keyword" }
  caution: { trigger: "^CAUTION:", style: "indented_bold_keyword" }
  warning: { trigger: "^WARNING:", style: "indented_bold_keyword" }

cross_references:
  patterns:
    - regex: 'Chapter (\d+), [""](.+?)[""],? on page (\d+)'
      type: "chapter_reference"
    - regex: '[""](.+?)[""] on page (\d+)'
      type: "section_reference"
  # Each pattern captures groups used to build wikilinks.
  # type identifies how the match is resolved to a target filename.
  wikilink_format: "[[{filename}|{display_text}]]"
  # Same-book wikilink. {filename} = sanitized chapter filename (no extension).
  cross_book_format: "[[{source_id}:{filename}|{display_text}]]"
  # Cross-book wikilink. {source_id} = the other book's source identifier.

tables:
  detection: "pymupdf_native"     # Primary table extraction method
  fallback: "column_alignment"    # Fallback if native extraction fails
  # detection values:
  #   pymupdf_native    — Use pymupdf's built-in table detection (best for ruled tables)
  #   column_alignment  — Infer columns from horizontal whitespace (for borderless tables)

code_blocks:
  sas_code: { font: "MonoFontName", indented: true }
  # indented: true means code blocks appear indented from body margin
  log_output: { font: "MonoFontName", background: "shaded" }
  # background: "shaded" means the block has a filled/gray background

images:
  handling: "description_only"    # "description_only" or (future) "extract_and_describe"
  notable:
    - page: N                     # PDF page number (1-based) containing the image
      description: "Description of diagram"
      # Write a concise description during inspection; used as alt-text placeholder

frontmatter_template:
  fields:
    - source_document     # Full book title (string)
    - source_id           # Identifier slug (string, e.g. "sas-ods-guide")
    - original_pdf        # PDF filename (string)
    - chapter_number      # Integer
    - chapter_title       # String
    - part                # Part name (string or null)
    - page_range          # "start-end" string
    - headings            # List of section heading strings found in chapter
    - tags                # List of keyword tags
    - links_to            # List of {target, context} objects for cross-references
```

---

## How to Run Inspection

Inspection is a manual LLM task. Follow these steps using the `pdf_utils.py` helpers or direct pymupdf calls to examine the PDF and fill in the profile.

### Step 1: Open the PDF and read basic metadata

```python
import fitz  # pymupdf

doc = fitz.open("path/to/book.pdf")
print(f"Pages: {len(doc)}")
print(f"Metadata: {doc.metadata}")
toc = doc.get_toc()
print(f"TOC entries: {len(toc)}")
for level, title, page in toc[:20]:
    print(f"  {'  ' * (level-1)}{title} → p{page}")
```

Fill in `source.total_pages`, `source.title`, and determine whether `chapter_detection.method` is `toc_bookmarks` (TOC has entries) or needs fallback.

### Step 2: Map the book structure

From the TOC or by scanning the first ~20 pages, identify:

- Parts (if any) — name and page range
- Front matter to skip (copyright, preface, TOC pages)
- Back matter to skip (index, bibliography, glossary if not wanted)

Fill in `structure.parts[]` with `skip: true` for excluded sections.

### Step 3: Discover fonts

Sample a body-text page, a chapter-title page, and a code-example page:

```python
def show_fonts(doc, page_num):
    page = doc[page_num - 1]
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                print(f"  size={span['size']:.1f} font={span['font']!r} text={span['text'][:60]!r}")

show_fonts(doc, 5)   # Likely a chapter title page
show_fonts(doc, 10)  # Likely body text
show_fonts(doc, 30)  # Likely includes code
```

Identify the font names and sizes for h1/h2/h3, body, and code. Note any color differences for heading levels. Fill in `fonts.*`.

### Step 4: Identify headers and footers

Check the top and bottom of several pages:

```python
page = doc[10]
blocks = page.get_text("dict")["blocks"]
page_height = page.rect.height
for b in blocks:
    bbox = b["bbox"]
    if bbox[1] < 60:   # near top
        print(f"  HEADER candidate: {b}")
    if bbox[3] > page_height - 60:  # near bottom
        print(f"  FOOTER candidate: {b}")
```

Note repeated text patterns (chapter name, book title, page numbers). Write regex patterns and fill in `headers_footers.*`.

### Step 5: Identify callout conventions

Search for "Note:", "Tip", "Caution:", "Warning:" occurrences on several pages. Observe:

- Is the keyword bold? Is it on its own line?
- Is there a visible box border or shaded background?
- Is the block indented compared to body text?

Fill in `callouts.*` with the trigger pattern and style for each type found.

### Step 6: Identify cross-reference patterns

Search for page-reference text in several chapters:

```python
for page_num in range(1, min(50, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    if "page " in text.lower():
        import re
        matches = re.findall(r'.{0,40}page \d+.{0,40}', text, re.IGNORECASE)
        for m in matches:
            print(f"  p{page_num+1}: {m.strip()}")
```

Identify recurring reference phrase patterns. Write capturing regexes. Fill in `cross_references.patterns[]`.

### Step 7: Check table rendering

Find a page with a table and test pymupdf native extraction:

```python
page = doc[page_num - 1]
tabs = page.find_tables()
print(f"Tables found: {len(tabs.tables)}")
if tabs.tables:
    print(tabs.tables[0].extract())
```

If the output looks correct, use `pymupdf_native`. If the table has no borders and native extraction fails, use `column_alignment`. Fill in `tables.*`.

### Step 8: Note significant diagrams

Scan pages for large image blocks. Note any diagrams that are important enough to describe for alt-text. Fill in `images.notable[]`.

### Step 9: Write and save the profile

Compile all findings into the YAML file and save as:

```
tools/extraction-profile-{source_id}.yaml
```

---

## Sample Pages to Inspect

These page categories are the minimum set to examine during inspection:

| Page Category | What to Check |
|---------------|---------------|
| **Title page / copyright** (pp. 1–4) | Book title, edition, publisher; confirm these as `skip: true` |
| **Table of contents** (pp. 5–15 approx.) | TOC structure, part groupings, chapter count |
| **First chapter opening page** | H1 font, chapter number format, chapter title font |
| **Second page of first chapter** | H2/H3 fonts, body font, running header/footer |
| **A code-heavy page** | Code font name and size; indentation depth; log output appearance |
| **A page with a Note or Tip** | Callout keyword, bold/box/indented style |
| **A page with a cross-reference** | Exact phrase pattern ("Chapter N, ..., on page N") |
| **A page with a table** | Table borders; test pymupdf native detection |
| **A diagram page** | Image presence; write description for `images.notable` |
| **Last few pages** | Index, glossary — confirm as `skip: true`; verify total page count |

---

## Common Publisher Patterns

Brief notes to guide initial guesses before detailed inspection:

### SAS Institute (SAS Press)

- **Body font:** Univers or Univers LT Std, ~10pt
- **Heading fonts:** Univers Bold or Univers LT Std Bold; H1 typically 18–24pt, H2 14–16pt, H3 12pt
- **Code font:** Courier New or SASMonospace, 9–10pt
- **Callouts:** "Note:" and "Caution:" appear with bold keyword, indented block style
- **Cross-references:** Often `"Chapter N, "Title," on page NNN"`; also `"the section "Title" on page NNN"`
- **Tables:** Mostly ruled (bordered); pymupdf native extraction usually works
- **Headers:** Chapter title on left, book title or part name on right; page number in footer center

### O'Reilly Media

- **Body font:** Georgia or similar serif, ~10pt
- **Heading fonts:** Helvetica Neue or similar sans-serif
- **Code font:** Constant Width (custom), ~9pt; code blocks have gray shaded background
- **Callouts:** Notes/tips/warnings appear in boxed callouts with icon-like formatting
- **Cross-references:** Often informal ("see Chapter N" without page number)
- **Tables:** Mix of ruled and borderless; test both detection methods

### Packt Publishing

- **Body font:** Source Serif Pro or similar, ~10pt
- **Heading fonts:** Bold sans-serif; H1 often has a colored top border rule
- **Code font:** Source Code Pro or Courier, ~9pt; inline code uses different shading than blocks
- **Callouts:** Info/Note/Important appear in distinctly shaded boxes
- **Chapter headings:** Often include chapter number as large decorative element

### Manning Publications

- **Body font:** Palatino or similar serif
- **Code font:** Monospace, smaller than body; listings are numbered
- **Callouts:** Annotations/sidebars in italics or boxed
- **Cross-references:** "section N.N" format common

> **Note:** Always verify against the actual PDF. Publisher styles evolve across editions and book series. The above are starting points, not definitive rules.

---

## Related Patterns

- `pdf.md` — Full three-stage extraction pipeline overview
- `local.md` — Where extracted markdown files are stored as a corpus source
- `shared.md` — Path utilities used in extraction scripts
