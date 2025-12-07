# Documentation Navigation Skills

Claude Code skills for indexing and navigating open source project documentation.

## Overview

This plugin provides skills to:
- Generate documentation plugins for any open source project
- Build collaborative, human-readable indexes
- Keep indexes in sync with upstream changes
- Navigate docs with or without a local clone

## Why use this?

### The problem with default documentation lookup

Without structured indexing, Claude investigates libraries by:

1. **Relying on training data** - May be outdated or incomplete
2. **Web searching** - Hit-or-miss, often finds outdated tutorials
3. **Fetching URLs on demand** - One page at a time, no context
4. **Reading installed packages** - Limited to code, not prose docs

**This means:**
- Rediscovering the same things every session
- No memory of what's relevant to *your* work
- Search results aren't curated
- Large doc sites are hard to navigate systematically
- Training cutoff means stale knowledge for fast-moving projects

### What this skill suite provides

| Capability | Benefit |
|------------|---------|
| **Curated index** | Built collaboratively around your actual use case |
| **Persistent** | Committed to repo, survives across sessions |
| **Current** | Tracks upstream commits, knows when it's stale |
| **Structured** | Systematically find relevant sections |
| **Flexible** | Works with local clone or remote fetch |

### When to use this vs. default lookup

**Use this skill suite when:**
- Documentation is large (100+ pages)
- You have specific, recurring needs (not one-off questions)
- Docs change frequently
- Official docs are the authoritative source

**Default lookup is fine when:**
- Quick one-off question
- Small library with simple docs
- Just need a code snippet
- Docs are stable and well-known

### The real win

The collaborative index building. Rather than Claude guessing what matters, you tell it: "I care about data modeling and ETL, skip the deployment stuff." That context persists across sessions.

## Structure

```
.
├── .claude-plugin/
│   └── plugin.json              # Root plugin manifest
├── skills/
│   ├── generate-docs-plugin/    # Create new doc plugins
│   ├── docs-init/               # Initialize index collaboratively
│   └── docs-maintain/           # Check status, update index
├── templates/                   # Templates for generated plugins
├── docs/                        # Specifications
└── clickhouse-docs/             # Example implementation
    ├── .claude-plugin/
    ├── skills/navigate/         # Per-project navigation skill
    └── data/
        ├── config.yaml          # Source metadata
        └── index.md             # Human-readable index
```

## Workflow

```
generate-docs-plugin  →  docs-init  →  docs-maintain
     (structure)         (index)       (updates)
```

| Skill | When | What |
|-------|------|------|
| `generate-docs-plugin` | Once per project | Creates folder structure, config, navigate skill |
| `docs-init` | Once per documentation source | Clones repo, builds index collaboratively with user |
| `docs-maintain` | Ongoing | Checks upstream, updates index when needed |

## Usage

### Create a new documentation plugin

```
"Create a docs plugin for Prisma"
```

This will:
1. Clone the docs repo temporarily
2. Analyze structure (framework, file types, organization)
3. Generate `prisma-docs/` with config and navigate skill

### Initialize the index

```
"Initialize the prisma-docs index"
```

This will:
1. Clone source to `.source/`
2. Scan and present the structure
3. Ask about your use case and priorities
4. Build `index.md` collaboratively
5. Save commit SHA for change tracking

### Navigate documentation

```
"How do I set up Prisma migrations?"
```

The per-project navigate skill will:
1. Search the index for relevant docs
2. Fetch content (local or remote)
3. Answer with citations

### Update the index

```
"Check if clickhouse-docs needs updating"
"Update the clickhouse-docs index"
```

## Design Principles

**Human-readable indexes**: Simple markdown with heading hierarchy, not complex YAML schemas.

**Collaborative building**: The index is built interactively based on user needs, not auto-generated.

**Works without local clone**: Navigate skill can fetch from raw GitHub URLs when `.source/` doesn't exist.

**Per-project discoverability**: Each doc plugin has its own navigate skill with a specific description (e.g., "Find ClickHouse documentation for data modeling, ETL, query optimization").

**Centralized maintenance**: One `docs-maintain` skill works across all doc plugins.

## Example: ClickHouse Docs

```
clickhouse-docs/
├── .claude-plugin/plugin.json
├── skills/navigate/SKILL.md     # "Find ClickHouse documentation..."
├── data/
│   ├── config.yaml              # Points to ClickHouse/clickhouse-docs
│   └── index.md                 # ~150 key docs organized by topic
└── .source/                     # Local clone (gitignored)
```

The index covers:
- Data Modeling (schema design, denormalization, projections)
- Table Engines (MergeTree family, integrations)
- SQL Reference (SELECT, INSERT, data types)
- Operations (deployment, monitoring, backups)
- Integrations (Kafka, S3, dbt)

## Adding a New Documentation Source

1. Run `generate-docs-plugin` with the repo URL
2. Run `docs-init` from the new plugin directory
3. Collaborate on index contents
4. Commit `data/index.md` and `data/config.yaml`

The navigate skill is immediately usable. Run `docs-maintain` periodically to check for upstream changes.

## Repository Organization

This repository contains the **meta-plugin** (skills for generating and maintaining doc plugins) plus **one reference implementation** (clickhouse-docs). Generated documentation plugins should live in their own repositories.

### Why separate repos?

**Indexes are personal.** The collaborative index you build reflects *your* priorities and use cases. Someone focused on ClickHouse analytics has different needs than someone building ETL pipelines. A centralized collection of "everyone's indexes" has limited value.

**Independent lifecycles.** Your doc plugin updates when *you* need it updated, not when someone else changes theirs.

**Lightweight installation.** Users install only the doc plugins they actually use.

### Recommended approach

| Repository | Contents |
|------------|----------|
| This repo | Meta-plugin skills + templates + reference implementation |
| `your-org/prisma-docs` | Your Prisma documentation plugin |
| `your-org/react-docs` | Your React documentation plugin |

### The clickhouse-docs example

The `clickhouse-docs/` directory serves as:
- A working reference implementation
- A test case for meta-plugin changes
- An example of index structure and organization

Feel free to use it directly, or use it as a template for your own plugins.

## Future Enhancements

See [docs/future-enhancements.md](docs/future-enhancements.md) for planned improvements including:
- Staleness warnings during navigation
- Version awareness
- Cross-project linking
- Curated external resources

## License

MIT
