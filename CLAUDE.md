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
├── lib/corpus/                       # Shell function library
│   ├── corpus-discovery-functions.sh # Find corpora across all locations
│   ├── corpus-status-functions.sh    # Check index status and freshness
│   ├── corpus-path-functions.sh      # Resolve paths within corpora
│   ├── corpus-context-functions.sh   # Context detection for init
│   ├── corpus-source-functions.sh    # Git/local/web source operations
│   ├── corpus-scan-functions.sh      # File scanning and analysis
│   └── corpus-index.md               # Library documentation
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
- Gateway command: `/hiivmind-corpus`
- Generated plugins: `hiivmind-corpus-{project}` (e.g., `hiivmind-corpus-polars`, `hiivmind-corpus-react`)
- Generated navigate skills: `hiivmind-corpus-navigate-{project}` (per-corpus navigation)

## Shell Function Library

The `lib/corpus/` directory contains reusable bash functions following hiivmind-pulse-gh patterns:

```bash
# Source the library
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-status-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-path-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-context-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-source-functions.sh"
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-scan-functions.sh"

# Composable operations
discover_all | filter_built | list_names
get_index_status "$corpus_path"
analyze_context  # → "established-project" | "fresh" | "marketplace-existing"
clone_source "https://github.com/user/repo" "source-id" "$corpus_path"
count_docs ".source/polars/docs"
```

| File | Functions | Purpose |
|------|-----------|---------|
| `corpus-discovery-functions.sh` | `discover_*`, `filter_*`, `format_*` | Find installed corpora |
| `corpus-status-functions.sh` | `get_*`, `check_*`, `compare_*` | Status and freshness |
| `corpus-path-functions.sh` | `get_*_path`, `resolve_*`, `exists_*` | Path resolution |
| `corpus-context-functions.sh` | `detect_*`, `analyze_*`, `scaffold_*`, `verify_*` | Context detection for init |
| `corpus-source-functions.sh` | `clone_*`, `fetch_*`, `pull_*`, `parse_*` | Git/local/web source operations |
| `corpus-scan-functions.sh` | `scan_*`, `detect_*`, `find_*`, `extract_*` | File scanning and analysis |
| `corpus-index.md` | - | Full function documentation |

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
- **Composable library**: `lib/corpus/` provides pipe-first bash functions for discovery and status

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

**IMPORTANT**: All 8 skills must remain aware of each other and share consistent knowledge about corpus features. When modifying any skill, check if other skills need updates.

### Cross-Cutting Concerns

These features span multiple skills and must stay synchronized:

| Feature | Relevant Skills | What to Check |
|---------|-----------------|---------------|
| Destination types | init, enhance, refresh, upgrade, discover | Prerequisites table lists all 4 types |
| Tiered indexes | build, enhance, refresh, upgrade | Detection logic, update handling |
| Source types (git/local/web) | add-source, build, enhance, refresh | Path formats, fetch methods |
| `⚡ GREP` markers | add-source, build, enhance | Large file detection, index format |
| Project awareness | init, upgrade | Template exists, navigate skill section |
| Config schema | all skills | Schema fields, validation |
| Discovery locations | discover, navigate, gateway command | All 4 location types scanned consistently |
| Corpus status detection | discover, navigate, gateway command | placeholder/built/stale logic |
| Parallel scanning | build, refresh, source-scanner agent | Multi-source detection, agent invocation |

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
         ├── discover ◄──── scans all installation locations
         │
         └── navigate ◄──── routes to per-corpus navigate skills
                    │
init ──────────► templates/
                    │
add-source ◄───────┤
                    │
build ◄────────────┤ ──► source-scanner agent (parallel multi-source)
                    │
enhance ◄──────────┤ (must know all features to validate)
                    │
refresh ◄──────────┤ ──► source-scanner agent (parallel multi-source)
                    │
upgrade ◄──────────┘ (must know all features to retrofit)
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
