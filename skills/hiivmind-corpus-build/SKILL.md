---
name: hiivmind-corpus-build
description: Analyze documentation and build the initial corpus index collaboratively. Use after running hiivmind-corpus-init.
---

# Corpus Index Builder

Prepare all sources and build the index collaboratively with the user.

## Prerequisites

Run from within a corpus skill directory (e.g., `hiivmind-corpus-polars/`).

Requires `data/config.yaml` with source configuration:
```yaml
sources:
  - id: "polars"
    type: "git"
    repo_url: "https://github.com/..."
```

## Process

```
1. PREPARE  →  2. SCAN  →  3. ASK  →  4. BUILD  →  5. SAVE
```

---

## Step 1: Prepare Sources

Read config and ensure all sources are available:

```bash
cat data/config.yaml
```

### Prepare Each Source Type

For each source in `sources:` array:

**Git sources:**
```bash
# Check if clone exists
ls .source/{source_id}

# If not, clone
git clone --depth 1 {repo_url} .source/{source_id}

# Get current SHA
cd .source/{source_id} && git rev-parse HEAD
```

**Local sources:**
```bash
# Verify uploads directory exists and has files
ls data/uploads/{source_id}
find data/uploads/{source_id} -name "*.md" -o -name "*.mdx"
```

If directory is empty, notify user to place files there.

**Web sources:**
```bash
# Check cache exists
ls .cache/web/{source_id}
```

If cache is missing, notify user to run `hiivmind-corpus-add-source` to fetch content.

---

## Step 2: Scan All Sources

Analyze each source and present a combined summary to user.

### Scan by Source Type

**Git sources:**
```bash
# Count files
find .source/{source_id}/{docs_root} -name "*.md" -o -name "*.mdx" | wc -l

# List top-level directories
ls -la .source/{source_id}/{docs_root}

# Sample some files
head -30 .source/{source_id}/{docs_root}/index.md
```

**Local sources:**
```bash
# Count files
find data/uploads/{source_id} -name "*.md" -o -name "*.mdx" | wc -l

# List files
ls -la data/uploads/{source_id}
```

**Web sources:**
```bash
# Count cached files
ls .cache/web/{source_id}/*.md | wc -l

# List cached files
ls -la .cache/web/{source_id}
```

### Present Combined Summary

Show user a summary of all sources:

```
Found 3 sources:

1. react (git): 150 doc files
   Location: .source/react/src/content/
   Sections: learn, reference, community

2. team-standards (local): 5 files
   Location: data/uploads/team-standards/
   Files: coding-guidelines.md, pr-process.md, ...

3. kent-testing-blog (web): 3 cached articles
   Location: .cache/web/kent-testing-blog/
   Articles: testing-implementation-details.md, ...
```

### Large Corpus Detection

Calculate total file count across all sources. If **total > 500 files**, flag for segmentation discussion in Step 3.

**Thresholds:**
| Total Files | Recommendation |
|-------------|----------------|
| < 200 | Single index works well |
| 200-500 | Consider segmentation |
| 500-2000 | Recommend segmentation |
| > 2000 | Strongly recommend segmentation |

---

## Step 3: Ask

Present findings and ask the user:

1. **Show what you found:**
   - Summary of all sources (from Step 2)
   - Total file count across sources
   - Key sections per source

2. **Ask about their use case:**
   - "What will you primarily use this corpus for?"
   - "Which sources are most important for your work?"
   - "Within each source, which sections matter most?"
   - "Any sources or sections you want to skip entirely?"

3. **Ask about organization:**
   - "How should I organize the index? By source? By topic across sources?"
   - "Should I include all docs or focus on key topics?"

### Segmentation Discussion (for large corpora)

**If total files > 500**, present segmentation options:

> "This is a large documentation set ({count} files). A single index file would be unwieldy. Let me explain your options:"

**Strategy A: Tiered Index (Recommended for 500+ files)**
```
data/
├── index.md              # Main index with section summaries + links
├── index-reference.md    # Detailed API reference entries
├── index-guides.md       # Detailed guides/tutorials
└── index-concepts.md     # Detailed conceptual docs
```

The main `index.md` contains:
- High-level topic summaries (1-2 sentences each)
- Links to detailed sub-indexes
- Quick reference for common lookups

Sub-indexes contain:
- Full entry listings for their section
- Detailed descriptions and paths

**Strategy B: By Section (Good for 200-500 files)**
```
data/
├── index.md              # Single file, organized by section headers
```

