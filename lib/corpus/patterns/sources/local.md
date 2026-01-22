# Pattern: Local Sources

Manage user-uploaded local documentation files.

## Storage Location

`data/uploads/{source_id}/`

## Operations

### Setup Local Source Directory

**Using bash:**
```bash
setup_local_source() {
    local corpus_path="$1"
    local source_id="$2"
    local uploads_path="${corpus_path%/}/data/uploads/${source_id}"

    mkdir -p "$uploads_path"
    echo "$uploads_path"
}
```

---

### List Local Files

**Using bash:**
```bash
list_local_files() {
    local corpus_path="$1"
    local source_id="$2"
    local uploads_path="${corpus_path%/}/data/uploads/${source_id}"

    find "$uploads_path" -type f -name "*.md" -o -name "*.mdx" 2>/dev/null
}
```

---

### Count Local Files

**Using bash:**
```bash
count_local_files() {
    local corpus_path="$1"
    local source_id="$2"

    list_local_files "$corpus_path" "$source_id" | wc -l | tr -d ' '
}
```

---

## Usage Notes

- Local sources have no version control - changes are tracked by file modification time
- Files must be manually placed in the uploads directory
- Supported formats: `.md`, `.mdx`, `.pdf`
- Use `hiivmind-corpus-add-source` to set up a local source

## PDF Document Handling

For large PDF files with chapters, see `pdf.md` for splitting into smaller files before adding as a local source.

**When to split:**
- PDFs with 50+ pages
- Documents with TOC/bookmarks (books, manuals)
- Content that benefits from chapter-level indexing

**Workflow:**
1. Detect chapters: `python -m lib.corpus.tools.split_pdf detect book.pdf`
2. Split with confirmation: `python -m lib.corpus.tools.split_pdf split book.pdf -o data/uploads/{source_id}`
3. Add as local source using files from `manifest.json`

Split chapters are stored in `data/uploads/{source_id}/` just like other local files.

## Related Patterns

- `shared.md` - Existence checks
- `../scanning.md` - File discovery
