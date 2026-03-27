---
name: hiivmind-corpus-enhance
description: >
  This skill should be used when the user asks to "add more detail to corpus", "enhance corpus coverage",
  "expand section in index", "need more depth on [topic]", "corpus is too shallow", "add entries for [topic]",
  or wants deeper coverage of specific topics in an existing corpus. Triggers on "enhance [topic] section",
  "more detail on [feature]", "expand the index", "add depth to corpus", or "hiivmind-corpus enhance".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
inputs:
  - name: topic
    type: string
    required: false
    description: Topic or section to enhance (prompted if not provided)
  - name: corpus_path
    type: string
    required: false
    description: Path to corpus skill directory (defaults to current directory)
outputs:
  - name: updated_index
    type: boolean
    description: Whether index.md (or sub-index) was modified
  - name: entries_added
    type: number
    description: Count of new entries added to the index
---

# Corpus Index Enhancement

Expand and deepen specific sections of an existing corpus index. Can search across all sources or focus on specific ones.

## Prerequisites

Run from within a corpus skill directory. Valid locations:

| Destination Type | Location |
|------------------|----------|
| User-level skill | `~/.claude/skills/{skill-name}/` |
| Repo-local skill | `{repo}/.claude-plugin/skills/{skill-name}/` |
| Single-corpus plugin | `{plugin-root}/` (with `.claude-plugin/plugin.json`) |
| Multi-corpus plugin | `{marketplace}/{plugin-name}/` |

Requires:
- `config.yaml` with at least one source configured
- `index.md` with real entries (run `hiivmind-corpus-build` first)

**Note:** This skill enhances index *depth*, not *freshness*. Use `hiivmind-corpus-refresh` to sync with upstream changes.

## When to Use vs Other Skills

| Situation | Use This Skill? | Instead Use |
|-----------|-----------------|-------------|
| Initial index was shallow on a topic | ✅ Yes | - |
| Need more detail on a feature | ✅ Yes | - |
| Want to reorganize or add subsections | ✅ Yes | - |
| Upstream docs have changed | ❌ No | `hiivmind-corpus-refresh` |
| Want to add a new source (git/local/web) | ❌ No | `hiivmind-corpus-add-source` |
| Corpus has no sources yet | ❌ No | `hiivmind-corpus-add-source` |
| First-time index building | ❌ No | `hiivmind-corpus-build` |

## State Flow

```
Step 1              Step 2                Step 3             Step 4               Step 5              Step 6
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
computed.sources -> computed.index     -> computed.topic  -> computed.findings -> computed.proposed -> computed
computed.config     computed.index_type   computed.goal      computed.sources     _changes             .entries
                    computed.sections     computed.depth      _searched           computed              _added
                                          computed.keywords  computed.new_docs    .keywords_applied
```

## Process

```
1. VALIDATE  →  2. READ INDEX  →  3. ASK USER  →  4. EXPLORE  →  5. ENHANCE  →  6. SAVE
```

---

## Step 1: Validate Prerequisites

**Inputs:** invocation args (topic, corpus_path)
**Outputs:** `computed.config`, `computed.sources`
**See:** `lib/corpus/patterns/config-parsing.md` and `lib/corpus/patterns/status.md`

Before proceeding, verify the corpus is ready for enhancement:

```pseudocode
VALIDATE_PREREQUISITES():
  computed.config = Read("config.yaml")
  IF computed.config IS error:
    DISPLAY "No config.yaml found. Are you in a corpus skill directory?"
    DISPLAY "Valid locations: ~/.claude/skills/{name}/, {repo}/.claude-plugin/skills/{name}/"
    EXIT

  computed.sources = extract_sources(computed.config)
  IF len(computed.sources) == 0:
    DISPLAY "No sources configured. Run hiivmind-corpus-add-source first."
    EXIT

  index_content = Read("index.md")
  IF index_content IS error:
    DISPLAY "No index.md found. Run hiivmind-corpus-build first."
    EXIT
  IF index_content matches /Run hiivmind-corpus-build/:
    DISPLAY "Index is a placeholder. Run hiivmind-corpus-build first."
    EXIT

  computed.index_raw = index_content
```

---

## Step 2: Read Index

**Inputs:** `computed.index_raw` (from Step 1)
**Outputs:** `computed.index`, `computed.index_type`, `computed.sections`
**See:** `lib/corpus/patterns/paths.md` for path resolution.

