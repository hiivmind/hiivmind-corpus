# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hiivmind-corpus** is a unified plugin for building AND reading documentation corpora in Claude Code. One plugin handles everything:

- **BUILD**: Create and maintain documentation indexes (init, add-source, build, refresh, enhance)
- **READ**: Navigate and query documentation (navigate, register, status, discover)

The core value: Persistent human-curated indexes that track upstream changes, instead of relying on training data or on-demand fetching.

## Ecosystem Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     hiivmind-corpus Ecosystem                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌────────────────────────────────────────────┐                    │
│   │           hiivmind-corpus (plugin)          │                    │
│   │                                             │                    │
│   │   BUILD                    READ             │                    │
│   │   ─────                    ────             │                    │
│   │   • init                   • navigate       │                    │
│   │   • add-source             • register       │                    │
│   │   • build                  • status         │                    │
│   │   • refresh                • discover       │                    │
│   │   • enhance                                 │                    │
│   │                                             │                    │
│   └────────────────────┬────────────────────────┘                    │
│                        │                                             │
│            PRODUCES    │    CONSUMES                                 │
│                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              Data-Only Corpus Repositories               │       │
│   │                                                          │       │
│   │  github.com/hiivmind/hiivmind-corpus-flyio              │       │
│   │  github.com/hiivmind/hiivmind-corpus-polars             │       │
│   │  github.com/yourorg/internal-api-corpus                 │       │
│   │                                                          │       │
│   │  Each contains:                                          │       │
│   │    • config.yaml  (source definitions + keywords)        │       │
│   │    • index.yaml   (structured index, machine-queryable)  │       │
│   │    • index.md     (human-readable, rendered from yaml)   │       │
│   │    • index-embeddings.lance/ (semantic search, COMMITTED)│       │
│   └─────────────────────────────────────────────────────────┘       │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              Per-Project Configuration                    │       │
│   │                                                          │       │
│   │  .hiivmind/corpus/registry.yaml                         │       │
│   │    - Which corpora are relevant to this project          │       │
│   │    - Source locations (GitHub refs or local paths)       │       │
│   │    - Caching preferences (per corpus)                    │       │
│   └─────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key insight:** One plugin does everything. Corpora are just data repositories.

## Architecture

```
├── skills/                           # Core skills
│   ├── hiivmind-corpus-init/         # Create new corpus scaffold
│   ├── hiivmind-corpus-add-source/   # Add git repos, local docs, or web pages
│   ├── hiivmind-corpus-build/        # Analyze docs, build index with user
│   ├── hiivmind-corpus-enhance/      # Deepen coverage on specific topics
│   ├── hiivmind-corpus-refresh/      # Refresh index from upstream changes
│   ├── hiivmind-corpus-discover/     # Find all installed corpora
│   ├── hiivmind-corpus-navigate/     # Global navigation across all corpora
│   ├── hiivmind-corpus-register/     # Register corpus with project
│   ├── hiivmind-corpus-status/       # Check corpus health and freshness
│   ├── hiivmind-corpus-graph/        # View, validate, edit concept graphs
│   └── hiivmind-corpus-bridge/       # Cross-corpus concept bridges
│
├── agents/                           # Agent definitions for parallel operations
│   └── source-scanner.md             # Parallel scanning of documentation sources
│
├── commands/                         # Slash commands
│   └── hiivmind-corpus.md            # Gateway command for corpus interaction
│
├── lib/corpus/                       # Pattern documentation library
│   └── patterns/                     # Tool-agnostic algorithm documentation
│       ├── tool-detection.md         # Detecting available tools (yq, python, etc.)
│       ├── config-parsing.md         # Extracting fields from config.yaml
│       ├── discovery.md              # Finding installed corpora
│       ├── status.md                 # Checking corpus freshness
│       ├── paths.md                  # Resolving paths within corpora
│       ├── sources/                  # Source type operations (per-type)
│       │   ├── README.md             # Overview and taxonomy
│       │   ├── git.md                # Git repository operations
│       │   ├── local.md              # Local file uploads
│       │   ├── web.md                # Web content caching
│       │   ├── generated-docs.md     # Hybrid git+web operations
│       │   ├── llms-txt.md           # llms.txt manifest sources
│       │   └── shared.md             # Cross-type utilities
│       └── scanning.md               # File discovery and analysis
│   └── scripts/                     # Python scripts for embedding operations
│       ├── detect.py                # Check fastembed availability
│       ├── embed.py                 # Generate embeddings into SQLite
│       └── search.py               # Query embeddings by cosine similarity
│
├── templates/                        # Templates for generating new corpus skills
│
└── docs/                             # Specifications and design docs
```

