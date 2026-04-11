---
name: hiivmind-corpus-build
description: >
  This skill should be used when the user asks to "build corpus index", "create index from docs",
  "analyze documentation", "populate corpus index", or needs to build the initial index for a
  corpus that was just initialized. Triggers on "build my corpus", "index the documentation",
  "create the index.md", "finish setting up corpus", "hiivmind-corpus build", or when a corpus
  has placeholder index.md that says "Run hiivmind-corpus-build", or "create the index.yaml".
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
  - name: index_yaml_path
    type: string
    description: Path to the generated index.yaml
  - name: segmentation_strategy
    type: string
    description: Strategy used (single, tiered, by-section, by-source)
  - name: entry_count
    type: number
    description: Total index entries created
---

# Corpus Build

Build the documentation corpus index. Prepares all sources, scans for content, consults
the user on organization preferences, generates `index.yaml` (structured, machine-queryable)
and renders `index.md` from it. Updates config metadata. Supports single and multi-source
corpora with tiered indexing for large (500+ file) corpora.

## Precondition

A `config.yaml` must exist with at least one source configured.
If not found, suggest running `hiivmind-corpus-init` and `hiivmind-corpus-add-source`.

## Process

```
1. PREPARE → 2. SCAN → 3. SEGMENT → 4. PREFERENCES → 5. INDEX → 6. GRAPH → 7. EMBEDDINGS → 8. SAVE
```

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
- Note: `.md` files may contain YAML frontmatter with `tags`, `headings`, and provenance
  metadata produced by the PDF extraction pipeline (see `lib/corpus/patterns/sources/pdf.md`).
  During scanning, extract `tags` and `headings` from frontmatter when present to enrich
  index entries rather than deriving them solely from file content.

**Web source:**
- Check if `.cache/web/{source_id}/` directory exists
- Verify it contains cached content files
- If missing, warn: "Web cache is empty. Run add-source to fetch content first."

**llms-txt source:**
- Check if `.cache/llms-txt/{source_id}/` exists
- Verify cached pages are present
- If empty, suggest fetching content first

**Self source:**
- Get repo root: `git rev-parse --show-toplevel`
- Normalize `docs_root`: if `"."`, treat as repo root
- Verify repo root exists and is accessible
- No cloning or fetching needed — files are read directly from repo
- Note: `.hiivmind/` is auto-excluded during scanning (see `lib/corpus/patterns/sources/self.md`)

Display: "Sources prepared: {count} ready, {skipped} skipped"

---

## Phase 2: Scan Sources

**Inputs:** prepared sources
**Outputs:** `computed.scan_results`

```pseudocode
GUARD_PHASE_2():
  IF computed.sources IS null OR len(computed.sources) == 0:
    DISPLAY "Cannot proceed: Phase 1 (Prepare Sources) has not completed."
    EXIT
```

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
{if source has sections: block in config}
sections_config:
  enabled: true
  min_level: {min_level}
  min_content_lines: {min_content_lines}
