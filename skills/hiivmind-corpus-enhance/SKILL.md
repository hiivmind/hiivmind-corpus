---
name: hiivmind-corpus-enhance
description: Enhance an existing corpus index by adding depth to specific topics. Use when you need more detail on particular areas.
---

# Corpus Index Enhancement

Expand and deepen specific sections of an existing corpus index.

## Prerequisites

Run from within a corpus skill directory (e.g., `hiivmind-corpus-polars/`).

Requires an initialized index at `data/index.md` (run `hiivmind-corpus-build` first).

**Note:** This skill enhances index *depth*, not *freshness*. Use `hiivmind-corpus-refresh` to sync with upstream changes.

## When to Use

- Initial index was broad but shallow on a topic you now need
- You've started using a feature that needs better coverage
- A section has grown stale in usefulness (not commits)
- You want to add subsections or reorganize a topic

## Process

```
1. READ INDEX  →  2. ASK USER  →  3. EXPLORE  →  4. ENHANCE  →  5. SAVE
```

---

## Step 1: Read Index

Load the current index to understand existing coverage:

```bash
cat data/index.md
```

Identify:
- Current sections and their depth
- Topics with minimal entries
- Areas that could benefit from subsections

---

## Step 2: Ask User

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

---

## Step 3: Explore

Search for relevant documentation not yet in the index.

### If `.source/` exists (local clone):

```bash
# Find docs in the target area
find .source/{docs_root}/{topic_path} -name "*.md" -o -name "*.mdx"

# Search for related content
grep -r "{keyword}" .source/{docs_root} --include="*.md" -l

# Read promising files
head -50 .source/{docs_root}/path/to/file.md
```

### If `.source/` doesn't exist (remote fetch):

Use raw GitHub URLs to explore:
```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
```

### What to Look For

- Files not currently in the index
- Sections within files that deserve separate entries
- Related docs that could be grouped together
- Anchor points (#headings) for specific topics within large files

---

## Step 4: Enhance

Update `data/index.md` collaboratively:

### Enhancement Patterns

**Adding entries to existing section:**
```markdown
## Existing Section
*Current description*

- **Existing Doc** `path/to/doc.md` - Description
- **New Doc** `path/to/new.md` - Added description
- **Another New** `path/to/another.md` - Added description
```

**Adding subsections:**
```markdown
## Existing Section
*Current description*

### New Subsection
- **Doc A** `path/to/a.md` - Description
- **Doc B** `path/to/b.md` - Description

### Another Subsection
- **Doc C** `path/to/c.md` - Description
```

**Adding anchor links for specificity:**
```markdown
- **Large Doc - Topic A** `path/to/large.md#topic-a` - Specific section
- **Large Doc - Topic B** `path/to/large.md#topic-b` - Another section
```

### Iteration

- Show proposed changes to user
- "Does this capture what you need?"
- "Should I go deeper on any of these?"
- "Any docs here that aren't actually useful?"

---

## Step 5: Save

Update `data/index.md` with enhancements.

**Do NOT update** `last_commit_sha` in config - that's for `docs-refresh`.

Remind user to commit:
```bash
git add data/index.md
git commit -m "Enhance {topic} section in docs index"
```

---

## Example Session

**User**: "Enhance the Query Optimization section"

**Step 1**: Read index, find Query Optimization has 3 entries

**Step 2**:
- User: "I'm working on slow queries and need more detail"
- User: "Focus on practical optimization, skip theory"

**Step 3**: Search `.source/docs/` for optimization, performance, explain, indexes
- Found 8 additional relevant files
- Found useful anchors in query-settings.md

**Step 4**: Propose expanded section:
```markdown
## Query Optimization
*Improving query performance*

### Understanding Query Execution
- **EXPLAIN** `sql-reference/explain.md` - Analyze query plans
- **Query Profiling** `operations/profiling.md` - Identify bottlenecks

### Optimization Techniques
- **Indexing Strategies** `guides/indexing.md` - When and how to index
- **Projections** `guides/projections.md` - Materialized aggregations
- **Query Settings** `sql-reference/settings.md#performance` - Runtime tuning

### Common Patterns
- **Filtering Best Practices** `best-practices/filtering.md`
- **Join Optimization** `best-practices/joins.md`
```

User: "Perfect, but add the PREWHERE section too"

**Step 5**: Save, remind to commit

---

## Reference

- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
