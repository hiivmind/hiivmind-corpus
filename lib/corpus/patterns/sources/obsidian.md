# Pattern: Obsidian Vault Source

## Purpose

Handle Obsidian vault sources for corpus indexing. Supports two storage modes: git-backed (cloned repo) and local (filesystem path). The `type: obsidian` signals the extraction pipeline to run.

## When to Use

- Source `type` is `obsidian` in config.yaml
- User provides an Obsidian vault (identified by `.obsidian/` directory)
- Processing vault content during add-source, build, or refresh

## Prerequisites

- For git-backed: `gh` CLI authenticated, repo accessible
- For local: vault path exists and is readable

---

### Detect Obsidian Vault

**Algorithm:**

1. If `repo_url` is present in source config → git-backed mode
2. If `vault_path` is present in source config → local mode
3. To auto-detect: check if target directory contains `.obsidian/` subdirectory

**Using bash (git-backed):**

```bash
# Check if remote repo is an Obsidian vault
gh api repos/{owner}/{repo}/contents/.obsidian --jq '.type' 2>/dev/null
# Returns "dir" if Obsidian vault
```

**Using Claude tools:**

```
Glob: pattern=".obsidian" path={source_path}
If match found → Obsidian vault confirmed
```

---

### Clone or Access

**Git-backed mode** — identical to `git` source type:

**Algorithm:**

1. Clone to `.source/{source_id}/` with `--depth 1`
2. Record SHA via `git rev-parse HEAD`
3. Navigate via `gh api repos/{owner}/{repo}/contents/{path}` at read time

**Using bash:**

```bash
git clone --depth 1 --branch {branch} https://github.com/{owner}/{repo}.git .source/{source_id}/
cd .source/{source_id} && git rev-parse HEAD
```

**Local mode** — identical to `local` source type:

**Algorithm:**

1. Read directly from `vault_path`
2. Track change via directory modification timestamp
3. Navigate via direct file read at read time

---

### Default Exclude Patterns

Obsidian vaults contain configuration and binary files that should not be indexed:

```yaml
exclude_patterns:
  - "**/.obsidian/plugins/**"     # Plugin JS/CSS bundles
  - "**/.obsidian/*.json"         # Vault config files
  - "**/.obsidian/workspace*"     # Workspace state
  - "**/images/**"                # Binary image assets
  - "**/.trash/**"                # Obsidian trash
  - "**/templates/**"             # Note templates (boilerplate, not content)
```

The `.obsidian/` directory itself is excluded from indexing but used for vault detection.

---

### Wikilink Resolution

Obsidian uses shortest-path wikilink matching. `[[Guest list]]` resolves to the file named `Guest list.md` regardless of its directory depth.

**Algorithm:**

1. Build a filename→path lookup table from all `.md` files in the source
2. For each `[[link]]` encountered:
   a. Strip any `|alias` suffix (e.g., `[[file|display text]]` → `file`)
   b. Strip any `#heading` suffix, preserve separately (e.g., `[[file#section]]` → `file`, anchor=`section`)
   c. Look up `{link}.md` in the filename table
   d. If exactly one match → resolved
   e. If multiple matches (filename collision) → skip with warning, do not add to extraction output
   f. If no match → skip (may be a non-existent note placeholder)

**Using bash:**

```bash
# Build lookup table
find .source/{source_id}/ -name '*.md' -printf '%f\t%P\n' | sort > /tmp/filename-lookup.tsv

# Extract wikilinks from a file
grep -oP '\[\[([^\]|#]+)' {file} | sed 's/\[\[//' | sort -u
```

**Using Claude tools:**

```
Glob: pattern="**/*.md" path=.source/{source_id}/
# Build lookup from results

Grep: pattern="\[\[([^\]|#]+)" path={file} output_mode=content
# Parse matches for link targets
```

---

### Config Entry Format

```yaml
sources:
  - id: "{source_id}"
    type: "obsidian"
    # Git-backed mode (one of):
    repo_url: "https://github.com/{owner}/{repo}"
    repo_owner: "{owner}"
    repo_name: "{repo}"
    branch: "{branch}"
    last_commit_sha: "{sha}"
    # Local mode (alternative):
    # vault_path: "{absolute_path}"

    include_patterns: ["**/*.md"]
    exclude_patterns:
      - "**/.obsidian/plugins/**"
      - "**/.obsidian/*.json"
      - "**/.obsidian/workspace*"
      - "**/images/**"
      - "**/.trash/**"
      - "**/templates/**"

    extraction:
      wikilinks: true
      frontmatter: true
      tags: true
      dataview: false

    last_indexed_at: null
```

---

### Index Path Format

Obsidian source entries use the standard `{source_id}:{path}` format:

```markdown
- **Dashboard Home** `dashboardpp:Dashboard++.md` - Main vault dashboard with links to all areas
- **S'mores Recipe** `dashboardpp:Family/Recipes/Smores.md` - Graham cracker s'mores recipe
```

With optional sub-file anchors for atomic concept entries:

```markdown
- **Family Section** `dashboardpp:Dashboard++.md#family` - Family activities hub
```

---

## Related Patterns

- [extraction.md](../extraction.md) — Cross-cutting extraction pipeline used by this source type
- [git.md](git.md) — Git-backed storage mode follows this pattern
- [local.md](local.md) — Local storage mode follows this pattern
- [shared.md](shared.md) — Shared source type operations
