---
name: hiivmind-corpus-navigate
description: This skill should be used when the user asks "find in the docs", "check the documentation", "what do the docs say about", "look up in corpus", "search all corpora", "query documentation", or asks questions that could be answered by installed documentation corpora. Routes queries across all installed hiivmind-corpus plugins.
---

# Global Corpus Navigator

Navigate across ALL installed hiivmind-corpus documentation corpora from a single entry point. Analyze user questions to identify the relevant corpus and route to the appropriate per-corpus navigate skill.

## When to Use

- User asks a documentation question without specifying which corpus
- User references a library/framework that has a corpus installed
- Working in a project that uses documented technologies
- User says "check the docs" or "look it up"

## Navigation Process

### Step 1: Check Cache, Then Discover

**Performance optimization:** Check for a cached corpus list before running full discovery.

#### Option A: Use Cached Corpus List (Fast Path)

**Check for cache in user's CLAUDE.md:**

```
Read: ~/.claude/CLAUDE.md
Look for: <!-- hiivmind-corpus-cache --> ... <!-- /hiivmind-corpus-cache -->
```

**If cache found and not empty:**
1. Parse cache table to extract: name, keywords, location
2. Use cached corpus list directly
3. Skip full discovery scan

**Cache format:**
```markdown
<!-- hiivmind-corpus-cache -->
| Corpus | Keywords | Location |
|--------|----------|----------|
| polars | dataframe, lazy, expressions | ~/.claude/plugins/... |
<!-- /hiivmind-corpus-cache -->
```

**Performance benefit:** Cache lookup is O(1) vs discovery which scans 4+ filesystem locations.

**Note:** Cache may be stale if user installed/removed corpora since last `discover`. When corpus not found at cached path, fall back to full discovery.

#### Option B: Full Discovery (Fallback)

**If cache not found, empty, or stale:**

Fall back to full discovery. See `lib/corpus/patterns/discovery.md` for detailed algorithms.

**Using Claude tools (recommended):**
```
Glob: ~/.claude/skills/hiivmind-corpus-*/data/config.yaml
Glob: .claude-plugin/skills/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/data/config.yaml
Glob: ~/.claude/plugins/marketplaces/hiivmind-corpus-*/data/config.yaml
```

**Using bash:**
```bash
# Find all corpus locations
for d in ~/.claude/skills/hiivmind-corpus-*/ \
         .claude-plugin/skills/hiivmind-corpus-*/ \
         ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ \
         ~/.claude/plugins/marketplaces/hiivmind-corpus-*/; do
    [ -d "$d" ] && [ -f "${d}data/config.yaml" ] && echo "$d"
done
```

For each corpus, extract (see `lib/corpus/patterns/config-parsing.md`):
- **Name**: Directory name (e.g., `hiivmind-corpus-polars`)
- **Display name**: From `.corpus.display_name` in config.yaml
- **Keywords**: From `.corpus.keywords[]` in config.yaml (or infer from name)

### Step 2: Analyze the Question

Examine the user's question to identify:

1. **Explicit mentions**: Does the question mention a project by name?
   - "How do I use Polars lazy API?" → `polars` mentioned
   - "What's the Ibis equivalent of..." → `ibis` mentioned

2. **Contextual signals**: What's the user working on?
   - Current file imports (e.g., `import polars as pl`)
   - Project dependencies (pyproject.toml, package.json)
   - Recent conversation context

3. **Topic matching**: Does the question match corpus keywords?
   - "How do I filter a dataframe?" → Could be Polars, Pandas, or Narwhals
   - "GitHub Actions workflow" → GitHub corpus

### Step 3: Route the Query

Based on analysis, take one of these paths:

**Clear match** (single corpus identified):
1. Read that corpus's `data/index.md`
2. Find relevant entries matching the question
3. Fetch documentation from source
4. Answer with citations

**Ambiguous match** (multiple possible corpora):
1. Present options to user:
   > "This question could be answered by multiple corpora:
   > - **Polars** - DataFrame operations
   > - **Narwhals** - DataFrame-agnostic API
   >
   > Which would you like me to check?"
