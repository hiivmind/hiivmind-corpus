# Corpus Pattern Library Index

Tool-agnostic pattern documentation for hiivmind-corpus operations. These patterns describe algorithms with multiple implementation options, letting skills adapt to available tools at runtime.

## Design Philosophy

Instead of executable bash scripts (which lock into Linux/macOS), pattern documentation:

- **Describes algorithms**, not implementations
- **Provides multiple tool options** (yq, python, grep fallbacks)
- **Prioritizes Claude tools** (Glob, Grep, Read) over bash commands
- **Enables cross-platform support** (Linux, macOS, Windows)

## Pattern Files

| Pattern | Purpose | When to Reference |
|---------|---------|-------------------|
| [tool-detection.md](patterns/tool-detection.md) | Detect available tools | Start of operations requiring specific tools |
| [config-parsing.md](patterns/config-parsing.md) | Extract YAML fields | Reading config.yaml |
| [discovery.md](patterns/discovery.md) | Find installed corpora | Discovery and navigation skills |
| [status.md](patterns/status.md) | Check corpus freshness | Refresh, navigate, gateway operations |
| [paths.md](patterns/paths.md) | Resolve paths within corpora | All navigation and file operations |
| [sources/](patterns/sources/) | Git/local/web operations | Init, add-source, build, refresh |
| [scanning.md](patterns/scanning.md) | File discovery and analysis | Build, enhance, add-source |
| [capability-awareness.md](patterns/capability-awareness.md) | Plugin skill registry & CLAUDE.md templates | Awareness skill, cache format |

## How to Use Patterns

Skills reference patterns with a `**See:**` directive:

```markdown
## Step 1: Validate Prerequisites

**See:** `lib/corpus/patterns/config-parsing.md` and `lib/corpus/patterns/status.md`

Read `data/config.yaml` to check configuration.
```

The LLM then:
1. Consults the referenced pattern(s) for algorithms
2. Detects available tools (see tool-detection.md)
3. Uses the best available implementation option
4. Falls back gracefully when tools are missing

## Tool Tiers

From `patterns/tool-detection.md`:

| Tier | Tools | Behavior |
|------|-------|----------|
| Required | git | Abort if missing |
| Strongly Recommended | yq, python+pyyaml | Warn if missing, use fallbacks |
| Helpful | rg, jq | Use if available, no warning |
| Always Available | grep, find, ls | Baseline fallbacks |

## Pattern Categories

### Configuration & Status
- **config-parsing.md** - How to extract corpus metadata from YAML
- **status.md** - How to determine if an index is built, placeholder, or stale
- **tool-detection.md** - How to detect what tools are available

### Discovery & Navigation
- **discovery.md** - How to find corpora across all installation locations
- **paths.md** - How to resolve source references to actual files

### Source Management
- **sources/** - How to clone, fetch, and update documentation sources (per-type patterns)
- **scanning.md** - How to analyze documentation structure and detect large files

## Migration from Shell Scripts

This pattern library replaces the previous shell function library (`corpus-*-functions.sh` files). The migration:

1. **Converted functions to algorithms** - Each bash function became a documented algorithm
2. **Added tool options** - Each algorithm shows yq, python, and fallback implementations
3. **Prioritized Claude tools** - Glob/Grep/Read shown first where applicable
4. **Removed platform dependencies** - No more bash-only constructs

Skills were updated to reference patterns with `**See:**` directives instead of `source` commands.

## Contributing New Patterns

When adding a new pattern:

1. Create `patterns/{name}.md` with clear sections:
   - Purpose and when to use
   - Algorithm description
   - Implementation options (Claude tools, yq, python, bash fallback)
   - Examples
   - Cross-references to related patterns

2. Update this index with the new pattern

3. Update CLAUDE.md architecture diagram

4. Reference the pattern in relevant skills with `**See:**` directive