```pseudocode
GUARD_STEP_2():
  IF computed.index_raw IS null:
    DISPLAY "Cannot proceed: Step 1 (Validate) has not completed."
    EXIT
```

Load the current index to understand existing coverage.

```pseudocode
DETECT_INDEX_STRUCTURE():
  sub_indexes = Glob("index-*.md")
  IF sub_indexes IS error:
    DISPLAY "Failed to scan for sub-index files: " + sub_indexes.message
    # Non-fatal — assume single index
    sub_indexes = []

  IF len(sub_indexes) > 0:
    computed.index_type = "tiered"
    computed.sub_indexes = sub_indexes
    # Ask user which index to target
  ELSE:
    computed.index_type = "single"
    computed.sub_indexes = []

  computed.index = computed.index_raw
  computed.sections = extract_sections(computed.index)
```

### Detect Index Structure

**Single index:** Only `index.md` exists
**Tiered index:** Multiple files like `index.md`, `index-reference.md`, `index-guides.md`

For tiered indexes:
- Main `index.md` contains section summaries and links to sub-indexes
- Sub-indexes contain detailed entries for each section
- User may want to enhance main index OR a specific sub-index

Ask user: "This corpus uses tiered indexing. Do you want to enhance the main index overview, or a specific section like `index-reference.md`?"

### Identify Enhancement Opportunities

- Current sections and their depth
- Topics with minimal entries
- Areas that could benefit from subsections
- Sections that link to sub-indexes (tiered only)

---

## Step 3: Ask User

**Inputs:** `computed.sections`, `computed.index_type` (from Step 2)
**Outputs:** `computed.topic`, `computed.goal`, `computed.depth`, `computed.keywords`

```pseudocode
GUARD_STEP_3():
  IF computed.sections IS null:
    DISPLAY "Cannot proceed: Step 2 (Read Index) has not completed."
    EXIT
```

Present the current structure and ask:

1. **Which topic to enhance?**
   - "Which section would you like to expand?"
   - "Is there a specific feature or concept you need more detail on?"

2. **What's the goal?**
   - "What are you trying to accomplish with this topic?"
   - "Any specific questions you want the index to help answer?"

3. **Desired depth?**
   - "Should I find all related docs, or focus on the essentials?"
   - "Do you want subsections, or just more entries?"

4. **Operational keywords?** (if applicable)
   - "Is this corpus paired with a routing guide or decision tree?"
   - "Should entries include searchable keywords for operational lookup?"
   - "What vocabulary does your routing system use?"

   If the user has a routing guide, ask to see the keyword vocabulary.

---

## Step 4: Explore

**Inputs:** `computed.topic`, `computed.goal`, `computed.sources` (from Steps 1, 3)
**Outputs:** `computed.findings`, `computed.sources_searched`, `computed.new_docs`
**See:** `lib/corpus/patterns/scanning.md` and `lib/corpus/patterns/sources/README.md`

```pseudocode
GUARD_STEP_4():
  IF computed.topic IS null:
    DISPLAY "Cannot proceed: Step 3 (Ask User) has not completed."
    EXIT
  IF computed.sources IS null OR len(computed.sources) == 0:
    DISPLAY "Cannot proceed: no sources available."
    EXIT
```

Search for relevant documentation not yet in the index.

### Identify Target Sources

```pseudocode
IDENTIFY_TARGETS():
  computed.sources_searched = []
  computed.findings = []
  computed.new_docs = []

  IF user specified a source name:
    targets = [s for s in computed.sources if s.id == user_source]
    IF len(targets) == 0:
      DISPLAY "Source '" + user_source + "' not found in config.yaml."
      DISPLAY "Available sources: " + join(s.id for s in computed.sources, ", ")
      EXIT
  ELSE:
    targets = computed.sources  # search all
```

### Search by Source Type

