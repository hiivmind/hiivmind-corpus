# hiivmind-corpus

Claude Code skills for creating and maintaining documentation corpus indexes.

## What is a "meta-skill"?

This is a skill that **creates other skills**.

Most Claude Code skills help you do something directly—write code, search files, fetch data. This plugin is different: it helps you **build custom corpus skills** for navigating any project's documentation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  hiivmind-corpus (meta-skill)                                               │
│                                                                             │
│  corpus-init  →  corpus-build  →  corpus-refresh                            │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ hiivmind-corpus-    │  │ hiivmind-corpus-    │  │ hiivmind-corpus-    │ │
│  │ prisma              │  │ clickhouse          │  │ react               │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
└─────────────┼─────────────────────────┼─────────────────────────┼───────────┘
              ▼                         ▼                         ▼
       Prisma docs               ClickHouse docs              React docs
```

The corpus skills you generate are:
- **Persistent** — committed to your repo, survive across sessions
- **Tailored** — built collaboratively around your actual use case
- **Maintainable** — track upstream changes, know when they're stale

Think of it as a skill factory: you feed it a documentation source, and it produces a specialized corpus skill for that project.

## Two ways to create corpus skills

When you run `hiivmind-corpus-init`, you'll choose where the skill should live:

### Project-local skill

```
your-project/
├── .claude-plugin/
│   └── skills/
│       └── hiivmind-corpus-polars/    ← Created here
│           ├── SKILL.md
│           └── data/
└── src/
    └── analysis.py
```

**Best for:**
- A specific project that needs library docs (e.g., data analysis project needing Polars)
- Teams—everyone who clones the repo automatically gets the skill
- No marketplace installation required

**Example use case:** "I'm building a data pipeline and need quick access to Polars documentation while I work."

### Standalone plugin

```
hiivmind-corpus-polars/            ← Created as separate directory/repo
├── .claude-plugin/
│   └── plugin.json
├── skills/navigate/
├── data/
└── README.md
```

**Best for:**
- Personal reuse across all your projects
- Sharing via the Claude Code marketplace
- Documentation you always want available

**Example use case:** "I work with React constantly—I want React docs available in every project."

| Aspect | Project-local | Standalone |
|--------|---------------|------------|
| Location | `.claude-plugin/skills/hiivmind-corpus-{lib}/` | `hiivmind-corpus-{lib}/` separate repo |
| Installation | None—just open the project | Marketplace install required |
| Scope | This project only | All your projects |
| Team sharing | Automatic (via git) | Each person installs |
| Maintenance | Tied to project lifecycle | Independent lifecycle |

## Installation

```bash
# Add the marketplace
/plugin marketplace add hiivmind/hiivmind-corpus

# Install the plugin
/plugin install hiivmind-corpus
```

## Overview

This plugin provides skills to:
- Generate corpus skills for any open source project
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

### What hiivmind-corpus provides

| Capability | Benefit |
|------------|---------|
| **Curated index** | Built collaboratively around your actual use case |
| **Persistent** | Committed to repo, survives across sessions |
| **Current** | Tracks upstream commits, knows when it's stale |
| **Structured** | Systematically find relevant sections |
| **Flexible** | Works with local clone or remote fetch |

### When to use this vs. default lookup

**Use hiivmind-corpus when:**
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
│   └── plugin.json                 # Root plugin manifest
├── skills/
│   ├── hiivmind-corpus-init/       # Create new corpus skills
│   ├── hiivmind-corpus-build/      # Analyze docs, build index
│   ├── hiivmind-corpus-enhance/    # Deepen specific topics
│   └── hiivmind-corpus-refresh/    # Refresh from upstream changes
├── templates/                      # Templates for generated skills
└── docs/                           # Specifications
```

## Workflow

```
hiivmind-corpus-init  →  hiivmind-corpus-build  →  hiivmind-corpus-refresh
     (structure)              (index)                 (upstream diff)
                                 ↓
                        hiivmind-corpus-enhance
                           (deepen topics)
```

| Skill | When | What |
|-------|------|------|
| `hiivmind-corpus-init` | Once per project | Creates folder structure, config, navigate skill |
| `hiivmind-corpus-build` | Once per documentation source | Analyzes docs, builds index collaboratively with user |
| `hiivmind-corpus-enhance` | As needed | Expands coverage on specific topics in existing index |
| `hiivmind-corpus-refresh` | Ongoing | Compares upstream diff, refreshes index when needed |

## Usage

### Create a new corpus skill

```
"Create a corpus skill for ClickHouse"
```

This will:
1. Clone the docs repo temporarily
2. Analyze structure (framework, file types, organization)
3. Generate `hiivmind-corpus-clickhouse/` with config and navigate skill

### Build the index

```
"Build the hiivmind-corpus-clickhouse index"
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

### Enhance a topic

```
"Enhance the Query Optimization section in hiivmind-corpus-clickhouse"
"I need more detail on migrations in hiivmind-corpus-prisma"
```

This will:
1. Read the current index
2. Ask what you need from that topic
3. Explore docs for additional relevant content
4. Collaboratively expand the section

### Refresh from upstream

```
"Check if hiivmind-corpus-clickhouse needs updating"
"Refresh the hiivmind-corpus-clickhouse index"
```

## Design Principles

**Human-readable indexes**: Simple markdown with heading hierarchy, not complex YAML schemas.

**Collaborative building**: The index is built interactively based on user needs, not auto-generated.

**Works without local clone**: Navigate skill can fetch from raw GitHub URLs when `.source/` doesn't exist.

**Per-project discoverability**: Each corpus skill has its own navigate skill with a specific description (e.g., "Find ClickHouse documentation for data modeling, ETL, query optimization").

**Centralized refresh**: One `hiivmind-corpus-refresh` skill works across all corpus skills.

## Example: ClickHouse Corpus

```
hiivmind-corpus-clickhouse/
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

1. Run `hiivmind-corpus-init` with the repo URL
2. Run `hiivmind-corpus-build` from the new skill directory
3. Collaborate on index contents
4. Commit `data/index.md` and `data/config.yaml`

The navigate skill is immediately usable. Run `hiivmind-corpus-refresh` periodically to check for upstream changes.

## Repository Organization

This repository contains the **meta-plugin** (skills for generating and maintaining corpus skills). Generated corpus skills should live in their own repositories following the `hiivmind-corpus-{project}` naming convention.

### Why separate repos?

**Indexes are personal.** The collaborative index you build reflects *your* priorities and use cases. Someone focused on ClickHouse analytics has different needs than someone building ETL pipelines. A centralized collection of "everyone's indexes" has limited value.

**Independent lifecycles.** Your corpus skill updates when *you* need it updated, not when someone else changes theirs.

**Lightweight installation.** Users install only the corpus skills they actually use.

### Recommended approach

| Repository | Contents |
|------------|----------|
| `hiivmind/hiivmind-corpus` | Meta-plugin skills + templates |
| `hiivmind/hiivmind-corpus-prisma` | Prisma documentation corpus |
| `hiivmind/hiivmind-corpus-react` | React documentation corpus |

## Future Enhancements

See [docs/future-enhancements.md](docs/future-enhancements.md) for planned improvements including:
- Staleness warnings during navigation
- Version awareness
- Cross-project linking
- Curated external resources

## License

MIT
