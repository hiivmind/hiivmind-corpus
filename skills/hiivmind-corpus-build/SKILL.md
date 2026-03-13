---
name: hiivmind-corpus-build
description: >
  This skill should be used when the user asks to "build corpus index", "create index from docs",
  "analyze documentation", "populate corpus index", or needs to build the initial index for a
  corpus that was just initialized. Triggers on "build my corpus", "index the documentation",
  "create the index.md", "finish setting up corpus", "hiivmind-corpus build", or when a corpus
  has placeholder index.md that says "Run hiivmind-corpus-build".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch, Task
inputs:
  - name: corpus_name
    type: string
    required: false
    description: Name of the corpus to build (uses current directory if not provided)
outputs:
  - name: index_path
    type: string
    description: Path to the generated index.md
  - name: segmentation_strategy
    type: string
    description: Strategy used (single, tiered, by-section, by-source)
  - name: entry_count
    type: number
    description: Total index entries created
---

# Corpus Build

Build the documentation corpus index. Prepares all sources, scans for content, consults
the user on organization preferences, generates `index.md`, and updates config metadata.
Supports single and multi-source corpora with tiered indexing for large (500+ file) corpora.

## Precondition

A `config.yaml` must exist with at least one source configured.
If not found, suggest running `hiivmind-corpus-init` and `hiivmind-corpus-add-source`.

---

## Phase 1: Prepare Sources

**Inputs:** working directory
**Outputs:** `computed.config`, `computed.sources`, all sources verified ready

1. Read and parse `config.yaml`
2. Verify at least one source exists
3. For each source, verify it's ready for scanning:

### Per-source preparation by type

**Git source:**
- Check if `.source/{source_id}/` clone exists
- If exists, verify it's a valid git repo
- If missing, clone: `git clone --depth 1 --branch {branch} {url} .source/{source_id}`

**Local source:**
- Check if `uploads/{source_id}/` directory exists
- Verify it contains at least one file (`.md`, `.mdx`, or `.pdf`)
- If empty, warn user and ask whether to continue or skip this source

**Web source:**
- Check if `.cache/web/{source_id}/` directory exists
- Verify it contains cached content files
- If missing, warn: "Web cache is empty. Run add-source to fetch content first."

**llms-txt source:**
- Check if `.cache/llms-txt/{source_id}/` exists
- Verify cached pages are present
- If empty, suggest fetching content first

Display: "Sources prepared: {count} ready, {skipped} skipped"

---

## Phase 2: Scan Sources

**Inputs:** prepared sources
**Outputs:** `computed.scan_results`

**See:** `lib/corpus/patterns/scanning.md`

### Single source

If only one source, scan directly:
- Read all documentation files under the source path
- For each file: extract title, section headings, size, frontmatter type
- Identify documentation framework (MkDocs, Docusaurus, Sphinx, etc.) if detectable
- Count total files and identify large files (> 1000 lines)
- Group files by directory into logical sections

### Multi-source (parallel agents)

If 2+ sources, spawn parallel `source-scanner` agents:

**See:** `agents/source-scanner.md`

For each source, create a Task with prompt:
```
Scan source '{source_id}' (type: {type}) at corpus path '{corpus_path}'.
Return YAML with: source_id, type, status, file_count, sections (name/path/file_count),
large_files, framework, frontmatter_type, notes.
{if source has extraction: block in config}
extraction_config:
  wikilinks: {true|false}
  frontmatter: {true|false}
  tags: {true|false}
  dataview: {true|false}
Include extraction output in your YAML report per the extraction output format in
${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/extraction.md § "Source-Scanner Extraction Output Format".
{end if}
```

Launch ALL tasks in a single response for parallel execution. Aggregate results.

### Present scan summary

Display results table:

```
Scan Results
──────────────────────────────────
| Source       | Type | Files | Sections | Framework    |
|-------------|------|-------|----------|--------------|
| {id}        | git  | 142   | 8        | Docusaurus   |
| {id}        | local| 12    | 1        | none         |

Total: {total_files} files across {source_count} sources
```

---

## Phase 3: Determine Segmentation Strategy

**Inputs:** `computed.scan_results`, total file count
**Outputs:** `computed.segmentation`

### Large corpus (500+ files)

Present segmentation options:

| Strategy | Description |
|----------|-------------|
| **Tiered (recommended)** | Main index.md with section summaries, detailed index-{section}.md files |
| **By source** | One sub-index per source |
| **By section** | Main index covers top 20-30% only, link to sources for rest |
| **Single file** | Everything in one index.md (not recommended for large corpora) |

If tiered or by-source selected, collect section definitions from user.

### Moderate corpus (200-500 files)

Suggest segmentation but don't require it: "This corpus has {n} files. A tiered index
is optional but can improve navigation. Use tiered indexing?"

### Small corpus (< 200 files)

Default to single file. No segmentation prompt needed.

---

## Phase 4: Collect User Preferences

**Inputs:** `computed.scan_results`
**Outputs:** `computed.user_preferences`

### Use case

Ask: "What's the primary use case for this corpus?"

| Option | Description |
|--------|-------------|
| **Reference** | API docs, configuration reference |
| **Learning** | Tutorials, getting started guides |
| **Troubleshooting** | Error handling, debugging guides |
| **Mixed** | General purpose documentation |

### Source priorities (multi-source only)

If multiple sources, ask: "Which sources should be prioritized in the index?"
Present sources for ordering. Higher priority sources get more detailed entries.

### Organization

Ask: "How should the index be organized?"