Generate section entries for qualifying headings per the Section Entry Generation
instructions in ${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md.
Also report heading_consistency in your scan output.
{end if}
{if source has chunking: block in config}
chunking_config:
  strategy: {strategy}
  target_tokens: {target_tokens}
  overlap_tokens: {overlap_tokens}
Run chunk.py on each file and include chunks in your output per the Chunk Generation
instructions in ${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md.
{end if}
Additionally, for each documentation file, include entry metadata in your output:
path, title, summary, tags, keywords, category, content_type, size, grep_hint, headings.
See ${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md § "Entry Metadata Generation" for field details.
{if type is "self"}
For self sources: scan from repo root {repo_root}/{docs_root}. Auto-exclude .hiivmind/ directory.
The repo root is: {output of git rev-parse --show-toplevel}
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

### Tree Thinning (post Phase 2c)

```pseudocode
GUARD_TREE_THINNING():
  section_count = count(entry for entry in computed.scan_results if entry.tier == "section")
  IF section_count == 0:
    SKIP "No section entries to thin."
    PROCEED to next phase

  has_token_config = ANY(source.sections.min_section_tokens IS NOT null for source in config.sources)
  IF NOT has_token_config:
    SKIP "Tree thinning not configured (no min_section_tokens in any source)."
    PROCEED to next phase

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/thin_sections.py --index index.yaml --min-tokens {min_section_tokens} --dry-run")

  IF result.exit_code != 0:
    DISPLAY "Tree thinning failed: {stderr}. Proceeding with unthinned sections."
    PROCEED to next phase

  IF result.sections_before == result.sections_after:
    DISPLAY "Tree thinning: all sections above threshold. No merges needed."
    PROCEED to next phase

  DISPLAY "Tree thinning would merge {sections_before - sections_after} sections."
  ASK user: "Apply these merges? [Y/n]"
  IF user approves:
    Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/thin_sections.py --index index.yaml --min-tokens {min_section_tokens}")
    DISPLAY "Thinned: {sections_before} → {sections_after} sections."
```

---

## Phase 3: Determine Segmentation Strategy

**Inputs:** `computed.scan_results`, total file count
**Outputs:** `computed.segmentation`

```pseudocode
GUARD_PHASE_3():
  IF computed.scan_results IS null:
    DISPLAY "Cannot proceed: Phase 2 (Scan Sources) has not completed."
    EXIT
```

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

**Inputs:** `computed.scan_results`, `computed.segmentation`
**Outputs:** `computed.user_preferences`

```pseudocode
GUARD_PHASE_4():
  IF computed.segmentation IS null:
    DISPLAY "Cannot proceed: Phase 3 (Determine Segmentation) has not completed."
    EXIT
```

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

### Indexing depth (per source)

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/section-indexing.md` and `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/chunking.md`

For each source, analyze scan results and recommend an indexing depth. Present
the recommendation with concrete consequences — estimated counts and sizes.

For each source, present:

```
Source: {source_id} ({type}, {file_count} files, {large_file_count} large files)

Recommended indexing depth: {recommendation}
  - File-level: {file_count} entries with metadata embeddings (current default)
  - Section-level: ~{section_estimate} additional entries from h{min_level}+ headings
  - Deep chunking: {chunk_estimate_or_"Not recommended"} using {strategy} strategy

Reason: {explanation based on scan results}

Options:
  a) File only (current behavior)
  b) File + Sections [recommended if heading_consistency is high]
  c) File + Chunks [recommended if heading_consistency is low]
  d) File + Sections + Chunks
```

**Recommendation logic:**

| Scan Result | Recommendation |
|------------|---------------|
| heading_consistency: high, large_files > 0 | File + Sections |
| heading_consistency: low or mixed | File + Chunks |
| heading_consistency: high, large_files > 0, file_count > 200 | File + Sections + Chunks |
| file_count < 50, no large files | File only |

**Estimation heuristics:**
- Section count: `sum(headings per file at min_level+) * 0.7` (30% filtered by min_content_lines)
- Chunk count: `sum(file_lines / target_lines_per_chunk)` across chunking-eligible files
- Embedding size: `entry_count * 2KB` for metadata, `chunk_count * 15KB` for chunks

After all sources are configured, show a confirmation table:

```
Indexing Depth Summary
──────────────────────────────────────────────────────────────
Source            | File | Sections | Chunks | Est. size
------------------|------|----------|--------|----------
polars-docs       |  142 |     ~200 |      — | ~4MB
meeting-notes     |  340 |        — |  ~3000 | ~45MB
obsidian-vault    |  215 |     ~180 |   ~800 | ~18MB
──────────────────────────────────────────────────────────────
```

Store user choices in `computed.indexing_depth` for use in later phases.

---

## Phase 5: Generate Index

**Inputs:** `computed.scan_results`, `computed.user_preferences`, `computed.segmentation`
**Outputs:** `computed.index`

```pseudocode
GUARD_PHASE_5():
  IF computed.user_preferences IS null:
    DISPLAY "Cannot proceed: Phase 4 (Collect User Preferences) has not completed."
    EXIT
