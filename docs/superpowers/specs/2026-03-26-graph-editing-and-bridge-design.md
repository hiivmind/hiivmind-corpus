# Graph Editing & Cross-Corpus Bridge — Design Spec

## Context

The hiivmind-corpus plugin has 10 implemented skills and 1 deferred skill (`hiivmind-corpus-bridge`). The graph skill (`hiivmind-corpus-graph`) currently supports only `show` and `validate` subcommands — `add-concept` and `add-relationship` are marked as deferred. The bridge skill's schema is fully defined in `lib/corpus/patterns/registry-graph.md` but no SKILL.md exists.

An audit of all skills, patterns, and cross-references confirmed these are the only implementation gaps. All 31 pattern files exist, all 8 source types are documented, and cross-references are consistent (with the bridge consistently marked as deferred across 11 files).

## Goal

Complete the skills suite by:
1. Implementing `add-concept` and `add-relationship` subcommands in the graph skill
2. Creating the `hiivmind-corpus-bridge` skill
3. Wiring Tier 4 cross-corpus traversal into the navigate skill
4. Cleaning up deferred markers and consistency gaps

## Dependency Chain

```
graph add-concept / add-relationship
        │
        │  (corpora need graph.yaml to bridge)
        ▼
hiivmind-corpus-bridge
        │
        │  (bridges enable cross-corpus traversal)
        ▼
navigate Tier 4 integration
```

## Non-Goals

- Outbound bridge hints from individual corpora (YAGNI — project-level bridges only)
- Fully automated graph generation as a standalone operation (build already does this)
- New pattern files (existing `graph.md` and `registry-graph.md` are complete)

---

## Feature 1: Graph Editing Subcommands

### add-concept

**Interaction model:** Semi-automated. User provides concept name, skill suggests entries.

**Workflow:**

1. User invokes: `graph add-concept "Query Optimization"` or interactively
2. Skill loads `graph.yaml` — if missing, offer to create a new empty graph
3. Slugify label to concept ID (`query-optimization`) per conventions in `graph.md`
4. Check concept ID doesn't already exist — if it does, error with suggestion to use a different name
5. Scan the corpus index for entries matching the concept:
   - Extract 2-4 search terms from the concept label
   - **v2 (index.yaml):** yq pre-filter on tags, keywords, summary fields
   - **v1 (index.md):** grep + LLM semantic judgment
   - Present top 10-15 candidates ranked by relevance
