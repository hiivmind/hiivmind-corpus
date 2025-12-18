# Corpus Keyword System: Entry-Level Tagging & Corpus-Level Routing

> **Proposal:** Two-level keyword system for corpus navigation - entry-level keywords for operational lookup, and corpus-level keywords for per-session routing.

## Overview

| Level | Purpose | Location | Populated By | Used By |
|-------|---------|----------|--------------|---------|
| **Corpus-level** | Route queries to the correct corpus | `data/config.yaml` per corpus | `init`, `upgrade` | `discover` → `navigate` (global) |
| **Entry-level** | Find specific entries within a corpus | `data/index.md` inline | `enhance` | Per-corpus navigate skill |

---

## Part 1: Entry-Level Keywords (Enhance Skill)

### The Problem

When a corpus is used for **operational lookup** (not just documentation browsing), the LLM needs to find entries using domain-specific vocabulary.

Example: A routing guide says "Milestones → Create → REST" with keywords `milestones, POST, create, title, due_on`. The corpus index needs entries tagged with these keywords so the search works.

Currently, `enhance` supports adding entries, subsections, anchor links, and cross-source grouping - but does NOT guide users to add **searchable keywords**.

### The Solution

Add a new enhancement pattern: **Keyword Tagging**

### Entry Keyword Format

```markdown
- **Entry Title** `source:path.md` - Description
  Keywords: `keyword1`, `keyword2`, `keyword3`
```

### Example - GitHub API Corpus

```markdown
## Milestones

### REST Operations
- **Create Milestone** `rest:repos/milestones.md#create` - Create a new milestone
  Keywords: `milestones`, `POST`, `create`, `title`, `due_on`, `description`

- **Update Milestone** `rest:repos/milestones.md#update` - Modify existing milestone
  Keywords: `milestones`, `PATCH`, `update`, `state`, `due_on`

### GraphQL Operations
- **List Milestones** `schema:schema.graphql` ⚡ GREP `repository.milestones` - Query milestones
  Keywords: `milestones`, `repository`, `query`, `states`, `OPEN`, `CLOSED`
```

### Keyword Selection Principles

| Include | Why |
|---------|-----|
| Domain terms | `milestones`, `issues`, `projects` |
| Operation verbs | `create`, `update`, `delete`, `list`, `query` |
| API-specific names | `createIssue`, `updatePullRequest`, `addProjectV2ItemById` |
| HTTP methods | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| Key parameters | `title`, `state`, `due_on`, `fieldId` |
| Common synonyms | `close`/`closed`, `merge`/`merged` |

**Do NOT include:**
- Actual syntax (endpoints, query structures) - let source docs handle this
- Version-specific details that may become stale
- Implementation details

**Compatibility:** Keyword lines work with all entry types including `⚡ GREP` markers.

### Enhance Skill Updates

**Process remains 6 steps** - keyword tagging integrates into Step 5:

```
1. VALIDATE  →  2. READ INDEX  →  3. ASK USER  →  4. EXPLORE  →  5. ENHANCE  →  6. SAVE
                                                                      ↓
                                                               (includes tagging
                                                                if operational)
```

**Add to Step 3 (Ask User):**

```markdown
4. **Operational keywords?** (if applicable)
   - "Is this corpus paired with a routing guide or decision tree?"
   - "Should entries include searchable keywords?"
   - "What vocabulary does your routing system use?"
```

**Add to Step 5 (Enhance) after "### Iteration":**

```markdown
### Keyword Application (Optional)

If the user indicated this is an operational corpus with keyword requirements:

**Identify Keywords for Each Entry:**
1. Domain (milestones, issues, projects, etc.)
2. Operation (create, update, list, query, etc.)
3. API-specific terms (REST method, GraphQL mutation name, parameters)

**Add Keyword Lines:**
- **Entry Title** `source:path.md` - Description
  Keywords: `keyword1`, `keyword2`, `keyword3`

**Validate Against Routing Guide:**
If user has a routing guide, cross-reference keywords:
- "These are the keywords I've added. Do they match your routing guide?"
- "Are there synonyms or alternative terms users might search?"
```

### Per-Corpus Navigate Template Updates

Add to `templates/navigate-command.md.template` in Step 2 (Search):

```markdown
### Searching Entry Keywords

