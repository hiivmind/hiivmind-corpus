# Embedded Corpus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support embedded corpora — a corpus living at `.hiivmind/corpus/` inside a documentation repo, indexing its own content via a new `type: self` source type.

**Architecture:** New `type: self` source type + 5th discovery location at `.hiivmind/corpus/`. Additive changes to existing pattern docs, skills, and agent. No breaking changes.

**Tech Stack:** Markdown pattern docs (SKILL.md files), YAML config schemas, bash algorithms

**Spec:** `docs/superpowers/specs/2026-03-25-embedded-corpus-design.md`

---

### Task 1: Create `type: self` source pattern doc

**Files:**
- Create: `lib/corpus/patterns/sources/self.md`

- [ ] **Step 1: Write the self source pattern doc**

Create `lib/corpus/patterns/sources/self.md` following the structure of existing source docs (e.g., `git.md`, `local.md`). Content:

```markdown
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

\`\`\`yaml
- id: "{source_id}"          # User-chosen identifier (e.g., "vault", "docs")
  type: "self"
  docs_root: "."              # Relative to repo root. "." = whole repo, "docs" = docs/ subtree
  last_commit_sha: null       # Scoped to docs_root via git log
  last_indexed_at: null
\`\`\`

**What self does NOT have** (compared to `type: git`): No `repo_url`, `repo_owner`, `repo_name`, `branch`. The repo is implicit.

## Path Resolution

Index entries use the standard `{source_id}:{relative_path}` format.

For `type: self`, resolution is:

\`\`\`
{source_id}:{relative_path} → {repo_root}/{docs_root}/{relative_path}
\`\`\`

**`docs_root` normalization:** `"."` is normalized to empty string before path concatenation. This is consistent with how existing git sources handle `docs_root: ""` / null (the segment is omitted). The `resolve_source_ref()` function in `paths.md` uses `[ -n "$docs_root" ]` to decide whether to insert the segment — `"."` must be treated as equivalent to empty.

Example: `vault:notes/architecture.md` with `docs_root: "."` → `/home/user/obsidian-vault/notes/architecture.md`

### Using bash

\`\`\`bash
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
\`\`\`

### Using Claude tools

\`\`\`
# Direct file read — no cloning or fetching needed
Read: {repo_root}/{docs_root}/{relative_path}
\`\`\`

## Freshness Tracking

Scoped to `docs_root` so unrelated commits don't trigger staleness:

\`\`\`bash
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
\`\`\`

**Note:** When `docs_root` is `"."` (whole repo), `git log -1 --format=%H` returns the most recent commit on the branch — any commit marks the corpus stale. The scoping benefit only applies when `docs_root` targets a subdirectory like `"docs"`.

### Compare for staleness

\`\`\`bash
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
\`\`\`

### Get changed files (for refresh)

\`\`\`bash
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
\`\`\`

## Auto-Exclusions

Build and refresh MUST auto-exclude `.hiivmind/` from scanning to avoid indexing the corpus's own files.

Add to `settings.exclude_patterns` in config.yaml during init:

\`\`\`yaml
settings:
  exclude_patterns:
    - "**/_*.md"
    - "**/_snippets/**"
    - ".hiivmind/**"
\`\`\`

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
```

- [ ] **Step 2: Verify file exists and is well-formed**

Run: `wc -l lib/corpus/patterns/sources/self.md`
Expected: ~150 lines

- [ ] **Step 3: Commit**

```bash
git add lib/corpus/patterns/sources/self.md
git commit -m "feat: add type:self source pattern documentation"
```

---

### Task 2: Update source taxonomy and decision tree

**Files:**
- Modify: `lib/corpus/patterns/sources/README.md:22-71`

- [ ] **Step 1: Add self to Source Type Taxonomy table**

In `lib/corpus/patterns/sources/README.md`, add a new row to the table at line 22-29, after the `obsidian` row:

```markdown
| `self` | repo root (via `docs_root`) | Scoped SHA | Local files | Embedded corpus in own repo | frontmatter, tags |
```