6. User selects which entries to include (confirm/deselect from list)
7. Ask for optional tags (suggest based on entry metadata if available)
8. Ask for one-line description (suggest based on selected entries' summaries)
9. Write concept to `graph.yaml`:
   ```yaml
   {concept-id}:
     label: "{User-Provided Label}"
     description: "{description}"
     entries:
       - "{source_id}:{path}"
       - "{source_id}:{path}"
     tags: ["{tag1}", "{tag2}"]
     entry_count: {n}
   ```
10. Update `meta.concept_count` and `meta.generated_at`
11. Confirm: "Added concept '{label}' with {n} entries to graph.yaml"

**Empty graph bootstrap:** If `graph.yaml` doesn't exist and user invokes `add-concept`, create a new graph with schema_version 1, empty relationships, and the first concept. Set `meta.sources_extracted: []` since this is manually curated.

### add-relationship

**Interaction model:** Semi-automated. Explicit or interactive.

**Explicit invocation:**
```
graph add-relationship "query-optimization" "lazy-frames" depends-on
```

1. Validate both concept IDs exist in `graph.yaml`
2. Validate relationship type is in controlled vocabulary (`includes`, `depends-on`, `see-also`, `extends`, `contrast-with`)
3. Check for duplicate (same from/to/type triple)
4. Optionally ask for evidence entry path
5. Write relationship:
   ```yaml
   - from: "query-optimization"
     to: "lazy-frames"
     type: "depends-on"
     origin: "manual"
     evidence: null  # or user-provided path
   ```
6. Update `meta.relationship_count` and `meta.generated_at`

**Interactive invocation** (no args):

1. Load graph.yaml, list all concepts
2. Analyze concept pairs for relationship candidates:
   - **Tag overlap:** Concepts sharing 2+ tags → strong candidate
   - **Entry cross-references:** If entries in concept A contain links to entries in concept B (check via wikilinks or markdown links in index metadata)
   - **Label/description keyword similarity:** Fuzzy match on concept descriptions
3. Present candidates: "These concept pairs look related — confirm or skip each:"
   ```
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

**Note:** All relationships added by this skill use `origin: "manual"`, which means refresh will preserve them (never overwritten by auto-extraction).

---

## Feature 2: Bridge Skill (`hiivmind-corpus-bridge`)

### Overview

New skill at `skills/hiivmind-corpus-bridge/SKILL.md`. Creates and manages cross-corpus concept bridges stored in `.hiivmind/corpus/registry-graph.yaml`.

### Subcommands

| Subcommand | Purpose |
|------------|---------|
| `bridge` (default) | Interactive bridge creation with candidate detection |
| `bridge show` | Display existing bridges and aliases |
| `bridge validate` | Check registry-graph.yaml integrity |
| `bridge add-alias` | Add a query-routing alias manually |

### Prerequisites

- `.hiivmind/corpus/registry.yaml` must exist with 2+ corpora
- At least 2 registered corpora must have `graph.yaml` files
- If not met, report what's missing and suggest next steps

### bridge (default) — Interactive Creation

**Workflow:**

1. **Load registry:** Read `.hiivmind/corpus/registry.yaml` to find registered corpora
2. **Fetch graphs:** For each corpus, fetch its `graph.yaml`:
   - GitHub sources: `gh api repos/{owner}/{repo}/contents/graph.yaml?ref={ref} --jq '.content' | base64 -d`
   - Local sources: `Read: {path}/graph.yaml`
   - Embedded (self) sources: `Read: .hiivmind/corpus/graph.yaml`
   - Skip corpora without graph.yaml (report which were skipped)
3. **Detect candidates** using the algorithm from `registry-graph.md`:
   a. **Label similarity:** Concepts with similar labels across corpora (fuzzy match — shared words after removing stop words)
   b. **Tag overlap:** Concepts sharing tags across corpora
   c. **Keyword overlap:** Corpus-level keywords that appear in another corpus's concept labels
4. **Present candidates** grouped by corpus pair:
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
5. **Collect notes:** For each confirmed bridge, optionally ask for a note explaining why they're related
6. **Suggest aliases:** After bridges confirmed, analyze bridge pairs for natural search terms:
   ```
   Suggested aliases:
   1. "lazy evaluation" → check polars:lazy-evaluation, ibis:deferred-execution
   2. "type system" → check polars:data-types, ibis:type-system
   [Confirm each / Skip all]
   ```
7. **Write registry-graph.yaml:**
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
     updated_at: "2026-03-26T12:00:00Z"
     bridge_count: 1
     corpora_linked: ["polars", "ibis"]
   ```
8. **Confirm:** "Created {n} bridges and {m} aliases in registry-graph.yaml"

### bridge show

Display human-readable summary:
```
Cross-Corpus Bridges (3):
  polars:lazy-evaluation ↔ ibis:deferred-execution (see-also)
    "Both implement deferred query execution"
  polars:data-types ↔ ibis:type-system (see-also)
  polars:io-formats ↔ narwhals:interchange (extends)

Aliases (2):
  "lazy evaluation" → polars:lazy-evaluation, ibis:deferred-execution
  "type system" → polars:data-types, ibis:type-system

Linked corpora: polars, ibis, narwhals
Last updated: 2026-03-26
```

### bridge validate

Run validation rules from `registry-graph.md`:
1. Schema compliance — required fields, correct types
2. Corpus resolution — each corpus_name resolves via registry.yaml
3. Concept resolution — each concept-id exists in the referenced corpus's graph.yaml
4. Dangling references — flag (warning) bridges where corpus is not installed
5. Relationship type vocabulary — controlled types only
6. Alias targets — each resolves to valid corpus + concept

Report errors (must fix) and warnings (review).

### bridge add-alias

Manual alias creation:
```
bridge add-alias "lazy evaluation" polars:lazy-evaluation ibis:deferred-execution
```

1. Validate corpus:concept references resolve
2. Check alias doesn't already exist (offer to update if it does)
3. Write to registry-graph.yaml aliases section
4. Update meta

---

## Feature 3: Navigate Tier 4 Integration

### Current State

Navigate Phase 4c handles graph enrichment with Tiers 1-3. Line 249 of the navigate SKILL.md says:
> **Note:** Tier 4 (registry-graph.yaml cross-corpus traversal) is deferred to the generalization pass.

### Change

Replace the deferred note with working Tier 4:

**Tier 4: Cross-corpus bridge traversal**

After Tier 3 completes (within the same corpus), check for cross-corpus bridges:

1. **Load registry-graph.yaml** from `.hiivmind/corpus/registry-graph.yaml`
   - If missing → skip Tier 4 silently
2. **Check aliases first:** Before corpus routing (Phase 2), check if query matches any alias keys. If so, add the alias target corpora/concepts to the routing candidates.
3. **Bridge traversal:** For each concept matched in Tiers 2-3, check if it participates in any bridge:
   ```bash
   # Find bridges involving a matched concept
   yq '.bridges[] | select(.concept_a == "{corpus}:{concept}" or .concept_b == "{corpus}:{concept}")' registry-graph.yaml
   ```
4. **Cross-corpus fetch:** For each bridge match, fetch the bridged concept's entries from the other corpus (using that corpus's source config for path resolution)
5. **Limits:** Up to 2 cross-corpus concepts, up to 3 entries per concept
6. **Annotation:** Mark Tier 4 results clearly:
   ```
   **Related (from Ibis corpus via bridge):**
   - [Deferred Execution](ibis:concepts/deferred.md) — Tier 4: bridged from polars:lazy-evaluation
   ```