```pseudocode
SEARCH_SOURCES(targets, topic):
  FOR source IN targets:
    computed.sources_searched.append(source.id)

    SWITCH source.type:
      CASE "git":
        base = ".source/" + source.id + "/" + source.docs_root
        results = Glob(base + "/**/*.md")
        IF results IS error:
          DISPLAY "Warning: could not scan " + base + " — " + results.message
          CONTINUE
        keyword_hits = Grep(topic, path=base, glob="*.md", output_mode="files_with_matches")

      CASE "local":
        base = "uploads/" + source.id
        results = Glob(base + "/**/*.md")
        keyword_hits = Grep(topic, path=base, glob="*.md", output_mode="files_with_matches")

      CASE "web":
        base = ".cache/web/" + source.id
        results = Glob(base + "/*.md")
        keyword_hits = Grep(topic, path=base, glob="*.md", output_mode="files_with_matches")

      CASE "self":
        repo_root = Bash("git rev-parse --show-toplevel").strip()
        docs_root = source.docs_root
        IF docs_root == ".": docs_root = ""
        base = repo_root + ("/" + docs_root IF docs_root ELSE "")
        results = Glob(base + "/**/*.md", exclude=".hiivmind/**")
        keyword_hits = Grep(topic, path=base, glob="*.md", output_mode="files_with_matches")

    # Filter to docs not already in the index
    FOR hit IN keyword_hits:
      entry_path = source.id + ":" + relative_path(hit, base)
      IF entry_path NOT IN computed.index:
        computed.new_docs.append({
          source: source.id,
          source_type: source.type,
          path: entry_path,
          file: hit
        })

    computed.findings.append({
      source: source.id,
      type: source.type,
      total_files: len(results),
      keyword_hits: len(keyword_hits),
      new_docs: len([d for d in computed.new_docs if d.source == source.id])
    })
```

**Git sources** (`.source/{source_id}/`):

If no local clone, use raw GitHub URLs (see `lib/corpus/patterns/paths.md`):
```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{docs_root}/{path}
```

**Local sources** (`uploads/{source_id}/`)

**Web sources** (`.cache/web/{source_id}/`)

### Cross-Source Discovery

If the topic spans multiple sources, search all and group findings by source:

```
Found related content in 2 sources:

react (git):
- src/content/reference/useCallback.md
- src/content/learn/you-might-not-need-an-effect.md

kent-testing-blog (web):
- testing-implementation-details.md (discusses React testing patterns)
```

### What to Look For

