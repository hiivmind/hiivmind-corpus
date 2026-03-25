# Embedded Corpus Design

**Date:** 2026-03-25
**Status:** Draft
**Scope:** Additive feature — no breaking changes to existing corpora

## Problem

The existing corpus pattern requires a standalone repository for each corpus. Content is cached or referenced inside the corpus repository, and sources are external (git repos, web pages, local uploads).

For documentation repositories — Obsidian vaults, docs sites, knowledge bases — this is backwards. The repo *is* the documentation. Creating a separate corpus repo to index it adds unnecessary indirection: the source and the index live apart, freshness tracking points at a remote, and the corpus must be installed separately.

## Solution

Support **embedded corpora** — a corpus that lives inside the documentation repo it indexes, at `.hiivmind/corpus/`. Same file structure as standalone corpora, powered by a new `type: self` source type.

## Design

### 1. New Source Type: `type: self`

A new source type in `config.yaml` that means "this repo is the source."

**Schema:**

```yaml
sources:
  - id: vault              # User-chosen identifier
    type: self
    docs_root: "."          # Relative to repo root. "." = whole repo, "docs" = docs/ subtree
    last_commit_sha: null   # Scoped to docs_root via git log
    last_indexed_at: null
```

**What it does NOT have** (compared to `type: git`): No `repo_url`, `repo_owner`, `repo_name`, `branch`. The repo is implicit.

**Path resolution:** Index entries use the standard `{source_id}:{relative_path}` format. For `type: self`, resolution is:

```
{source_id}:{relative_path}  →  {repo_root}/{docs_root}/{relative_path}
```

**`docs_root` normalization:** `"."` is normalized to empty string before path concatenation, consistent with how existing git sources handle `docs_root: ""` / null (omitting the segment entirely). The existing `resolve_source_ref()` in `paths.md` uses `[ -n "$docs_root" ]` to decide whether to insert the segment — `"."` must be treated as equivalent to empty in this check. This normalization is documented in `lib/corpus/patterns/sources/self.md` and applied in the `paths.md` update.

Example: `vault:notes/architecture.md` with `docs_root: "."` → `/home/user/obsidian-vault/notes/architecture.md` (not `/home/user/obsidian-vault/./notes/architecture.md`)

**Note on scoping:** When `docs_root` is `"."` (whole repo), `git log -1 --format=%H -- .` is equivalent to `git log -1 --format=%H` — any commit marks the corpus stale, not just documentation changes. The scoping benefit only applies when `docs_root` targets a subdirectory like `"docs"`.

**Freshness tracking:** Scoped to `docs_root` so unrelated commits don't trigger staleness:

```bash
git log -1 --format=%H -- {docs_root}
```

**Auto-exclusions:** Build and refresh auto-exclude `.hiivmind/` from scanning to avoid indexing the corpus's own files.

**Relationship to `type: obsidian`:** The existing source taxonomy includes `type: obsidian` for standalone corpora that index an Obsidian vault from a separate repo. `type: self` is for embedded corpora where the index lives *inside* the vault. The distinction: `type: obsidian` = external index pointing at a vault; `type: self` = index co-located with the content. The decision tree in `sources/README.md` should be updated to route "corpus lives inside the source repo" to `type: self`.

**Pattern doc:** New file at `lib/corpus/patterns/sources/self.md`.

### 2. Embedded Corpus Directory Structure

**Location:** `.hiivmind/corpus/` within the host repo.

```
my-obsidian-vault/
├── .hiivmind/
│   └── corpus/
│       ├── config.yaml          # Embedded corpus config (type: self)
│       ├── index.md             # Main index
│       ├── index-*.md           # Sub-indexes (tiered, if needed)
│       ├── registry.yaml        # Existing registry (for remote corpora)
│       └── .gitignore           # Minimal or empty
│
├── notes/                       # The actual documentation
├── projects/
└── ...
```

**What's absent** (compared to standalone corpora):

