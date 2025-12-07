# Documentation Skill Plugin Specification

## Purpose

A reusable pattern for creating Claude Code **plugins** that provide always-current documentation access for any open source project. Each documentation source gets its own plugin repository.

## Scope

- **One plugin per documentation source** (e.g., `clickhouse-docs/` for ClickHouse)
- **Two skills per plugin**: index maintenance + documentation navigation
- **Local clone** of the documentation repo, updated on-demand
- **Structured index** that maps the entire repo with rich metadata

---

## Repository Structure

```
{project}-docs/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest (name, description, version, author)
├── skills/
│   ├── navigate/
│   │   └── SKILL.md          # Navigation skill - finds relevant docs
│   └── maintain/
│       └── SKILL.md          # Index build/update skill
├── data/
│   ├── config.yaml           # Tracks source repo + last indexed commit
│   └── index.yaml            # Structured index of all paths and content
├── .source/                  # Cloned documentation repo (gitignored)
├── .gitignore                # Excludes .source/
└── README.md                 # Plugin documentation
```

---

## Plugin Manifest

```json
// .claude-plugin/plugin.json
{
  "name": "clickhouse-docs",
  "description": "Always-current ClickHouse documentation with indexed navigation",
  "version": "1.0.0",
  "author": {
    "name": "Your Name"
  },
  "repository": "https://github.com/you/clickhouse-docs",
  "keywords": ["clickhouse", "documentation", "database"]
}
```

---

## Configuration Schema

```yaml
# data/config.yaml
source:
  repo_url: "https://github.com/ClickHouse/clickhouse-docs"
  branch: "main"
  docs_root: "docs/"          # Subdirectory containing docs (optional)
  
index:
  last_commit_sha: "abc123..."
  last_indexed_at: "2025-01-15T10:30:00Z"
  
settings:
  include_patterns:
    - "**/*.md"
    - "**/*.mdx"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/CHANGELOG.md"
```

---

## Index Schema

```yaml
# data/index.yaml
version: 1
generated_at: "2025-01-15T10:30:00Z"

# Directory tree (all paths, not just markdown)
tree:
  - path: "docs/"
    type: directory
    children:
      - path: "docs/en/"
        type: directory
        children:
          - path: "docs/en/getting-started/"
            type: directory
          - path: "docs/en/sql-reference/"
            type: directory
            # ... nested structure

# Indexed documentation files (markdown only)
files:
  - path: "docs/en/getting-started/install.md"
    title: "Installation Guide"
    summary: "System requirements, installation methods (Docker, binary, package managers), and initial configuration"
    key_concepts:
      - installation
      - docker
      - system requirements
      - configuration
    sections:
      - "Prerequisites"
      - "Docker Installation"
      - "Binary Installation"
      - "Package Managers"
      - "Post-Installation Setup"
    related_paths:
      - "docs/en/getting-started/quick-start.md"
      - "docs/en/operations/configuration.md"
    
  - path: "docs/en/sql-reference/statements/select.md"
    title: "SELECT Statement"
    summary: "Query syntax, clauses (WHERE, GROUP BY, ORDER BY, LIMIT), joins, subqueries, and query optimization hints"
    key_concepts:
      - SELECT
      - queries
      - joins
      - aggregation
      - filtering
    sections:
      - "Basic Syntax"
      - "WHERE Clause"
      - "JOIN Types"
      - "Aggregation"
      - "Performance Tips"
    related_paths:
      - "docs/en/sql-reference/functions/"
      - "docs/en/sql-reference/statements/create.md"
```

---

## Skill Definitions

### skills/navigate/SKILL.md

```markdown
---
name: navigate-docs
description: Find relevant documentation for coding tasks. Use when working with {project} code, APIs, configuration, or troubleshooting {project} issues.
---

# {Project} Documentation Navigator

Find and retrieve relevant documentation from the {project} docs repository.

## Instructions

1. Read `data/index.yaml` to understand available documentation
2. Match the user's task against `key_concepts`, `summary`, and `sections`
3. Return ranked list of relevant file paths
4. Read content from `.source/{path}` for the most relevant files
5. Synthesize information to answer the user's question

## Index Location

- Index file: `data/index.yaml`
- Documentation source: `.source/` (cloned repo)

## Matching Strategy

1. **Direct concept match**: User mentions a `key_concept` directly
2. **Summary relevance**: Task relates to a file's `summary`
3. **Section search**: Specific question maps to a `section` heading
4. **Related traversal**: Follow `related_paths` for broader context

## Output

- Cite specific documentation sections
- Include file paths for user reference
- Note if documentation is incomplete or unclear
```

