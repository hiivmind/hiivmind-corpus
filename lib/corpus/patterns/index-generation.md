# Index Generation Patterns

Generate documentation corpus indexes based on scan results and user preferences.

## Context Variables

All sections receive these context variables:

```yaml
config:           # Corpus configuration from config.yaml
sources:          # Array of source configurations
scan_results:     # Object of scan results keyed by source_id
user_preferences: # User's stated preferences
  use_case:       # daily_reference | learning | debugging | onboarding
  priority_sources: # Ordered list of source IDs
  skip_sections:  # Sections to exclude
  organization:   # by-topic | by-source | mixed | by-workflow
segmentation:     # Segmentation configuration
  strategy:       # single | tiered | by-section | by-source
  sections:       # List of section names for tiered strategy
total_files:      # Total file count across all sources
```

---

## single

Generate a single comprehensive index file.

### Process

1. **Build header**
   ```markdown
   # {config.corpus.name} Documentation Index

   > Sources: {sources.map(s => s.id).join(', ')}
   > Last updated: {current_date}

   ---
   ```

2. **Organize by user preference**

   **If organization == "by-topic":**
   - Group entries by topic across all sources
   - Identify common themes from scan_results sections
   - Create topic headers based on most common section names

   **If organization == "by-source":**
   - Create one section per source
   - List entries under source headers

   **If organization == "mixed":**
   - Lead with cross-source topics (most important)
   - Follow with source-specific sections

   **If organization == "by-workflow":**
   - Getting Started (tutorials, quickstart guides)
   - Common Tasks (how-to guides, recipes)
   - Concepts (explanations, architecture)
   - Reference (API docs, configuration)
   - Troubleshooting (FAQ, common errors)

3. **Generate entries**

   For each file in scan_results:
   - Extract title from frontmatter or first heading
   - Generate path in format `{source_id}:{relative_path}`
   - Create brief description (first paragraph or frontmatter description)
   - Mark large files with `⚡ GREP` and suggested pattern

   **Entry format:**
   ```markdown
   - **{Title}** `{source_id}:{path}` - {description}
   ```

   **Large file entry format:**
   ```markdown
   - **{Title}** `{source_id}:{path}` ⚡ GREP - {description}. Search with: `{grep_pattern}`
   ```

4. **Apply filters**
   - Skip files in `user_preferences.skip_sections`
   - Prioritize sources in `user_preferences.priority_sources` order

5. **Store result**
   ```
   state.index.content = generated_markdown
   ```

### Example Output

```markdown
# Polars Documentation Index

> Sources: polars
> Last updated: 2025-01-15

---

## Getting Started

- **Installation** `polars:getting-started/install.md` - Install Polars via pip or conda
- **10 Minute Tour** `polars:getting-started/tour.md` - Quick introduction to core concepts

## Expressions

- **Expression Basics** `polars:expressions/basics.md` - Building blocks of Polars operations
- **Column Selection** `polars:expressions/column-selection.md` - Selecting and manipulating columns

## Reference

- **API Reference** `polars:reference/api.md` ⚡ GREP - Complete API (5000+ lines). Search with: `grep -n "^## " FILE`
```

---

## tiered

Generate a main index with links to detailed sub-indexes.

### Process

1. **Build main index header**
   ```markdown
   # {config.corpus.name} Documentation Corpus

   > {total_files}+ documentation files organized by topic
   > Last updated: {current_date}

   ## How to Use This Index

   This corpus uses a **tiered index** due to its size. Start here for an overview, then drill into sub-indexes for detailed entries.

   ---
   ```

2. **Create Quick Reference section**
   - Select 10-20 most commonly needed entries
   - Include full paths for direct access

   ```markdown
   ## Quick Reference

   Common lookups (full path for direct access):

   - **{Title}** `{source_id}:{path}`
   ...
   ```

3. **Create section summaries**

   For each section in `segmentation.sections`:
   ```markdown
   ## {Section Name}
   *{brief description of section content}*

   → See [index-{section-slug}.md](index-{section-slug}.md) for {count} detailed entries

   Key topics: {top 5-7 topics from this section}
   ```

4. **Generate sub-index files**

   For each section, create `index-{section-slug}.md`:
   ```markdown
   # {Section Name} - Detailed Index

   > Part of the {config.corpus.name} Documentation Corpus
   > Back to [main index](index.md)

   ---

   {organized entries for this section}
   ```

