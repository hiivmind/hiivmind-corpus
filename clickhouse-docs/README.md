# ClickHouse Documentation Plugin

A Claude Code plugin providing always-current access to ClickHouse documentation with intelligent navigation.

## Features

- **Indexed Navigation**: Structured index of all ClickHouse documentation with summaries, key concepts, and cross-references
- **Automatic Updates**: Incremental index updates from upstream documentation changes
- **Smart Matching**: Finds relevant docs based on concepts, summaries, and section headings

## Installation

### As a Plugin

```bash
# Add the marketplace containing this plugin
/plugin marketplace add hiivmind/documentation_skills

# Install the plugin
/plugin install clickhouse-docs

# Restart Claude Code
```

### Manual Installation

Clone this repository to your Claude Code plugins directory.

## First-Time Setup

After installing, invoke the maintenance skill to build the index:

```
Please build the ClickHouse documentation index
```

This will:
1. Clone the ClickHouse docs repository to `.source/`
2. Build the full index
3. Write `data/config.yaml` and `data/index.yaml`

## Usage

### Automatic Navigation

The navigation skill is model-invoked. Simply ask questions about ClickHouse:

```
How do I configure replication in ClickHouse?
What's the difference between MergeTree and ReplacingMergeTree?
How do I optimize a slow ClickHouse query?
```

Claude will automatically find and cite relevant documentation.

### Manual Index Updates

Check if updates are available:

```
Check if the ClickHouse documentation index needs updating
```

Force a full rebuild:

```
Rebuild the ClickHouse documentation index from scratch
```

## Skills

### clickhouse-navigate

Finds relevant documentation for ClickHouse-related coding tasks. Automatically invoked when you ask about:

- Table engines (MergeTree, ReplicatedMergeTree, etc.)
- SQL syntax and functions
- Configuration and operations
- Client interfaces and integrations

### clickhouse-maintain

Manages the documentation index:

- **build**: Full index rebuild
- **update**: Incremental update from git diff
- **status**: Check index freshness

## File Structure

```
clickhouse-docs/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   ├── navigate/
│   │   └── SKILL.md          # Documentation navigation
│   └── maintain/
│       └── SKILL.md          # Index maintenance
├── data/
│   ├── config.yaml           # Source repo + settings
│   └── index.yaml            # Generated documentation index
├── .source/                  # Cloned docs repo (gitignored)
└── README.md
```

## Configuration

Edit `data/config.yaml` to customize:

- **include_patterns**: File patterns to index
- **exclude_patterns**: Files to skip
- **language_filter**: Documentation language (default: "en")
- **priority_paths**: Sections to index with more detail

## Requirements

- Git (for cloning and updating documentation)
- Claude Code with plugin support

## License

MIT