## Skill Lifecycle

```
                        /hiivmind-corpus (gateway command)
                                 │
                    hiivmind-corpus-discover ← finds installed corpora
                                 │
                    hiivmind-corpus-navigate ← queries across all corpora
                                 │
                                 ▼
hiivmind-corpus-init → hiivmind-corpus-build → hiivmind-corpus-refresh
       (once)                 (once)                  (periodic)
                                 ↓
                        hiivmind-corpus-enhance
                            (as needed)
```

**Creation & Maintenance Skills:**
1. **hiivmind-corpus-init**: Scaffolds a new data-only corpus repository
2. **hiivmind-corpus-add-source**: Adds git repos, local documents, or web pages to existing corpus
3. **hiivmind-corpus-build**: Analyzes docs, builds `index.md` collaboratively with user
4. **hiivmind-corpus-enhance**: Deepens coverage on specific topics (runs on existing index)
5. **hiivmind-corpus-refresh**: Compares against upstream commits, refreshes index based on diff

**Discovery & Navigation Skills:**
6. **hiivmind-corpus-discover**: Scans for installed corpora
7. **hiivmind-corpus-navigate**: Global navigator that routes queries to appropriate corpora
8. **hiivmind-corpus-register**: Connects a corpus to the current project
9. **hiivmind-corpus-status**: Checks corpus health and freshness

**Gateway Command:**
- **/hiivmind-corpus**: Interactive entry point for discovering and interacting with installed corpora

**Agents:**

| Agent | Purpose | Model | Used By |
|-------|---------|-------|---------|
| `source-scanner` | Parallel scanning of documentation sources | haiku | build, refresh |

Agents enable parallel processing of multi-source corpora. When a corpus has 2+ sources, skills spawn multiple `source-scanner` agents concurrently to analyze each source, then aggregate results. This provides 40-60% speedup for corpora with 3+ sources.

## Corpus Repository Structure

`hiivmind-corpus-init` creates data-only repositories:

```
hiivmind-corpus-{project}/
├── config.yaml              # Source definitions + keywords
├── index.yaml               # Structured index (v2, machine-queryable)
├── index.md                 # Human-readable markdown index (rendered from index.yaml)
├── index-*.md               # Sub-indexes (tiered corpora only)
├── graph.yaml               # Concept graph (if extraction enabled)
├── index-embeddings.lance/  # Semantic search embeddings (COMMITTED, not gitignored)
├── render-index.sh          # Deterministic index.yaml → index.md renderer
├── .source/                 # Local clones (gitignored)
├── uploads/                 # Local document sources
├── .cache/                  # Web/llms-txt cached content
├── CLAUDE.md                # Project awareness
├── README.md
├── .gitignore
└── LICENSE
```

## Naming Convention

All components follow the `hiivmind-corpus-*` naming pattern:
- Meta-plugin: `hiivmind-corpus`
- Build skills: `hiivmind-corpus-init`, `hiivmind-corpus-add-source`, `hiivmind-corpus-build`, `hiivmind-corpus-enhance`, `hiivmind-corpus-refresh`
- Read skills: `hiivmind-corpus-discover`, `hiivmind-corpus-navigate`, `hiivmind-corpus-register`, `hiivmind-corpus-status`, `hiivmind-corpus-graph`, `hiivmind-corpus-bridge`
- Gateway command: `/hiivmind-corpus`
- Generated corpora: `hiivmind-corpus-{project}` (e.g., `hiivmind-corpus-flyio`, `hiivmind-corpus-polars`)

## Pattern Documentation Library

The `lib/corpus/patterns/` directory contains tool-agnostic algorithm documentation. Skills reference these patterns and adapt to available tools at runtime.

**Design philosophy**: Instead of executable bash scripts (which lock into Linux/macOS), pattern documentation describes algorithms with multiple implementation options, letting the LLM adapt to the user's environment.

| Pattern | Purpose | Key Sections |
|---------|---------|--------------|
| `tool-detection.md` | Detect available tools | Tool tiers, detection commands, capability matrix |
| `config-parsing.md` | Extract YAML fields | yq, python+pyyaml, grep fallback methods |
| `discovery.md` | Find installed corpora | Location types, scanning algorithms |
| `status.md` | Check corpus freshness | Index status, SHA comparison |
| `paths.md` | Resolve paths | Source reference parsing, path resolution |
| `sources/` | Git/local/web/llms-txt/self operations | Per-type patterns (git, local, web, generated-docs, llms-txt, self) |
| `scanning.md` | Documentation analysis | File discovery, framework detection, large files |
| `freshness.md` | SHA-gated freshness | Read-time checks, CI refresh, stale flagging |

