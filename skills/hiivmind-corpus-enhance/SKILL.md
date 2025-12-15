---
name: hiivmind-corpus-enhance
description: Enhance an existing corpus index by adding depth to specific topics. Use when you need more detail on particular areas.
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
- `data/config.yaml` with at least one source configured
- `data/index.md` with real entries (run `hiivmind-corpus-build` first)

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

## Process

```
1. VALIDATE  →  2. READ INDEX  →  3. ASK USER  →  4. EXPLORE  →  5. ENHANCE  →  6. SAVE
```

---

## Step 1: Validate Prerequisites

**See:** `lib/corpus/patterns/config-parsing.md` and `lib/corpus/patterns/status.md`

Before proceeding, verify the corpus is ready for enhancement:

**Check 1: Sources exist**
Read `data/config.yaml` and check the `sources:` array (see `lib/corpus/patterns/config-parsing.md`):
- If `sources:` array is empty → **STOP**: Run `hiivmind-corpus-add-source` to add sources first
- If sources exist → Continue

**Check 2: Index exists**
Read `data/index.md` and check content (see `lib/corpus/patterns/status.md`):
- If only placeholder text ("Run hiivmind-corpus-build...") → **STOP**: Run `hiivmind-corpus-build` first
- If index has real entries → Continue

---

## Step 2: Read Index

**See:** `lib/corpus/patterns/paths.md` for path resolution.

Load the current index to understand existing coverage by reading `data/index.md`.

### Detect Index Structure

Check if this is a **tiered index** (for large corpora):

**Using Claude tools:**
```
Glob: data/index-*.md
```

**Single index:** Only `data/index.md` exists
**Tiered index:** Multiple files like `data/index.md`, `data/index-reference.md`, `data/index-guides.md`

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

**See:** `lib/corpus/patterns/scanning.md` and `lib/corpus/patterns/sources.md`

Search for relevant documentation not yet in the index.

### Identify Target Sources

Based on user's topic, determine which source(s) to explore:
- Specific source if user mentioned it
- All sources if topic is cross-cutting
- Read `data/config.yaml` to see available sources (see `lib/corpus/patterns/config-parsing.md`)

### Search by Source Type

**Git sources** (`.source/{source_id}/`):

Using Claude tools:
```
Glob: .source/{source_id}/{docs_root}/{topic_path}/**/*.md
Grep: {keyword}
  path: .source/{source_id}/{docs_root}
  glob: *.md
  output_mode: files_with_matches
```

If no local clone, use raw GitHub URLs (see `lib/corpus/patterns/paths.md`):
```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{docs_root}/{path}
```

**Local sources** (`data/uploads/{source_id}/`):
```
Glob: data/uploads/{source_id}/**/*.md
Grep: {keyword}
  path: data/uploads/{source_id}
  glob: *.md
```

**Web sources** (`.cache/web/{source_id}/`):
```
Glob: .cache/web/{source_id}/*.md
Grep: {keyword}
  path: .cache/web/{source_id}
```

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

Update `data/index.md` (or target sub-index file) collaboratively:

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

Update target index file(s) with enhancements.

**Do NOT update** `last_commit_sha` in config - that's for `hiivmind-corpus-refresh`.

### For Single Index
```bash
git add data/index.md
git commit -m "Enhance {topic} section in docs index"
```

### For Tiered Index
```bash
# If enhanced main index
git add data/index.md
# If enhanced sub-index
git add data/index-{section}.md
# If both
git add data/index.md data/index-{section}.md

git commit -m "Enhance {topic} section in docs index"
```

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
- `team-standards` (local): Found testing.md in `data/uploads/team-standards/`

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
- Found `data/index.md` with tiered structure
- Found `data/index-actions.md` sub-index linked from main index
- Ask user: "This corpus uses tiered indexing. Do you want to enhance the main index Actions summary, or the detailed `index-actions.md`?"

User: "The detailed actions sub-index"

**Step 3**: Ask user what they need
- User: "I need more coverage of reusable workflows"

**Step 4**: Explore `.source/github/actions/using-workflows/` for reusable workflow docs
- Found 5 additional files not in current index

**Step 5**: Propose additions to `data/index-actions.md`:
```markdown
### Reusable Workflows
- **Creating reusable workflows** `github:actions/using-workflows/reusing-workflows.md` - Build once, use everywhere
- **Calling reusable workflows** `github:actions/using-workflows/calling-reusable-workflows.md` - Using workflows from other repos
- **Workflow inputs and outputs** `github:actions/using-workflows/workflow-inputs-outputs.md` - Passing data between workflows
```

**Step 6**: Save `data/index-actions.md`, remind to commit

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
- `lib/corpus/patterns/sources.md` - Source operations

**Related skills:**
- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
