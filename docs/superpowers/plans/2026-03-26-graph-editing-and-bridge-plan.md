# Graph Editing & Cross-Corpus Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the hiivmind-corpus skills suite by implementing graph editing subcommands (add-concept, add-relationship) and the cross-corpus bridge skill, then wiring Tier 4 traversal into navigate.

**Architecture:** Extend the existing graph skill SKILL.md with two new subcommand sections, create a new bridge skill SKILL.md, update navigate to load registry-graph.yaml and use it for alias routing and Tier 4 traversal, then clean up deferred markers across all skills.

**Tech Stack:** Claude Code plugin skills (SKILL.md markdown), YAML schemas (graph.yaml, registry-graph.yaml), yq queries, bash

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `skills/hiivmind-corpus-graph/SKILL.md` | Modify | Replace deferred add-concept/add-relationship with full sections |
| `skills/hiivmind-corpus-bridge/SKILL.md` | Create | New skill — cross-corpus bridges and aliases |
| `skills/hiivmind-corpus-navigate/SKILL.md` | Modify | Wire alias routing (Phase 1+2) and Tier 4 (Phase 4c) |
| `commands/hiivmind-corpus.md` | Modify | Remove deferred marker, add menu items |
| `skills/hiivmind-corpus-init/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-add-source/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-build/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-enhance/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-refresh/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-discover/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-register/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `skills/hiivmind-corpus-status/SKILL.md` | Modify | Update bridge deferred → normal reference |
| `CLAUDE.md` | Modify | Add bridge to Key Design Decisions and cross-cutting table |
| `.claude-plugin/plugin.json` | Modify | Version bump 1.1.0 → 1.2.0 |

**Total: 14 files (1 created, 13 modified)**

---

### Task 1: Implement add-concept subcommand in graph skill

**Files:**
- Modify: `skills/hiivmind-corpus-graph/SKILL.md:80-82`

- [ ] **Step 1: Read the current graph SKILL.md**

Read `skills/hiivmind-corpus-graph/SKILL.md` to confirm the exact deferred markers at lines 80-82.

- [ ] **Step 2: Replace the deferred add-concept marker with full section**

Replace lines 80 of `skills/hiivmind-corpus-graph/SKILL.md`:

```
### add-concept (deferred — vertical slice excludes this)
```

With the full add-concept section:

```markdown
### add-concept

Add a new concept to graph.yaml with semi-automated entry suggestion.

**Invocation:** `graph add-concept "Concept Label"` or interactive (no args → prompt for label)

**Procedure:**

1. **Slugify label** to concept ID per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` § Concept ID Conventions:
   ```bash
   slugify() {
     echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//'
   }
   ```
2. **Check for duplicates** — if concept ID already exists in graph.yaml, error:
   "Concept '{id}' already exists. Use a different name or edit the existing concept."
3. **Scan index for matching entries:**
   - Extract 2-4 search terms from the concept label
   - **v2 (index.yaml):** yq pre-filter on tags, keywords, summary fields. If yq unavailable, read index.yaml directly and use LLM judgment.
     ```bash
     yq '.entries[] | select(
       (.tags[] | test("term1|term2"; "i")) or
       (.keywords[] | test("term1|term2"; "i")) or
       (.summary | test("term1.*term2|term2.*term1"; "i"))
     ) | {id, title, summary, tags}' index.yaml
     ```
   - **v1 (index.md):** grep for search terms + LLM semantic judgment
   - Present top 10-15 candidates ranked by relevance
4. **User selects entries** — present numbered list, user confirms/deselects
5. **Suggest tags** — based on selected entries' metadata (if available from index.yaml)
6. **Suggest description** — one-line summary based on selected entries' summaries
7. **Write concept to graph.yaml:**
   ```yaml
   {concept-id}:
     label: "{User-Provided Label}"
     description: "{description}"
     entries:
       - "{source_id}:{path}"
     tags: ["{tag1}", "{tag2}"]
     entry_count: {n}
   ```
8. **Update meta** — increment `concept_count`, recompute `entry_count` (total across all concepts), set `generated_at` to current ISO-8601 timestamp

**Empty graph bootstrap:** If `graph.yaml` doesn't exist, create a new one:

```yaml
schema_version: 1

concepts:
  {concept-id}:
    label: "{label}"
    description: "{description}"
    entries:
      - "{source_id}:{path}"
    tags: []
    entry_count: {n}