5. **Store results**
   ```
   state.index.content = main_index_markdown
   state.index.sub_indexes = [
     { filename: "index-{section}.md", content: sub_index_markdown },
     ...
   ]
   ```

### Example Main Index

```markdown
# GitHub Documentation Corpus

> 3,200+ documentation files organized by topic
> Last updated: 2025-01-15

## How to Use This Index

This corpus uses a **tiered index** due to its size. Start here for an overview, then drill into sub-indexes for detailed entries.

---

## Quick Reference

Common lookups (full path for direct access):

- **Creating a repository** `github:get-started/quickstart/create-a-repo.md`
- **Workflow syntax** `github:actions/using-workflows/workflow-syntax-for-github-actions.md`
- **REST API auth** `github:rest/overview/authenticating-to-the-rest-api.md`

---

## Getting Started
*First steps with GitHub - creating accounts, repos, basic workflows*

→ See [index-getting-started.md](index-getting-started.md) for 45 detailed entries

Key topics: Account setup, repository creation, basic Git operations, GitHub Desktop

## Actions & CI/CD
*GitHub Actions workflows, runners, marketplace actions*

→ See [index-actions.md](index-actions.md) for 280 detailed entries

Key topics: Workflow syntax, triggers, runners, secrets, reusable workflows, marketplace
```

---

## by-section

Generate a single curated index with only the most important entries.

### Process

1. **Calculate target size**
   - Target: 20-30% of total files
   - For 500 files: ~100-150 entries
   - For 1000 files: ~200-300 entries

2. **Rank entries by importance**

   Priority order:
   1. Files in priority_sources (if specified)
   2. Files with "getting-started", "quickstart", "tutorial" in path
   3. Files matching use_case keywords
   4. Files with high section coverage (represent more topics)
   5. Files frequently linked from other docs

3. **Build header**
   ```markdown
   # {config.corpus.name} Documentation Index (Curated)

   > Selected {entry_count} key documents from {total_files} total
   > Last updated: {current_date}

   ---
   ```

4. **Generate entries**
   - Include only top-ranked entries
   - Organize by user_preferences.organization

5. **Add "See Also" section**
   ```markdown
   ---

   ## Additional Resources

   This curated index covers the most important documentation. For complete coverage, you can also access:

   - Full source at `.source/{source_id}/`
   - Complete file listing via `Glob "*.md" at {source_path}`
   ```

---

## by-source

Generate separate index files for each source.

### Process

1. **Build main index**
   ```markdown
   # {config.corpus.name} Documentation Corpus

   > {len(sources)} documentation sources
   > Last updated: {current_date}

   ## Sources

   {for each source in sources}
   ### {source.id}
   *{source_description or type}*

   → See [index-{source.id}.md](index-{source.id}.md) for {file_count} entries

   {end for}
   ```

2. **Generate per-source indexes**

   For each source, create `index-{source.id}.md`:
   ```markdown
   # {source.id} Documentation Index

   > Part of the {config.corpus.name} Documentation Corpus
   > Back to [main index](index.md)

   > Source type: {source.type}
   > Location: {source_path}

   ---

   {organized entries for this source}
   ```

3. **Store results**
   ```
   state.index.content = main_index_markdown
   state.index.sub_indexes = [
     { filename: "index-{source.id}.md", content: source_index_markdown },
     ...
   ]
   ```

---

## Single Source Scan

Direct scanning for single-source corpora (no agent overhead).

### Process

1. **Determine source path**
   ```
   git: .source/{source.id}/{source.docs_root}/
   local: data/uploads/{source.id}/
   web: .cache/web/{source.id}/
   llms-txt: .cache/llms-txt/{source.id}/
   ```

2. **Count files**
   ```
   Glob: {source_path}/**/*.md
   Glob: {source_path}/**/*.mdx
   ```

3. **Identify sections**
   - List immediate subdirectories
   - Count files per subdirectory

4. **Detect framework**
   - Check for framework config files (see source-scanner agent)

5. **Find large files**
   - Identify files > 1000 lines
   - Generate suggested grep patterns

6. **Store result**
   ```yaml
   computed.scan_result:
     source_id: "{source.id}"
     type: "{source.type}"
     status: "ready"
     file_count: {count}
     sections:
       - name: "{section}"
         path: "{path}"
         file_count: {count}
     large_files:
       - path: "{path}"
         lines: {count}
         suggested_grep: "{pattern}"
     framework: "{framework}"
     frontmatter_type: "{yaml|toml|none}"
   ```