When searching indexes, also check `Keywords:` lines:

```bash
# Search entry descriptions AND keywords
grep -ri "{term}" data/ --include="*.md"
```

**Priority matching:**
1. **Keyword match** - Term in `Keywords:` line → high confidence
2. **Description match** - Term in entry description → medium confidence
3. **Section match** - Term in section heading → context match

When multiple search terms match an entry's keywords, that entry is a strong candidate.
```

---

## Part 2: Corpus-Level Routing (Per-Session Discovery)

### The Problem

The global `hiivmind-corpus-navigate` skill has a **hardcoded keyword table** (lines 121-132):

```markdown
| Corpus | Keywords |
|--------|----------|
| hiivmind-corpus-polars | polars, dataframe, lazy, expression, series, arrow |
| hiivmind-corpus-ibis | ibis, sql, backend, duckdb, bigquery, postgres |
```

This is wrong for a generic skill. Corpora are installed/uninstalled frequently via marketplaces - routing must be dynamic.

### The Solution: Per-Session Discovery

**Key insight:** Routing metadata lives in each corpus, discovered fresh per session. No global persistence.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SESSION START                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  First docs question (or explicit /hiivmind-corpus)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Global navigate invokes DISCOVER                                        │
│                                                                          │
│  Scans all 4 location types:                                            │
│    • ~/.claude/skills/hiivmind-corpus-*/           (user-level)         │
│    • .claude-plugin/skills/hiivmind-corpus-*/      (repo-local)         │
│    • ~/.claude/plugins/marketplaces/hiivmind-corpus-*/  (single)        │
│    • ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/ (multi)        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  For EACH corpus found, read data/config.yaml:                          │
│                                                                          │
│    project_name: polars                                                  │
│    display_name: Polars                                                  │
│    keywords:              ←── ROUTING METADATA (source of truth)        │
│      - polars                                                            │
│      - dataframe                                                         │
│      - lazy                                                              │
│      - expression                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Build IN-MEMORY routing table for this session                         │
│                                                                          │
│  ┌──────────────────┬────────────────────────────────────┐              │
│  │ Corpus           │ Keywords                           │              │
│  ├──────────────────┼────────────────────────────────────┤              │
│  │ polars           │ polars, dataframe, lazy, expr...   │              │
│  │ ibis             │ ibis, sql, backend, duckdb...      │              │
│  │ narwhals         │ narwhals, agnostic, pandas...      │              │
│  └──────────────────┴────────────────────────────────────┘              │
│                                                                          │
│  (Held in conversation context - not persisted)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Match user query against routing table                                  │
│                                                                          │
│  Query: "How do I filter a dataframe?"                                  │
│                                                                          │
│  Matches:                                                                │
│    • polars (dataframe) ✓                                               │
│    • narwhals (dataframe) ✓                                             │
│    • ibis (no match)                                                     │
│                                                                          │
│  Multiple matches → Check project context or ask user                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Route to selected corpus's per-corpus navigate skill                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why Per-Session Discovery?

| Approach | Problem |
|----------|---------|
| Hardcoded table | Doesn't know about user's installed corpora |
| Global cache file | Gets stale when corpora installed/uninstalled |
| **Per-session discovery** | Always accurate, corpora self-describe |

Corpora come and go as users manage marketplace plugins. The only reliable source of truth is the corpora themselves.

### Config Schema Update

Add optional `keywords` field to `data/config.yaml`:

```yaml
schema_version: 2
project_name: polars
display_name: Polars
keywords:                    # NEW: Corpus-level routing keywords
  - polars
  - dataframe
  - lazy
  - expression
  - series
  - arrow
  - pl                       # Common alias
sources:
  - id: polars
    type: git
    # ...