| Option | Description |
|--------|-------------|
| **By topic** | Group entries by subject area across sources |
| **By source** | Group entries by documentation source |
| **Mixed** | Topics first, source attribution inline |

### Skip sections

Ask: "Are there sections to exclude? (e.g., changelog, internal docs)"
Allow comma-separated section names or "none".

---

## Phase 5: Generate Index

**Inputs:** `computed.scan_results`, `computed.user_preferences`, `computed.segmentation`
**Outputs:** `computed.index`

### Index path format

All file paths in the index use: `{source_id}:{relative_path}`

| Source Type | Format | Example |
|-------------|--------|---------|
| git | `{source_id}:{path}` | `react:reference/hooks.md` |
| local | `local:{source_id}/{file}` | `local:team-docs/guidelines.md` |
| web | `web:{source_id}/{file}` | `web:blog/article.md` |
| llms-txt | `llms-txt:{source_id}/{path}` | `llms-txt:claude-code/skills.md` |

### Generate draft

Read the documentation files, analyze their content, and generate an index organized
per user preferences. Each entry should include:

- **Title** and source path reference
- **Brief summary** (1-2 sentences describing the content)
- **Key topics** covered

For tiered indexes, generate the main `index.md` with section summaries and separate
`index-{section}.md` files with detailed entries.

**See:** `lib/corpus/patterns/index-generation.md`

### Show draft and refine

Present the draft to the user and ask: "How does this look?"

| Option | Action |
|--------|--------|
| **Looks good** | Proceed to save |
| **Expand sections** | Ask which sections to expand, regenerate with more detail |
| **Reorganize** | Ask for new organization preference, regenerate |
| **Missing coverage** | Ask what topics are missing, add entries |
| **Custom feedback** | Apply user's specific feedback |

Loop back to showing the draft after each refinement until the user is satisfied.

---

## Phase 5b: Graph Generation

**Inputs:** `computed.scan_results` (with extraction data from sources that had it enabled)
**Outputs:** `graph.yaml` written alongside `index.md`

**Precondition:** At least one source in `computed.scan_results` has an `extraction:` block in its scan report.

**Skip condition:** If no source produced extraction data → skip this phase entirely. No graph.yaml is written.

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` and `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/extraction.md`

### Steps

1. **Merge extraction data**

   Collect `extraction:` blocks from all source-scanner reports. For each source's extraction data, prefix all file paths with `{source_id}:` to create corpus-scoped references. Merge into a unified extraction dataset:
   - All wikilinks (with prefixed `from` and `to` paths)
   - All tags (with prefixed file lists)
   - All frontmatter keys (with prefixed file lists)

2. **Cluster entries into concepts**

   Apply the clustering algorithm from `graph.md` § "Graph Generation from Extraction Output":
   - Group by directory structure (subdirectory = candidate concept)
   - Group by shared tags
   - Identify wikilink hub pages (pages linking to many others)

3. **Propose concepts to user**

   Present a table of proposed concepts with their candidate labels and entry counts:

   ```
   Proposed Concepts from Extraction
   ────────────────────────────────────────
   | Concept (proposed)  | Entries | Based On        |
   |---------------------|---------|-----------------|
   | family-activities   | 12      | directory + tags |
   | work-projects       | 8       | tags            |
   | recipes             | 5       | directory       |

   Accept all / Rename / Merge / Discard unwanted
   ```

   Allow the user to rename, merge, or discard proposed concepts before proceeding.

4. **Generate relationships**

   From the merged extraction data and confirmed concepts:
   - Wikilinks between entries in different concepts → typed relationship (origin: `wikilink`)
   - Hub pages spanning multiple concepts → `includes` relationships
   - Shared tags across concepts → `see-also` relationships (origin: `tag`)
   - Record `evidence` path for each auto-generated relationship

5. **Write graph.yaml**

   Write `graph.yaml` to the same directory as `index.md`, following the strict schema in `graph.md` § "Schema Definition (Strict)". Set `meta.generated_at` to current timestamp, populate `meta.sources_extracted` with source IDs that contributed extraction data.

   Display: "Graph generated: graph.yaml ({concept_count} concepts, {relationship_count} relationships)"

---

## Phase 6: Save and Complete

**Inputs:** `computed.index`, `computed.segmentation`

### Save index files

1. Write `index.md` with the generated content
2. If tiered: write each `index-{section}.md` sub-index file

### Update config metadata

1. Set `index.last_updated_at` to current timestamp
2. For each source, update `last_indexed_at` to current timestamp
3. If git source: update `last_commit_sha` to current clone HEAD
4. Save `config.yaml`

### Completion

Display summary:

```
Build complete!

Index: index.md ({entry_count} entries)
{if tiered: Sub-indexes: {count} files}
Strategy: {segmentation_strategy}
Sources indexed: {source_count}
```

---

## Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| No config.yaml | "No config.yaml found" | Run hiivmind-corpus-init |
| No sources | "No sources configured" | Run hiivmind-corpus-add-source |
| Clone failed | "Failed to clone {url}" | Check URL and network |
| Local source empty | "No files in uploads/{id}/" | Add documents or skip source |
| Scan failed | "Failed to scan source" | Check source accessibility |
| Save failed | "Failed to write index" | Check file permissions |

---

## Pattern Documentation

- **Scanning:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/scanning.md`
- **Parallel scanning:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/parallel-scanning.md`
- **Index generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-generation.md`
- **Config parsing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-parsing.md`
- **Source patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/`
- **Extraction pipeline:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/extraction.md`
- **Graph generation:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md`

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented)
