# Pattern: Discovery

## Purpose

Find all installed hiivmind-corpus corpora across user-level, repo-local, and marketplace locations.

## When to Use

- At the start of navigation operations (routing queries to correct corpus)
- When listing available corpora for the user
- When checking corpus health across installations
- Per-session discovery for keyword routing

## Prerequisites

- **Tool detection** (see `tool-detection.md`) - For YAML parsing of corpus metadata
- Knowledge of user's home directory

## Installation Locations

### Location Types

| Type | Unix Path | Windows Path | Use Case |
|------|-----------|--------------|----------|
| **User-level** | `~/.claude/skills/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\skills\hiivmind-corpus-*\` | Personal use across all projects |
| **Repo-local** | `{repo}/.claude-plugin/skills/hiivmind-corpus-*/` | Same | Team sharing via git |
| **Marketplace-single** | `~/.claude/plugins/marketplaces/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\plugins\marketplaces\hiivmind-corpus-*\` | Published single-corpus plugins |
| **Marketplace-multi** | `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/` | `%USERPROFILE%\.claude\plugins\marketplaces\*\hiivmind-corpus-*\` | Published multi-corpus marketplaces |

### Directory Structure Validation

A valid corpus directory must have one of two structures:

**Data-only corpus (preferred for new corpora):**
```
{corpus}/
├── config.yaml       # Required: corpus configuration (root level)
├── index.md          # Documentation index
└── README.md
```

**Legacy plugin corpus:**
```
{corpus}/
├── data/
│   └── config.yaml    # Required: corpus configuration
├── skills/navigate/SKILL.md  # or SKILL.md at root
└── .claude-plugin/plugin.json
```

**Detection order:** Check root-level `config.yaml` first, then `data/config.yaml`.

---

## Discovery Algorithms

### Discover User-Level Corpora

**Algorithm:**
1. Expand home directory path
2. List directories matching `~/.claude/skills/hiivmind-corpus-*/`
3. For each, verify `config.yaml` exists (check root first, then `data/`)
4. Extract corpus name from directory name

**Using bash:**
```bash
for d in ~/.claude/skills/hiivmind-corpus-*/; do
    [ -d "$d" ] || continue
    # Check root first (data-only), then data/ (legacy)
    if [ -f "${d}config.yaml" ] || [ -f "${d}data/config.yaml" ]; then
        echo "user-level|$(basename "$d")|$d"
    fi
done
```

**Using PowerShell:**
```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\hiivmind-corpus-*" -Directory | ForEach-Object {
    # Check root first (data-only), then data/ (legacy)
    if ((Test-Path "$($_.FullName)\config.yaml") -or (Test-Path "$($_.FullName)\data\config.yaml")) {
        "user-level|$($_.Name)|$($_.FullName)\"
    }
}
```

**Using Claude tools:**
```
# Data-only corpora (check first)
Glob: ~/.claude/skills/hiivmind-corpus-*/config.yaml

# Legacy corpora
Glob: ~/.claude/skills/hiivmind-corpus-*/data/config.yaml
```
Then extract corpus paths from results, deduplicate if needed.

---

### Discover Repo-Local Corpora

**Algorithm:**
1. Check for `.claude-plugin/skills/` in current directory (or specified base)
2. List directories matching `hiivmind-corpus-*/`
3. Verify `config.yaml` exists (check root first, then `data/`)

**Using bash:**
```bash
base_dir="${1:-.}"
for d in "$base_dir"/.claude-plugin/skills/hiivmind-corpus-*/; do
    [ -d "$d" ] || continue
    # Check root first (data-only), then data/ (legacy)
    if [ -f "${d}config.yaml" ] || [ -f "${d}data/config.yaml" ]; then
        echo "repo-local|$(basename "$d")|$d"
    fi
done
```

**Using PowerShell:**
```powershell
$baseDir = if ($args[0]) { $args[0] } else { "." }
Get-ChildItem "$baseDir\.claude-plugin\skills\hiivmind-corpus-*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    # Check root first (data-only), then data/ (legacy)
    if ((Test-Path "$($_.FullName)\config.yaml") -or (Test-Path "$($_.FullName)\data\config.yaml")) {
        "repo-local|$($_.Name)|$($_.FullName)\"
    }
}
```

**Using Claude tools:**
```
# Data-only corpora (check first)
Glob: .claude-plugin/skills/hiivmind-corpus-*/config.yaml