```

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

### Generate index.yaml (v2)

From the source-scanner output, construct `index.yaml` following the strict schema in `lib/corpus/patterns/index-format-v2.md`.

For each entry from each source-scanner report:

1. Construct `id` as `{source_id}:{path}`
2. Map scanner output fields directly: `title`, `summary`, `tags`, `keywords`, `category`, `content_type`, `size`, `grep_hint`, `headings`
3. Set `source` to the source ID
4. Set `links_to` from extraction wikilinks (if extraction was enabled)
5. Compute `links_from` by cross-referencing all entries' `links_to` lists
6. Set `frontmatter` from extraction frontmatter data (if available, else `{}`)
7. Set `concepts` to empty list `[]` (populated later by Phase 6 if graph extraction is enabled, or manually via graph add-concept)
8. Set `stale: false`, `stale_since: null`, `last_indexed` to current timestamp
9. For section entries from source-scanner reports (entries with `tier: section`):
   - Construct `id` as `{source_id}:{path}#{anchor}`
   - Set `parent` to the file entry ID (`{source_id}:{path}`)
   - Map scanner output: `title`, `summary`, `tags`, `keywords`, `anchor`, `heading_level`, `line_range`
   - Set `tier: section`
   - Set `concepts` to empty list (populated by Phase 6 if applicable)
   - Section entries do NOT have: `size`, `grep_hint`, `headings`, `links_to`, `links_from`, `frontmatter`

Construct `meta`:
- `generated_at`: current timestamp
- `entry_count`: total entries

Write `index.yaml` to the corpus root.

### Render index.md

After writing index.yaml, render index.md deterministically:

```bash
bash render-index.sh index.yaml
```

If `render-index.sh` does not exist in the corpus root, copy it from `${CLAUDE_PLUGIN_ROOT}/templates/render-index.sh` first.

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-rendering.md`

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

## Phase 6: Graph Generation

**Inputs:** `computed.scan_results` (with extraction data from sources that had it enabled)
**Outputs:** `graph.yaml` written alongside `index.md`

```pseudocode
GUARD_PHASE_6():
  IF computed.index IS null:
    DISPLAY "Cannot proceed: Phase 5 (Generate Index) has not completed."
    EXIT
```

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

   Write `graph.yaml` to the same directory as `index.md`, following the strict schema in `graph.md` § "Schema Definition (Strict)" (schema_version: 2 — no entry lists in concepts). Set `meta.generated_at` to current timestamp.

   Display: "Graph generated: graph.yaml ({concept_count} concepts, {relationship_count} relationships)"

6. **Populate concepts in index.yaml entries:**

   After graph.yaml concepts are confirmed, update index.yaml entries with concept membership:
   - For each concept, identify which entries belong to it (from extraction clustering)
   - Set `concepts: ["{concept-id}"]` on each matched entry in index.yaml
   - Entries may belong to multiple concepts
   - Re-render index.md after updating index.yaml

   **graph.yaml v1 compatibility:** If an existing `graph.yaml` with `schema_version: 1` is detected (concepts have `entries[]` lists):
   1. Read the entry lists from each concept
   2. For each entry ID, find the entry in index.yaml and add the concept ID to its `concepts[]` field
   3. Remove `entries` and `entry_count` from each concept in graph.yaml
   4. Set `schema_version: 2`
   5. Save both files

---

## Phase 7: Generate Embeddings (optional)

**Inputs:** `computed.index` (index.yaml written), entry count
**Outputs:** `index-embeddings.lance/` (if user opts in)

```pseudocode
GUARD_PHASE_7():
  IF computed.index IS null:
    DISPLAY "Cannot proceed: Phase 5 (Generate Index) has not completed."
    EXIT
```

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`

### Procedure

1. Run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py`
2. Check heuristic: `entry_count > 150` OR corpus has tiered indexes (index-*.md files exist)
3. If heuristic not met: skip silently, proceed to Phase 8
4. If heuristic met:
   a. If detect.py reports "ready" or "no-model":
      Ask: "This corpus has {entry_count} entries. Semantic search improves retrieval for corpora this size. Enable it?"
   b. If detect.py exits 1 (not installed):
      Ask: "This corpus has {entry_count} entries. Semantic search improves retrieval for corpora this size. Enable it? Requires: `pip install fastembed lancedb pyyaml` (~260MB)"
   c. If user declines: skip, proceed to Phase 8
   d. If user accepts and fastembed not installed: run `pip install fastembed lancedb pyyaml`
   e. If detect.py reports "no-model": inform user "Downloading embedding model (~80MB, one-time)..."
5. Run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/`
6. Display: "Generated embeddings for {entry_count} entries"

