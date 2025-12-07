# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **meta-plugin system** for Claude Code that creates reusable documentation navigation plugins for any open-source project. It provides a workflow to index, maintain, and navigate project documentation through Claude Code skills.

The core value: Instead of relying on training data, web search, or on-demand fetching, this creates persistent human-curated indexes that track upstream changes.

## Architecture

```
├── skills/                     # Three core skills (the meta-plugin)
│   ├── generate-docs-plugin/   # Step 1: Create plugin structure from template
│   ├── docs-init/              # Step 2: Build index collaboratively with user
│   └── docs-maintain/          # Step 3: Check and update stale indexes
│
├── templates/                  # Templates for generating new doc plugins
│
├── docs/                       # Specifications and design docs
│
└── clickhouse-docs/            # Example implementation for ClickHouse
    ├── .claude-plugin/         # Plugin manifest
    ├── skills/navigate/        # "Find ClickHouse documentation..." skill
    ├── data/                   # config.yaml + index.md
    └── .source/                # Local clone of docs (gitignored)
```

## Skill Lifecycle

```
generate-docs-plugin → docs-init → docs-maintain
     (once)              (once)       (periodic)
```

1. **generate-docs-plugin**: Clones target repo, analyzes structure, generates plugin directory
2. **docs-init**: Builds `index.md` collaboratively, focused on user's priorities
3. **docs-maintain**: Checks upstream commits, updates index when stale

## Generated Plugin Structure

Each documentation plugin follows this pattern:

```
{project}-docs/
├── .claude-plugin/plugin.json   # Plugin manifest
├── skills/navigate/SKILL.md     # Project-specific navigation skill
├── data/
│   ├── config.yaml              # Source repo URL, branch, last indexed commit SHA
│   └── index.md                 # Human-readable markdown index
├── .source/                     # Local clone (gitignored)
└── README.md
```

## Key Design Decisions

- **Human-readable indexes**: Simple markdown with headings, not complex schemas
- **Collaborative building**: User guides what's important, not automation
- **Works without local clone**: Falls back to raw GitHub URLs
- **Change tracking**: Stores commit SHA to know when index is stale
- **Per-project skills**: Each doc plugin has its own navigate skill for discoverability

## Index Format

The `index.md` uses markdown headings to organize topics:

```markdown
## Data Modeling
- **Primary Keys** (`docs/guides/creating-tables.md#primary-keys`) - How to choose...
- **Partitioning** (`docs/guides/partitioning.md`) - When and how to partition...

## Integrations
- **Kafka Setup** (`docs/integrations/kafka.md`) - Connecting to Kafka...
```

## Navigation Behavior

When answering questions, the navigate skill:
1. Reads `index.md` to find relevant file paths
2. Fetches from `.source/{path}` (local) or `raw.githubusercontent.com/{path}` (remote)
3. Warns if local clone is newer than last indexed commit
4. Cites file paths and suggests related docs

## Working with Templates

Templates in `templates/` use placeholders like `{{project_name}}`, `{{repo_url}}`, etc. The `generate-docs-plugin` skill fills these based on target repository analysis.