- [ ] **Step 2: Update the decision tree**

In `lib/corpus/patterns/sources/README.md`, update the decision tree (lines 33-48) to add `type: self` as the first check:

```
Is the corpus embedded in the source repo (.hiivmind/corpus/ exists)?
├─ Yes → self source
└─ No: Is it an Obsidian vault (has `.obsidian/` directory)?
        ├─ Yes → obsidian source
        └─ No: Is the documentation in a git repository?
                ...rest unchanged...
```

- [ ] **Step 3: Add self.md to File Organization table**

In `lib/corpus/patterns/sources/README.md`, add to the table at lines 62-71:

```markdown
| `self.md` | Embedded self-source — repo root path resolution, scoped SHA freshness, auto-exclusions | ~150 |
```

- [ ] **Step 4: Add self to Quick Reference table**

Add to the Quick Reference table (lines 79-91):

```markdown
| Get self source SHA | `self.md` | `get_self_sha()` |
| Check self freshness | `self.md` | `check_self_freshness()` |
| Get self file changes | `self.md` | `get_self_changes()` |
```

- [ ] **Step 5: Commit**

```bash
git add lib/corpus/patterns/sources/README.md
git commit -m "feat: add type:self to source taxonomy and decision tree"
```

---

### Task 3: Update path resolution patterns

**Files:**
- Modify: `lib/corpus/patterns/paths.md:322-380`

- [ ] **Step 1: Add self to Full Path Resolution section**

In `lib/corpus/patterns/paths.md`, update the `resolve_source_ref()` function (line 360-378). Add a `self` case to the case statement:

```bash
        self)
            # Normalize "." to empty
            [ "$docs_root" = "." ] && docs_root=""
            if [ -n "$docs_root" ]; then
                # repo_root is parent of .hiivmind/corpus/
                local repo_root
                repo_root=$(git -C "$corpus_path" rev-parse --show-toplevel 2>/dev/null || echo "$corpus_path/../..")
                echo "$repo_root/$docs_root/$relative_path"
            else
                local repo_root
                repo_root=$(git -C "$corpus_path" rev-parse --show-toplevel 2>/dev/null || echo "$corpus_path/../..")
                echo "$repo_root/$relative_path"
            fi
            ;;
```

Also update the algorithm description at line 331-334 to include:
```
   - `self`: `{repo_root}/{docs_root}/{relative_path}` (docs_root "." normalized to empty)
```

- [ ] **Step 2: Update the Python version**

Add the `self` case to the Python version at lines 382-416:

```python
elif source_type == 'self':
    docs_root = source.get('docs_root', '.')
    if docs_root == '.':
        docs_root = ''
    repo_root = os.popen(f'git -C {corpus_path} rev-parse --show-toplevel 2>/dev/null').read().strip() or os.path.join(corpus_path, '..', '..')
    if docs_root:
        print(f'{repo_root}/{docs_root}/{relative_path}')
    else:
        print(f'{repo_root}/{relative_path}')
```

- [ ] **Step 3: Add self source path format to Source Path Format section**

At line 228-231, add:
```markdown
- `vault:notes/architecture.md` → Self source "vault", file at `notes/architecture.md` (resolved relative to repo root)
```

- [ ] **Step 4: Commit**

```bash
git add lib/corpus/patterns/paths.md
git commit -m "feat: add type:self path resolution to paths pattern"
```

---

### Task 4: Update config parsing and formatting patterns

**Files:**
- Modify: `lib/corpus/patterns/config-parsing.md:56-170`
- Modify: `lib/corpus/patterns/config-yaml-formatting.md:63-170`

- [ ] **Step 1: Add self source schema to config-parsing.md**

After the Generated-Docs source section (around line 156), add:

```markdown
### Self Source

Embedded source — the corpus indexes the repo it lives in:

\`\`\`yaml
- id: "vault"
  type: "self"
  docs_root: "."                     # "." = whole repo, "docs" = docs/ subtree
  last_commit_sha: null              # Scoped to docs_root
  last_indexed_at: null
\`\`\`

**Key differences from other source types:**
- No `repo_url`, `repo_owner`, `repo_name`, `branch` — the repo is implicit
- `docs_root` uses `"."` for whole repo (normalized to empty during path resolution)
- Freshness tracked via `git log -1 --format=%H -- {docs_root}`
```

- [ ] **Step 2: Add self source entry schema to config-yaml-formatting.md**

After the existing source entry schemas, add:

```markdown
### Self Source Entry

Embedded source for corpora that index their own repository:

\`\`\`yaml
- id: "{source_id}"
  type: "self"
  docs_root: "."
  last_commit_sha: null
  last_indexed_at: null
\`\`\`

| Field | Source | Notes |
|-------|--------|-------|
| `id` | User-provided or derived from repo name | Lowercase, alphanumeric + hyphens |
| `type` | Always `"self"` | Embedded source |
| `docs_root` | User-confirmed | `"."` for whole repo, `"docs"` for subdirectory |
| `last_commit_sha` | Set by build | Scoped to docs_root |
| `last_indexed_at` | Set by build | Timestamp of last index |
```

- [ ] **Step 3: Commit**

```bash
git add lib/corpus/patterns/config-parsing.md lib/corpus/patterns/config-yaml-formatting.md
git commit -m "feat: add type:self schema to config parsing and formatting patterns"
```

---

### Task 5: Update freshness pattern

**Files:**
- Modify: `lib/corpus/patterns/freshness.md:14-48`

- [ ] **Step 1: Add self source to prerequisites**

At line 16, update prerequisites to note that self sources use local git commands instead of `gh api`:

```markdown
- `config.yaml` with `sources[].last_commit_sha`
  - For `git`/`generated-docs`: also needs `repo_owner`, `repo_name`, `branch`
  - For `self`: uses local `git log` (no remote needed)
```

- [ ] **Step 2: Add self source freshness algorithm**

After the Navigate Freshness Check section (line 39), add a new subsection:

```markdown
### Self Source Navigate Freshness Check

Self sources use local `git log` instead of `gh api` since the source is the current repo:

\`\`\`bash
DOCS_ROOT=$(yq '.sources[] | select(.type == "self") | .docs_root // "."' config.yaml)
INDEXED_SHA=$(yq '.sources[] | select(.type == "self") | .last_commit_sha' config.yaml)

# Normalize "." to empty for git log scoping
[ "$DOCS_ROOT" = "." ] && DOCS_ROOT=""

if [ -n "$DOCS_ROOT" ]; then
  CURRENT_SHA=$(git log -1 --format=%H -- "$DOCS_ROOT")
else
  CURRENT_SHA=$(git log -1 --format=%H)
fi

if [ "$CURRENT_SHA" != "$INDEXED_SHA" ]; then
  # Warn: corpus was indexed at {short_sha}, repo is now at {current_short_sha}
fi
\`\`\`

| Condition | Behavior |
|-----------|----------|
| SHAs match | Proceed silently |
| SHAs differ | Warn user, suggest refresh |
| Not a git repo | Skip silently |
```

- [ ] **Step 3: Add self source to CI freshness section**

In the CI Freshness Check algorithm (line 64-88), add a note after step 2:

```markdown
> **Self sources:** Replace `gh api` SHA lookup with `git log -1 --format=%H -- {docs_root}`. File diff uses `git diff {old_sha}..{new_sha} -- {docs_root}`.
```

- [ ] **Step 4: Commit**

```bash
git add lib/corpus/patterns/freshness.md
git commit -m "feat: add type:self freshness tracking to freshness pattern"
```

---

### Task 6: Update scanning pattern

**Files:**
- Modify: `lib/corpus/patterns/scanning.md:17`

- [ ] **Step 1: Add auto-exclusion note**

After the Prerequisites section (line 17), add:

```markdown
### Self Source Auto-Exclusions

When scanning a `type: self` source, always exclude the corpus's own directory:
- `.hiivmind/**` — corpus config, index, and metadata files

This is in addition to the standard `exclude_patterns` from config.yaml.
```

- [ ] **Step 2: Commit**

```bash
git add lib/corpus/patterns/scanning.md
git commit -m "feat: add self source auto-exclusion to scanning pattern"
```

---

### Task 7: Update discovery pattern

**Files:**
- Modify: `lib/corpus/patterns/discovery.md:19-28,212-248`

- [ ] **Step 1: Add embedded location to Location Types table**

In `lib/corpus/patterns/discovery.md`, add a new row to the table at lines 23-28:

```markdown
| **Embedded** | `{repo}/.hiivmind/corpus/` | Same | Corpus about the current repo |
```

- [ ] **Step 2: Add Discover Embedded Corpus section**

After the "Discover Marketplace Corpora (Single-Corpus)" section (after line 209), add:

```markdown
### Discover Embedded Corpus

**Algorithm:**
1. Check if `.hiivmind/corpus/config.yaml` exists in the current repo
2. If exists, this is an embedded corpus
3. Extract corpus name from `config.yaml`'s `corpus.name` field (required for embedded corpora since the directory is always `corpus/`)

**Using bash:**
\`\`\`bash
if [ -f ".hiivmind/corpus/config.yaml" ]; then
    echo "embedded|$(yq '.corpus.name' .hiivmind/corpus/config.yaml)|.hiivmind/corpus/"
fi
\`\`\`

**Using Claude tools:**
\`\`\`
Glob: .hiivmind/corpus/config.yaml
\`\`\`
If found, read config.yaml to extract `corpus.name`.
```

- [ ] **Step 3: Update Discover All function**

In the `discover_all()` function (lines 221-248), add the embedded check:

```bash
    # Embedded corpus
    if [ -f ".hiivmind/corpus/config.yaml" ]; then
        local name
        name=$(yq '.corpus.name' .hiivmind/corpus/config.yaml 2>/dev/null || grep 'name:' .hiivmind/corpus/config.yaml | head -1 | sed 's/.*name: *//' | tr -d '"')
        echo "embedded|$name|.hiivmind/corpus/"
    fi
```

- [ ] **Step 4: Commit**

```bash
git add lib/corpus/patterns/discovery.md
git commit -m "feat: add embedded corpus as 5th discovery location"
```

---

### Task 8: Update source scanner agent

**Files:**
- Modify: `agents/source-scanner.md:29-42,179-187`

- [ ] **Step 1: Add self to source types in agent description**

At line 31, update the Input description to include `self`:

```markdown
- Source type (git, local, web, or self)
```

- [ ] **Step 2: Add self to verification step**

At lines 40-42, add:

```markdown
   - Self: Verify repo root exists and `docs_root` is accessible. Get repo root via `git rev-parse --show-toplevel`
```

- [ ] **Step 3: Add self to Path Resolution table**

At lines 181-187, add:

```markdown
| self | `{repo_root}/{docs_root}/` (docs_root "." normalized to empty, repo_root from `git rev-parse --show-toplevel`) |
```

- [ ] **Step 4: Commit**

```bash
git add agents/source-scanner.md
git commit -m "feat: add type:self support to source-scanner agent"
```

---

### Task 9: Update init skill for embedded mode

**Files:**
- Modify: `skills/hiivmind-corpus-init/SKILL.md`

- [ ] **Step 1: Add embedded mode detection before Phase 1**

After the Corpus Structure section (line 51) and before Phase 1, add a new section:

```markdown
## Embedded Mode Detection

Before collecting project info, check if the user wants an embedded corpus:

**Detection heuristic:** If the current working directory is a git repo with documentation-like content, offer embedded mode:

1. Check: is this a git repo? (`git rev-parse --show-toplevel`)
2. Check for doc indicators: `.obsidian/` directory, `docs/` folder, or 10+ `.md` files at root
3. If indicators found, ask:

> "This looks like a documentation repository. Would you like to:
> (A) Create an embedded corpus at `.hiivmind/corpus/` that indexes this repo's own content
> (B) Create a standalone corpus in a new repository"

If user chooses (A), switch to embedded init flow (Phase 4-embedded below).
If user chooses (B), continue with standard flow.
```

- [ ] **Step 2: Add Phase 4-embedded scaffold**

After Phase 4 (Scaffold section, around line 207), add:

```markdown
## Phase 4-embedded: Scaffold Embedded Corpus

**Inputs:** `computed.corpus_name`, `computed.display_name`, `computed.keywords`
**Outputs:** `computed.corpus_root`, files on disk

Create the embedded corpus at `.hiivmind/corpus/`:

\`\`\`bash
mkdir -p .hiivmind/corpus
\`\`\`

### 4e-1: Detect docs_root

Suggest `docs_root` based on repo structure:
- If `docs/` directory exists → suggest `"docs"`
- If `.obsidian/` exists (Obsidian vault) → suggest `"."`
- Otherwise → suggest `"."`

Confirm with user: "What directory contains the documentation? (default: {suggestion})"

### 4e-2: config.yaml

Write `.hiivmind/corpus/config.yaml` using the full schema from `config-yaml-formatting.md`, with these differences:
- `sources` is pre-populated with a `type: self` entry (NOT empty)
- `settings.exclude_patterns` includes `.hiivmind/**`

\`\`\`yaml
schema_version: 2

corpus:
  name: "{name}"
  display_name: "{Display Name}"
  keywords:
    - "{keyword1}"
    - "{keyword2}"
  created_at: null

sources:
  - id: "{source_id}"
    type: "self"
    docs_root: "{docs_root}"
    last_commit_sha: null
    last_indexed_at: null

index:
  format: "markdown"
  last_updated_at: null

settings:
  include_patterns:
    - "**/*.md"
    - "**/*.mdx"
  exclude_patterns:
    - "**/_*.md"
    - "**/_snippets/**"
    - ".hiivmind/**"
\`\`\`

### 4e-3: index.md

Write `.hiivmind/corpus/index.md` using the same placeholder template as standard init.

### 4e-4: .gitignore

Minimal or empty — embedded corpora commit everything (no `.source/`, `.cache/`, `uploads/`).

### 4e-5: Verify

Verify these exist:
- `.hiivmind/corpus/config.yaml`
- `.hiivmind/corpus/index.md`

### 4e-6: Skip add-source delegation

Embedded corpora do NOT delegate to add-source. The `type: self` source is already configured. Display:

\`\`\`
Embedded corpus '{name}' initialized at .hiivmind/corpus/

Files created:
  .hiivmind/corpus/config.yaml
  .hiivmind/corpus/index.md

Source: this repository (docs_root: {docs_root})

Next: Run hiivmind-corpus-build to create the index.
\`\`\`

Done — do NOT invoke add-source.
```

- [ ] **Step 3: Commit**

```bash
git add skills/hiivmind-corpus-init/SKILL.md
git commit -m "feat: add embedded mode to corpus init skill"
```

---

### Task 10: Update build skill for type:self

**Files:**
- Modify: `skills/hiivmind-corpus-build/SKILL.md:53-75`

- [ ] **Step 1: Add self source to per-source preparation**

In the "Per-source preparation by type" section (lines 53-75), add after the llms-txt source block:

```markdown
**Self source:**
- Get repo root: `git rev-parse --show-toplevel`
- Normalize `docs_root`: if `"."`, treat as repo root
- Verify repo root exists and is accessible
- No cloning or fetching needed — files are read directly from repo
- Note: `.hiivmind/` is auto-excluded during scanning (see `lib/corpus/patterns/sources/self.md`)
```

- [ ] **Step 2: Update the source-scanner agent prompt**

In the multi-source scanning section (lines 95-118), update the prompt template to handle `type: self`:

Add to the prompt context:
```
For self sources: scan from repo root {repo_root}/{docs_root}. Auto-exclude .hiivmind/ directory.
The repo root is: {output of git rev-parse --show-toplevel}
```

- [ ] **Step 3: Commit**

```bash
git add skills/hiivmind-corpus-build/SKILL.md
git commit -m "feat: add type:self handling to build skill"
```

---

### Task 11: Update refresh skill for type:self

**Files:**
- Modify: `skills/hiivmind-corpus-refresh/SKILL.md:87-127,176-215`

- [ ] **Step 1: Add self source to freshness check**

In "Per-source freshness check by type" (lines 87-127), add after generated-docs:

```markdown
**Self sources** — See `lib/corpus/patterns/sources/self.md` § "Freshness Tracking":

\`\`\`pseudocode
docs_root = source.docs_root (normalize "." to "")
if docs_root:
    current_sha = git log -1 --format=%H -- {docs_root}
else:
    current_sha = git log -1 --format=%H
status = (current_sha == last_commit_sha) ? "current" : "stale"
\`\`\`

Report: source_id, type, indexed_sha, current_sha, status
```

- [ ] **Step 2: Add self source to update loop**

In "Update loop" section (lines 176-215), add after generated-docs:

```markdown
**Self source update:**

1. No clone or fetch needed — files are already local
2. Get current scoped SHA: `git log -1 --format=%H -- {docs_root}`
3. Get file changes: `git diff --name-status {old_sha}..{new_sha} -- {docs_root}`
4. Filter changes to `include_patterns` from config
5. Store new SHA
6. Collect changes for index update
```

- [ ] **Step 3: Add self source to pattern documentation references**

In the Pattern Documentation section (lines 298-308), add:

```markdown
- **Self sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/self.md`
```

- [ ] **Step 4: Commit**

```bash
git add skills/hiivmind-corpus-refresh/SKILL.md
git commit -m "feat: add type:self handling to refresh skill"
```

---

### Task 12: Update discover skill for embedded corpora

**Files:**
- Modify: `skills/hiivmind-corpus-discover/SKILL.md:33-56,103-128,245-278`

- [ ] **Step 1: Add embedded to Discovery Sources section**

In "Discovery Sources" (lines 33-56), add a new subsection between Registry and Legacy:

```markdown
### 2. Embedded Corpus (Local Repo)

Check `.hiivmind/corpus/config.yaml` in the current repo:

\`\`\`
Read: .hiivmind/corpus/config.yaml
\`\`\`

If it exists and contains `corpus.name`, this is an embedded corpus. Extract `corpus.name`, `corpus.display_name`, `corpus.keywords` directly.

Name derivation: use `corpus.name` field (required for embedded corpora since the directory is always `corpus/`).
```

Renumber the existing "Legacy Plugin Locations" to become section 3.

- [ ] **Step 2: Add embedded check to Step 2**

In "Step 2: Discover All Corpora" (lines 103-128), add before the legacy plugin globs:

```markdown
**Embedded corpus (local check):**
\`\`\`
Glob: .hiivmind/corpus/config.yaml
\`\`\`
If found, read it to extract corpus metadata. This is faster than the legacy plugin scan.
```

- [ ] **Step 3: Add embedded to Type Detection table**

In the Type Detection table (lines 248-254), add:

```markdown
| `.hiivmind/corpus/` (has config.yaml) | `embedded` |
```

- [ ] **Step 4: Add embedded to Corpus Path Resolution**

In "Corpus Path Resolution" (lines 256-279), add:

```markdown
**Embedded corpus:**
\`\`\`
.hiivmind/corpus/
├── config.yaml
└── index.md
\`\`\`
Note: No `data/` subdirectory — embedded corpora are always data-only format with files at the corpus root.
```

- [ ] **Step 5: Commit**

```bash
git add skills/hiivmind-corpus-discover/SKILL.md
git commit -m "feat: add embedded corpus discovery to discover skill"
```

---

### Task 13: Update navigate skill for type:self