2. Wait for user selection
3. Route to selected corpus

**No match** (no relevant corpus installed):
1. Inform user:
   > "I don't have a documentation corpus installed for this topic.
   > Available corpora: Polars, Ibis, Narwhals
   >
   > Would you like me to search the web, or would you like to install a corpus?"

### Step 4: Fetch and Answer

Once a corpus is selected, use its navigate skill:

1. **Read the index**: `{corpus_path}/data/index.md`
2. **Find relevant section**: Match question to index headings
3. **Parse path format**: `{source_id}:{relative_path}`
4. **Look up source**: Get details from `{corpus_path}/data/config.yaml`
5. **Fetch content**: Based on source type (see below)
6. **Answer**: Cite source and file path

#### Fetching by Source Type

**Git sources:**
- Read from `.source/{source_id}/{path}` if clone exists
- Fallback: Fetch via raw.githubusercontent.com

**Local sources:**
- Read from `data/uploads/{source_id}/{path}`

**Web sources:**
- Read from cached file: `.cache/web/{source_id}/{cached_file}`

**Generated-docs sources:**

**See:** `lib/corpus/patterns/sources/generated-docs.md` for generated-docs operations.

Generated-docs sources fetch content **live** via WebFetch (unless caching is enabled).

1. **Look up source config:**
   ```yaml
   sources:
     - id: "gh-cli-manual"
       type: "generated-docs"
       web_output:
         base_url: "https://cli.github.com/manual"
   ```

2. **Construct URL from index path:**
   - Index entry: `gh-cli-manual:/gh_pr_create`
   - Base URL: `https://cli.github.com/manual`
   - Full URL: `https://cli.github.com/manual/gh_pr_create`

3. **Fetch content live:**
   ```
   WebFetch: {base_url}{path}
   ```

4. **Optional cache check:**
   - If `cache.enabled: true`, check `.cache/web/{source_id}/` first
   - If cached file exists and recent, use it
   - Otherwise, fetch live and optionally cache

**URL Construction Pattern:**

```
Index entry:     {source_id}:{path}
Source config:   web_output.base_url = "https://example.com/docs"
Full URL:        {base_url}{path}
                 https://example.com/docs{path}
```

**Example:**
- Index: `gh-cli-manual:/gh_pr_create`
- Config: `base_url: "https://cli.github.com/manual"`
- URL: `https://cli.github.com/manual/gh_pr_create`

**Worked example with index gap handling:**

When user asks: "How do I create a PR with gh CLI?"

1. Search index for matching entry:
   ```markdown
   - **gh pr create** `gh-cli-manual:/gh_pr_create` - Create a new pull request
   ```

2. Parse path: `gh-cli-manual:/gh_pr_create`
   - Source ID: `gh-cli-manual`
   - Path: `/gh_pr_create`

3. Look up source in config.yaml:
   ```yaml
   - id: "gh-cli-manual"
     type: "generated-docs"
     web_output:
       base_url: "https://cli.github.com/manual"
   ```

4. Construct URL: `https://cli.github.com/manual/gh_pr_create`

5. Fetch: `WebFetch: https://cli.github.com/manual/gh_pr_create`

**If index entry not found:**
- Check `discovered_urls` in config for direct path match
- Suggest related entries from index
- Offer to search the docs site directly

## Multi-Corpus Queries

For questions spanning multiple technologies:

**Example**: "How do I convert a Polars DataFrame to an Ibis table?"

1. Identify both corpora are relevant: `polars`, `ibis`
2. Query each corpus for relevant entries:
   - Polars: Export/conversion functions
   - Ibis: Import/creation methods
3. Synthesize answer from both sources
4. Cite both corpora

## Corpus Index Quick Reference

Build a mental map of installed corpora by reading their indexes:

**Using Claude tools:**
```
For each discovered corpus path:
  Read: {corpus_path}/data/index.md (first 50 lines)
```

This provides topic coverage for routing decisions.

## Per-Session Corpus Routing

