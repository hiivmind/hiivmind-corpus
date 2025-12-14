---
name: hiivmind-corpus-navigate
description: This skill should be used when the user asks "find in the docs", "check the documentation", "what do the docs say about", "look up in corpus", or asks questions that could be answered by installed documentation corpora. Routes queries across all installed hiivmind-corpus plugins.
---

# Global Corpus Navigator

Navigate across ALL installed hiivmind-corpus documentation corpora from a single entry point. Analyze user questions to identify the relevant corpus and route to the appropriate per-corpus navigate skill.

## When to Use

- User asks a documentation question without specifying which corpus
- User references a library/framework that has a corpus installed
- Working in a project that uses documented technologies
- User says "check the docs" or "look it up"

## Navigation Process

### Step 1: Discover Available Corpora

First, identify all installed corpora using the discover skill logic:

```bash
# Find all corpus locations
USER_CORPORA=$(ls -d ~/.claude/skills/hiivmind-corpus-*/ 2>/dev/null)
REPO_CORPORA=$(ls -d .claude-plugin/skills/hiivmind-corpus-*/ 2>/dev/null)
MARKETPLACE_SINGLE=$(ls -d ~/.claude/plugins/marketplaces/hiivmind-corpus-*/ 2>/dev/null)
MARKETPLACE_MULTI=$(ls -d ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ 2>/dev/null)

# Combine all
ALL_CORPORA="$USER_CORPORA $REPO_CORPORA $MARKETPLACE_SINGLE $MARKETPLACE_MULTI"
```

For each corpus, extract:
- **Name**: Directory name (e.g., `hiivmind-corpus-polars`)
- **Display name**: From skill metadata (e.g., `Polars`)
- **Keywords**: From config.yaml or infer from name

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
5. **Fetch content**: Read from `.source/` or fetch via raw.githubusercontent.com
6. **Answer**: Cite source and file path

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

Build a mental map of installed corpora:

```bash
# For each corpus, read its index summary
for corpus in $ALL_CORPORA; do
  echo "=== $(basename $corpus) ==="
  head -20 "$corpus/data/index.md"
done
```

This provides topic coverage for routing decisions.

## Per-Session Corpus Routing

Keywords are discovered dynamically from each installed corpus's `config.yaml`. This ensures routing stays accurate as corpora are installed/uninstalled.

### Building the Routing Table

On first documentation question in a session:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"

# Discover all corpora with routing metadata
discover_all | format_routing
# Output: name|display_name|keywords|status|path

# Example output:
# hiivmind-corpus-polars|Polars|polars,dataframe,lazy,expression|built|/path/to/corpus
# hiivmind-corpus-ibis|Ibis|ibis,sql,backend,duckdb|built|/path/to/corpus
```

This builds an in-memory routing table for the session. Keywords come from each corpus's `data/config.yaml`:

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

For large indexes or tiered indexes:

1. **Check for tiered structure**:
   ```bash
   ls {corpus_path}/data/index-*.md 2>/dev/null
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

- Discovery: `skills/hiivmind-corpus-discover/SKILL.md`
- Per-corpus navigate: `templates/navigate-skill.md.template`
- Gateway command: `commands/hiivmind-corpus.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
