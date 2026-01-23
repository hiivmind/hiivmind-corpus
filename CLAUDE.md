# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hiivmind-corpus** is a meta-plugin system for Claude Code that creates reusable documentation corpus skills for any open-source project. It provides a workflow to index, maintain, and navigate project documentation through Claude Code skills.

The core value: Instead of relying on training data, web search, or on-demand fetching, this creates persistent human-curated indexes that track upstream changes.

## Architecture

```
├── skills/                           # Eight core skills (the meta-plugin)
│   ├── hiivmind-corpus-init/         # Step 1: Create skill structure from template
│   ├── hiivmind-corpus-build/        # Step 2: Analyze docs, build index with user
│   ├── hiivmind-corpus-add-source/   # Add git repos, local docs, or web pages
│   ├── hiivmind-corpus-enhance/      # Deepen coverage on specific topics
│   ├── hiivmind-corpus-refresh/      # Refresh index from upstream changes
│   ├── hiivmind-corpus-upgrade/      # Upgrade existing corpora to latest standards
│   ├── hiivmind-corpus-discover/     # Find all installed corpora
│   └── hiivmind-corpus-navigate/     # Global navigation across all corpora
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
│
├── lib/workflow/                     # Workflow framework documentation
│   ├── consequences.md               # Hub document (links to consequences/)
│   ├── consequences/                 # Modular consequence documentation
│   │   ├── README.md                 # Taxonomy and quick reference
│   │   ├── core/                     # Intrinsic workflow engine (3 files)
│   │   │   ├── workflow.md           # State, evaluation, user interaction, control flow, skill, utility
│   │   │   ├── shared.md             # Common patterns: interpolation, parameters, failure handling
│   │   │   └── intent-detection.md   # 3VL routing system
│   │   └── extensions/               # Domain-specific corpus extensions (5 files)
│   │       ├── README.md             # Extension overview
│   │       ├── file-system.md        # Corpus file operations
│   │       ├── config.md             # Config.yaml operations
│   │       ├── git.md                # Git operations
│   │       ├── web.md                # Web operations
│   │       └── discovery.md          # Corpus discovery
│   ├── schema.md                     # Workflow YAML structure
│   ├── preconditions.md              # Boolean evaluations
│   ├── execution.md                  # Turn loop
│   └── state.md                      # Runtime state structure
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
                                 ↓
                        hiivmind-corpus-upgrade
                      (when meta-plugin updates)
```

**Creation & Maintenance Skills:**
1. **hiivmind-corpus-init**: Clones target repo, analyzes structure, generates skill directory
2. **hiivmind-corpus-add-source**: Adds git repos, local documents, or web pages to existing corpus
3. **hiivmind-corpus-build**: Analyzes docs, builds `index.md` collaboratively with user
4. **hiivmind-corpus-enhance**: Deepens coverage on specific topics (runs on existing index)
5. **hiivmind-corpus-refresh**: Compares against upstream commits, refreshes index based on diff
6. **hiivmind-corpus-upgrade**: Updates existing corpora to latest template standards

**Discovery & Navigation Skills:**
7. **hiivmind-corpus-discover**: Scans for installed corpora across user-level, repo-local, and marketplace locations
8. **hiivmind-corpus-navigate**: Global navigator that routes queries to appropriate per-corpus navigate skills

**Setup & Configuration Skills:**
9. **hiivmind-corpus-awareness**: Adds plugin awareness to CLAUDE.md, teaches Claude when to use corpus skills

**Gateway Command:**
- **/hiivmind-corpus**: Interactive entry point for discovering and interacting with installed corpora

**Agents:**

| Agent | Purpose | Model | Used By |
|-------|---------|-------|---------|
| `source-scanner` | Parallel scanning of documentation sources | haiku | build, refresh |

Agents enable parallel processing of multi-source corpora. When a corpus has 2+ sources, skills spawn multiple `source-scanner` agents concurrently to analyze each source, then aggregate results. This provides 40-60% speedup for corpora with 3+ sources.

## Four Destination Types

`hiivmind-corpus-init` detects context and offers appropriate destinations:

| Type | Location | Best For |
|------|----------|----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-{lib}/` | Personal use everywhere |
| **Repo-local** | `{repo}/.claude-plugin/skills/hiivmind-corpus-{lib}/` | Team sharing via git |
| **Single-corpus** | `hiivmind-corpus-{lib}/` (standalone repo) | Marketplace publishing |
| **Multi-corpus** | `{marketplace}/hiivmind-corpus-{lib}/` | Marketplace publishing (related projects) |

## Generated Structures

**Project-local:**
```
.claude-plugin/skills/hiivmind-corpus-{lib}/
├── SKILL.md                     # Navigate skill
├── data/
│   ├── config.yaml
│   ├── index.md
│   └── project-awareness.md     # Snippet for project CLAUDE.md
└── .source/                     # Gitignored
```

**Standalone plugin:**
```
hiivmind-corpus-{project}/
├── .claude-plugin/plugin.json   # Plugin manifest
├── skills/navigate/SKILL.md     # Project-specific navigation skill
├── data/
│   ├── config.yaml              # Source repo URL, branch, last indexed commit SHA
│   ├── index.md                 # Human-readable markdown index
│   └── project-awareness.md     # Snippet for project CLAUDE.md
├── .source/                     # Local clone (gitignored)
└── README.md
```

## Naming Convention

All components follow the `hiivmind-corpus-*` naming pattern:
- Meta-plugin: `hiivmind-corpus`
- Creation skills: `hiivmind-corpus-init`, `hiivmind-corpus-add-source`, `hiivmind-corpus-build`, `hiivmind-corpus-enhance`, `hiivmind-corpus-refresh`, `hiivmind-corpus-upgrade`
- Discovery skills: `hiivmind-corpus-discover`, `hiivmind-corpus-navigate`
- Setup skills: `hiivmind-corpus-awareness`
- Gateway command: `/hiivmind-corpus`
- Generated plugins: `hiivmind-corpus-{project}` (e.g., `hiivmind-corpus-polars`, `hiivmind-corpus-react`)
- Generated navigate skills: `hiivmind-corpus-navigate-{project}` (per-corpus navigation)

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
| `sources/` | Git/local/web/llms-txt operations | Per-type patterns (git, local, web, generated-docs, llms-txt) |
| `scanning.md` | Documentation analysis | File discovery, framework detection, large files |

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
- **Upgradeable**: `hiivmind-corpus-upgrade` brings existing corpora to latest template standards
- **Discoverable**: `hiivmind-corpus-discover` finds corpora across all installation types
- **Unified access**: `/hiivmind-corpus` gateway provides single entry point for all corpus interaction
- **Global navigation**: `hiivmind-corpus-navigate` routes queries across all installed corpora
- **Tool-agnostic patterns**: `lib/corpus/patterns/` documents algorithms, not executable scripts
- **Cross-platform**: Works on Linux, macOS, and Windows with appropriate tool fallbacks
- **Forked context execution**: Navigate skills run in isolated sub-agent (`context: fork`) to keep main conversation clean (ADR-007)
- **llms.txt support**: Sites with llms.txt manifests get efficient manifest-driven discovery with hash-based change detection (ADR-008)

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

Templates in `templates/` use placeholders like `{{project_name}}`, `{{repo_url}}`, etc. The `hiivmind-corpus-init` skill fills these based on target repository analysis.

## Maintaining Skill Alignment

**IMPORTANT**: All 9 skills must remain aware of each other and share consistent knowledge about corpus features. When modifying any skill, check if other skills need updates.

### Cross-Cutting Concerns

These features span multiple skills and must stay synchronized:

| Feature | Relevant Skills | What to Check |
|---------|-----------------|---------------|
| Destination types | init, enhance, refresh, upgrade, discover | Prerequisites table lists all 4 types |
| Tiered indexes | build, enhance, refresh, upgrade | Detection logic, update handling |
| Source types (git/local/web/generated-docs/llms-txt) | add-source, build, enhance, refresh | Path formats, fetch methods |
| `⚡ GREP` markers | add-source, build, enhance | Large file detection, index format |
| Project awareness | init, upgrade, navigate command (template) | Template exists, command help mentions it, skill has NO project awareness section |
| Config schema | all skills | Schema fields, validation |
| Discovery locations | discover, navigate, gateway command | All 4 location types scanned consistently |
| Corpus status detection | discover, navigate, gateway command | placeholder/built/stale logic |
| Parallel scanning | build, refresh, source-scanner agent | Multi-source detection, agent invocation |
| Entry keywords | enhance, refresh, navigate (template) | Keyword line format, search logic, preserve on refresh |
| Corpus keywords | discover, navigate (global), init, upgrade | config.yaml schema, per-session discovery |
| CLAUDE.md cache | awareness, discover, navigate | Cache format, HTML markers, cache-first lookup |
| Injection targets | awareness | User-level vs repo-level templates |
| Fork context (ADR-007) | navigate (template), upgrade | Frontmatter: context, agent, allowed-tools |
| Command/skill separation | navigate (template), upgrade | Command is thin wrapper (~30 lines), skill has no maintenance refs |
| Modular consequences | all workflow-based skills, gateway command | Domain file references, new consequence types |

### When Adding New Features

1. **Implement in the primary skill** (where the feature originates)
2. **Update skills that validate prerequisites** (enhance, refresh) with awareness
3. **Update hiivmind-corpus-upgrade** to detect and apply the feature to existing corpora
4. **Update templates** if the navigate skill needs new sections
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
refresh ◄───────────┤ ──► source-scanner agent (parallel multi-source)
                     │
upgrade ◄───────────┘ (must know all features to retrofit)
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