**See:** `lib/corpus/patterns/discovery.md` and `lib/corpus/patterns/config-parsing.md`

Keywords are discovered dynamically from each installed corpus's `config.yaml`. This ensures routing stays accurate as corpora are installed/uninstalled.

### Building the Routing Table

On first documentation question in a session:

1. **Discover all corpora** (see Step 1 above)
2. **For each corpus**, extract routing metadata from `data/config.yaml`:
   - Display name: `.corpus.display_name`
   - Keywords: `.corpus.keywords[]`
3. **Check status**: Read `data/index.md` to determine if built or placeholder

**Output format:**
```
name|display_name|keywords|status|path
hiivmind-corpus-polars|Polars|polars,dataframe,lazy,expression|built|/path/to/corpus
hiivmind-corpus-ibis|Ibis|ibis,sql,backend,duckdb|built|/path/to/corpus
```

Keywords come from each corpus's `data/config.yaml`:

```yaml
corpus:
  name: "polars"
  display_name: "Polars"
  keywords:
    - polars
    - dataframe
    - lazy
    - expression
```

If a corpus lacks explicit keywords, the name is inferred from the directory (e.g., `hiivmind-corpus-polars` → `polars`).

### Keyword Matching Algorithm

1. **Extract terms** from user query (nouns, technical terms, project names)
2. **Score each corpus** by keyword matches:
   - Exact match on project name → high confidence
   - Multiple keyword matches → medium confidence
   - Single keyword match → low confidence
3. **Select routing**:
   - Single high-confidence match → route directly
   - Multiple matches → check project context or ask user
   - No matches → report no relevant corpus installed

## Context-Aware Routing

When working in a project, consider:

**Python project with polars in dependencies:**
- Questions about dataframes → default to Polars corpus
- "How do I filter?" → Check Polars first

**Project CLAUDE.md with corpus awareness:**
- Read project's CLAUDE.md for corpus hints
- Injected awareness sections indicate preferred corpus

**Recent conversation:**
- If user was just asking about Polars → continue with Polars
- Topic continuity improves routing accuracy

## Index Reading Pattern

**See:** `lib/corpus/patterns/paths.md` for path resolution.

For large indexes or tiered indexes:

1. **Check for tiered structure**:
   ```
   Glob: {corpus_path}/data/index-*.md
   ```

2. **If tiered**: Read main index to find section, then read sub-index

3. **If flat**: Scan main index for matching entries

4. **For large files** (marked with `⚡ GREP`): Use Grep instead of Read

## Error Handling

**Corpus index not built:**
> "The {corpus} corpus hasn't been indexed yet. Run `hiivmind-corpus-build` first."

**Source not cloned:**
> "The source files aren't available locally. Fetching from GitHub..."
> (Then use raw.githubusercontent.com fallback)

**Stale index:**
> "Note: The {corpus} index may be outdated. The source has been updated since last indexing."

## Output Format

When answering from a corpus:

```markdown
## Answer

[Answer content with code examples]

---
**Source**: hiivmind-corpus-polars
**File**: `polars:docs/user-guide/expressions.md`

**Related docs**:
- Filtering: `polars:docs/user-guide/filtering.md`
- Selecting: `polars:docs/user-guide/selecting.md`
```

## Integration Points

This skill is invoked by:
- **`/hiivmind-corpus` command**: When user selects "Navigate" from corpus menu
- **Direct trigger**: When user asks documentation questions
- **Project awareness**: When CLAUDE.md references corpus

This skill uses:
- **`hiivmind-corpus-discover`**: To find installed corpora
- **Per-corpus navigate skills**: For actual documentation fetching

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/discovery.md` - Corpus discovery algorithms
- `lib/corpus/patterns/config-parsing.md` - YAML config extraction
- `lib/corpus/patterns/paths.md` - Path resolution
- `lib/corpus/patterns/status.md` - Index status checking

**Related skills:**
- Discovery: `skills/hiivmind-corpus-discover/SKILL.md`
- Per-corpus navigate: `templates/navigate-skill.md.template`
- Gateway command: `commands/hiivmind-corpus.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