relationships: []

meta:
  generated_at: "{ISO-8601}"
  entry_count: {n}
  concept_count: 1
  relationship_count: 0
  sources_extracted: []
```

**Output:** "Added concept '{label}' with {n} entries to graph.yaml"
```

- [ ] **Step 3: Verify the edit**

Read `skills/hiivmind-corpus-graph/SKILL.md` and confirm:
- The `### add-concept` section is properly formatted
- It sits between `### validate` and `### add-relationship`
- The deferred marker is gone

- [ ] **Step 4: Commit**

```bash
git add skills/hiivmind-corpus-graph/SKILL.md
git commit -m "feat(graph): implement add-concept subcommand"
```

---

### Task 2: Implement add-relationship subcommand in graph skill

**Files:**
- Modify: `skills/hiivmind-corpus-graph/SKILL.md:82` (now shifted by the add-concept insertion)

- [ ] **Step 1: Replace the deferred add-relationship marker with full section**

Replace:

```
### add-relationship (deferred — vertical slice excludes this)
```

With the full add-relationship section:

```markdown
### add-relationship

Add a typed relationship between two existing concepts. Supports explicit (args) and interactive (no args) modes.

**Explicit invocation:** `graph add-relationship "{from-concept}" "{to-concept}" {type}`

**Procedure (explicit):**

1. **Validate concept IDs** — both `from` and `to` must exist in graph.yaml. If not:
   "Concept '{id}' not found. Available concepts: {list}"
2. **Validate relationship type** — must be one of the controlled vocabulary:
   `includes`, `depends-on`, `see-also`, `extends`, `contrast-with`
   (see `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` § Relationship Type Vocabulary)
3. **Check for duplicates** — same from/to/type triple already exists:
   "Relationship '{from}' → '{to}' ({type}) already exists."
4. **Optionally ask for evidence** — an entry path that demonstrates the link (can be null)
5. **Write relationship to graph.yaml:**
   ```yaml
   - from: "{from-concept}"
     to: "{to-concept}"
     type: "{type}"
     origin: "manual"
     evidence: null
   ```
6. **Update meta** — increment `relationship_count`, set `generated_at`

**Interactive invocation** (no args):

1. Load graph.yaml, list all concepts
2. Analyze concept pairs for relationship candidates:
   - **Tag overlap:** Concepts sharing 2+ tags → strong candidate
   - **Entry cross-references:** If entries in concept A link to entries in concept B
   - **Label/description keyword similarity:** Fuzzy match on descriptions
3. Present candidates:
   ```
   These concept pairs look related — confirm or skip each:

   1. query-optimization → lazy-frames
      Reason: shared tags [performance, optimization]
      Suggested type: depends-on
      [Confirm / Change type / Skip]

   2. data-types → serialization
      Reason: entries cross-reference each other
      Suggested type: see-also
      [Confirm / Change type / Skip]
   ```
4. For each confirmed pair, write relationship with `origin: "manual"`
5. Summary: "Added {n} relationships to graph.yaml"

**Note:** All relationships added by this subcommand use `origin: "manual"`, which means refresh will preserve them (never overwritten by auto-extraction).
```

- [ ] **Step 2: Verify the edit**

Read `skills/hiivmind-corpus-graph/SKILL.md` and confirm:
- The `### add-relationship` section is properly formatted
- It sits after `### add-concept` and before `## Error Handling`
- The deferred marker is gone
- Both subcommands are now present

- [ ] **Step 3: Commit**

```bash
git add skills/hiivmind-corpus-graph/SKILL.md
git commit -m "feat(graph): implement add-relationship subcommand"
```

---

### Task 3: Create the bridge skill SKILL.md

**Files:**
- Create: `skills/hiivmind-corpus-bridge/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p skills/hiivmind-corpus-bridge
```

- [ ] **Step 2: Write the bridge SKILL.md**

Create `skills/hiivmind-corpus-bridge/SKILL.md` with this content:

```markdown
---
name: hiivmind-corpus-bridge
description: >
  Create and manage cross-corpus concept bridges in registry-graph.yaml. Use when users
  want to link concepts across corpora, create query-routing aliases, or validate
  cross-corpus relationships. Triggers: "bridge", "cross-corpus", "link corpora",
  "registry graph", "alias", "bridge show", "bridge validate", "add alias".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
---

# Cross-Corpus Concept Bridge

Create and manage cross-corpus concept bridges stored in `.hiivmind/corpus/registry-graph.yaml`.
Bridges link concepts that exist in different corpora, and aliases provide query-routing hints
so searches can span multiple corpora.

## Precondition

- `.hiivmind/corpus/registry.yaml` must exist with 2+ registered corpora
- At least 2 registered corpora must have `graph.yaml` files

If prerequisites not met:
- No registry: "No corpus registry found at .hiivmind/corpus/registry.yaml. Register corpora first: `/hiivmind-corpus register`"
- Fewer than 2 corpora: "Bridge requires at least 2 registered corpora. Found: {n}"
- No corpora with graph.yaml: "No registered corpora have concept graphs. Build graphs first with `/hiivmind-corpus graph add-concept` or run build with extraction."

---

## Phase 1: Load Registry + Fetch Graphs

**Inputs:** Project working directory

**Procedure:**

1. Read `.hiivmind/corpus/registry.yaml`
2. For each registered corpus, fetch its `graph.yaml`:
   - Resolve source details from registry entry: `source.repo` (split on `/` for owner/repo) and `source.ref`
   - **GitHub sources:** `gh api repos/{owner}/{repo}/contents/graph.yaml?ref={ref} --jq '.content' | base64 -d`
   - **Local sources:** `Read: {path}/graph.yaml`
   - **Embedded (self) sources:** `Read: .hiivmind/corpus/graph.yaml`
   - Skip corpora without graph.yaml (report which were skipped)
3. Build in-memory map: `corpus_name → { concepts, relationships }`
4. Report: "Loaded graphs from {n} corpora: {names}. Skipped {m}: {names} (no graph.yaml)"

**Pattern references:**
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-loading.md`
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-graph.md`

---

## Phase 2: Execute Subcommand

Determine which subcommand to run based on user intent:

### bridge (default) — Interactive Creation

Detect bridge candidates and present for user confirmation.

**Procedure:**

1. **Detect candidates** using algorithm from `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-graph.md` § Bridge Candidate Detection:
   a. **Label similarity** — concepts with similar labels across corpora (shared words after removing stop words like "the", "and", "of")
   b. **Tag overlap** — concepts sharing tags across corpora
   c. **Keyword overlap** — corpus-level keywords that appear in another corpus's concept labels
2. **Present candidates** grouped by corpus pair:
   ```
   Between Polars and Ibis (3 candidates):

   1. polars:lazy-evaluation ↔ ibis:deferred-execution
      Match: tag overlap [performance, lazy], label similarity
      Suggested type: see-also
      [Confirm / Change type / Skip]

   2. polars:data-types ↔ ibis:type-system
      Match: tag overlap [types, schema]
      Suggested type: see-also
      [Confirm / Change type / Skip]
   ```
3. **Collect notes** — for each confirmed bridge, optionally ask for a note
4. **Suggest aliases** — analyze confirmed bridge pairs for natural search terms:
   ```
   Suggested aliases:
   1. "lazy evaluation" → polars:lazy-evaluation, ibis:deferred-execution
   2. "type system" → polars:data-types, ibis:type-system
   [Confirm each / Skip all]
   ```
5. **Write registry-graph.yaml** (create or update):
   ```yaml
   schema_version: 1

   bridges:
     - concept_a: "polars:lazy-evaluation"
       concept_b: "ibis:deferred-execution"
       type: "see-also"
       note: "Both implement deferred query execution for performance"

   aliases:
     "lazy evaluation":
       - corpus: "polars"
         concept: "lazy-evaluation"
       - corpus: "ibis"
         concept: "deferred-execution"

   meta:
     updated_at: "{ISO-8601}"
     bridge_count: 1
     corpora_linked: ["polars", "ibis"]
   ```
6. **Confirm:** "Created {n} bridges and {m} aliases in registry-graph.yaml"

### show

Display existing bridges and aliases in human-readable format.

**Procedure:**

1. Read `.hiivmind/corpus/registry-graph.yaml`
2. If not found: "No cross-corpus bridges configured. Run `bridge` to create some."
3. Display:
   ```
   Cross-Corpus Bridges ({n}):
     polars:lazy-evaluation ↔ ibis:deferred-execution (see-also)
       "Both implement deferred query execution"
     polars:data-types ↔ ibis:type-system (see-also)

   Aliases ({m}):
     "lazy evaluation" → polars:lazy-evaluation, ibis:deferred-execution
     "type system" → polars:data-types, ibis:type-system

   Linked corpora: polars, ibis
   Last updated: {date}
   ```

### validate

Check registry-graph.yaml for issues.

**Procedure:**

1. Read `.hiivmind/corpus/registry-graph.yaml`
2. Run validation rules from `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-graph.md` § Validation Rules:
   a. **Schema compliance** — all required fields present, correct types
   b. **Corpus resolution** — each `corpus_name` resolves to an installed corpus via registry.yaml
   c. **Concept resolution** — each `concept-id` exists in the referenced corpus's graph.yaml
   d. **Dangling references** — flag bridges where one side's corpus is not installed (warning, not error)
   e. **Relationship type vocabulary** — only controlled types used
   f. **Alias targets** — each alias target resolves to valid corpus + concept
3. Report errors (must fix) and warnings (should review)
4. If clean: "Registry graph validates OK — {n} bridges, {m} aliases, no issues."

### add-alias

Manually add a query-routing alias.

**Invocation:** `bridge add-alias "search term" corpus1:concept1 corpus2:concept2`

**Procedure:**

1. Validate each `corpus:concept` reference resolves (corpus in registry, concept in its graph.yaml)
2. Check if alias key already exists — if so, offer to update:
   "Alias 'search term' already exists. Update it? [Yes / No]"
3. Write alias to registry-graph.yaml:
   ```yaml
   aliases:
     "search term":
       - corpus: "corpus1"
         concept: "concept1"
       - corpus: "corpus2"
         concept: "concept2"
   ```
4. Update `meta.updated_at`
5. Confirm: "Added alias 'search term' → corpus1:concept1, corpus2:concept2"

---

## Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| No registry | "No corpus registry found at .hiivmind/corpus/registry.yaml" | Suggest `/hiivmind-corpus register` |
| Fewer than 2 corpora | "Bridge requires at least 2 registered corpora. Found: {n}" | Suggest registering more |
| No corpora with graph.yaml | "No registered corpora have concept graphs. Build graphs first." | Suggest `/hiivmind-corpus graph add-concept` or build with extraction |
| Invalid registry-graph.yaml | "registry-graph.yaml has syntax errors: {details}" | Show error location |
| Network error fetching graph | "Could not fetch graph.yaml for corpus '{id}': {error}" | Skip that corpus, continue with others |
| Dangling concept reference | "Concept '{id}' not found in corpus '{name}' graph.yaml" | Warning during validate, not blocking |

---

## Pattern Documentation

- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-graph.md` — Registry graph schema, validation rules, bridge detection
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/graph.md` — Per-corpus graph schema (concepts, relationships)
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-loading.md` — Registry loading patterns
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/corpus-routing.md` — Query routing (aliases enhance this)
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/discovery.md` — Corpus location discovery