| Standalone | Embedded | Why |
|------------|----------|-----|
| `.source/` | Not needed | Repo root is the source |
| `.cache/` | Not needed | No web content to cache |
| `uploads/` | Not needed | Repo files are the content |
| `README.md` | Not needed | Host repo has its own |
| `LICENSE` | Not needed | Host repo has its own |
| `CLAUDE.md` | Not needed | Host repo has its own |

**Coexistence with registry:** The registry at `.hiivmind/corpus/registry.yaml` and the embedded corpus config at `.hiivmind/corpus/config.yaml` are different files at the same path level. Registry tracks remote corpora; `config.yaml` defines the local embedded corpus. Discovery uses the presence of `config.yaml` to detect an embedded corpus.

### 3. Discovery — 5th Location

A new discovery location added to the existing four:

| Type | Path | Use Case |
|------|------|----------|
| User-level | `~/.claude/skills/hiivmind-corpus-*/` | Personal corpora |
| Repo-local | `.claude-plugin/skills/hiivmind-corpus-*/` | Team-shared plugin corpora |
| Marketplace-multi | `~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/` | Published packages |
| Marketplace-single | `~/.claude/plugins/marketplaces/hiivmind-corpus-*/` | Published individual |
| **Embedded** | **`.hiivmind/corpus/`** | **Corpus about the current repo** |

**Detection:** `.hiivmind/corpus/config.yaml` exists → embedded corpus found.

**Name derivation:** Other locations derive the corpus name from the directory name. Embedded corpora derive the name from `config.yaml`'s `corpus.name` field, since the directory is always `corpus/`. This makes `corpus.name` a required field for embedded corpora (it is optional for standalone corpora where the directory name suffices).

**Status determination:** Same as other corpora — check `index.md` exists, check for placeholder text, check freshness via scoped SHA.

**External access:** Other projects reference embedded corpora in their registry:

```yaml
# In another project's .hiivmind/corpus/registry.yaml
corpora:
  - id: my-vault
    source:
      type: local
      path: /home/user/obsidian-vault/.hiivmind/corpus  # Full path to corpus directory
    # OR
    source:
      type: github
      repo: user/obsidian-vault
      ref: main
      path: .hiivmind/corpus    # Subdirectory within the repo
```

The registry schema's existing `path` field handles the subdirectory case.

### 4. Init — Embedded Mode

`hiivmind-corpus-init` gains an embedded mode.

**Detection heuristic:** If the current working directory is a git repo with documentation-like content (markdown files, `.obsidian/` directory, `docs/` folder), offer the embedded option:

> "This looks like a documentation repository. Would you like to:
> (A) Create an embedded corpus at `.hiivmind/corpus/` that indexes this repo's own content
> (B) Create a standalone corpus in a new repository"

**What init does in embedded mode:**

1. Creates `.hiivmind/corpus/` directory
2. Writes `config.yaml` with a `type: self` source pre-populated
3. Writes placeholder `index.md`
4. Does **not** create `README.md`, `LICENSE`, `CLAUDE.md`, `uploads/`, `.source/`
5. Does **not** call `add-source` — the source is implicit

**`docs_root` detection:** If `docs/` exists, suggest `"docs"`. If the repo is an Obsidian vault (flat markdown), suggest `"."`. User confirms or overrides.

**After init:** User runs build as normal.

### 5. Build, Refresh, Navigate — `type: self` Handling

These three skills resolve source paths. Changes are thin.

**Build:**

- Source scanner receives `type: self` source
- Scans `{repo_root}/{docs_root}` instead of `.source/{id}/` or `uploads/`
- Auto-excludes `.hiivmind/` from scanning
- Uses same `include_patterns`/`exclude_patterns` from config
- Sets `last_commit_sha` via `git log -1 --format=%H -- {docs_root}`
- All other build behavior (collaborative indexing, tiered indexes, entry keywords) unchanged

**Refresh:**

