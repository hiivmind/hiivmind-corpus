---
name: hiivmind-corpus-navigate
description: >
  Navigate and query documentation from registered corpora. Use when users ask documentation
  questions, want to look up API references, or mention keywords matching registered corpora.
  Triggers: documentation, docs, lookup, search corpus, what does, how to, API reference.
  Auto-triggers when query contains keywords from any registered corpus (flyio, polars, etc.).
allowed-tools: Read, Glob, Grep, Bash, WebFetch, AskUserQuestion
---

# Corpus Navigate Skill

Search and retrieve documentation from registered corpora. This skill handles the READ side
of the corpus ecosystem - finding and presenting documentation based on user queries.

## When This Skill Activates

- User asks a question matching corpus keywords (e.g., "how do I deploy to fly.io?")
- User explicitly invokes: `/hiivmind-corpus navigate [corpus] [query]`
- Gateway routes a documentation query to this skill

## Prerequisites

**Registry required:** `.hiivmind/corpus/registry.yaml` must exist with at least one corpus.

If no registry exists:
```
No corpus registry found. Register a corpus first:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

## Workflow

### Phase 1: Load Registry

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-loading.md`

1. Read `.hiivmind/corpus/registry.yaml`
2. Parse registered corpora
3. Build in-memory corpus index

```yaml
# Registry structure
corpora:
  - id: flyio
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main
```

### Phase 2: Route Query to Corpus

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/corpus-routing.md`

**If corpus specified explicitly:**
```
Arguments: "flyio how to deploy"
→ corpus = flyio, query = "how to deploy"
```

**If corpus not specified:**
1. Load keywords from each corpus config
2. Score query against keywords
3. If single match → use that corpus
4. If multiple matches → ask user to clarify
5. If no matches → list available corpora

### Phase 3: Fetch Corpus Index

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-fetching.md`

**From GitHub source (using gh api - preferred):**
```bash
gh api repos/{owner}/{repo}/contents/index.md --jq '.content' | base64 -d

# With subdirectory path:
gh api repos/{owner}/{repo}/contents/{path}/index.md --jq '.content' | base64 -d

# With specific ref:
gh api repos/{owner}/{repo}/contents/index.md?ref={ref} --jq '.content' | base64 -d
```

**Fallback (WebFetch):**
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/{ref}/index.md
prompt: "Return the full markdown content"
```

**From local source:**
```
Read: {source.path}/index.md
```

### Phase 4: Search Index

Search the index for relevant entries:

1. Extract search terms from user query
2. Search index.md for matching entries
3. If tiered index, search relevant sub-index
4. Extract `source:path` references from matches

**Index entry format:**
```markdown
- **Install flyctl** `flyio:flyctl/install.html.markerb` - Description
```

**Search approach:**
- Use Grep with search terms against index content
- Look for entries with backtick-wrapped paths
- Rank by relevance (keyword match > description match)

### Phase 4b: Graph Enrichment

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md`

**Optional** — skip this phase if no `graph.yaml` exists in the same location as `index.md`.

**Check:** After fetching the index, attempt to load `graph.yaml` from the same location (same repo path or local directory). If missing or fetch fails → skip phase, proceed to Phase 5 with only Tier 1 results.

**When graph.yaml exists:**

1. **Load graph.yaml** — parse concepts and relationships

2. **Tier 2: Concept membership**

   For each Tier 1 matched entry (`source_id:path`), find which concepts it belongs to. Collect all other entries in those same concepts as Tier 2 candidates. These are topically related pages that may answer the query from a different angle.

   Limit: up to 5 additional entries per matched concept.

3. **Tier 3: Relationship traversal (1 hop)**

   For each concept matched in Tier 2, follow typed relationships in `graph.yaml` to find related concepts (1 hop only — do not recurse). Add entries from those related concepts as Tier 3 candidates, ranked by relationship type:
   - `includes` / `extends` → high relevance
   - `depends-on` → medium relevance
   - `see-also` / `contrast-with` → lower relevance

   Limit: up to 3 entries per related concept, up to 2 relationship types considered as traversal candidates (1 hop only — do not recurse).

   > **Note:** Tier 4 (registry-graph.yaml cross-corpus traversal) is deferred to the generalization pass.

4. **Fetch priority**

   - **Tier 1** entries: always fetch
   - **Tier 2** entries: fetch if Tier 1 content doesn't fully answer the query
   - **Tier 3** entries: fetch only if the query touches concepts not covered by Tiers 1–2

   Annotate each fetched item with its tier in the presented response for transparency.

### Phase 5: Fetch Documentation

For matched entry `source_id:relative_path`:

1. Read source config from corpus config.yaml:  CRITICAL. You MUST read config.yaml FIRST to resolve source_id: prefixes to actual repository URLs. Never guess repository names.
2. Build gh api command or local path to documentation
3. Fetch content

**From GitHub (using gh api - preferred):**
```bash
# Get source details from config, then fetch:
gh api repos/{source_owner}/{source_repo}/contents/{docs_root}/{path}?ref={branch} --jq '.content' | base64 -d
```

**Fallback (WebFetch):**
```
WebFetch: https://raw.githubusercontent.com/{source_owner}/{source_repo}/{branch}/{docs_root}/{path}
prompt: "Return the documentation content"
```

**From local cache:**
```
Read: .corpus-cache/{corpus_id}/.source/{source_id}/{path}
```

### Phase 6: Present Answer

Format the response with:
- Documentation content
- Source citation
- Related documentation suggestions

```markdown
## {Topic Name}

**Source:** {corpus}:{path}

---

{documentation content}

---

**Related:**
- [Related Topic 1](related-path-1)
- [Related Topic 2](related-path-2)
```

## Clarification Flow

When no exact match is found in the index:

```
I searched for '{terms}' in the {corpus} corpus but didn't find an exact match.

I found these related entries:
- Entry 1
- Entry 2

How would you like to proceed?

1. Rephrase my question
2. Show available sections
3. This topic is missing
```

## Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `{corpus}` | Optional corpus ID | `flyio` |
| `{query}` | Search query | `"postgres configuration"` |

**Usage examples:**
```
/hiivmind-corpus navigate flyio "postgres setup"
/hiivmind-corpus navigate "how to deploy"
"How do I set up Postgres on Fly.io?" (auto-triggers via keywords)
```

## Error Handling

**Registry not found:**
```
No corpus registry found at .hiivmind/corpus/registry.yaml

To register a corpus:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

**Corpus not registered:**
```
Corpus '{corpus}' is not registered.

Available corpora: flyio, polars

Register with: /hiivmind-corpus register github:owner/repo
```

**Index fetch failed:**
```
Could not fetch index for corpus '{corpus}'.

The corpus may be offline or the URL has changed.
Try: /hiivmind-corpus status {corpus}
```

**Document not found:**
```
Document not found: {source}:{path}

The documentation may have moved. Try:
  /hiivmind-corpus refresh {corpus}
```

## Pattern Documentation

- **Graph enrichment:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md`

## Related Skills

- **Register:** `hiivmind-corpus-register` - Add corpora to the registry
- **Status:** `hiivmind-corpus-status` - Check corpus health
- **Discover:** `hiivmind-corpus-discover` - Find available corpora
- **Refresh:** `hiivmind-corpus-refresh` - Update corpus from upstream
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented)