# Legacy corpora
Glob: .claude-plugin/skills/hiivmind-corpus-*/data/config.yaml
```

---

### Discover Marketplace Corpora (Multi-Corpus)

**Algorithm:**
1. List directories in `~/.claude/plugins/marketplaces/`
2. For each marketplace, look for `hiivmind-corpus-*/` subdirectories
3. Verify each has `config.yaml` (check root first, then `data/`)

**Using bash:**
```bash
for d in ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/; do
    [ -d "$d" ] || continue
    # Check root first (data-only), then data/ (legacy)
    if [ -f "${d}config.yaml" ] || [ -f "${d}data/config.yaml" ]; then
        echo "marketplace|$(basename "$d")|$d"
    fi
done
```

**Using PowerShell:**
```powershell
Get-ChildItem "$env:USERPROFILE\.claude\plugins\marketplaces\*\hiivmind-corpus-*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    # Check root first (data-only), then data/ (legacy)
    if ((Test-Path "$($_.FullName)\config.yaml") -or (Test-Path "$($_.FullName)\data\config.yaml")) {
        "marketplace|$($_.Name)|$($_.FullName)\"
    }
}
```

**Using Claude tools:**
```
# Data-only corpora (check first)
Glob: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/config.yaml

# Legacy corpora
Glob: ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/data/config.yaml
```

---

### Discover Marketplace Corpora (Single-Corpus)

**Algorithm:**
1. List `hiivmind-corpus-*/` directories directly in marketplaces
2. Skip if has child `hiivmind-corpus-*/` dirs (that's a multi-corpus marketplace)
3. Verify has `config.yaml` (check root first, then `data/`)

**Using bash:**
```bash
for d in ~/.claude/plugins/marketplaces/hiivmind-corpus-*/; do
    [ -d "$d" ] || continue
    # Skip multi-corpus marketplaces
    ls "$d"/hiivmind-corpus-*/ >/dev/null 2>&1 && continue
    # Check root first (data-only), then data/ (legacy)
    if [ -f "${d}config.yaml" ] || [ -f "${d}data/config.yaml" ]; then
        echo "marketplace-single|$(basename "$d")|$d"
    fi
done
```

**Using PowerShell:**
```powershell
Get-ChildItem "$env:USERPROFILE\.claude\plugins\marketplaces\hiivmind-corpus-*" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    # Skip if has child corpus directories
    $hasChildren = Get-ChildItem "$($_.FullName)\hiivmind-corpus-*" -Directory -ErrorAction SilentlyContinue
    # Check root first (data-only), then data/ (legacy)
    if (-not $hasChildren -and ((Test-Path "$($_.FullName)\config.yaml") -or (Test-Path "$($_.FullName)\data\config.yaml"))) {
        "marketplace-single|$($_.Name)|$($_.FullName)\"
    }
}
```

---

### Discover All Corpora

**Algorithm:**
1. Run all four discovery methods
2. Combine results
3. Deduplicate if necessary (same corpus could appear in multiple locations)

**Using bash:**
```bash
discover_all() {
    # Helper to check for config.yaml (root or data/)
    has_config() {
        [ -f "${1}config.yaml" ] || [ -f "${1}data/config.yaml" ]
    }

    # User-level
    for d in ~/.claude/skills/hiivmind-corpus-*/; do
        [ -d "$d" ] && has_config "$d" && echo "user-level|$(basename "$d")|$d"
    done

    # Repo-local
    for d in ./.claude-plugin/skills/hiivmind-corpus-*/; do
        [ -d "$d" ] && has_config "$d" && echo "repo-local|$(basename "$d")|$d"
    done

    # Marketplace multi
    for d in ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/; do
        [ -d "$d" ] && has_config "$d" && echo "marketplace|$(basename "$d")|$d"
    done

    # Marketplace single
    for d in ~/.claude/plugins/marketplaces/hiivmind-corpus-*/; do
        [ -d "$d" ] || continue
        ls "$d"/hiivmind-corpus-*/ >/dev/null 2>&1 && continue
        has_config "$d" && echo "marketplace-single|$(basename "$d")|$d"
    done
}
```

---

## Status Detection

### Determine Corpus Status

For each discovered corpus, determine if it's built or placeholder.

**Algorithm:**
1. Read `data/index.md`
2. If contains "Run hiivmind-corpus-build" → `placeholder`
3. If has real content → `built`
4. If file missing → `no-index`

**Using bash:**
```bash
get_status() {
    local corpus_path="$1"
    local index_file="${corpus_path}data/index.md"

    if [ ! -f "$index_file" ]; then
        echo "no-index"
    elif grep -q "Run hiivmind-corpus-build" "$index_file" 2>/dev/null; then
        echo "placeholder"
    else
        echo "built"
    fi
}
```

**Using Claude tools:**
```
Read: {corpus_path}/data/index.md
Check if content contains "Run hiivmind-corpus-build"
```

---

## Metadata Extraction

### Get Routing Metadata

For per-session routing, extract metadata needed to match queries to corpora.

**Fields needed:**
- `name` - Corpus identifier
- `display_name` - Human-readable name
- `keywords` - Routing keywords
- `status` - built/placeholder/no-index

**Algorithm:**
1. For each corpus, read `data/config.yaml`
2. Extract `corpus.display_name` (or infer from name)
3. Extract `corpus.keywords[]` (or infer from name)
4. Determine status from index.md

**Output format (for routing):**
```
name|display_name|keywords|status|path
hiivmind-corpus-polars|Polars|polars,dataframe,lazy|built|/path/to/corpus/
```

See `config-parsing.md` for YAML extraction methods.

---

## Filtering

### Filter by Status

**Built corpora only:**
```bash
discover_all | while IFS='|' read -r type name path; do
    [ "$(get_status "$path")" = "built" ] && echo "$type|$name|$path"