---

### skills/maintain/SKILL.md

```markdown
---
name: maintain-docs-index
description: Build and update the documentation index. Use when setting up a new docs plugin, refreshing stale index, or after upstream documentation changes.
---

# Documentation Index Maintenance

Build and maintain the structured index for {project} documentation.

## Commands

- **build**: Full index build from scratch (initial setup or major refresh)
- **update**: Incremental update based on git diff since last indexed commit
- **status**: Report current index state vs upstream

## Instructions

### Status Check

1. Read `data/config.yaml` for `last_commit_sha`
2. Run `git fetch` in `.source/`
3. Compare local SHA with `origin/{branch}`
4. Report: files changed, added, deleted since last index

### Incremental Update

1. Run `git diff --name-status {last_sha}..origin/{branch}` in `.source/`
2. For each changed file:
   - **Added (A)**: Generate full index entry
   - **Modified (M)**: Re-read file, update if structure changed
   - **Deleted (D)**: Remove from index
   - **Renamed (R)**: Update path, preserve metadata
3. Update `data/config.yaml` with new SHA and timestamp
4. Write updated `data/index.yaml`

### Full Build

1. Clone/pull repo to `.source/`
2. Walk directory tree per `settings.include_patterns`
3. For each markdown file:
   - Extract title (first H1 or frontmatter `title`)
   - Generate: summary, key_concepts, sections
   - Identify related files via cross-references
4. Write `data/index.yaml` and update `data/config.yaml`

## Index Entry Generation

For each file, generate:

```yaml
- path: "relative/path/to/file.md"
  title: "Extracted or frontmatter title"
  summary: "2-3 sentence description of content and purpose"
  key_concepts:
    - concept1
    - concept2
  sections:
    - "Section Heading 1"
    - "Section Heading 2"
  related_paths:
    - "path/to/related/file.md"
```

## File Locations

- Config: `data/config.yaml`
- Index: `data/index.yaml`
- Source: `.source/`
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Plugin not standalone skills | Centralised metadata, easier distribution via marketplaces |
| YAML over JSON for data files | More readable, comments allowed, easier hand-editing |
| Separate tree and files in index | Tree gives navigation context; files have rich metadata |
| data/ directory for config/index | Clear separation from skills/, persistent across git |
| Local clone in .source/ | Claude Code has persistence; avoids repeated clone overhead |
| Two skills not one | Separation of concerns; maintenance can run independently |
| Model-invoked skills | Claude decides when to use based on task context |

---

## Installation & Usage

### As a Plugin

```bash
# Add marketplace containing this plugin
/plugin marketplace add your-org/doc-plugins

# Install the plugin
/plugin install clickhouse-docs@your-org

# Restart Claude Code
```

### First-Time Setup

After installing, invoke the maintenance skill:

```
Please build the documentation index for this plugin
```

This will:
1. Clone the source repository to `.source/`
2. Build the full index
3. Write `data/config.yaml` and `data/index.yaml`

### Navigation Usage

The navigate skill is model-invoked. Simply ask questions about the documented project:

```
How do I configure replication in ClickHouse?
```

Claude will automatically use the navigation skill to find relevant documentation.

### Keeping Current

Periodically update the index:

```
Check if the documentation index needs updating
```

---

## Open Questions

1. **Index size limits** - Very large doc repos (e.g., Kubernetes) may need index chunking or hierarchical loading. At what threshold?

2. **Related paths detection** - Automated via link parsing, or LLM-inferred, or manual curation?

3. **Multi-language docs** - Some repos have `/en/`, `/zh/`, etc. Index all or configurable?

4. **Version handling** - Docs often have version branches. Support multiple versions or single branch only?

5. **Marketplace distribution** - Create a central marketplace for doc plugins, or encourage per-project distribution?