## Related Skills

- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — Per-corpus concept graph (view, validate, edit)
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-navigate/SKILL.md` — Uses bridges for Tier 4 cross-corpus retrieval
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-register/SKILL.md` — Registers corpora to project registry
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-discover/SKILL.md` — Finds installed corpora
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-status/SKILL.md` — Reports corpus health
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md` — Generates graph.yaml during build
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md` — Updates auto-extracted relationships
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md` — Deepens coverage on topics
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md` — Initializes corpus
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md` — Adds documentation sources
```

- [ ] **Step 3: Verify the file**

Read `skills/hiivmind-corpus-bridge/SKILL.md` and confirm:
- Frontmatter has name, description, allowed-tools
- Phase 1 and Phase 2 structure matches other skills
- All 4 subcommands documented (bridge, show, validate, add-alias)
- Error handling table present
- Related Skills section references all other skills

- [ ] **Step 4: Commit**

```bash
git add skills/hiivmind-corpus-bridge/SKILL.md
git commit -m "feat: create hiivmind-corpus-bridge skill"
```

---

### Task 4: Wire alias routing into navigate Phase 1 + Phase 2

**Files:**
- Modify: `skills/hiivmind-corpus-navigate/SKILL.md:34-70`

- [ ] **Step 1: Read navigate Phase 1 and Phase 2**

Read `skills/hiivmind-corpus-navigate/SKILL.md` lines 34-70 to confirm exact content.

