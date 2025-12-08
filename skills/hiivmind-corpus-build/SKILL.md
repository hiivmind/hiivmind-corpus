---
name: hiivmind-corpus-build
description: Analyze documentation and build the initial corpus index collaboratively. Use after running hiivmind-corpus-init.
---

# Corpus Index Builder

Clone the documentation source and build the index collaboratively with the user.

## Prerequisites

Run from within a corpus skill directory (e.g., `hiivmind-corpus-polars/`).

Requires `data/config.yaml` with source configuration:
```yaml
source:
  repo_url: "https://github.com/..."
  branch: "main"
  docs_root: "docs/"
```

## Process

```
1. CLONE  →  2. SCAN  →  3. ASK  →  4. BUILD  →  5. SAVE
```

---

## Step 1: Clone

Read config and clone the source repository:

```bash
# Read repo_url from data/config.yaml
git clone --depth 1 {repo_url} .source
```

Get the current commit SHA:
```bash
cd .source && git rev-parse HEAD
```

---

## Step 2: Scan

Analyze the documentation structure:

```bash
# Count files
find .source/{docs_root} -name "*.md" -o -name "*.mdx" | wc -l

# List top-level directories
ls -la .source/{docs_root}

# Sample some files to understand structure
head -30 .source/{docs_root}/index.md
```

---

## Step 3: Ask

Present findings and ask the user:

1. **Show what you found:**
   - Total file count
   - Top-level sections/directories
   - Doc framework detected (if any)

2. **Ask about their use case:**
   - "What will you primarily use these docs for?"
   - "Which sections are most important for your work?"
   - "Any sections you want to skip entirely?"

3. **Ask about depth:**
   - "Should I include all docs or focus on key topics?"

---

## Step 4: Build

Generate `data/index.md` based on user input:

### Index Format

```markdown
# {Project} Documentation Index

> Source: {repo_url}
> Last updated: {date}
> Commit: {sha}

---

## Section Name
*Brief description*

- **Doc Title** `path/to/file.md` - Description
- **Another Doc** `path/to/another.md`

### Subsection
- **Doc** `path/to/doc.md`
```

### Building Process

1. Start with sections user identified as important
2. For each section, list key documents with paths
3. Add brief descriptions from frontmatter or first paragraph
4. Show draft to user for feedback
5. Iterate until user is satisfied

### Iteration Prompts

- "Which sections should I expand?"
- "Any docs I missed that are important?"
- "Should I trim any sections?"
- "Is the organization clear?"

---

## Step 5: Save

Update `data/config.yaml` with metadata:

```yaml
index:
  last_commit_sha: "{sha}"
  last_indexed_at: "{ISO-8601 timestamp}"
  format: "markdown"
```

Remind user to commit:
```bash
git add data/index.md data/config.yaml
git commit -m "Initialize {project} docs index"
```

---

## Example Session

**User**: "Build the hiivmind-corpus-prisma index"

**Step 1**: Clone `https://github.com/prisma/docs`

**Step 2**:
- Found 450 MDX files
- Sections: getting-started, concepts, guides, reference

**Step 3**:
- User: "I mainly work with Prisma Client and migrations"
- User: "Skip the 'about' and 'support' sections"

**Step 4**:
- Generate index focusing on Client, Migrate, Schema
- User: "Can you add more detail on the Query section?"
- Expand Query subsection
- User: "Perfect"

**Step 5**: Update config, remind to commit

---

## Reference

- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh from upstream: `skills/hiivmind-corpus-refresh/SKILL.md`
