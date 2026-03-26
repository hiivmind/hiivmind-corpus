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

For PDF files, use the three-stage extraction pipeline to produce markdown with
YAML frontmatter and wikilinks. See `pdf.md` for the full pipeline.

**Workflow:**
1. LLM inspects source PDF → extraction profile
2. LLM writes bespoke extraction script using `pdf_utils.py` building blocks
3. Run script → markdown files in `uploads/{source_id}/`
4. Add as local source referencing `.md` files

Output markdown files have YAML frontmatter with provenance metadata,
headings, tags, and cross-reference wikilinks.

---

### Extraction Support

Local sources can opt into the extraction pipeline for markdown files.

**Default extraction config:**

```yaml
extraction:
  wikilinks: false      # Standard markdown links extracted; Obsidian-style [[wikilinks]] not expected
  frontmatter: true     # YAML frontmatter commonly present in local documentation
  tags: true            # Hashtags extracted as concept candidates
  dataview: false       # Not applicable
```

To enable: add `extraction:` block to the source entry in config.yaml. Extraction runs during `build` and `refresh` via the source-scanner agent.

**See:** [../extraction.md](../extraction.md) for full pipeline documentation

## Related Patterns

- `shared.md` - Existence checks
- `../scanning.md` - File discovery
- [../extraction.md](../extraction.md) — Cross-cutting extraction pipeline