```

### Keyword Fallback

If a corpus lacks the `keywords` field, infer from name:

```bash
# hiivmind-corpus-polars → polars
echo "$corpus_name" | sed 's/hiivmind-corpus-//'
```

This ensures older corpora still route correctly.

### Discover Skill Updates

The discover skill becomes the **authoritative source** for corpus routing data.

**Update output format** to include keywords:

```yaml
corpora:
  - name: hiivmind-corpus-polars
    display_name: Polars
    type: marketplace-multi
    location: ~/.claude/plugins/marketplaces/hiivmind-corpus-data/hiivmind-corpus-polars
    status: built
    keywords:                    # NEW
      - polars
      - dataframe
      - lazy
    sources: 1
    last_indexed: "2025-12-10"
```

**Add keyword extraction** to discovery process:

```bash
# Extract keywords from config, fall back to name inference
get_corpus_keywords() {
  local corpus_path="$1"
  local config="$corpus_path/data/config.yaml"

  # Try explicit keywords first
  keywords=$(yq -r '.keywords[]' "$config" 2>/dev/null | tr '\n' ',')

  if [[ -z "$keywords" ]]; then
    # Fall back to name inference
    keywords=$(basename "$corpus_path" | sed 's/hiivmind-corpus-//')
  fi

  echo "$keywords"
}
```

### Global Navigate Skill Updates

**Delete the hardcoded table entirely** (lines 121-132).

**Replace with dynamic discovery section:**

```markdown
## Corpus-Level Routing

Route queries to the correct corpus using per-session discovery.

### Step 1: Discover Available Corpora

On first docs question in a session, discover all installed corpora:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"

# Get all corpora with routing metadata
discover_all | format_routing
# Output: name|display_name|keywords|path
```

This builds an in-memory routing table for the session.

### Step 2: Match Query to Corpus

Extract key terms from the user's question and match against corpus keywords:

**Clear match (single corpus):**
- Route directly to that corpus's navigate skill

**Multiple matches:**
- Check project context (CLAUDE.md, dependencies) for hints
- If still ambiguous, ask user:
  > "This question could be answered by multiple corpora:
  > - **Polars** - DataFrame operations
  > - **Narwhals** - DataFrame-agnostic API
  >
  > Which would you like me to check?"

**No match:**
- Inform user no relevant corpus is installed
- Suggest web search or installing a corpus

### Step 3: Route to Per-Corpus Navigate

Once a corpus is selected, delegate to its navigate skill for actual doc fetching.
The per-corpus skill handles index search, source access, and citation.
```

### Context-Aware Routing

When multiple corpora match, use project context as a tiebreaker:

```markdown
### Project Context Signals

1. **Project CLAUDE.md** - Corpus awareness snippets indicate preferred corpus
2. **Dependencies** - pyproject.toml, package.json, go.mod, etc.
3. **Imports in current file** - `import polars as pl` → prefer polars
4. **Conversation history** - Recent corpus usage in this session
```

---

## Cross-Skill Alignment

This feature affects multiple skills:

| Skill | Update Required | Details |
|-------|-----------------|---------|
| `discover` | **Yes** | Add keyword extraction, update output format |
| `navigate` (global) | **Yes** | Delete hardcoded table, add dynamic routing |
| `navigate` (template) | **Yes** | Add entry keyword search |
| `enhance` | **Yes** | New keyword tagging pattern |
| `init` | **Yes** | Prompt for corpus keywords during creation |
| `refresh` | **Yes** | Preserve keyword lines during refresh |
| `upgrade` | **Yes** | Detect missing keywords field, suggest adding |
| `build` | **Optional** | Could support keyword tagging during initial build |

### Init Skill Updates

When creating a new corpus, prompt for routing keywords:

```markdown
**Step N: Corpus Keywords**

"What keywords should route documentation questions to this corpus?"
"These help the global navigator find this corpus when users ask questions."

Suggested based on project name: `{project_name}`
Additional suggestions based on domain: `{inferred_keywords}`

User can accept defaults or customize.
```

### Refresh Behavior

When `hiivmind-corpus-refresh` updates entries:
- **Preserve existing keyword lines** - They are human-curated
- **Flag entries with new content** that might need keyword updates
- **Do NOT auto-generate keywords** - Leave that to `enhance`

### Upgrade Behavior

When `hiivmind-corpus-upgrade` runs:
- **Detect missing `keywords` field** in config.yaml
- **Suggest adding** corpus-level keywords based on name/domain
- **Do NOT retrofit entry keywords** - That's an enhance operation