done
```

**Placeholder corpora only:**
```bash
discover_all | while IFS='|' read -r type name path; do
    [ "$(get_status "$path")" = "placeholder" ] && echo "$type|$name|$path"
done
```

### Filter by Name Pattern

```bash
# Find polars corpus
discover_all | grep "|hiivmind-corpus-polars|"

# Find all corpora containing "data"
discover_all | grep "data"
```

### Filter by Type

```bash
# User-level only
discover_all | grep "^user-level|"

# Marketplace only
discover_all | grep "^marketplace"
```

---

## Output Formatting

### Simple List

```
hiivmind-corpus-polars (user-level) - built
hiivmind-corpus-react (marketplace) - built
hiivmind-corpus-project (repo-local) - placeholder
```

### Table Format

```
Name                    | Type        | Status      | Path
hiivmind-corpus-polars  | user-level  | built       | ~/.claude/skills/...
hiivmind-corpus-react   | marketplace | built       | ~/.claude/plugins/...
```

### YAML Format (for routing)

```yaml
corpora:
  - name: hiivmind-corpus-polars
    display_name: Polars
    keywords: [polars, dataframe, lazy]
    status: built
    path: /home/user/.claude/skills/hiivmind-corpus-polars/
```

---

## Cross-Platform Notes

| Aspect | Unix | Windows |
|--------|------|---------|
| Home directory | `$HOME`, `~` | `$env:USERPROFILE` |
| Glob expansion | Shell expands `*` | PowerShell uses `Get-ChildItem` |
| Path separator | `/` | `\` (PowerShell accepts both) |
| Checking directory | `[ -d "$d" ]` | `Test-Path $d -PathType Container` |

---

## Error Handling

### No Corpora Found

```
No hiivmind-corpus plugins found.

Checked locations:
- ~/.claude/skills/ (user-level)
- ./.claude-plugin/skills/ (repo-local)
- ~/.claude/plugins/marketplaces/ (marketplace)

To create a corpus:
1. Run `hiivmind-corpus-init` to initialize a new corpus
2. Or install from marketplace: /plugin marketplace add hiivmind/hiivmind-corpus-data
```

### Permission Issues

```
Unable to read directory: ~/.claude/skills/
Permission denied.

Check directory permissions: ls -la ~/.claude/
```

### Malformed Corpus

```
Found corpus directory but missing config.yaml:
  ~/.claude/skills/hiivmind-corpus-broken/

This corpus may be corrupted or incompletely installed.
Consider removing and reinstalling.
```

---

## Examples

### Example 1: List All Built Corpora

**User request:** "What documentation corpora do I have?"

**Process:**
1. Discover all corpora across all locations
2. Filter to built status only
3. Extract routing metadata
4. Present formatted list

**Sample output:**
```
Found 3 built documentation corpora:

1. Polars (hiivmind-corpus-polars)
   Location: user-level
   Keywords: polars, dataframe, lazy, expression

2. React (hiivmind-corpus-react)
   Location: marketplace (hiivmind-corpus-data)
   Keywords: react, hooks, components

3. Project Docs (hiivmind-corpus-project)
   Location: repo-local
   Keywords: api, internal
```

### Example 2: Route Query to Corpus

**User query:** "How do I filter a dataframe?"

**Routing process:**
1. Discover all built corpora
2. Extract keywords for each
3. Match "dataframe" against keywords
4. Found: hiivmind-corpus-polars has keyword "dataframe"
5. Route query to that corpus's navigate skill

---

## Related Patterns

- **tool-detection.md** - Required for YAML parsing capability
- **config-parsing.md** - Methods to extract corpus metadata
- **status.md** - Detailed status and freshness checking
- **paths.md** - Path resolution within corpora