### Graceful Degradation Addition

Add to navigate's degradation table:
| No registry-graph.yaml | Skip cross-corpus bridges and aliases |

---

## Feature 4: Cross-Cutting Updates

### Files Modified

| File | Change |
|------|--------|
| `skills/hiivmind-corpus-graph/SKILL.md` | Replace deferred `add-concept` and `add-relationship` with full sections |
| `skills/hiivmind-corpus-bridge/SKILL.md` | **New file** — full skill definition |
| `skills/hiivmind-corpus-navigate/SKILL.md` | Wire Tier 4, add alias check to Phase 2, update degradation table |
| `commands/hiivmind-corpus.md` | Remove "(deferred)" from bridge row, add to interactive menu and Available Skills table |
| `skills/hiivmind-corpus-discover/SKILL.md` | Add missing Related Skills section |
| `skills/hiivmind-corpus-enhance/SKILL.md` | Add missing Related Skills section |
| All other skill SKILL.md files | Update bridge reference from "(deferred — ...)" to normal reference |
| `CLAUDE.md` | Update Key Design Decisions, cross-cutting concerns table |
| `.claude-plugin/plugin.json` | Version bump `1.1.0` → `1.2.0` |

### No New Pattern Files

Both `graph.md` and `registry-graph.md` already fully define the schemas, algorithms, and validation rules. The skill implementations reference these patterns — no new patterns needed.

### Implementation Order

1. **Graph editing** — `add-concept` and `add-relationship` in existing graph skill
2. **Bridge skill** — new `hiivmind-corpus-bridge/SKILL.md`
3. **Navigate Tier 4** — wire cross-corpus traversal
4. **Cross-cutting cleanup** — deferred markers, Related Skills sections, gateway, CLAUDE.md, version bump
