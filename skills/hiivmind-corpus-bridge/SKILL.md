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
   d. **Embedding similarity** (if `registry-embeddings.lance/` exists and fastembed available):
      - For each concept, run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/search.py .hiivmind/corpus/registry-embeddings.lance/ "{concept.label} {concept.description}" --top-k 5 --json`
      - Filter results to exclude same-corpus matches
      - Concepts from other corpora with score > 0.7 are bridge candidates
      - Merge with candidates from label/tag/keyword matching (deduplicate)
2. **Present candidates** grouped by corpus pair:
   ```
   Between Polars and Ibis (3 candidates):

   1. polars:lazy-evaluation ↔ ibis:deferred-execution
      Match: embedding similarity 0.84, tag overlap [performance, lazy]
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
7. **Generate registry-embeddings.lance/** (if fastembed available):
   - Run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py`
   - If exit 1 and project has 2+ registered corpora:
     Ask: "Cross-corpus semantic routing improves query accuracy for multi-corpus projects. Enable it? Requires: `pip install fastembed lancedb pyyaml` (~260MB)"
   - If fastembed available:
     - For each registered corpus with `graph.yaml`, extract concepts (namespaced as `{corpus_id}:{concept-id}`)
     - Write to temporary `concepts.yaml`:
       ```yaml
       concepts:
         - id: "{corpus_id}:{concept-id}"
           label: "{label}"
           description: "{description}"
           tags: ["{tag1}", "{tag2}"]
       ```
     - Run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py --mode concepts concepts.yaml .hiivmind/corpus/registry-embeddings.lance/`
     - Clean up temporary `concepts.yaml`
     - Display: "Generated cross-corpus embeddings for {n} concepts across {m} corpora"
   - **Gitignore:** Ensure `.hiivmind/corpus/registry-embeddings.lance/` is in the project's `.gitignore`. The bridge skill is the sole owner of this file.

**Regeneration triggers:**
- New corpus registered → rebuild registry-embeddings.lance/
- Any corpus's graph.yaml updated (after build/enhance) → rebuild
- Bridge manually adds/removes concepts → rebuild

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md`

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
- `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md` — Embedding generation for cross-corpus concepts

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