- [ ] **Step 2: Add registry-graph.yaml loading to Phase 1**

In `skills/hiivmind-corpus-navigate/SKILL.md`, after line 41 (the embedded corpora note ending with `...alongside registry entries.`), add:

```markdown

> **Cross-corpus bridges:** Also attempt to load `.hiivmind/corpus/registry-graph.yaml`. If found, extract the `aliases` section for use in Phase 2 routing. If missing or malformed, skip silently — bridges are optional.
```

- [ ] **Step 3: Add alias matching to Phase 2**

In `skills/hiivmind-corpus-navigate/SKILL.md`, after line 64 ("**If corpus not specified:**"), insert a new step before the keyword scoring:

Replace lines 64-70:

```markdown
**If corpus not specified:**
1. Load keywords from each corpus config
2. Score query against keywords
3. If single match → use that corpus
4. If multiple matches → ask user to clarify
5. If no matches → list available corpora
```

With:

```markdown
**If corpus not specified:**
1. **Check aliases** (if registry-graph.yaml was loaded in Phase 1): match query against alias keys (exact or substring). If an alias matches, add its target corpora/concepts to routing candidates.
2. Load keywords from each corpus config
3. Score query against keywords (alias matches count as additional keyword hits)
4. If single match → use that corpus
5. If multiple matches → ask user to clarify
6. If no matches → list available corpora
```

- [ ] **Step 4: Verify the edits**

Read `skills/hiivmind-corpus-navigate/SKILL.md` lines 34-75 and confirm:
- Phase 1 mentions registry-graph.yaml loading
- Phase 2 has the alias check as step 1

- [ ] **Step 5: Commit**

```bash
git add skills/hiivmind-corpus-navigate/SKILL.md
git commit -m "feat(navigate): add alias routing from registry-graph.yaml"
```

---

### Task 5: Wire Tier 4 bridge traversal into navigate Phase 4c

**Files:**
- Modify: `skills/hiivmind-corpus-navigate/SKILL.md:247-267`

- [ ] **Step 1: Read navigate Phase 4c Tier 3 ending and Graceful Degradation**

Read `skills/hiivmind-corpus-navigate/SKILL.md` lines 245-270 to confirm exact content.

- [ ] **Step 2: Replace the deferred Tier 4 note with working traversal**

Replace line 249:

```markdown
   > **Note:** Tier 4 (registry-graph.yaml cross-corpus traversal) is deferred to the generalization pass.
```

With:

```markdown
4. **Tier 4: Cross-corpus bridge traversal**

   Check for cross-corpus bridges via `registry-graph.yaml` (loaded in Phase 1). If not loaded → skip Tier 4.

   For each concept matched in Tiers 2-3, check if it participates in any bridge:

   **v2 mode (yq queries):**
   ```bash
   # Find bridges involving a matched concept
   yq '.bridges[] | select(.concept_a == "{corpus}:{concept}" or .concept_b == "{corpus}:{concept}")' .hiivmind/corpus/registry-graph.yaml
   ```

   **v1 mode:** Read registry-graph.yaml directly and search bridges manually.

   For each bridge match, fetch the bridged concept's entries from the other corpus (using that corpus's source config for path resolution).

   Limits: up to 2 cross-corpus concepts, up to 3 entries per concept.

   Annotate Tier 4 results:
   ```
   **Related (from {other_corpus} corpus via bridge):**
   - [{entry_title}]({entry_path}) — Tier 4: bridged from {source_corpus}:{source_concept}
   ```
```

- [ ] **Step 3: Update the fetch priority section**

In the fetch priority section (currently item 4 in Phase 4c), add Tier 4:

After the line about Tier 3 entries, add:
```markdown
   - **Tier 4** entries: fetch only if query explicitly spans topics covered by multiple corpora
```

- [ ] **Step 4: Add registry-graph.yaml to Graceful Degradation table**

In the Graceful Degradation table (around line 261), add a new row:

```markdown
| No registry-graph.yaml | Skip cross-corpus bridges and aliases |
```

- [ ] **Step 5: Add registry-graph.md to Pattern Documentation section**

In the Pattern Documentation section (around line 399), add:

```markdown
- **Registry graph:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/registry-graph.md`
```

- [ ] **Step 6: Verify all edits**

Read `skills/hiivmind-corpus-navigate/SKILL.md` lines 245-275 and confirm:
- Tier 4 section replaces the deferred note
- Graceful Degradation table has the new row
- Pattern Documentation has registry-graph.md

- [ ] **Step 7: Commit**

```bash
git add skills/hiivmind-corpus-navigate/SKILL.md
git commit -m "feat(navigate): implement Tier 4 cross-corpus bridge traversal"
```

---

### Task 6: Update gateway command

**Files:**
- Modify: `commands/hiivmind-corpus.md:46,64-76,119`

- [ ] **Step 1: Read the gateway command**

Read `commands/hiivmind-corpus.md` to confirm exact content.

- [ ] **Step 2: Remove "(deferred)" from bridge routing row**

In `commands/hiivmind-corpus.md`, replace line 46:

```markdown
| `hiivmind-corpus-bridge` (deferred) | bridge, cross-corpus, link corpora, registry graph, alias | "bridge polars and clickhouse" |
```

With:

```markdown
| `hiivmind-corpus-bridge` | bridge, cross-corpus, link corpora, registry graph, alias | "bridge polars and clickhouse" |
```

- [ ] **Step 3: Add Graph and Bridge to interactive menu**

In the Interactive Menu section, after line 75 (`9. Status — Check corpus health and freshness`), add:

```markdown
10. Graph — View, validate, edit concept graphs
11. Bridge — Cross-corpus concept links and aliases
```

- [ ] **Step 4: Update Available Skills table**

Replace line 119:

```markdown
| `hiivmind-corpus-bridge` | Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented) |
```

With:

```markdown
| `hiivmind-corpus-bridge` | Cross-corpus concept bridges and aliases |
```

- [ ] **Step 5: Verify the edits**

Read `commands/hiivmind-corpus.md` and confirm:
- Routing table has bridge without "(deferred)"
- Menu has 11 items
- Available Skills table has bridge as implemented

- [ ] **Step 6: Commit**

```bash
git add commands/hiivmind-corpus.md
git commit -m "feat(gateway): activate bridge skill routing and menu entry"
```

---

### Task 7: Update deferred markers in all skill files

**Files:**
- Modify: `skills/hiivmind-corpus-init/SKILL.md:352`
- Modify: `skills/hiivmind-corpus-add-source/SKILL.md:331`
- Modify: `skills/hiivmind-corpus-build/SKILL.md:428`
- Modify: `skills/hiivmind-corpus-enhance/SKILL.md:673`
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md:344`
- Modify: `skills/hiivmind-corpus-discover/SKILL.md:384`
- Modify: `skills/hiivmind-corpus-register/SKILL.md:276`
- Modify: `skills/hiivmind-corpus-status/SKILL.md:335`
- Modify: `skills/hiivmind-corpus-navigate/SKILL.md:413`

- [ ] **Step 1: Update all 9 skill files**

In each file listed above, replace:

```markdown
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented)
```

With:

```markdown
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
```

The exact files and their line numbers:

| File | Line |
|------|------|
| `skills/hiivmind-corpus-init/SKILL.md` | 352 |
| `skills/hiivmind-corpus-add-source/SKILL.md` | 331 |
| `skills/hiivmind-corpus-build/SKILL.md` | 428 |
| `skills/hiivmind-corpus-enhance/SKILL.md` | 673 |
| `skills/hiivmind-corpus-refresh/SKILL.md` | 344 |
| `skills/hiivmind-corpus-discover/SKILL.md` | 384 |
| `skills/hiivmind-corpus-register/SKILL.md` | 276 |
| `skills/hiivmind-corpus-status/SKILL.md` | 335 |
| `skills/hiivmind-corpus-navigate/SKILL.md` | 413 |

- [ ] **Step 2: Normalize Related Skills heading in discover and enhance**

In `skills/hiivmind-corpus-discover/SKILL.md` (line 376), replace:

```markdown
**Related skills:**
```

With:

```markdown
## Related Skills
```

In `skills/hiivmind-corpus-enhance/SKILL.md` (line 664), replace:

```markdown
**Related skills:**
```

With:

```markdown
## Related Skills
```

This normalizes the heading format to match all other skills which use `## Related Skills`.

- [ ] **Step 3: Update bridge description in graph skill for consistency**

In `skills/hiivmind-corpus-graph/SKILL.md` (line 107), replace:

```markdown
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus graph overlay
```

With:

```markdown
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
```

- [ ] **Step 4: Verify no deferred markers remain**