- Files not currently in the index
- Sections within files that deserve separate entries
- Related docs that could be grouped together
- Anchor points (#headings) for specific topics within large files
- Cross-source connections (e.g., blog post explaining library feature)
- **Large structured files** that need special handling (see below)

### Detecting Large Structured Files

**See:** `lib/corpus/patterns/scanning.md` for large file detection.

When enhancing, check if any discovered files are too large to read (>1000 lines).

**If file > 1000 lines**, mark it with `⚡ GREP` in the index:

```markdown
- **OpenAPI Spec** `api-docs:openapi.yaml` ⚡ GREP - Full API spec (5k lines). Search with: `grep -n "/users" ... -A 20`
```

Common patterns for large file types:

| File Type | Search Pattern |
|-----------|----------------|
| GraphQL | `grep -n "^type {Name}" file -A 30` |
| OpenAPI | `grep -n "/{path}" file -A 20` |
| JSON Schema | `grep -n '"{property}"' file -A 10` |

---

## Step 5: Enhance

**Inputs:** `computed.new_docs`, `computed.findings`, `computed.topic` (from Steps 3, 4)
**Outputs:** `computed.proposed_changes`, `computed.keywords_applied`

```pseudocode
GUARD_STEP_5():
  IF computed.new_docs IS null OR computed.findings IS null:
    DISPLAY "Cannot proceed: Step 4 (Explore) has not completed."
    EXIT

  IF len(computed.new_docs) == 0:
    DISPLAY "No new documentation found for topic '" + computed.topic + "'."
    DISPLAY "All relevant docs are already in the index, or try different search terms."
    EXIT

  computed.proposed_changes = []
  computed.keywords_applied = false
```

Update `index.md` (or target sub-index file) collaboratively:

### Enhancement Patterns

All paths use the format: `{source_id}:{relative_path}`

**Adding entries to existing section:**
```markdown
## Existing Section
*Current description*

- **Existing Doc** `react:reference/hooks.md` - Description
- **New Doc** `react:reference/useCallback.md` - Added description
- **Blog Post** `web:kent-blog/you-might-not-need-effect.md` - External perspective
```

**Adding subsections:**
```markdown
## React Hooks
*Hook patterns and usage*

### Core Hooks
- **useState** `react:reference/useState.md` - State management
- **useEffect** `react:reference/useEffect.md` - Side effects

### Performance Hooks
- **useMemo** `react:reference/useMemo.md` - Memoized values
- **useCallback** `react:reference/useCallback.md` - Memoized callbacks
```

**Adding anchor links for specificity:**
```markdown
- **Settings - Performance** `polars:reference/settings.md#performance` - Runtime tuning
- **Settings - Memory** `polars:reference/settings.md#memory` - Memory configuration
```

**Cross-source topic grouping:**
```markdown
## Testing Best Practices
*Combined from official docs and blog posts*

- **Testing Overview** `react:learn/testing.md` - Official testing guide
- **Implementation Details** `web:kent-blog/testing-implementation-details.md` - What not to test
- **Our Testing Standards** `local:team-standards/testing.md` - Team conventions
```

### Iteration

- Show proposed changes to user
- "Does this capture what you need?"
- "Should I go deeper on any of these?"
- "Any docs here that aren't actually useful?"
- "Should I group these by source or by subtopic?"

### Keyword Application (Optional)

If the user indicated this is an operational corpus with keyword requirements:

**Entry Keyword Format:**
```markdown
- **Entry Title** `source:path.md` - Description
  Keywords: `keyword1`, `keyword2`, `keyword3`
```

**Identify Keywords for Each Entry:**
1. **Domain terms** - milestones, issues, projects, etc.
2. **Operation verbs** - create, update, delete, list, query
3. **API-specific terms** - REST method, GraphQL mutation name, parameters
4. **Common synonyms** - close/closed, merge/merged

**Example with Keywords:**
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

**Validate Against Routing Guide:**
If user has a routing guide, cross-reference keywords:
- "These are the keywords I've added. Do they match your routing guide?"
- "Are there synonyms or alternative terms users might search?"

**Keywords work with all entry types** including `⚡ GREP` markers.

---

## Step 6: Save

**Inputs:** `computed.proposed_changes`, `computed.index_type`, `computed.topic` (from Steps 3, 5)
**Outputs:** `computed.entries_added`

```pseudocode
GUARD_STEP_6():
  IF computed.proposed_changes IS null OR len(computed.proposed_changes) == 0:
    DISPLAY "Cannot proceed: Step 5 (Enhance) produced no changes."
    EXIT

SAVE_INDEX():
  # Apply changes via Edit tool
  FOR change IN computed.proposed_changes:
    result = Edit(change.file, old_string=change.old, new_string=change.new)
    IF result IS error:
      DISPLAY "Failed to apply change to " + change.file + ": " + result.message
      DISPLAY "You may need to apply this change manually."
      CONTINUE

  computed.entries_added = count_new_entries(computed.proposed_changes)

  # Stage appropriate files
  IF computed.index_type == "tiered":
    DISPLAY "Updated files: index.md and/or index-{section}.md"
  ELSE:
    DISPLAY "Updated file: index.md"
```

Update target index file(s) with enhancements.

**Do NOT update** `last_commit_sha` in config - that's for `hiivmind-corpus-refresh`.

### For Single Index
```bash
git add index.md
git commit -m "Enhance {topic} section in docs index"
```

### For Tiered Index
```bash
# If enhanced main index
git add index.md
# If enhanced sub-index
git add index-{section}.md
# If both
git add index.md index-{section}.md

git commit -m "Enhance {topic} section in docs index"
```

### Embedding Update

After saving updated index.yaml:

1. If `embeddings.db` exists in corpus root:
   - Run: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml embeddings.db`
   - (Incremental — only re-embeds changed/new entries)
   - Display: "Updated embeddings for {n} modified entries"

2. If `embeddings.db` does not exist:
   - Check heuristic: entry_count > 150 OR tiered indexes exist
   - If met: prompt user with same opt-in question as build Phase 5c
   - See `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/embeddings.md` § Heuristic for Opt-in

---

## Next Steps Guidance

After enhancement, suggest appropriate next actions:

| Situation | Recommend |
|-----------|-----------|
| User mentions wanting to add new docs from a different repo | `hiivmind-corpus-add-source` |
| User asks about upstream changes | `hiivmind-corpus-refresh` |
| Enhanced section now feels too large | Consider tiered indexing (see `hiivmind-corpus-build`) |
| Index is still shallow in other areas | Run `hiivmind-corpus-enhance` again on those sections |

---

## Example Sessions

### Single-Source Enhancement

**User**: "Enhance the Query Optimization section"

**Step 1**: Validate - config is schema_version 2, sources exist, index has entries
**Step 2**: Read index, find Query Optimization has 3 entries (all from `polars` source)

**Step 3**:
- User: "I'm working on slow queries and need more detail"
- User: "Focus on practical optimization, skip theory"

**Step 4**: Search `.source/polars/docs/` for optimization, performance, explain
- Found 8 additional relevant files
- Found useful anchors in settings.md

**Step 5**: Propose expanded section:
```markdown
## Query Optimization
*Improving query performance*

### Understanding Query Execution
- **EXPLAIN** `polars:sql-reference/explain.md` - Analyze query plans
- **Query Profiling** `polars:operations/profiling.md` - Identify bottlenecks

### Optimization Techniques
- **Indexing Strategies** `polars:guides/indexing.md` - When and how to index
- **Query Settings** `polars:sql-reference/settings.md#performance` - Runtime tuning

### Common Patterns
- **Filtering Best Practices** `polars:best-practices/filtering.md`
```

User: "Perfect"

**Step 6**: Save, remind to commit

---

### Cross-Source Enhancement

**User**: "Enhance the Testing section with more depth"

**Step 1**: Validate - config is schema_version 2, sources exist, index has entries
**Step 2**: Read index, find Testing section has entries from `react` source only

**Step 3**:
- User: "I want to include the Kent C. Dodds blog posts too"
- User: "Focus on practical patterns"

**Step 4**: Search across sources:
- `react` (git): Found 3 testing docs in `.source/react/src/content/learn/`
- `kent-testing-blog` (web): Found 3 cached articles in `.cache/web/kent-testing-blog/`
- `team-standards` (local): Found testing.md in `uploads/team-standards/`

**Step 5**: Propose cross-source section:
```markdown
## Testing Best Practices
*Comprehensive testing guidance from multiple sources*

### Official React Testing
- **Testing Overview** `react:learn/testing.md` - Official guide
- **React Testing Library** `react:learn/testing-library.md` - Recommended tools

### Expert Insights
- **Implementation Details** `web:kent-testing-blog/testing-implementation-details.md` - What not to test
- **Common Mistakes** `web:kent-testing-blog/common-rtl-mistakes.md` - Pitfalls to avoid

### Team Standards
- **Our Testing Guidelines** `local:team-standards/testing.md` - Team conventions
```

User: "Great, but can you add a subsection for mocking?"

**Step 6**: Save, remind to commit

---

### Tiered Index Enhancement

**User**: "Enhance the Actions section of my GitHub docs corpus"

**Step 1**: Validate prerequisites - all pass
**Step 2**: Read index
- Found `index.md` with tiered structure
- Found `index-actions.md` sub-index linked from main index
- Ask user: "This corpus uses tiered indexing. Do you want to enhance the main index Actions summary, or the detailed `index-actions.md`?"

User: "The detailed actions sub-index"

**Step 3**: Ask user what they need
- User: "I need more coverage of reusable workflows"

**Step 4**: Explore `.source/github/actions/using-workflows/` for reusable workflow docs
- Found 5 additional files not in current index

**Step 5**: Propose additions to `index-actions.md`:
```markdown
### Reusable Workflows
- **Creating reusable workflows** `github:actions/using-workflows/reusing-workflows.md` - Build once, use everywhere
- **Calling reusable workflows** `github:actions/using-workflows/calling-reusable-workflows.md` - Using workflows from other repos
- **Workflow inputs and outputs** `github:actions/using-workflows/workflow-inputs-outputs.md` - Passing data between workflows
```

**Step 6**: Save `index-actions.md`, remind to commit

---

### Blocked: No Sources Configured

**User**: "Enhance the API section"

**Step 1**: Validate prerequisites
- Read config: `sources:` array is empty

**Response**: "This corpus doesn't have any sources configured yet. You need to add documentation sources before enhancement is possible.

**Recommended next step:** Run `hiivmind-corpus-add-source` to add a git repo, local files, or web pages."

---

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/tool-detection.md` - Detect available tools
- `lib/corpus/patterns/config-parsing.md` - YAML config extraction
- `lib/corpus/patterns/status.md` - Index status checking
- `lib/corpus/patterns/paths.md` - Path resolution
- `lib/corpus/patterns/scanning.md` - File discovery and analysis
- `lib/corpus/patterns/sources/` - Source type operations (git, local, web, generated-docs, self)
- `lib/corpus/patterns/embeddings.md` - Embedding generation, detection, search, heuristics

## Related Skills

- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