- Compares stored `last_commit_sha` against current scoped SHA
- If different, runs `git diff {old_sha}..{new_sha} -- {docs_root}` to find changed files
- Feeds changed files into existing refresh machinery (stale flagging, differential updates)
- Updates `last_commit_sha` after refresh

**Navigate:**

- Sees `type: self` in config
- Resolves `vault:notes/architecture.md` → `{repo_root}/{docs_root}/notes/architecture.md`
- Reads directly with the Read tool
- **When accessed remotely** (another project registered this corpus): falls back to `gh api` or raw.githubusercontent.com. The registry's `path: .hiivmind/corpus` locates the config and index; source references resolve against the repo root.

**Source scanner agent:**

- Needs awareness of `type: self` to scan repo root instead of `.source/`
- Otherwise identical — file discovery, framework detection, large file handling all apply

### 6. Files Changed

**New files:**

| File | Purpose |
|------|---------|
| `lib/corpus/patterns/sources/self.md` | `type: self` source pattern documentation |

**Updated pattern docs:**

| File | Change |
|------|--------|
| `lib/corpus/patterns/discovery.md` | 5th location, name derivation from `corpus.name` |
| `lib/corpus/patterns/paths.md` | `type: self` path resolution |
| `lib/corpus/patterns/sources/README.md` | Add `self` to taxonomy |
| `lib/corpus/patterns/config-parsing.md` | `type: self` schema fields |
| `lib/corpus/patterns/freshness.md` | Scoped SHA via `git log -- {docs_root}` (also add to CLAUDE.md pattern table) |
| `lib/corpus/patterns/scanning.md` | Auto-exclude `.hiivmind/` for self sources |

**Updated skills (SKILL.md):**

| Skill | Change |
|-------|--------|
| `init` | Embedded mode, detection heuristic, `type: self` pre-population |
| `build` | Handle `type: self` in source scanner dispatch |
| `refresh` | Handle `type: self` freshness comparison |
| `discover` | Scan `.hiivmind/corpus/` as 5th location |
| `navigate` (template) | Resolve `type: self` paths to repo root |
| `register` | Document embedded corpus external access with `path:` |
| `status` | Embedded corpus freshness display |
| `source-scanner` agent | `type: self` scan from repo root |

**Updated project docs:**

| File | Change |
|------|--------|
| `CLAUDE.md` | Key Design Decisions, cross-cutting concerns, discovery locations |

**Minimal changes:**

| File | Change |
|------|--------|
| `enhance` | Path resolution delegates to shared `resolve_source_ref()` which gets `type: self` support from `paths.md` update — verify this delegation exists, add if missing |
| `add-source` | Add validation: reject `add-source` on embedded corpora (`type: self` must be the only source) |

**No changes needed:**

| File | Why |
|------|-----|
| Gateway command | Routes to existing skills; no new routing |

## Constraints

- Single embedded corpus per repo (one `.hiivmind/corpus/` directory)
- `type: self` source must be the only source in an embedded corpus (enforced by `add-source` rejecting operations on embedded corpora). Rationale: embedded corpora are about self-contained documentation repos. If you need to mix in external sources, use a standalone corpus instead. This keeps path resolution simple and avoids needing `.source/` and `.cache/` directories inside `.hiivmind/corpus/`
- Embedded corpora are always committed to the host repo (not gitignored)
- The `.hiivmind/` directory itself is always excluded from scanning

## Success Criteria

1. `hiivmind-corpus-init` in an Obsidian vault creates an embedded corpus at `.hiivmind/corpus/`
2. `hiivmind-corpus-build` indexes the vault's own content via `type: self`
3. `hiivmind-corpus-discover` finds the embedded corpus automatically
4. `hiivmind-corpus-navigate` reads documentation directly from the repo
5. `hiivmind-corpus-refresh` detects changes scoped to `docs_root`
6. Another project can register the embedded corpus via `local:` or `github:` with `path: .hiivmind/corpus`
7. No changes to existing standalone corpus behavior
