# hiivmind-corpus

A meta-plugin that creates documentation corpus skills for Claude Code.

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

## The Six Skills

| Skill | Process | Purpose |
|-------|---------|---------|
| **init** | `INPUT → SCAFFOLD → CLONE → RESEARCH → GENERATE → VERIFY` | Create corpus structure |
| **add-source** | `LOCATE → TYPE → COLLECT → SETUP → INDEX?` | Add git/local/web sources |
| **build** | `PREPARE → SCAN → ASK → BUILD → SAVE` | Build index collaboratively |
| **enhance** | `VALIDATE → READ → ASK → EXPLORE → ENHANCE → SAVE` | Deepen topic coverage |
| **refresh** | `VALIDATE → DETECT → CHECK → REPORT/UPDATE` | Sync with upstream changes |
| **upgrade** | `LOCATE → DETECT → COMPARE → REPORT → APPLY → VERIFY` | Update to latest standards |

### Skill Lifecycle

```
┌─────────┐    ┌────────────┐    ┌───────┐
│  init   │ →  │ add-source │ →  │ build │
└─────────┘    └────────────┘    └───────┘
                                     ↓
┌─────────┐    ┌─────────┐    ┌─────────┐
│ upgrade │ ←  │ refresh │ ←  │ enhance │
└─────────┘    └─────────┘    └─────────┘
     ↑              ↑              ↑
     └──────────────┴──────────────┘
              (as needed)
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

**Create a corpus:**
```
"Create a corpus skill for Polars"
```
→ runs `init` → scaffolds structure → clones docs

**Build the index:**
```
"Build the polars corpus index"
```
→ runs `build` → scans sources → collaboratively creates index

**Add more sources:**
```
"Add Kent C. Dodds testing blog posts to my corpus"
```
→ runs `add-source` → fetches/caches content → offers to index

**Check for updates:**
```
"Check if my corpus needs updating"
```
→ runs `refresh status` → compares SHAs → reports changes

**Deepen a topic:**
```
"Enhance the Query Optimization section"
```
→ runs `enhance` → searches sources → expands index collaboratively

**Upgrade to latest:**
```
"Upgrade my polars corpus to latest standards"
```
→ runs `upgrade` → detects missing features → applies updates

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

Use **hiivmind-corpus-polars-navigate** when working with Polars.
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

- **Human-readable indexes** — Simple markdown with headings, not complex schemas
- **Collaborative building** — User guides what's important, not automation
- **Works without local clone** — Falls back to raw GitHub URLs
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
