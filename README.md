# hiivmind-corpus

A Claude Code plugin for creating persistent, curated documentation indexes from any documentation source—reliable, up-to-date, authoritative context that persists across sessions.

Think of it like [Claude Projects](https://claude.ai) for Claude Code—but better. With Projects, you dump docs, code, and PDFs into a collection that persists across chats. But everything consumes context, there's no way to prioritize what matters, no freshness tracking, no namespacing, no search.

A corpus solves all of this. You build a curated index once, Claude searches it directly without filling your context window, and the index tracks exactly where everything came from and how fresh it is. Install as many as you need—they're lightweight and independent.

This follows the ["just in time" context pattern](https://www.anthropic.com/engineering/claude-code-best-practices) recommended by Anthropic: rather than loading all documentation up front, the index maintains lightweight identifiers (file paths, URLs) that Claude uses to dynamically load relevant content at runtime. It mirrors how humans work—we don't memorize entire corpuses, we build indexing systems to retrieve information on demand.

## Getting Started

```
/hiivmind-corpus
```

One command, natural language. Describe what you need:

- *"Create a corpus for Polars"* → scaffolds a new corpus
- *"What corpora do I have?"* → discovers all installed corpora
- *"How do I use lazy frames in Polars?"* → navigates across your corpora
- *"Refresh my React corpus"* → checks for upstream changes
- *"Add the TanStack Query docs to my fullstack corpus"* → extends with new sources

## What It Creates

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  hiivmind-corpus (meta-plugin)                                               │
│                                                                              │
│  init → add-source → build → enhance/refresh → upgrade                       │
│                        ↓                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ hiivmind-corpus-fullstack                                             │   │
│  │   Sources: react (git) + team-standards (local) + blog-posts (web)    │   │
│  └───────────────────────────────┬───────────────────────────────────────┘   │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   ▼
                 React docs + Team docs + Blog articles
```

The corpus skills you generate are:
- **Persistent** — committed to your repo, survive across sessions
- **Tailored** — built collaboratively around your actual use case
- **Maintainable** — track upstream changes, know when they're stale
- **Multi-source** — combine git repos, local documents, and web content

## Installation

```bash
# Add the marketplace
/plugin marketplace add hiivmind/hiivmind-corpus

# Install the plugin
/plugin install hiivmind-corpus@hiivmind
```

Or use `/plugin` to browse and install interactively.

## Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| **git** | any | Clone source repos, track commits |
| **yq** | 4.0+ | Parse YAML config files |
| **curl** | any | Fetch remote docs (fallback when no local clone) |

## The Eight Skills

| Skill | Purpose |
|-------|---------|
| **discover** | Find all installed corpora across user-level, repo-local, and marketplace locations |
| **navigate** | Query across all your corpora—routes to the right per-corpus navigate skill |
| **init** | Create corpus structure from a GitHub repo URL |
| **add-source** | Add git repos, local documents, or web pages to existing corpora |
| **build** | Build index collaboratively with user guidance |
| **enhance** | Deepen topic coverage in specific areas |
| **refresh** | Sync with upstream changes (compare SHAs, update index) |
| **upgrade** | Update existing corpora to latest template standards |

### Skill Lifecycle

```
                    /hiivmind-corpus
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │ discover │  │ navigate │  │   init   │
       └──────────┘  └──────────┘  └────┬─────┘
            │              │             │
            └──────────────┘             ▼
         (query existing)        ┌────────────┐
                                 │ add-source │
                                 └─────┬──────┘
                                       ▼
┌─────────┐    ┌─────────┐    ┌─────────────┐
│ upgrade │ ←  │ refresh │ ←  │    build    │
└─────────┘    └─────────┘    └──────┬──────┘
     ↑              ↑                │
     └──────────────┴────────────────┘
                (as needed)          ▼
                                ┌─────────┐
                                │ enhance │
                                └─────────┘
```

## Where Corpora Live

`init` detects your context and offers appropriate destinations:

| Type | Location | Best For |
|------|----------|----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-{lib}/` | Personal use everywhere |
| **Repo-local** | `{repo}/.claude-plugin/skills/hiivmind-corpus-{lib}/` | Team sharing via git |
| **Single-corpus** | `hiivmind-corpus-{lib}/` (standalone repo) | Marketplace publishing |
| **Multi-corpus** | `{marketplace}/hiivmind-corpus-{lib}/` | Marketplace publishing (related projects) |

## Source Types

| Type | Storage | Example |
|------|---------|---------|
| **git** | `.source/{source_id}/` | Library docs, framework APIs |
| **local** | `data/uploads/{source_id}/` | Team standards, internal docs |
| **web** | `.cache/web/{source_id}/` | Blog posts, articles |

All paths in the index use `{source_id}:{relative_path}` format.

## Quick Start

Just type `/hiivmind-corpus` and describe what you need:

| You say... | What happens |
|------------|--------------|
| *"Create a corpus for Polars"* | `init` scaffolds structure, clones docs |
| *"What corpora do I have?"* | `discover` lists all installed corpora |
| *"How do lazy frames work?"* | `navigate` searches your corpora and fetches docs |
| *"Build the polars index"* | `build` scans sources, collaboratively creates index |
| *"Add TanStack Query to my fullstack corpus"* | `add-source` clones repo, offers to index |
| *"Check if my corpus needs updating"* | `refresh` compares SHAs, reports changes |
| *"Enhance the Query Optimization section"* | `enhance` searches sources, expands index |
| *"Upgrade my polars corpus"* | `upgrade` applies latest template standards |

## Advanced Features

### Tiered Indexes

For 500+ file documentation sets, `build` offers tiered indexing:

```
data/
├── index.md              # Main index with section summaries + links
├── index-reference.md    # Detailed API reference
├── index-guides.md       # Detailed guides/tutorials
└── index-concepts.md     # Detailed conceptual docs
```

The `enhance` and `refresh` skills understand this structure and update appropriate files.

### Large Structured Files

Files marked with `⚡ GREP` in the index are too large to read directly:

```markdown
- **GraphQL Schema** `api:schema.graphql` ⚡ GREP - 15k lines. Search: `grep -n "^type {Name}" -A 30`
```

The navigate skill uses Grep instead of Read for these.

### Project Awareness

Each corpus includes `data/project-awareness.md` — a snippet for any project's CLAUDE.md:

```markdown
# Polars Documentation Corpus

Use **hiivmind-corpus-navigate-polars** when working with Polars.
```

This makes Claude proactively use the corpus in projects that need it.

### Multi-Source Corpora

A single corpus can combine multiple source types—git repos, web pages, and local uploads:

```
data/
├── config.yaml              # Sources array with git, web, local entries
├── index.md                 # Unified index with source prefixes
└── uploads/team-standards/  # Local documents
.source/                     # Git clones (gitignored)
├── react/
└── tanstack-query/
.cache/web/kent-blog/        # Cached web content (gitignored)
```

Index entries use `{source_id}:{path}` format to identify the source:

```markdown
## React Fundamentals
- **Hooks Overview** `react:reference/hooks.md` - Introduction to hooks

## Testing
- **Implementation Details** `web:kent-blog/testing-impl.md` - What not to test
- **Our Standards** `local:team-standards/testing.md` - Team conventions
```

Use `add-source` to extend any corpus with additional git repos, web articles, or local files.

## Design Principles

- **Unified access** — One command (`/hiivmind-corpus`) to create, discover, navigate, and maintain all corpora
- **Human-readable indexes** — Simple markdown with headings, not complex schemas
- **Collaborative building** — User guides what's important, not automation
- **Works without local clone** — Falls back to raw GitHub URLs
- **Discoverable** — `discover` finds all installed corpora; `navigate` queries across them
- **Per-project discoverability** — Each corpus has its own navigate skill description
- **Project awareness** — Corpora include snippets for CLAUDE.md injection
- **Upgradeable** — Existing corpora update to latest standards via `upgrade`
- **Scalable** — Tiered indexes for large corpora, grep for large files

## Why This Exists

### The problem with default documentation lookup

Without structured indexing, Claude investigates libraries by:

1. **Relying on training data** — May be outdated or incomplete
2. **Web searching** — Hit-or-miss, often finds outdated tutorials
3. **Fetching URLs on demand** — One page at a time, no context
4. **Reading installed packages** — Limited to code, not prose docs

This means rediscovering the same things every session, no memory of what's relevant to *your* work, and stale knowledge for fast-moving projects.

### The real win

The collaborative index building. Rather than Claude guessing what matters, you tell it: "I care about data modeling and ETL, skip the deployment stuff." That context persists across sessions.

It also aids **feature discovery**. Ask "What useful Polars features have I missed in my project?" and Claude can scan your code against the index to suggest capabilities you're not using yet.

### Why not MCP-based documentation?

MCP documentation servers typically use vector databases and embeddings to index docs. Here's why we think the corpus approach is better:

**Known freshness.** With hiivmind-corpus, you know exactly how old your sources are—commit SHA tracking tells you precisely. With MCP/vector solutions, who knows when they last re-indexed or refreshed their embeddings?

**Zero infrastructure.** No vector databases, no embedding models, no server deployments, no API keys. Just markdown files in your repo.

**Zero cost.** On Claude Code's non-API plans, there's no setup cost and no per-query cost. MCP servers often require paid embedding APIs or hosted vector databases.

**Human curation beats auto-indexing.** You decide what matters. "I care about data modeling and ETL, skip the deployment stuff" isn't something a vector embedding understands.

**Fast local access.** Yes, you need to be online (Claude needs it), but local file caches are dramatically faster and more searchable than web fetches or API calls to vector databases.

**Portable and versionable.** Your index is just markdown—commit it, diff it, review it, share it with your team. Try doing that with vector embeddings.

### Why corpora are independent

Regardless of where you put them (user-level, repo-local, or marketplace), corpora are designed to be self-contained:

**Indexes are personal.** The collaborative index you build reflects *your* priorities. Someone focused on ClickHouse analytics has different needs than someone building ETL pipelines. A team's repo-local corpus reflects that team's focus.

**Independent lifecycles.** Your corpus updates when *you* need it. A user-level skill evolves with your learning; a repo-local skill evolves with the project; a marketplace plugin evolves with its maintainer.

**Lightweight by design.** Each corpus contains only what it needs—no shared dependencies, no version conflicts. Install what you use.

## Example Structures

**User-level skill:**
```
~/.claude/skills/hiivmind-corpus-polars/
├── SKILL.md                     # Navigate skill
├── data/
│   ├── config.yaml
│   ├── index.md
│   └── project-awareness.md
└── .source/polars/              # Local clone
```

**Repo-local skill:**
```
my-data-project/
├── .claude-plugin/
│   └── skills/
│       └── hiivmind-corpus-polars/
│           ├── SKILL.md         # Navigate skill
│           └── data/
│               ├── config.yaml
│               ├── index.md
│               └── project-awareness.md
├── .gitignore                   # Include: .claude-plugin/skills/*/.source/
└── src/
    └── analysis.py
```

**Single-corpus plugin:**
```
hiivmind-corpus-polars/
├── .claude-plugin/plugin.json
├── skills/navigate/SKILL.md
├── data/
│   ├── config.yaml
│   ├── index.md
│   └── project-awareness.md
└── .source/polars/              # gitignored
```

**Multi-corpus repo (marketplace):**
```
hiivmind-corpus-data/                # Marketplace root
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json             # Lists child plugins
├── hiivmind-corpus-polars/          # Child plugin
│   ├── .claude-plugin/plugin.json
│   ├── skills/navigate/SKILL.md
│   └── data/
├── hiivmind-corpus-ibis/            # Child plugin
│   └── ...
└── hiivmind-corpus-narwhals/        # Child plugin
    └── ...
```

## License

MIT