One file, but aggressively curated:
- Only include most-used 20-30% of docs
- Group by workflow (getting started → common tasks → advanced)
- Skip auto-generated API docs (use source directly)

**Strategy C: By Source (Good for multi-source corpora)**
```
data/
├── index.md              # Master index linking to source indexes
├── index-{source1}.md    # Detailed index for source 1
└── index-{source2}.md    # Detailed index for source 2
```

**Ask the user:**
- "Which strategy fits your workflow?"
- "For tiered indexing: what are the main sections you'd want?"
- "Should I prioritize breadth (cover everything lightly) or depth (detailed coverage of key areas)?"

---

## Step 4: Build

Generate `data/index.md` based on user input:

### Index Format (Multi-Source)

All file paths use the format: `{source_id}:{relative_path}`

```markdown
# {Corpus Name} Documentation Index

> Sources: react, team-standards, kent-testing-blog
> Last updated: {date}

---

## React Fundamentals
*Core React concepts from official docs*

- **Hooks Overview** `react:reference/hooks.md` - Introduction to React hooks
- **useEffect** `react:reference/useEffect.md` - Side effects in components

## Team Standards
*Internal team documentation*

- **Coding Guidelines** `local:team-standards/coding-guidelines.md` - Our coding conventions
- **PR Process** `local:team-standards/pr-process.md` - Code review workflow

## Testing Best Practices
*From Kent C. Dodds blog*

- **Testing Implementation Details** `web:kent-testing-blog/testing-implementation-details.md` - Why to avoid
- **Common RTL Mistakes** `web:kent-testing-blog/common-mistakes-rtl.md` - Pitfalls to avoid
```

### Path Format by Source Type

| Source Type | Path Format | Example |
|-------------|-------------|---------|
| git | `{source_id}:{relative_path}` | `react:reference/hooks.md` |
| local | `local:{source_id}/{filename}` | `local:team-standards/guidelines.md` |
| web | `web:{source_id}/{cached_file}` | `web:kent-blog/article.md` |

### Tiered Index Format (for large corpora)

When using Strategy A (tiered), create a main index that links to sub-indexes:

**Main index (`data/index.md`):**
```markdown
# GitHub Documentation Corpus

> 3,200+ documentation files organized by topic
> Last updated: 2025-01-15

## How to Use This Index

This corpus uses a **tiered index** due to its size. Start here for an overview, then drill into sub-indexes for detailed entries.

---

## Quick Reference

Common lookups (full path for direct access):

- **Creating a repository** `github:get-started/quickstart/create-a-repo.md`
- **GitHub Actions workflow syntax** `github:actions/using-workflows/workflow-syntax-for-github-actions.md`
- **REST API authentication** `github:rest/overview/authenticating-to-the-rest-api.md`

---

## Getting Started
*First steps with GitHub - creating accounts, repos, basic workflows*

→ See [index-getting-started.md](index-getting-started.md) for 45 detailed entries

Key topics: Account setup, repository creation, basic Git operations, GitHub Desktop

## Actions & CI/CD
*GitHub Actions workflows, runners, marketplace actions*

→ See [index-actions.md](index-actions.md) for 280 detailed entries

Key topics: Workflow syntax, triggers, runners, secrets, reusable workflows, marketplace

## REST API
*Complete REST API reference*

→ See [index-rest-api.md](index-rest-api.md) for 450 detailed entries

Key topics: Authentication, endpoints by resource, pagination, rate limits

## GraphQL API
*GraphQL schema and queries*

→ See [index-graphql.md](index-graphql.md) for 180 detailed entries

Key topics: Schema exploration, common queries, mutations, pagination
```

**Sub-index (`data/index-actions.md`):**
```markdown
# GitHub Actions - Detailed Index

> Part of the GitHub Documentation Corpus
> Back to [main index](index.md)

---

## Workflow Basics

- **Workflow syntax reference** `github:actions/using-workflows/workflow-syntax-for-github-actions.md` - Complete YAML syntax for workflow files
- **Triggering workflows** `github:actions/using-workflows/triggering-a-workflow.md` - Events that can trigger workflow runs
- **Workflow commands** `github:actions/using-workflows/workflow-commands-for-github-actions.md` - Commands for communication between steps

## Runners

- **About self-hosted runners** `github:actions/hosting-your-own-runners/about-self-hosted-runners.md` - When and why to use your own runners
- **Runner groups** `github:actions/hosting-your-own-runners/managing-access-to-self-hosted-runners-using-groups.md` - Organizing runners for teams
...
```

### Building Process