```bash
grep -r "deferred — schema defined, skill not yet implemented" skills/ commands/
```

Expected: no output (all markers replaced)

- [ ] **Step 5: Verify consistent bridge descriptions**

```bash
grep -r "hiivmind-corpus-bridge" skills/ --include="*.md" | grep -v "concept bridges and aliases"
```

Expected: no output (all bridge references use consistent description)

- [ ] **Step 6: Commit**

```bash
git add skills/ commands/
git commit -m "chore: remove deferred markers, normalize Related Skills headings, fix bridge descriptions"
```

---

### Task 8: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md:209-280`

- [ ] **Step 1: Read CLAUDE.md Key Design Decisions and cross-cutting table**

Read `CLAUDE.md` lines 209-280 to confirm exact content.

- [ ] **Step 2: Add bridge to Key Design Decisions**

In `CLAUDE.md`, after line 224 (the embedded corpora bullet), add:

```markdown
- **Cross-corpus bridges**: Projects with 2+ registered corpora can create concept bridges in `registry-graph.yaml`, with query-routing aliases — see spec at `docs/superpowers/specs/2026-03-26-graph-editing-and-bridge-design.md`
```

- [ ] **Step 3: Add bridge row to cross-cutting concerns table**

In the cross-cutting concerns table (around line 264), add a new row after the "Embedded corpora" row:

```markdown
| Cross-corpus bridges | bridge, navigate, graph, discover | registry-graph.yaml schema, Tier 4 traversal, alias routing, graph.yaml prerequisite |
```

- [ ] **Step 4: Update Architecture tree to include bridge skill**

In the Architecture section (around line 66), after the graph skill line, add:

```
│   ├── hiivmind-corpus-graph/        # View, validate, edit concept graphs
│   ├── hiivmind-corpus-bridge/       # Cross-corpus concept bridges
```

If graph isn't listed yet, add both. Check the current tree first.

- [ ] **Step 5: Update Naming Convention**

In the Naming Convention section (around line 168-169), ensure bridge is listed. Add to Read skills line:

```markdown
- Read skills: `hiivmind-corpus-discover`, `hiivmind-corpus-navigate`, `hiivmind-corpus-register`, `hiivmind-corpus-status`, `hiivmind-corpus-graph`, `hiivmind-corpus-bridge`
```

- [ ] **Step 6: Verify edits**

Read `CLAUDE.md` and confirm:
- Key Design Decisions includes bridge bullet
- Cross-cutting concerns table includes bridge row
- Architecture tree includes bridge skill
- Naming convention includes bridge

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add cross-corpus bridge to CLAUDE.md design decisions and cross-cutting table"
```

---

### Task 9: Version bump

**Files:**
- Modify: `.claude-plugin/plugin.json:4`

- [ ] **Step 1: Read plugin.json**

Read `.claude-plugin/plugin.json` to confirm current version.

- [ ] **Step 2: Bump version**

In `.claude-plugin/plugin.json`, replace:

```json
"version": "1.1.0",
```

With:

```json
"version": "1.2.0",
```

- [ ] **Step 3: Verify**

Read `.claude-plugin/plugin.json` and confirm version is `1.2.0`.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 1.2.0"
```

---

### Task 10: Final verification

- [ ] **Step 1: Verify no deferred markers remain**

```bash
grep -r "deferred" skills/ commands/ --include="*.md" | grep -i bridge
```

Expected: no output. All bridge-related deferred markers should be gone.

- [ ] **Step 2: Verify the new bridge skill is discoverable**

```bash
ls skills/hiivmind-corpus-bridge/SKILL.md
```

Expected: file exists.

- [ ] **Step 3: Verify graph skill has all 4 subcommands**

```bash
grep "^### " skills/hiivmind-corpus-graph/SKILL.md
```

Expected output should include: `show`, `validate`, `add-concept`, `add-relationship`

- [ ] **Step 4: Verify navigate has Tier 4**

```bash
grep -c "Tier 4" skills/hiivmind-corpus-navigate/SKILL.md
```

Expected: at least 2 occurrences (section header + fetch priority)

- [ ] **Step 5: Verify plugin version**

```bash
grep '"version"' .claude-plugin/plugin.json
```

Expected: `"version": "1.2.0",`

- [ ] **Step 6: Review git log**

```bash
git log --oneline -10
```

Verify all commits are present and well-formed.