---

## Example Sessions

### Keyword-Tagged Enhancement (Operational Corpus)

**Context**: User has a GitHub API corpus paired with a routing guide.

**User**: "Enhance the Milestones section with keywords for our routing guide"

**Step 1**: Validate - corpus exists and has entries

**Step 2**: Read index - find Milestones section has 3 entries, no keywords

**Step 3**: Ask user
- "Is this corpus paired with a routing guide?" → "Yes, api-routing.md"
- "Can you show me the milestone keywords from your routing guide?"
- User shares keyword table

**Step 4**: Explore - find 2 more milestone docs not in index

**Step 5**: Enhance with keywords

```markdown
## Milestones
*Query via GraphQL, CRUD via REST*

### REST Operations
- **Create Milestone** `rest:repos/milestones.md#create` - Create new milestone
  Keywords: `milestones`, `POST`, `create`, `title`, `due_on`, `description`

- **Update Milestone** `rest:repos/milestones.md#update` - Modify milestone
  Keywords: `milestones`, `PATCH`, `update`, `state`

### GraphQL Operations
- **List Milestones** `schema:schema.graphql` ⚡ GREP `repository.milestones`
  Keywords: `milestones`, `repository`, `query`, `states`, `OPEN`, `CLOSED`
```

**Step 6**: Save and commit

### Per-Session Corpus Discovery

**User**: "How do I do a lazy join?"

**Global navigate**:
1. First docs question in session → trigger discovery
2. Discover finds 3 corpora: polars, ibis, narwhals
3. Extract keywords from each config.yaml
4. Match "lazy" + "join" → polars has both keywords
5. Route to polars corpus
6. Per-corpus navigate finds the lazy join docs

**User** (later): "What about in Ibis?"

**Global navigate**:
1. Routing table already in memory from earlier discovery
2. User explicitly mentioned "Ibis" → route to ibis corpus
3. Per-corpus navigate searches for join operations

---

## CLAUDE.md Cross-Cutting Table Update

Add to the "Cross-Cutting Concerns" table:

```markdown
| Entry keywords | enhance, refresh, navigate (template) | Keyword line format, search logic, preserve on refresh |
| Corpus keywords | discover, navigate (global), init, upgrade | config.yaml schema, per-session discovery, no persistence |
```

---

## Summary

| Component | Responsibility |
|-----------|----------------|
| `data/config.yaml` | Corpus-level keywords (routing) |
| `data/index.md` | Entry-level keywords (search within corpus) |
| `discover` skill | Extract keywords from all installed corpora |
| `navigate` (global) | Per-session routing table, query matching, disambiguation |
| `navigate` (per-corpus) | Entry keyword search, doc fetching, citation |
| `init` skill | Prompt for corpus keywords during creation |
| `enhance` skill | Add entry keywords to index entries |
| `refresh` skill | Preserve keyword lines |
| `upgrade` skill | Retrofit corpus keywords to older corpora |

**Keywords are the interface contract between user queries and corpus content.**

---

## Implementation Checklist

### Part 1: Entry-Level Keywords
- [ ] Update `hiivmind-corpus-enhance/SKILL.md` with keyword tagging pattern
- [ ] Update `templates/navigate-command.md.template` with entry keyword search
- [ ] Update `hiivmind-corpus-refresh/SKILL.md` to preserve keyword lines

### Part 2: Corpus-Level Routing
- [ ] Add `keywords` field to config.yaml schema
- [ ] Update `hiivmind-corpus-discover/SKILL.md` with keyword extraction
- [ ] Update discover library functions to return keywords
- [ ] Delete hardcoded table from `hiivmind-corpus-navigate/SKILL.md`
- [ ] Add dynamic routing section to `hiivmind-corpus-navigate/SKILL.md`
- [ ] Update `hiivmind-corpus-init/SKILL.md` to prompt for keywords
- [ ] Update `hiivmind-corpus-upgrade/SKILL.md` to suggest adding keywords

### Documentation
- [ ] Update `CLAUDE.md` cross-cutting concerns table
- [ ] Update `lib/corpus/corpus-index.md` with new functions