1. Organize by user preference (by source, by topic, or mixed)
2. For each section, list key documents with source-prefixed paths
3. Add brief descriptions from content
4. **Detect large structured files** and add access hints (see below)
5. Show draft to user for feedback
6. Iterate until user is satisfied

**For tiered indexes (Strategy A):**
1. First, identify the major sections (5-10 top-level categories)
2. Build the main `index.md` with section summaries and links
3. For each section, build a sub-index file (`index-{section}.md`)
4. Include a "Quick Reference" section in main index with 10-20 most common lookups
5. Each sub-index should link back to main index
6. Show main index first, then build sub-indexes one at a time with user feedback

### Detecting Large Structured Files

During scanning, identify files that are too large to read directly:

```bash
# Find files over 1000 lines
find .source/{source_id} -name "*.graphql" -o -name "*.json" -o -name "*.yaml" | xargs wc -l | awk '$1 > 1000'
```

**File types to check:**
- GraphQL schemas (`.graphql`, `.gql`)
- OpenAPI/Swagger specs (`.yaml`, `.json`)
- JSON Schema files
- Large config files
- Any file > 1000 lines

**Mark these in the index with `⚡ GREP`:**

```markdown
- **GraphQL Schema** `graphql-schema:schema.docs.graphql` ⚡ GREP - Complete API schema (70k lines). Search with: `grep -n "^type {TypeName}" ... -A 30`
```

The `⚡ GREP` marker tells the navigator to use Grep instead of Read. Include an example search pattern relevant to the file type.

### Iteration Prompts

- "Which sections should I expand?"
- "Any docs I missed that are important?"
- "Should I reorganize by topic instead of source?"
- "Is the organization clear?"

---

## Step 5: Save

Update `data/config.yaml` with per-source metadata:

For each source that was indexed, update its tracking fields:

**Git sources:**
```yaml
- id: "react"
  type: "git"
  # ... other fields ...
  last_commit_sha: "{current_sha}"
  last_indexed_at: "{ISO-8601 timestamp}"
```

**Local sources:**
```yaml
- id: "team-standards"
  type: "local"
  # ... other fields ...
  files:
    - path: "coding-guidelines.md"
      last_modified: "{file_mtime}"
  last_indexed_at: "{ISO-8601 timestamp}"
```

**Web sources:**
```yaml
- id: "kent-testing-blog"
  type: "web"
  # ... other fields ...
  last_indexed_at: "{ISO-8601 timestamp}"
```

Also update the top-level index metadata:
```yaml
index:
  format: "markdown"
  last_updated_at: "{ISO-8601 timestamp}"
```

Remind user to commit:
```bash
git add data/index.md data/config.yaml
git commit -m "Build {corpus_name} docs index"
```

---

## Example Session

### Single-Source Corpus

**User**: "Build the hiivmind-corpus-prisma index"

**Step 1**: Prepare source `prisma` (git)
- Clone `https://github.com/prisma/docs` to `.source/prisma/`

**Step 2**: Scan
- Found 450 MDX files in `.source/prisma/content/`
- Sections: getting-started, concepts, guides, reference

**Step 3**: Ask
- User: "I mainly work with Prisma Client and migrations"
- User: "Skip the 'about' and 'support' sections"

**Step 4**: Build
- Generate index with `prisma:` prefix on all paths
- User: "Can you add more detail on the Query section?"
- Expand Query subsection
- User: "Perfect"

**Step 5**: Update config with SHA, remind to commit

---

### Multi-Source Corpus

**User**: "Build my fullstack corpus index"

**Step 1**: Prepare all sources
- react (git): Clone to `.source/react/`
- team-standards (local): Verify `data/uploads/team-standards/` has files
- kent-blog (web): Verify `.cache/web/kent-blog/` has cached articles

**Step 2**: Scan
```
Found 3 sources:
1. react (git): 150 files
2. team-standards (local): 5 files
3. kent-blog (web): 3 articles
```

**Step 3**: Ask
- User: "Organize by topic, not by source"
- User: "Focus on hooks, testing, and team standards"

**Step 4**: Build
```markdown
## React Hooks
- **useEffect** `react:reference/useEffect.md` - Side effects
- **Custom Hooks** `react:learn/custom-hooks.md` - Creating reusable hooks

## Testing
- **Testing Implementation Details** `web:kent-blog/testing-impl.md` - Best practices
- **Our Test Guidelines** `local:team-standards/testing.md` - Team conventions

## Team Standards
- **PR Process** `local:team-standards/pr-process.md` - Review workflow
```

**Step 5**: Update per-source metadata, remind to commit

---

## Reference

- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