---

## Expand Sections

Expand specific sections with more detail.

### Input

- `current_index`: Current index markdown content
- `scope`: "all" or "specific"
- `sections`: Comma-separated section names (if scope == "specific")

### Process

1. **Parse current index**
   - Extract existing sections and entries

2. **Identify sections to expand**
   - If scope == "all": expand all sections
   - If scope == "specific": expand named sections only

3. **Add more entries**

   For each section to expand:
   - Query scan_results for more files in that section
   - Add entries that aren't already in the index
   - Maintain consistent formatting with existing entries

4. **Regenerate index**
   - Keep existing structure
   - Insert new entries in appropriate locations

5. **Update state**
   ```
   state.index.content = expanded_markdown
   ```

---

## Custom Reorganization

Apply custom organization based on user request.

### Input

- `current_index`: Current index markdown content
- `request`: User's reorganization request (free text)

### Process

1. **Parse reorganization request**
   - Identify desired structure
   - Determine if grouping, ordering, or hierarchy change

2. **Parse current index**
   - Extract all entries with their paths and descriptions

3. **Reorganize entries**
   - Apply requested organization
   - Maintain all existing entries (don't drop any)

4. **Regenerate index**
   - New section headers per request
   - Entries grouped as requested

5. **Update state**
   ```
   state.index.content = reorganized_markdown
   ```

---

## Add Missing Docs

Add documentation entries based on user description.

### Input

- `current_index`: Current index markdown content
- `request`: User's description of missing docs

### Process

1. **Parse request**
   - Identify topics or documents user wants added

2. **Search sources**

   For each topic mentioned:
   - Grep scan_results for matching files
   - Search file paths and content for keywords

3. **Find matching files**
   - Identify files not currently in index that match request
   - Prioritize by relevance to request

4. **Add entries**
   - Generate entries for found files
   - Insert in appropriate sections

5. **Report findings**
   - If files found: add them
   - If not found: inform user these docs may not exist in sources

6. **Update state**
   ```
   state.index.content = updated_markdown
   ```

---

## Custom Refinement

Apply arbitrary refinement based on user feedback.

### Input

- `current_index`: Current index markdown content
- `request`: User's custom refinement request

### Process

1. **Interpret request**
   - Understand what change the user wants
   - Could be: reordering, renaming sections, adding context, removing entries, etc.

2. **Apply changes**
   - Make requested modifications
   - Preserve overall structure unless explicitly changing it

3. **Update state**
   ```
   state.index.content = refined_markdown
   ```

---

## Entry Format Reference

### Standard Entry
```markdown
- **{Title}** `{source_id}:{path}` - {description}
```

### Large File Entry (needs GREP)
```markdown
- **{Title}** `{source_id}:{path}` ⚡ GREP - {description}. Search with: `{grep_pattern}`
```

### Path Format by Source Type

| Source Type | Format | Example |
|-------------|--------|---------|
| git | `{source_id}:{relative_path}` | `react:reference/hooks.md` |
| local | `local:{source_id}/{filename}` | `local:team-standards/guidelines.md` |
| web | `web:{source_id}/{cached_file}` | `web:kent-blog/article.md` |
| llms-txt | `llms-txt:{source_id}/{path}` | `llms-txt:claude-code/skills.md` |

### Large File Detection

Files over 1000 lines should be marked with `⚡ GREP`.

**Suggested grep patterns by file type:**

| File Type | Pattern |
|-----------|---------|
| Markdown | `grep -n "^## " FILE -A 20` |
| GraphQL | `grep -n "^type {TypeName}" FILE -A 30` |
| OpenAPI | `grep -n "/{path}:" FILE -A 20` |
| JSON Schema | `grep -n "\"{property}\":" FILE -A 10` |

---

## Quality Checklist

Before finalizing any index:

- [ ] All paths use correct format (`source_id:relative_path`)
- [ ] Large files (>1000 lines) marked with `⚡ GREP`
- [ ] Skip sections are excluded
- [ ] Priority sources appear first or prominently
- [ ] Organization matches user preference
- [ ] Header includes source list and date
- [ ] No duplicate entries
- [ ] All entries have descriptions
