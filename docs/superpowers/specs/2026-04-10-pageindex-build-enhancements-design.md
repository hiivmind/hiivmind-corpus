# PageIndex-Inspired Build Enhancements — Design

**Date:** 2026-04-10
**Status:** Draft
**Scope:** Five new deterministic scripts + source-scanner/build/refresh skill updates

## Goal

Adapt five algorithms from [VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex) to improve corpus build quality: exploit pre-existing navigation structure, verify index accuracy, merge trivially small sections, auto-split large files, and chunk at natural document boundaries.

## Context

PageIndex is a vectorless RAG system that builds hierarchical tree indexes from documents. Its build-time algorithms — particularly TOC detection, verification loops, tree thinning, recursive node splitting, and overlapping page groups — solve problems that corpus's current pipeline handles with simpler heuristics.

These five algorithms slot into existing build phases as enhancements. No phases are removed or reordered. The index.yaml schema, embedding format, navigate skill, and user-facing workflow are unchanged.

## Non-Goals

- PageIndex's retrieval-time tree-reasoning (query-time LLM navigation of tree structure). We evaluated this and chose build-time only.
- Using PageIndex as a runtime dependency. All algorithms are reimplemented as deterministic Python scripts + source-scanner prompt updates.
- PDF-specific page-offset calculation (PageIndex maps logical page numbers to physical page numbers in PDFs with roman-numeral prefaces). Not relevant to corpus's text-based sources.
- Changes to the navigate skill, embedding pipeline, or index.yaml schema.

## Architecture

All five algorithms follow the same pattern as existing `lib/corpus/scripts/`:

- **Deterministic Python scripts** handle data preparation, parsing, counting, and transformation.
- **LLM inference** (source-scanner agent, build/refresh skills) handles summarization, classification, and judgment calls.
- **LLM orchestration** (build skill) handles user interaction and pipeline decisions.

New scripts are standalone CLI tools with JSON input/output, callable via `python3 script.py [args]`.

### Dependency on existing infrastructure

| New script | Depends on | Notes |
|---|---|---|
| `detect_nav.py` | PyYAML (already optional dep) | Falls back to regex if unavailable |
| `verify_entries.py` | PyYAML | Data prep only; LLM does actual verification |
| `thin_sections.py` | PyYAML, fastembed (for token counting) | Falls back to word-count heuristic if no fastembed |
| `detect_large_files.py` | None (uses `wc` or Python line/word counting) | Zero dependencies |
| `split_by_headings.py` | None | Pure Python regex |
| `chunk_with_overlap.py` | None | Extends existing `chunk.py` patterns |

Token counting: scripts that need token counts use `fastembed`'s tokenizer if available, otherwise fall back to `len(text.split()) * 1.3` (word-count approximation). This matches corpus's existing "graceful degradation" principle.

---

## Algorithm 1: Nav Detection

**Phase:** 2a (file discovery), new fast path before glob-and-scan
**Type:** Deterministic script + LLM orchestration decision

### Problem

The source-scanner currently globs for all `.md`/`.mdx` files, groups by directory, and detects the documentation framework. Framework detection already finds `mkdocs.yml` but only reports the framework name — it doesn't parse the navigation structure. This means the scanner treats a well-organized MkDocs site the same as a random collection of markdown files.

### Solution

**Script:** `lib/corpus/scripts/detect_nav.py`

```
INTERFACE:
  Input:  source_root (path to .source/{source_id}/ or uploads/{source_id}/)
  Output: JSON to stdout
    {
      "found": true/false,
      "nav_file": "mkdocs.yml" | "_sidebar.md" | "SUMMARY.md" | null,
      "framework": "mkdocs" | "docsify" | "mdbook" | "gitbook" | "custom" | null,
      "hierarchy": [
        {
          "title": "Getting Started",
          "path": "docs/getting-started.md",
          "level": 1,
          "children": [
            {"title": "Installation", "path": "docs/install.md", "level": 2, "children": []}
          ]
        }
      ],
      "coverage": {
        "nav_entries": 45,
        "files_resolved": 42,
        "files_missing": 3,
        "total_md_files": 50,
        "coverage_pct": 84.0
      }
    }

ALGORITHM:
  1. Scan for nav files in priority order:
     a. mkdocs.yml          → parse nav: key (YAML, recursive)
     b. mkdocs.yaml         → same
     c. docusaurus.config.js → parse sidebars object (regex extraction of sidebar items)
     d. _sidebar.md          → parse "- [Title](path)" with indent nesting (docsify)
     e. SUMMARY.md           → parse "- [Title](path)" with indent nesting (mdbook/gitbook)
     f. _toc.yml             → parse YAML toc structure
     g. book.toml + src/SUMMARY.md → mdbook variant
  
  2. If found, parse into hierarchy:
     - Normalize all paths relative to source root
     - Resolve each path: check file exists, record missing
     - Compute coverage: files_resolved / total_md_files_in_source
  
  3. Output JSON to stdout

FALLBACK:
  If no nav file found: output {"found": false, ...}
  If PyYAML unavailable and nav file is YAML: attempt regex extraction of
    nav entries (pattern: "- title: ... path: ..." or "- Title: path"),
    set framework: "custom", warn in stderr
```