**How skills use patterns:**

```markdown
## Step 1: Validate Prerequisites

**See:** `lib/corpus/patterns/config-parsing.md` and `lib/corpus/patterns/status.md`

Read `data/config.yaml` to check configuration.

Using Claude tools (preferred):
- Read: data/config.yaml
- Check for sources array

Using bash with yq:
- yq '.sources | length' data/config.yaml
```

**Tool detection strategy**: Skills detect tools once per session and use the best available option. Required tools (like git) are enforced; optional tools (like yq) have fallbacks.

## Key Design Decisions

- **Human-readable indexes**: Simple markdown with headings, not complex schemas
- **Collaborative building**: User guides what's important, not automation
- **Works without local clone**: Falls back to raw GitHub URLs
- **Change tracking**: Stores commit SHA to know when index is stale
- **Per-project skills**: Each corpus skill has its own navigate skill for discoverability
- **Project awareness**: Corpora include snippets for injecting into project CLAUDE.md files
- **Discoverable**: `hiivmind-corpus-discover` finds available corpora
- **Unified access**: `/hiivmind-corpus` gateway provides single entry point for all corpus interaction
- **Global navigation**: `hiivmind-corpus-navigate` routes queries across all installed corpora
- **Tool-agnostic patterns**: `lib/corpus/patterns/` documents algorithms, not executable scripts
- **Cross-platform**: Works on Linux, macOS, and Windows with appropriate tool fallbacks
- **Forked context execution**: Navigate skills run in isolated sub-agent (`context: fork`) to keep main conversation clean (ADR-007)
- **llms.txt support**: Sites with llms.txt manifests get efficient manifest-driven discovery with hash-based change detection (ADR-008)
- **Embedded corpora**: Documentation repos can contain their own corpus at `.hiivmind/corpus/`, powered by `type: self` sources — see spec at `docs/superpowers/specs/2026-03-25-embedded-corpus-design.md`
- **Cross-corpus bridges**: Projects with 2+ registered corpora can create concept bridges in `registry-graph.yaml`, with query-routing aliases — see spec at `docs/superpowers/specs/2026-03-26-graph-editing-and-bridge-design.md`
- **Optional embeddings**: Entry-level semantic embeddings (`index-embeddings.lance/`) via fastembed enhance retrieval for large/tiered corpora. Cross-corpus concept embeddings (`registry-embeddings.lance/`) improve query routing. Opt-in during build with heuristic-based advice. Graceful fallback to keyword/LLM approach when fastembed unavailable — see specs at `docs/superpowers/specs/2026-03-27-rag-embeddings-design.md` and `docs/superpowers/specs/2026-03-27-lancedb-revision-design.md`

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
2. Fetches documentation content:
   - **Local:** Read from `.source/{path}` if clone exists
   - **Remote (preferred):** Use `gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d`
   - **Remote (fallback):** Use WebFetch with `raw.githubusercontent.com/{path}` if gh unavailable
3. Warns if local clone is newer than last indexed commit
4. Cites file paths and suggests related docs

**Note:** The `gh api` method is preferred for remote fetching as it works consistently for all public repositories and uses authenticated access for better rate limits.

## Working with Templates

Templates in `templates/` use placeholders like `{{project_name}}`, `{{repo_url}}`, etc. The `hiivmind-corpus-init` skill fills these based on target repository analysis.

## Maintaining Skill Alignment

**IMPORTANT**: All skills must remain aware of each other and share consistent knowledge about corpus features. When modifying any skill, check if other skills need updates.

### Cross-Cutting Concerns

These features span multiple skills and must stay synchronized:

| Feature | Relevant Skills | What to Check |
|---------|-----------------|---------------|
| Tiered indexes | build, enhance, refresh | Detection logic, update handling |
| Source types (git/local/web/generated-docs/llms-txt/self) | add-source, build, enhance, refresh | Path formats, fetch methods |
| `⚡ GREP` markers | add-source, build, enhance | Large file detection, index format |
| Project awareness | init, navigate command (template) | Template exists, command help mentions it |
| Config schema | all skills | Schema fields, validation |
| Discovery locations | discover, navigate, gateway command | All 5 location types scanned consistently (including embedded at `.hiivmind/corpus/`) |
| Embedded corpora | init, discover, navigate, build, refresh, status, add-source, enhance, source-scanner | `type: self` source type, `.hiivmind/corpus/` discovery, `docs_root` normalization |
| Cross-corpus bridges | bridge, navigate, graph, discover | registry-graph.yaml schema, Tier 4 traversal, alias routing, graph.yaml prerequisite |
| Corpus status detection | discover, navigate, gateway command | placeholder/built/stale logic |
| Parallel scanning | build, refresh, source-scanner agent | Multi-source detection, agent invocation |
| Entry keywords | enhance, refresh, navigate (template) | Keyword line format, search logic, preserve on refresh |
| Corpus keywords | discover, navigate (global), init | config.yaml schema, per-session discovery |
| CLAUDE.md cache | awareness, discover, navigate | Cache format, HTML markers, cache-first lookup |
| Injection targets | awareness | User-level vs repo-level templates |
| Fork context (ADR-007) | navigate (template) | Frontmatter: context, agent, allowed-tools |
| Embeddings | build, enhance, refresh, navigate, bridge, graph, discover, status | `index-embeddings.lance/` generation/query, `registry-embeddings.lance/` generation, fastembed detection, heuristic prompt, graph-boost, graceful fallback |

### When Adding New Features

1. **Implement in the primary skill** (where the feature originates)
2. **Update skills that validate prerequisites** (enhance, refresh) with awareness
3. **Update templates** if the navigate skill needs new sections
5. **Update this CLAUDE.md** with the feature in Key Design Decisions and/or this table

### Skill Dependency Chain

```
/hiivmind-corpus (gateway command)
         │
         ├── discover ◄──── scans all installation locations, updates cache
         │       │
         │       └──► ~/.claude/CLAUDE.md (corpus cache)
         │                     ▲
         ├── navigate ◄────────┘ (checks cache first)
         │
         └── awareness ◄──── edits CLAUDE.md with skill awareness
                    │
init ──────────► templates/
    │                │
    └──► add-source ◄┤ (init delegates source setup to add-source)
                     │
build ◄─────────────┤ ──► source-scanner agent (parallel multi-source)
                     │
enhance ◄───────────┤ (must know all features to validate)
                     │
refresh ◄───────────┘ ──► source-scanner agent (parallel multi-source)

build ──► index-embeddings.lance/ (optional, Phase 5c)
enhance ──► index-embeddings.lance/ (incremental update)
refresh ──► index-embeddings.lance/ (incremental update, if model ready)
bridge ──► registry-embeddings.lance/ (cross-corpus concepts)
navigate ◄── index-embeddings.lance/ + registry-embeddings.lance/ (retrieval enhancement)
graph ◄── index-embeddings.lance/ (relationship candidate detection)
```

### Reference Sections

Every skill has a `## Reference` section at the bottom listing all other skills. When adding a new skill, update all existing skills' Reference sections.

## Plugin Development Resources

**IMPORTANT**: This is a Claude Code plugin. When working on plugin structure, installation, or distribution, use the `plugin-dev` skills for authoritative guidance.

### Available Plugin-Dev Skills

| Skill | Use When |
|-------|----------|
| `plugin-dev:plugin-structure` | Plugin manifest, directory layout, component organization |
| `plugin-dev:skill-development` | Writing SKILL.md files, descriptions, progressive disclosure |
| `plugin-dev:command-development` | Slash commands, YAML frontmatter, arguments |
| `plugin-dev:agent-development` | Subagent definitions, triggering, tools |
| `plugin-dev:hook-development` | Event hooks, PreToolUse/PostToolUse, validation |
| `plugin-dev:mcp-integration` | MCP server configuration, external services |
| `plugin-dev:plugin-settings` | Plugin configuration, .local.md files |

### Plugin Installation (Marketplace)

Users install this plugin via the Claude Code marketplace:

```bash
# Add the marketplace
/plugin marketplace add hiivmind/hiivmind-corpus

# Install the plugin
/plugin install hiivmind-corpus@hiivmind
```

Or interactively via `/plugin`.

### Key Plugin Conventions

- **Manifest location**: `.claude-plugin/plugin.json` (required)
- **Component directories**: At plugin root, NOT inside `.claude-plugin/`
- **Path references**: Use `${CLAUDE_PLUGIN_ROOT}` for portability
- **Naming**: kebab-case for all directories and files

When in doubt about plugin structure or Claude Code conventions, invoke the relevant `plugin-dev` skill rather than guessing.