**Commit guidance:** `index-embeddings.lance/` MUST be committed alongside `index.yaml` and `index.md`. It is a distributable artifact, not a cache. Do NOT add to `.gitignore`.

---

## Phase 7b: Generate Chunk Embeddings (optional)

**Inputs:** `computed.scan_results` (with chunks data), `computed.indexing_depth`
**Outputs:** `chunks-embeddings.lance/` (if any source has chunking enabled)

**Skip condition:** No source in `computed.indexing_depth` has chunks enabled.

### Procedure

1. Aggregate all chunks from source-scanner reports into a single JSON file:
   - Write `chunks.json` to a temporary location
   - Each chunk must have: `id`, `parent`, `source`, `path`, `chunk_index`, `chunk_text`, `line_range`, `overlap_prev`

2. Run dependency detection:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py
   ```
   If not installed, prompt user (same as Phase 7).

3. Run chunk embedding:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py --mode chunks chunks.json chunks-embeddings.lance/
   ```

4. Clean up temporary `chunks.json`

5. Display: "Generated chunk embeddings for {chunk_count} chunks across {source_count} sources"

**Commit guidance:** `chunks-embeddings.lance/` MUST be committed alongside other corpus files. Do NOT add to `.gitignore`.

---

## Phase 7c: Verification

```pseudocode
GUARD_PHASE_7C_VERIFICATION():
  IF computed.index IS null:
    DISPLAY "Cannot verify: index has not been generated."
    EXIT

  verify_enabled = config.build.verify_on_build
  IF verify_enabled IS null:
    verify_enabled = (computed.index.meta.entry_count < 200)

  IF verify_enabled == false:
    SKIP "Verification skipped."
    PROCEED to Phase 8

  sample_size = config.build.verify_sample_size OR 20
  result = Bash("python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/verify_entries.py --index index.yaml --source-root .source/ --sample {sample_size}")

  IF result.exit_code != 0:
    DISPLAY "Verification script failed. Proceeding without verification."
    PROCEED to Phase 8

  # LLM verification of previews in batches of 10
  inaccurate = LLM_VERIFY(result)

  IF len(inaccurate) == 0:
    DISPLAY "Verification passed: all entries accurate."
  ELSE:
    DISPLAY "Verification found {N} entries with summary drift."
    ASK user: "Regenerate summaries for these entries? [Y/n]"
    IF user approves:
      regenerate and re-embed if needed
```

---

## Phase 8: Save and Complete

**Inputs:** `computed.index`, `computed.segmentation`

```pseudocode
GUARD_PHASE_8():
  IF computed.index IS null:
    DISPLAY "Cannot proceed: Phase 5 (Generate Index) has not completed."
    EXIT
  # Phase 6 (Graph) and Phase 7 (Embeddings) are optional —
  # but verify they were evaluated, not skipped silently.
  # Graph: skip condition is "no extraction data" (checked in Phase 6)
  # Embeddings: skip condition is "heuristic not met" (checked in Phase 7)
```

### Save index files

1. Write `index.yaml` with the structured index
2. Copy `${CLAUDE_PLUGIN_ROOT}/templates/render-index.sh` to corpus root (if not already present)
3. Run `bash render-index.sh index.yaml` to generate `index.md`
4. If tiered: write each `index-{section}.md` sub-index file (v1 format only — tiered v2 is deferred)

### Update config metadata

1. Set `index.last_updated_at` to current timestamp
2. For each source, update `last_indexed_at` to current timestamp
3. If git source: update `last_commit_sha` to current clone HEAD
4. Save `config.yaml`

### Completion

Display summary:

```
Build complete!

Index: index.yaml ({entry_count} entries, {section_count} sections)
Rendered: index.md
{if graph: Graph: graph.yaml ({concept_count} concepts, {relationship_count} relationships)}
{if embeddings: Embeddings: index-embeddings.lance/ ({entry_count + section_count} entries)}
{if chunks: Chunks: chunks-embeddings.lance/ ({chunk_count} chunks)}
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
- **Index v2 schema:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-format-v2.md`
- **Index rendering:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-rendering.md`
- **Freshness:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/freshness.md`
- **Embeddings:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`
- **Section indexing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/section-indexing.md`
- **Deep chunking:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/chunking.md`

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