**Source-scanner integration:**

The source-scanner agent runs `detect_nav.py` as its first step. Decision logic:

- If `coverage_pct >= 80`: Use the nav hierarchy as the entry skeleton. For each nav entry, read the file and generate summary/tags/keywords (Phase 2b, unchanged). Files not in the nav are scanned normally and appended.
- If `coverage_pct` between 50–80: Present the nav hierarchy to the user and ask whether to use it or fall back to full scanning. Note which files are outside the nav.
- If `coverage_pct < 50` or `found: false`: Fall back to current glob-and-scan approach (unchanged).

### What changes in existing code

- Source-scanner agent prompt (`agents/source-scanner.md`): Add "Step 0: Check for navigation structure" before file discovery.
- `lib/corpus/patterns/scanning.md`: Add nav detection as first scanning strategy.
- No changes to build skill, index.yaml schema, or config.yaml.

---

## Algorithm 2: Verification Loop

**Phase:** New Phase 8.5 (between index generation and save), also available in refresh
**Type:** Deterministic data-prep script + LLM inference

### Problem

After building or refreshing an index, there is no check that entry summaries actually match the content they describe. The refresh skill detects staleness by commit SHA comparison, but a stale entry might have an accurate summary (if the relevant content didn't change) or a fresh entry might have an inaccurate summary (if the scanner misread the file).

### Solution

**Script:** `lib/corpus/scripts/verify_entries.py`

```
INTERFACE:
  Input:
    --index PATH          (path to index.yaml)
    --source-root PATH    (path to source root, e.g., .source/{source_id}/)
    --token-limit N       (max tokens of content preview per entry, default 500)
    --sample N            (verify N random entries instead of all, default: all)
    --entries ID,ID,...    (verify specific entry IDs only, optional)
  Output: JSON to stdout
    [
      {
        "entry_id": "polars-docs:docs/guides/expressions.md",
        "title": "Expressions",
        "summary": "How to write and compose expressions...",
        "source_path": "docs/guides/expressions.md",
        "content_preview": "# Expressions\n\nPolars expressions are...",
        "token_count": 487
      },
      ...
    ]

ALGORITHM:
  1. Parse index.yaml
  2. For each entry (or sampled/specified subset):
     a. Resolve source_path against source-root
     b. If file exists: read content, truncate to token_limit tokens
     c. If file missing: emit entry with content_preview: null
     d. Emit {entry_id, title, summary, source_path, content_preview, token_count}
  3. Output JSON array to stdout

NOTES:
  - This is data preparation only. The script does NOT judge accuracy.
  - For remote corpora (no local clone), skip verification and note in output.
  - Token counting uses fastembed tokenizer if available, else word-count approximation.
```

**Build/refresh skill integration:**

After generating or updating index.yaml, the build/refresh skill:

1. Runs `verify_entries.py --sample 20` (or all entries for small corpora <50 entries).
2. Feeds the output to the LLM in batches of ~10 entries:
   ```
   For each entry below, check whether the summary accurately describes
   the content preview. Return JSON: [{entry_id, accurate: true/false, issue: "..."}]
   ```
3. Presents inaccurate entries to the user:
   ```
   Verification found 3 entries where summaries may not match content:
   - expressions.md: Summary says "compose expressions" but content is about "expression contexts"
   - ...
   Regenerate summaries for these? [Y/n]
   ```
4. If user approves, regenerates summaries for flagged entries and re-embeds if embeddings exist.

### Configuration

New optional field in `config.yaml`:

```yaml
build:
  verify_on_build: true    # default: true for corpora with <200 entries, false otherwise
  verify_sample_size: 20   # entries to sample for verification, 0 = all
```

### What changes in existing code

- Build skill (`skills/hiivmind-corpus-build/SKILL.md`): Add verification step after Phase 7/7b, before Phase 8.
- Refresh skill (`skills/hiivmind-corpus-refresh/SKILL.md`): Add optional verification after updating stale entries.
- `config.yaml` template: Add `build.verify_on_build` and `build.verify_sample_size` fields.
- No changes to index.yaml schema, source-scanner, or navigate skill.

---

## Algorithm 3: Tree Thinning

**Phase:** 2c (section indexing), replaces `min_content_lines` heuristic
**Type:** Entirely deterministic

### Problem

Section indexing currently uses `min_content_lines` (default: 3) to filter out trivially small headings. This is a poor heuristic: a 3-line section with a code block might be 200 tokens of valuable content, while a 10-line section of boilerplate navigation links is noise. PageIndex's tree thinning uses token counts and bottom-up merging, which produces better results.

### Solution

**Script:** `lib/corpus/scripts/thin_sections.py`

```
INTERFACE:
  Input:
    --index PATH              (path to index.yaml)
    --min-tokens N            (minimum tokens for a section to survive, default 300)
    --dry-run                 (print what would be merged, don't modify)
  Output:
    Modified index.yaml (in-place) unless --dry-run
    JSON summary to stdout:
    {
      "sections_before": 245,
      "sections_after": 189,
      "merged": [
        {
          "removed_id": "src:docs/api.md#parameters",
          "merged_into": "src:docs/api.md#methods",
          "reason": "42 tokens (below 300 threshold)"
        }
      ]
    }

ALGORITHM:
  1. Parse index.yaml
  2. Extract all entries with tier: section
  3. Build parent-child tree:
     - Group sections by their parent entry ID
     - Order by line_range within each group
     - Nest children based on heading_level
  4. Bottom-up traversal (deepest sections first):
     for each section:
       total_tokens = estimate_tokens(section.summary + section.keywords)
       if total_tokens < min_tokens AND section has no children:
         mark for merge into nearest sibling or parent
  5. For each marked section:
     - If previous sibling exists: append summary to sibling, extend sibling line_range
     - Else: append summary to parent entry's summary, remove section
  6. Renumber/recount meta.entry_count
  7. Write updated index.yaml (unless --dry-run)

TOKEN ESTIMATION:
  If fastembed available: use tokenizer
  Else: len(text.split()) * 1.3 (English word-to-token approximation)

MERGE RULES:
  - Never merge a section that has children (merge children first, bottom-up)
  - Never merge across different source files (parent must share same source_path prefix)
  - Preserve the merged section's keywords by appending to target's keywords
```

### Configuration

Section indexing config gains a new optional field:

```yaml
sources:
  - id: docs
    sections:
      enabled: true
      min_level: 2
      min_content_lines: 3    # DEPRECATED, still honored if set
      min_section_tokens: 300  # NEW, takes precedence over min_content_lines
```

If `min_section_tokens` is set, tree thinning runs as a post-processing step after section entries are generated. If only `min_content_lines` is set, the existing behavior is preserved. If both are set, `min_section_tokens` takes precedence.

### What changes in existing code

- Source-scanner agent (`agents/source-scanner.md`): No change. Section entries are still generated with the existing heading-depth approach.
- Build skill (`skills/hiivmind-corpus-build/SKILL.md`): After Phase 2c generates section entries and before Phase 5 assembles index.yaml, run `thin_sections.py` if `min_section_tokens` is configured. Present the merge summary to the user.
- `config.yaml` template: Add `min_section_tokens` field to sections config.
- Existing corpora: No impact. `min_content_lines` continues to work. Tree thinning only activates when `min_section_tokens` is explicitly configured.

---

## Algorithm 4: Large-Node Splitting

**Phase:** 2a–2b (scanning + metadata), upgrades `size: large` + GREP marker approach
**Type:** Deterministic scripts + LLM inference for summaries

### Problem

Files exceeding 1000 lines currently get a `size: large` flag and a `grep_hint` for the GREP marker pattern. The user must manually decide how to handle them. For files with heading structure, the scanner could automatically generate sub-entries — the same thing section indexing does, but triggered by file size rather than explicit configuration.

### Solution

Two scripts, called in sequence:

**Script:** `lib/corpus/scripts/detect_large_files.py`

```
INTERFACE:
  Input:
    --source-root PATH     (path to source root)
    --max-tokens N         (threshold for "large", default 15000)
    --paths FILE           (optional: only check these paths, one per line)
  Output: JSON to stdout
    [
      {
        "path": "docs/api/reference.md",
        "token_count": 23400,
        "line_count": 1842,
        "has_headings": true,
        "heading_count": 34,
        "deepest_heading_level": 4
      }
    ]

ALGORITHM:
  1. For each .md/.mdx file in source-root (or specified paths):
     a. Read file, count tokens (fastembed tokenizer or word approximation)
     b. If token_count > max_tokens:
        - Count headings (regex: /^#{1,6}\s/)
        - Record deepest heading level
        - Emit entry
  2. Output JSON array to stdout
```

**Script:** `lib/corpus/scripts/split_by_headings.py`

```
INTERFACE:
  Input:
    --file PATH            (path to markdown file)
    --min-level N          (minimum heading level to split at, default 2)
    --max-level N          (maximum heading level to split at, default 4)
    --min-tokens N         (minimum tokens for a split section, default 200)
  Output: JSON to stdout
    [
      {
        "title": "Authentication",
        "level": 2,
        "line_start": 45,
        "line_end": 122,
        "token_count": 3200,
        "anchor": "authentication",
        "text_preview": "## Authentication\n\nThe API uses OAuth 2.0..."
      }
    ]

ALGORITHM:
  1. Parse all headings (regex: /^(#{1,6})\s+(.+)$/, skip code blocks)
  2. For each heading at min_level..max_level:
     a. Calculate text range: from this heading to next heading at same-or-higher level
     b. Count tokens in range
     c. Generate anchor from title (lowercase, replace spaces with hyphens, strip punctuation)
     d. Extract first 200 chars as text_preview
  3. Apply tree thinning: if section token_count < min_tokens, merge into previous section
  4. Output JSON array to stdout

NOTES:
  - Code block detection: track ``` delimiters, skip headings inside code blocks
  - Anchor generation matches existing section-indexing anchor logic
  - text_preview is for the LLM to generate summaries without reading the full file
```

**Source-scanner integration:**

After file discovery (Phase 2a), the source-scanner:

1. Runs `detect_large_files.py` on the source.
2. For each large file with `has_headings: true`:
   - Runs `split_by_headings.py` on the file.
   - Generates one parent entry for the file (with a high-level summary).
   - Generates child entries for each split section (with `tier: section`, `parent` set to the file entry ID).
   - LLM inference generates summary/tags/keywords for each child entry based on `text_preview`.
3. For each large file with `has_headings: false`:
   - Falls back to existing behavior: `size: large` flag + `grep_hint`.

### Interaction with section indexing

If `sections.enabled: true` is configured for the source AND a file is large, large-node splitting takes priority for that file (since it produces section entries with the same schema). The per-source section config still applies to non-large files.

If `sections.enabled: false` (or not configured), large-node splitting still runs for files exceeding the threshold. This means large files get automatic sub-entries even without explicit section indexing — section indexing is an opt-in for all files, large-node splitting is automatic for large files only.

### Configuration

New optional field in `config.yaml`:

```yaml
build:
  large_file_threshold: 15000  # tokens, default 15000. Set 0 to disable.
```

### What changes in existing code

- Source-scanner agent (`agents/source-scanner.md`): Add "Step 1b: Detect and split large files" after file discovery, before per-file metadata generation.
- Build skill: No direct changes — the source-scanner returns additional section entries in its report, which the build skill processes normally.
- `lib/corpus/patterns/scanning.md`: Document large-file splitting as a scanning strategy.
- `config.yaml` template: Add `build.large_file_threshold` field.
- Existing `size: large` and `grep_hint` behavior: Preserved as fallback for files without heading structure.

---

## Algorithm 5: Structure-Aware Chunking

**Phase:** 2d (deep chunking), upgrades `chunk.py` markdown strategy
**Type:** Entirely deterministic

### Problem

`chunk.py`'s markdown strategy uses boundary scoring based on heading weight, blank lines, and paragraph breaks, with a target of ~900 tokens per chunk. This produces chunks that can split mid-section, losing structural context. PageIndex preserves document hierarchy by using natural section boundaries as primary split points, only subdividing when a section exceeds the token limit.

### Solution

**Script:** `lib/corpus/scripts/chunk_with_overlap.py`

This is a new chunking strategy, not a replacement for `chunk.py`. It can be invoked as an alternative strategy or integrated into `chunk.py` as a new `--strategy headings` option.

```
INTERFACE:
  Input:
    --file PATH               (path to markdown file)
    --max-tokens N            (maximum tokens per chunk, default 900)
    --overlap-tokens N        (overlap at chunk boundaries, default 100)
    --min-level N             (minimum heading level for primary splits, default 2)
    --json                    (output as JSON)
  Output: JSON to stdout
    [
      {
        "chunk_index": 0,
        "line_start": 1,
        "line_end": 45,
        "token_count": 780,
        "heading_context": "## Getting Started",
        "overlap_prev": false,
        "text": "## Getting Started\n\nThis guide walks you through..."
      },
      {
        "chunk_index": 1,
        "line_start": 42,
        "line_end": 98,
        "token_count": 850,
        "heading_context": "## Getting Started > ### Installation",
        "overlap_prev": true,
        "text": "...previous section ending...\n### Installation\n\n..."
      }
    ]

ALGORITHM:
  1. Parse headings at min_level and deeper (reuse split_by_headings logic)
  2. Build section tree with token counts
  
  3. For each section (depth-first):
     if section.token_count <= max_tokens:
       emit section as one chunk
       set heading_context = ancestor heading chain ("## Parent > ### Child")
     
     else:
       # Section too large — split at sub-headings first
       if section has sub-headings:
         recurse into sub-sections
       else:
         # No sub-headings — split at paragraph boundaries
         paragraphs = split_on_blank_lines(section.text)
         current_chunk = []
         current_tokens = 0
         
         for each paragraph:
           if current_tokens + paragraph_tokens > max_tokens:
             emit current_chunk
             # Start new chunk with overlap from end of previous
             overlap = last_N_tokens(current_chunk, overlap_tokens)
             current_chunk = [overlap, paragraph]
             current_tokens = overlap_tokens + paragraph_tokens
           else:
             current_chunk.append(paragraph)
             current_tokens += paragraph_tokens
         
         emit remaining current_chunk
  
  4. Each emitted chunk carries:
     - heading_context: nearest ancestor heading chain
     - overlap_prev: true if chunk starts with overlap from previous chunk
     - line_start/line_end: original file line numbers

HEADING CONTEXT FORMAT:
  "## Data Modeling > ### Primary Keys > #### Composite Keys"
  This gives each chunk the structural context that token-window chunking loses.
  The heading_context is included in the chunk's embedding text by the embed pipeline.

OVERLAP BEHAVIOR:
  Overlap only occurs when a section is split at paragraph boundaries (not between
  heading-bounded sections). If section A ends and section B begins, there is no overlap
  — the heading boundary is a clean break. Overlap only handles the case where a single
  large section without sub-headings must be split mid-content.
```

### Integration with existing chunk.py

Two options (recommend Option A):

**Option A: New strategy in chunk.py.** Add `--strategy headings` to `chunk.py` that delegates to the algorithm above. The existing `markdown`, `transcript`, `code`, `paragraph` strategies are unchanged. The source-scanner chooses `headings` strategy when the file has consistent heading structure, falls back to `markdown` otherwise.

**Option B: Separate script.** Ship as `chunk_with_overlap.py` alongside `chunk.py`. The source-scanner calls whichever is appropriate.

Option A is cleaner — one entry point, one JSON output format, strategy selection is the only change.

### Configuration

The chunking config gains a new strategy option:

```yaml
sources:
  - id: docs
    chunking:
      enabled: true
      strategy: headings   # NEW. Options: headings (new default), markdown, transcript, code, paragraph
      target_tokens: 900
      overlap_tokens: 100
```

If `strategy` is not set, default to `headings` for sources where `detect_nav.py` or heading analysis indicates consistent heading structure, otherwise fall back to `markdown`.

### Embedding integration

The `heading_context` field is prepended to chunk text when generating embeddings:

```
Current:  "passage: {chunk_text}"
Proposed: "passage: {heading_context} | {chunk_text}"
```

This means a chunk from "## Data Modeling > ### Primary Keys" gets embedded with that structural context, improving retrieval for queries about "primary keys in data modeling" even when the chunk text doesn't repeat those terms.

### What changes in existing code

- `lib/corpus/scripts/chunk.py`: Add `headings` strategy option. Internal refactor to call heading-aware splitting logic.
- Source-scanner agent (`agents/source-scanner.md`): Default to `headings` strategy when heading structure is detected.
- `lib/corpus/scripts/embed.py`: Prepend `heading_context` to chunk embedding text when available.
- `config.yaml` template: Add `strategy` field to chunking config.

---

## Skill and Agent Integration: Guards, Skips, and Post-Checks

Each algorithm integration follows the existing patterns: GUARD blocks at phase entry, skip conditions for optional features, and post-step verification with user-facing summaries.

### Source-Scanner Agent Updates

The source-scanner agent (`agents/source-scanner.md`) gains three new steps. Each follows the existing step format with inline verification.

**New Step 0: Check for navigation structure** (before existing Step 1: File Discovery)

```pseudocode
STEP_0_NAV_DETECTION():
  # Pre-check: source root must be resolved
  IF source_root IS NOT accessible:
    SKIP "Cannot check nav structure: source root not resolved"
    PROCEED to Step 1 (existing file discovery)

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/detect_nav.py --source-root {source_root}")

  IF result.exit_code != 0:
    DISPLAY "Nav detection failed: {stderr}. Falling back to file scanning."
    PROCEED to Step 1

  IF result.found == false:
    PROCEED to Step 1

  # Post-check: evaluate coverage
  IF result.coverage.coverage_pct >= 80:
    computed.nav_skeleton = result.hierarchy
    computed.nav_source = result.nav_file
    DISPLAY "Found {result.nav_file} with {result.coverage.coverage_pct}% coverage ({result.coverage.files_resolved}/{result.coverage.nav_entries} files resolved). Using nav skeleton."
    # Step 1 file discovery will use nav_skeleton as entry list, scan remaining files normally
  ELIF result.coverage.coverage_pct >= 50:
    DISPLAY "Found {result.nav_file} with {result.coverage.coverage_pct}% coverage. {result.coverage.files_missing} files referenced but not found."
    ASK user: "Use this nav structure as the index skeleton? Files outside the nav will still be scanned. [Y/n]"
    IF user approves:
      computed.nav_skeleton = result.hierarchy
  ELSE:
    DISPLAY "Found {result.nav_file} but only {result.coverage.coverage_pct}% coverage. Falling back to file scanning."
    PROCEED to Step 1
```

**New Step 1b: Detect and split large files** (after existing Step 1: File Discovery, before Step 2: Sample Files)

```pseudocode
STEP_1B_LARGE_FILE_SPLITTING():
  # Pre-check: file discovery must have completed
  IF computed.file_list IS null OR len(computed.file_list) == 0:
    SKIP "No files discovered. Skipping large file detection."
    PROCEED to Step 2

  # Skip condition: check if feature is disabled
  large_threshold = config.build.large_file_threshold OR 15000
  IF large_threshold == 0:
    SKIP "Large file splitting disabled (threshold = 0)."
    PROCEED to Step 2

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/detect_large_files.py --source-root {source_root} --max-tokens {large_threshold}")

  IF result.exit_code != 0:
    DISPLAY "Large file detection failed: {stderr}. Continuing without splitting."
    PROCEED to Step 2

  IF len(result) == 0:
    DISPLAY "No files exceed {large_threshold} token threshold."
    PROCEED to Step 2

  # Post-check: split each large file that has headings
  computed.large_files = result
  computed.split_entries = []
  FOR file IN result:
    IF file.has_headings:
      split = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/split_by_headings.py --file {source_root}/{file.path} --min-tokens 200")
      IF split.exit_code == 0 AND len(split) > 1:
        computed.split_entries.append({file: file.path, sections: split})
        DISPLAY "Split {file.path} ({file.token_count} tokens) into {len(split)} sections."
      ELSE:
        DISPLAY "Could not split {file.path} by headings. Will use GREP marker fallback."
    ELSE:
      DISPLAY "{file.path} ({file.token_count} tokens) has no heading structure. Using size: large + grep_hint."

  # Summary
  split_count = sum(len(s.sections) for s in computed.split_entries)
  fallback_count = len(result) - len(computed.split_entries)
  DISPLAY "Large files: {len(result)} detected, {split_count} sub-entries generated, {fallback_count} using GREP fallback."
```

**Modified Step (chunking):** When chunking is enabled, select strategy based on heading analysis.

```pseudocode
STEP_CHUNKING_STRATEGY_SELECTION():
  # Pre-check: chunking must be enabled for this source
  IF source.chunking.enabled != true:
    SKIP chunking entirely

  strategy = source.chunking.strategy OR "auto"

  IF strategy == "auto":
    # Use heading analysis from Step 0 or Step 1b
    IF computed.nav_skeleton IS NOT null:
      strategy = "headings"
    ELIF computed.heading_consistency == "high":
      strategy = "headings"
    ELSE:
      strategy = "markdown"  # existing default

  DISPLAY "Chunking strategy for {source.id}: {strategy}"
  # Proceed with selected strategy
```

### Build Skill Updates

**New GUARD for verification (after Phase 7b, before Phase 8):**

```pseudocode
GUARD_PHASE_7C_VERIFICATION():
  IF computed.index IS null:
    DISPLAY "Cannot verify: index has not been generated."
    EXIT

  # Skip condition
  verify_enabled = config.build.verify_on_build
  IF verify_enabled IS null:
    # Default: true for <200 entries, false otherwise
    verify_enabled = (computed.index.meta.entry_count < 200)

  IF verify_enabled == false:
    SKIP "Verification skipped (verify_on_build: false or entry_count >= 200)."
    PROCEED to Phase 8

  sample_size = config.build.verify_sample_size OR 20
  IF sample_size > computed.index.meta.entry_count:
    sample_size = 0  # 0 means all

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/verify_entries.py --index index.yaml --source-root .source/ --sample {sample_size}")

  IF result.exit_code != 0:
    DISPLAY "Verification script failed: {stderr}. Proceeding without verification."
    PROCEED to Phase 8

  IF len(result) == 0:
    DISPLAY "No entries to verify (all entries may be remote-only)."
    PROCEED to Phase 8

  # LLM verification of extracted previews (batched)
  inaccurate = []
  FOR batch IN chunk(result, size=10):
    verification = LLM_CALL("For each entry, check if summary matches content_preview.
                              Return [{entry_id, accurate: true/false, issue: '...'}]", batch)
    inaccurate.extend([v for v in verification if v.accurate == false])

  # Post-check: present results
  IF len(inaccurate) == 0:
    DISPLAY "Verification passed: {len(result)} entries checked, all accurate."
  ELSE:
    DISPLAY "Verification found {len(inaccurate)} entries with summary drift:"
    FOR entry IN inaccurate:
      DISPLAY "  - {entry.entry_id}: {entry.issue}"
    ASK user: "Regenerate summaries for these entries? [Y/n]"
    IF user approves:
      regenerate_summaries(inaccurate)
      IF index-embeddings.lance/ exists:
        re_embed(inaccurate)
```

**New GUARD for tree thinning (after Phase 2c section indexing, before Phase 5):**

```pseudocode
GUARD_TREE_THINNING():
  # Pre-check: section entries must exist
  section_count = count(entry for entry in computed.scan_results if entry.tier == "section")
  IF section_count == 0:
    SKIP "No section entries to thin."
    PROCEED to next phase

  # Skip condition: min_section_tokens must be configured
  has_token_config = ANY(source.sections.min_section_tokens IS NOT null for source in config.sources)
  IF NOT has_token_config:
    SKIP "Tree thinning not configured (no min_section_tokens in any source)."
    PROCEED to next phase

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/thin_sections.py --index index.yaml --min-tokens {min_section_tokens} --dry-run")

  IF result.exit_code != 0:
    DISPLAY "Tree thinning failed: {stderr}. Proceeding with unthinned sections."
    PROCEED to next phase

  IF result.sections_before == result.sections_after:
    DISPLAY "Tree thinning: all {result.sections_before} sections above token threshold. No merges needed."
    PROCEED to next phase

  # Post-check: present merge plan and confirm
  DISPLAY "Tree thinning would merge {result.sections_before - result.sections_after} sections:"
  FOR merge IN result.merged[:10]:  # show first 10
    DISPLAY "  - {merge.removed_id} → {merge.merged_into} ({merge.reason})"
  IF len(result.merged) > 10:
    DISPLAY "  ... and {len(result.merged) - 10} more."

  ASK user: "Apply these merges? [Y/n]"
  IF user approves:
    Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/thin_sections.py --index index.yaml --min-tokens {min_section_tokens}")
    DISPLAY "Thinned: {result.sections_before} → {result.sections_after} sections."
```

### Refresh Skill Updates

**New optional step after Phase 6 (Apply Changes):**

```pseudocode
GUARD_REFRESH_VERIFICATION():
  # Pre-check: changes must have been applied
  IF computed.changes_applied IS null OR len(computed.changes_applied) == 0:
    SKIP "No changes applied. Skipping verification."
    PROCEED to Phase 7

  # Skip condition: only verify if entries were actually modified
  modified_ids = [c.entry_id for c in computed.changes_applied if c.action in ("modified", "added")]
  IF len(modified_ids) == 0:
    SKIP "Only deletions applied. Skipping verification."
    PROCEED to Phase 7

  result = Bash("python3 ${PLUGIN_ROOT}/lib/corpus/scripts/verify_entries.py --index index.yaml --source-root .source/ --entries {','.join(modified_ids)}")

  IF result.exit_code != 0:
    DISPLAY "Post-refresh verification failed: {stderr}. Proceeding without verification."
    PROCEED to Phase 7

  # LLM verification (same pattern as build)
  inaccurate = []
  FOR batch IN chunk(result, size=10):
    verification = LLM_CALL(...)
    inaccurate.extend(...)

  IF len(inaccurate) > 0:
    DISPLAY "Post-refresh verification found {len(inaccurate)} entries with summary drift."
    ASK user: "Regenerate? [Y/n]"
    ...
```

---

## Cross-Cutting Concerns

### Script dependencies

All new scripts require only Python 3 stdlib. PyYAML is used by `detect_nav.py`, `verify_entries.py`, and `thin_sections.py` but is already an optional dependency. Token counting uses fastembed tokenizer if available, otherwise word-count approximation.

No new required dependencies.

### Error handling

All scripts:
- Exit 0 on success with JSON to stdout.
- Exit 1 on error with error message to stderr.
- Never modify files without explicit `--in-place` or `--output` flag (except `thin_sections.py` which modifies index.yaml in-place, with `--dry-run` option).

### Backward compatibility

- Existing `config.yaml` files work without changes. All new fields are optional with sensible defaults.
- Existing corpora do not need rebuilding. New features activate only when configured or when thresholds are exceeded.
- `min_content_lines` in section config is deprecated but still honored. `min_section_tokens` takes precedence if both are set.

### Updated cross-cutting concerns table

New rows for CLAUDE.md cross-cutting concerns:

| Feature | Relevant Skills | What to Check |
|---|---|---|
| Nav detection | source-scanner, build, add-source | `detect_nav.py` called before glob scan, coverage threshold logic |
| Verification loop | build, refresh | `verify_entries.py` + LLM verification, config flag |
| Tree thinning | build, enhance, refresh | `thin_sections.py` post-processing, `min_section_tokens` config |
| Large-node splitting | source-scanner, build | `detect_large_files.py` + `split_by_headings.py`, interaction with section indexing |
| Structure-aware chunking | build, source-scanner, navigate | `headings` strategy in `chunk.py`, `heading_context` in embeddings |

## Acceptance Criteria

### Algorithm 1: Nav Detection
- [ ] `detect_nav.py` parses `mkdocs.yml` nav, `_sidebar.md`, and `SUMMARY.md` into hierarchy JSON.
- [ ] Coverage percentage is calculated correctly (resolved files / total files).
- [ ] Source-scanner uses nav skeleton when coverage >= 80%, falls back otherwise.
- [ ] Files outside the nav are still scanned and included.

### Algorithm 2: Verification Loop
- [ ] `verify_entries.py` extracts content previews for specified entries.
- [ ] Build skill runs verification after index generation (when `verify_on_build: true`).
- [ ] Inaccurate entries are presented to user with option to regenerate.
- [ ] Refresh skill can call verification after updating stale entries.

### Algorithm 3: Tree Thinning
- [ ] `thin_sections.py` merges sections below `min_section_tokens` bottom-up.
- [ ] Merged sections preserve keywords from removed children.
- [ ] Never merges across different source files.
- [ ] `--dry-run` mode shows what would be merged without modifying files.
- [ ] Existing `min_content_lines` config still works when `min_section_tokens` is not set.

### Algorithm 4: Large-Node Splitting
- [ ] `detect_large_files.py` identifies files exceeding token threshold.
- [ ] `split_by_headings.py` produces section entries with correct line ranges and anchors.
- [ ] Source-scanner generates parent + child entries for large files with headings.
- [ ] Files without headings fall back to existing `size: large` + `grep_hint`.
- [ ] Large-node splitting and section indexing coexist without duplicate entries.

### Algorithm 5: Structure-Aware Chunking
- [ ] `chunk.py` gains `--strategy headings` option.
- [ ] Heading-bounded sections that fit in `max_tokens` are emitted as single chunks.
- [ ] Sections exceeding `max_tokens` are split at paragraph boundaries with overlap.
- [ ] Each chunk carries `heading_context` (ancestor heading chain).
- [ ] `embed.py` prepends `heading_context` to chunk embedding text.
- [ ] Existing chunking strategies (`markdown`, `transcript`, `code`, `paragraph`) are unchanged.

### Guards, Skips, and Post-Checks
- [ ] Source-scanner Step 0 (nav detection) has pre-check for source root accessibility, graceful fallback on script failure, and coverage-threshold decision logic with user prompt at 50–80%.
- [ ] Source-scanner Step 1b (large files) has pre-check for `computed.file_list`, skip when `large_file_threshold == 0`, graceful fallback on script failure, and post-step summary of split vs fallback counts.
- [ ] Source-scanner chunking step has pre-check for `chunking.enabled`, auto-strategy selection based on heading analysis, and strategy display.
- [ ] Build Phase 7c (verification) has GUARD for `computed.index`, skip condition based on `verify_on_build` config with default heuristic, graceful fallback on script failure, and post-check presenting inaccurate entries with regeneration prompt.
- [ ] Build tree-thinning step has pre-check for section entry existence, skip when `min_section_tokens` not configured, dry-run preview before applying, and user confirmation gate.
- [ ] Refresh verification step has pre-check for `computed.changes_applied`, skip when only deletions applied, and targets only modified/added entries.
- [ ] All new steps degrade gracefully: script failure → DISPLAY warning → PROCEED to next phase (never EXIT on script failure).
- [ ] All new steps with user interaction offer `[Y/n]` confirmation before modifying index.yaml.

### Integration
- [ ] All scripts exit 0 with JSON stdout on success, exit 1 with stderr on error.
- [ ] No new required dependencies (PyYAML and fastembed remain optional).
- [ ] Existing corpora continue to work without rebuilding.
- [ ] CLAUDE.md cross-cutting concerns table is updated.
