# Pattern: PDF Pre-Processing

PDF documents require splitting before corpus import. This is a pre-processing step - the resulting chapters become a `local` source.

## When to Use

- User provides a `.pdf` file
- PDF has multiple chapters (detected via TOC or text patterns)
- Large PDFs (> ~50 pages) benefit from chapter-based indexing
- PDF contains structured content (books, manuals, technical specs)

## Tool Location

`lib/corpus/tools/split_pdf.py`

**Requirements:** `pip install pymupdf`

## Storage Location

Split chapters: `data/uploads/{source_id}/`
Output format: Individual chapter PDFs + `manifest.json`

## Operations

### Check PDF Page Count

**Using Python:**
```python
import pymupdf
doc = pymupdf.open(input_path)
page_count = len(doc)
doc.close()
```

**Using bash with pdfinfo (if available):**
```bash
pdfinfo "$input_path" | grep "Pages:" | awk '{print $2}'
```

---

### Detect Chapters

Detect chapter boundaries from TOC bookmarks or text patterns.

**Using the split tool:**
```bash
python -m lib.corpus.tools.split_pdf detect book.pdf
python -m lib.corpus.tools.split_pdf detect book.pdf -l 2  # Level 2 (sections)
```

**Output example:**
```
Detected 12 chapters in book.pdf:

    #  Title                                          Pages         Size
  ---  --------------------------------------------- ---------- ------------
    1  Introduction                                      1-15       15 pages
    2  Getting Started                                  16-42       27 pages
    3  Core Concepts                                    43-89       47 pages
  ...
```

**Detection methods:**
1. **TOC/Bookmarks** (preferred): Most PDFs with chapters have embedded bookmarks
2. **Text patterns** (fallback): Searches for "Chapter X" patterns on page starts

---

### Split into Chapters

Execute the split, creating individual chapter PDFs and a manifest.

**Using the split tool:**
```bash
# With confirmation prompt
python -m lib.corpus.tools.split_pdf split book.pdf

# To specific directory
python -m lib.corpus.tools.split_pdf split book.pdf -o data/uploads/programming-book

# Skip confirmation
python -m lib.corpus.tools.split_pdf split book.pdf --yes -o data/uploads/programming-book
```

**Output structure:**
```
data/uploads/programming-book/
├── 01_Introduction.pdf
├── 02_Getting_Started.pdf
├── 03_Core_Concepts.pdf
├── ...
└── manifest.json
```

---

### Manifest Format

The split tool generates a `manifest.json` describing all chapters:

```json
{
  "source": "book.pdf",
  "chapters": [
    {
      "index": 1,
      "title": "Introduction",
      "file": "01_Introduction.pdf",
      "pages": "1-15"
    },
    {
      "index": 2,
      "title": "Getting Started",
      "file": "02_Getting_Started.pdf",
      "pages": "16-42"
    }
  ]
}
```

This manifest can be used to:
- Generate index entries automatically
- Track original page numbers
- Verify split completeness

---

### Import via Local Source

After splitting, add as a `local` source with the manifest-provided file list.

**Config entry:**
```yaml
- id: "{source_id}"
  type: "local"
  path: "uploads/{source_id}/"
  description: "Split from {original_filename} ({N} chapters)"
  files:
    - "01_Introduction.pdf"
    - "02_Getting_Started.pdf"
    # ... from manifest
  last_indexed_at: null
```

**Index entries:**
```markdown
## {Book Title} (from {source_id})

- **Introduction** `{source_id}:01_Introduction.pdf` - Overview and motivation (pages 1-15)
- **Getting Started** `{source_id}:02_Getting_Started.pdf` - Initial setup (pages 16-42)
```

---

## Integration with Add-Source Workflow

When the add-source skill detects a PDF file:

1. **Check file size/page count**
   - Small PDFs (< 50 pages): Offer to add directly as local source
   - Large PDFs: Suggest chapter splitting

2. **Detect chapters**
   - Run `detect` command to show proposed splits
   - Show chapter count and page ranges to user

3. **User decision**
   - Accept proposed splits → proceed to split
   - Decline → add as single local file
   - Adjust level (use `-l 2` for sections instead of chapters)

4. **Execute split**
   - Run `split` command with user-confirmed settings
   - Chapters saved to `data/uploads/{source_id}/`

5. **Configure as local source**
   - Read manifest.json for file list
   - Add source entry to config.yaml
   - Files listed come from manifest

6. **Offer indexing**
   - Use manifest to suggest index entries
   - Include original page ranges in descriptions

---

## Usage Notes

- **PDF is NOT a source type** - it's a pre-processing step before `local` source
- Split PDFs are treated the same as any other local uploads
- The manifest.json is for human reference and index generation, not runtime config
- Chapter splitting only makes sense for structured documents (books, manuals)
- For PDFs without TOC, the tool attempts text-based chapter detection
- If no chapters detected, user should add the PDF as a single local file

## Handling PDFs Without Chapters

If `detect` finds no chapters:

```
No chapters detected in document.pdf

Possible reasons:
  - The PDF has no bookmarks/TOC
  - No entries at the requested level (-l option)
  - Chapter text patterns not recognized

Consider specifying manual page ranges or adding bookmarks first.
```

**Options:**
1. Add as single local file (no splitting)
2. User manually defines page ranges (future enhancement)
3. User adds bookmarks to PDF externally and re-runs

## Related Patterns

- `local.md` - Where split chapters are stored
- `../scanning.md` - File discovery after splitting
- `shared.md` - Path utilities