**Files:**
- Modify: `skills/hiivmind-corpus-navigate/SKILL.md`

- [ ] **Step 1: Add embedded corpus handling to Phase 1**

In "Phase 1: Load Registry" (lines 34-50), add a note that embedded corpora are also discovered:

```markdown
> **Embedded corpora:** If `.hiivmind/corpus/config.yaml` exists in the current repo, it is available for navigation without registry registration. Treat it as an additional corpus alongside registry entries.
```

- [ ] **Step 2: Add self source freshness check to Phase 3**

In "Step 3b: Freshness check" (lines 96-114), add handling for self sources:

```markdown
> **Self sources:** Use local `git log` instead of `gh api`:
> \`\`\`bash
> DOCS_ROOT=$(yq '.sources[] | select(.type == "self") | .docs_root // "."' config.yaml)
> [ "$DOCS_ROOT" = "." ] && DOCS_ROOT=""
> if [ -n "$DOCS_ROOT" ]; then
>   CURRENT_SHA=$(git log -1 --format=%H -- "$DOCS_ROOT")
> else
>   CURRENT_SHA=$(git log -1 --format=%H)
> fi
> \`\`\`
```

- [ ] **Step 3: Add self source content fetching**

In the Phase 5 documentation fetching section, add a self source handling path:

```markdown
### Self Source Content Fetching

For `type: self` sources, read files directly from the repo:

\`\`\`
# Resolve path
docs_root = source.docs_root (normalize "." to "")
file_path = {repo_root}/{docs_root}/{relative_path}

# Read directly
Read: {file_path}
\`\`\`

No cloning, no remote fetch, no `gh api` call needed. The file is already local.
```

- [ ] **Step 4: Commit**

```bash
git add skills/hiivmind-corpus-navigate/SKILL.md
git commit -m "feat: add type:self content fetching to navigate skill"
```

---

### Task 14: Update add-source skill to reject embedded corpora

**Files:**
- Modify: `skills/hiivmind-corpus-add-source/SKILL.md:41-49`

- [ ] **Step 1: Add validation in Phase 1**

In "Phase 1: Locate Corpus" (lines 41-49), add after step 2:

```markdown
3. Check if any existing source has `type: self`:
   - If yes, display:
     \`\`\`
     This is an embedded corpus (type: self). Additional sources cannot be added.
     Embedded corpora index their own repository content only.
     To add external sources, create a standalone corpus instead.
     \`\`\`
   - STOP — do not proceed to Phase 2
```

- [ ] **Step 2: Commit**

```bash
git add skills/hiivmind-corpus-add-source/SKILL.md
git commit -m "feat: reject add-source on embedded corpora"
```

---

### Task 15: Verify enhance skill path resolution delegation

**Files:**
- Verify: `skills/hiivmind-corpus-enhance/SKILL.md`

- [ ] **Step 1: Check if enhance delegates path resolution to shared patterns**

Read `skills/hiivmind-corpus-enhance/SKILL.md` and search for how it resolves source file paths (Glob, Read, or `resolve_source_ref()`).

If it delegates to `paths.md` patterns or uses `resolve_source_ref()`: no changes needed — the `type: self` case in `paths.md` (Task 3) covers it.

If it hardcodes path resolution (e.g., directly constructing `.source/{id}/` paths): add a `self` branch alongside the existing source types.

- [ ] **Step 2: Add reference to self source pattern if needed**

If the skill references source patterns in its Reference section, add:

```markdown
- **Self sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/self.md`
```

- [ ] **Step 3: Commit (only if changes were made)**

```bash
git add skills/hiivmind-corpus-enhance/SKILL.md
git commit -m "feat: verify/update enhance skill for type:self path resolution"
```

---

### Task 16: Update status and register skill

**Files:**
- Modify: `skills/hiivmind-corpus-status/SKILL.md`
- Modify: `skills/hiivmind-corpus-register/SKILL.md`

- [ ] **Step 1: Add self source to status skill freshness check**

In the status skill's freshness check section, add handling for `type: self` sources:

```markdown
**Self sources:**
- Use local `git log -1 --format=%H -- {docs_root}` (normalize "." to "")
- Compare against `last_commit_sha` in config
- Report as "current" or "stale"
- No network required — purely local check
```

- [ ] **Step 2: Add embedded corpus documentation to register skill**

In the register skill, add a note about embedded corpora:

```markdown
### Registering Embedded Corpora (External Access)

