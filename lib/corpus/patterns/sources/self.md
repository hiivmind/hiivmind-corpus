# Pattern: Self Source

Manage documentation from the containing repository itself. The corpus indexes content from the repo it lives in.

## When to Use

- Embedded corpora at `.hiivmind/corpus/` within a documentation repo
- Obsidian vaults, docs sites, or knowledge bases that want to index their own content
- The source IS the repo — no external fetching needed

## Prerequisites

- **Git** — required for freshness tracking via `git log`
- **Config parsing** (see `../config-parsing.md`) — reading source configuration

## Source Schema

```yaml
- id: "{source_id}"          # User-chosen identifier (e.g., "vault", "docs")
  type: "self"
  docs_root: "."              # Relative to repo root. "." = whole repo, "docs" = docs/ subtree
  last_commit_sha: null       # Scoped to docs_root via git log
  last_indexed_at: null
```

**What self does NOT have** (compared to `type: git`): No `repo_url`, `repo_owner`, `repo_name`, `branch`. The repo is implicit.

## Path Resolution

Index entries use the standard `{source_id}:{relative_path}` format.

For `type: self`, resolution is:

```
{source_id}:{relative_path} → {repo_root}/{docs_root}/{relative_path}
```

**`docs_root` normalization:** `"."` is normalized to empty string before path concatenation. This is consistent with how existing git sources handle `docs_root: ""` / null (the segment is omitted). The `resolve_source_ref()` function in `paths.md` uses `[ -n "$docs_root" ]` to decide whether to insert the segment — `"."` must be treated as equivalent to empty.

Example: `vault:notes/architecture.md` with `docs_root: "."` → `/home/user/obsidian-vault/notes/architecture.md`

### Using bash

```bash
resolve_self_source() {
    local repo_root="$1"
    local docs_root="$2"
    local relative_path="$3"

    # Normalize "." to empty
    [ "$docs_root" = "." ] && docs_root=""

    if [ -n "$docs_root" ]; then
        echo "$repo_root/$docs_root/$relative_path"
    else
        echo "$repo_root/$relative_path"
    fi
}
```

### Using Claude tools

```
# Direct file read — no cloning or fetching needed
Read: {repo_root}/{docs_root}/{relative_path}
```

## Freshness Tracking

Scoped to `docs_root` so unrelated commits don't trigger staleness:

```bash
get_self_sha() {
    local repo_root="$1"
    local docs_root="$2"

    # Normalize "." to empty
    [ "$docs_root" = "." ] && docs_root=""

    if [ -n "$docs_root" ]; then
        git -C "$repo_root" log -1 --format=%H -- "$docs_root"
    else
        git -C "$repo_root" log -1 --format=%H
    fi
}
```

**Note:** When `docs_root` is `"."` (whole repo), `git log -1 --format=%H` returns the most recent commit on the branch — any commit marks the corpus stale. The scoping benefit only applies when `docs_root` targets a subdirectory like `"docs"`.

### Compare for staleness

```bash
check_self_freshness() {
    local repo_root="$1"
    local docs_root="$2"
    local indexed_sha="$3"

    local current_sha
    current_sha=$(get_self_sha "$repo_root" "$docs_root")

    if [ "$current_sha" = "$indexed_sha" ]; then
        echo "current"
    else
        echo "stale"
    fi
}
```

### Get changed files (for refresh)

```bash
get_self_changes() {
    local repo_root="$1"
    local docs_root="$2"
    local old_sha="$3"
    local new_sha="$4"

    # Normalize "." to empty
    [ "$docs_root" = "." ] && docs_root=""

    if [ -n "$docs_root" ]; then
        git -C "$repo_root" diff --name-status "$old_sha..$new_sha" -- "$docs_root"
    else
        git -C "$repo_root" diff --name-status "$old_sha..$new_sha"
    fi
}
```

## Auto-Exclusions

Build and refresh MUST auto-exclude `.hiivmind/` from scanning to avoid indexing the corpus's own files.

Add to `settings.exclude_patterns` in config.yaml during init:

```yaml
settings:
  exclude_patterns:
    - "**/_*.md"
    - "**/_snippets/**"
    - ".hiivmind/**"
```

## Storage

Self sources do NOT use:
- `.source/` — the repo root IS the source
- `.cache/` — no web content to cache
- `uploads/` — repo files are the content

## Relationship to `type: obsidian`

`type: obsidian` is for standalone corpora that index an Obsidian vault from a separate repo. `type: self` is for embedded corpora where the index lives inside the vault. The distinction: `type: obsidian` = external index pointing at a vault; `type: self` = index co-located with the content.

## Related Patterns

- **paths.md** — Full path resolution including `type: self`
- **freshness.md** — SHA-gated freshness checks
- **scanning.md** — File discovery patterns
- **config-parsing.md** — Config schema
