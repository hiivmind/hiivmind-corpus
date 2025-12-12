# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hiivmind-corpus** is a meta-plugin system for Claude Code that creates reusable documentation corpus skills for any open-source project. It provides a workflow to index, maintain, and navigate project documentation through Claude Code skills.

The core value: Instead of relying on training data, web search, or on-demand fetching, this creates persistent human-curated indexes that track upstream changes.

## Architecture

```
├── skills/                           # Six core skills (the meta-plugin)
│   ├── hiivmind-corpus-init/         # Step 1: Create skill structure from template
│   ├── hiivmind-corpus-build/        # Step 2: Analyze docs, build index with user
│   ├── hiivmind-corpus-add-source/   # Add git repos, local docs, or web pages
│   ├── hiivmind-corpus-enhance/      # Deepen coverage on specific topics
│   ├── hiivmind-corpus-refresh/      # Refresh index from upstream changes
│   └── hiivmind-corpus-upgrade/      # Upgrade existing corpora to latest standards
│
├── templates/                        # Templates for generating new corpus skills
│
└── docs/                             # Specifications and design docs
```

## Skill Lifecycle

```
hiivmind-corpus-init → hiivmind-corpus-build → hiivmind-corpus-refresh
       (once)                 (once)                  (periodic)
                                 ↓
                        hiivmind-corpus-enhance
                            (as needed)
                                 ↓
                        hiivmind-corpus-upgrade
                      (when meta-plugin updates)
```

1. **hiivmind-corpus-init**: Clones target repo, analyzes structure, generates skill directory
2. **hiivmind-corpus-add-source**: Adds git repos, local documents, or web pages to existing corpus
3. **hiivmind-corpus-build**: Analyzes docs, builds `index.md` collaboratively with user
4. **hiivmind-corpus-enhance**: Deepens coverage on specific topics (runs on existing index)
5. **hiivmind-corpus-refresh**: Compares against upstream commits, refreshes index based on diff
6. **hiivmind-corpus-upgrade**: Updates existing corpora to latest template standards

## Two Destination Types

`hiivmind-corpus-init` asks users to choose where the skill should live:

### Project-local skill
- Created in `.claude-plugin/skills/hiivmind-corpus-{lib}/` within an existing project
- No marketplace installation needed—just opening the project activates it
- Great for teams: everyone who clones the repo gets the skill
- Example: A data analysis project that needs Polars docs

### Standalone plugin
- Created as a separate `hiivmind-corpus-{lib}/` directory (becomes its own repo)
- Requires marketplace installation for reuse
- Available across all projects for the user
- Example: "I always want React docs available everywhere"

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
- Skills: `hiivmind-corpus-init`, `hiivmind-corpus-add-source`, `hiivmind-corpus-build`, `hiivmind-corpus-enhance`, `hiivmind-corpus-refresh`, `hiivmind-corpus-upgrade`
- Generated skills: `hiivmind-corpus-{project}` (e.g., `hiivmind-corpus-polars`, `hiivmind-corpus-react`)

## Key Design Decisions

- **Human-readable indexes**: Simple markdown with headings, not complex schemas
- **Collaborative building**: User guides what's important, not automation
- **Works without local clone**: Falls back to raw GitHub URLs
- **Change tracking**: Stores commit SHA to know when index is stale
- **Per-project skills**: Each corpus skill has its own navigate skill for discoverability
- **Project awareness**: Corpora include snippets for injecting into project CLAUDE.md files
- **Upgradeable**: `hiivmind-corpus-upgrade` brings existing corpora to latest template standards

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

**IMPORTANT**: All 6 skills must remain aware of each other and share consistent knowledge about corpus features. When modifying any skill, check if other skills need updates.

### Cross-Cutting Concerns

These features span multiple skills and must stay synchronized:

| Feature | Relevant Skills | What to Check |
|---------|-----------------|---------------|
| Destination types | init, enhance, refresh, upgrade | Prerequisites table lists all 4 types |
| Tiered indexes | build, enhance, refresh, upgrade | Detection logic, update handling |
| Source types (git/local/web) | add-source, build, enhance, refresh | Path formats, fetch methods |
| `⚡ GREP` markers | add-source, build, enhance | Large file detection, index format |
| Project awareness | init, upgrade | Template exists, navigate skill section |
| Config schema | all skills | Schema fields, validation |

### When Adding New Features

1. **Implement in the primary skill** (where the feature originates)
2. **Update skills that validate prerequisites** (enhance, refresh) with awareness
3. **Update hiivmind-corpus-upgrade** to detect and apply the feature to existing corpora
4. **Update templates** if the navigate skill needs new sections
5. **Update this CLAUDE.md** with the feature in Key Design Decisions and/or this table

### Skill Dependency Chain

```
init ──────────► templates/
                    │
add-source ◄───────┤
                    │
build ◄────────────┤
                    │
enhance ◄──────────┤ (must know all features to validate)
                    │
refresh ◄──────────┤ (must know all features to validate)
                    │
upgrade ◄──────────┘ (must know all features to retrofit)
```

### Reference Sections

Every skill has a `## Reference` section at the bottom listing all other skills. When adding a new skill, update all existing skills' Reference sections.