Other projects can register an embedded corpus from another repo:

\`\`\`
/hiivmind-corpus register local:/path/to/vault/.hiivmind/corpus
/hiivmind-corpus register github:user/vault@main path:.hiivmind/corpus
\`\`\`

The `path` parameter is required for GitHub sources since the corpus lives at a subdirectory, not the repo root.
```

- [ ] **Step 3: Commit**

```bash
git add skills/hiivmind-corpus-status/SKILL.md skills/hiivmind-corpus-register/SKILL.md
git commit -m "feat: add type:self to status and register skills"
```

---

### Task 17: Update CLAUDE.md with embedded corpus documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add to Key Design Decisions**

In the "Key Design Decisions" section, add:

```markdown
- **Embedded corpora**: Documentation repos can contain their own corpus at `.hiivmind/corpus/`, powered by `type: self` sources — see ADR in `docs/superpowers/specs/2026-03-25-embedded-corpus-design.md`
```

- [ ] **Step 2: Update discovery locations**

In the Architecture section or wherever discovery locations are mentioned, add the 5th location.

- [ ] **Step 3: Add to cross-cutting concerns table**

In the "Cross-Cutting Concerns" table, add:

```markdown
| Embedded corpora | init, discover, navigate, build, refresh, status, add-source, source-scanner | `type: self` source type, `.hiivmind/corpus/` discovery, `docs_root` normalization |
```

- [ ] **Step 4: Add freshness.md to pattern table**

In the Pattern Documentation Library table, add `freshness.md` (addressing the review finding):

```markdown
| `freshness.md` | SHA-gated freshness | Read-time checks, CI refresh, stale flagging |
```

- [ ] **Step 5: Update source types in documentation**

Wherever source types are listed (e.g., "Source types: git, local, web, llms-txt, generated-docs"), add `self`.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add embedded corpus and type:self to CLAUDE.md"
```

---

### Task 18: Final verification

- [ ] **Step 1: Verify all new and modified files**

Run a grep to verify `type: self` or `self` source appears in all expected files:

```bash
grep -rl "type.*self\|self source\|type: self\|self:" lib/corpus/patterns/ agents/ skills/ CLAUDE.md | sort
```

Expected files (19 total):
- `lib/corpus/patterns/sources/self.md` (new)
- `lib/corpus/patterns/sources/README.md`
- `lib/corpus/patterns/paths.md`
- `lib/corpus/patterns/config-parsing.md`
- `lib/corpus/patterns/config-yaml-formatting.md`
- `lib/corpus/patterns/freshness.md`
- `lib/corpus/patterns/scanning.md`
- `lib/corpus/patterns/discovery.md`
- `agents/source-scanner.md`
- `skills/hiivmind-corpus-init/SKILL.md`
- `skills/hiivmind-corpus-build/SKILL.md`
- `skills/hiivmind-corpus-refresh/SKILL.md`
- `skills/hiivmind-corpus-discover/SKILL.md`
- `skills/hiivmind-corpus-navigate/SKILL.md`
- `skills/hiivmind-corpus-add-source/SKILL.md`
- `skills/hiivmind-corpus-enhance/SKILL.md` (verify/update)
- `skills/hiivmind-corpus-status/SKILL.md`
- `skills/hiivmind-corpus-register/SKILL.md`
- `CLAUDE.md`

- [ ] **Step 2: Verify spec alignment**

Read `docs/superpowers/specs/2026-03-25-embedded-corpus-design.md` and confirm all items in the "Files Changed" section (Section 6) have been addressed.

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address any gaps from final verification"
```
