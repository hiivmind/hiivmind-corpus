---
name: hiivmind-corpus-refresh
description: >
  This skill should be used when the user asks to "refresh corpus", "sync documentation",
  "update corpus index", "check for upstream changes", "corpus is stale", "docs are outdated",
  or mentions that documentation sources have changed. Triggers on "refresh my [corpus name] corpus",
  "sync corpus with upstream", "check if docs are current", "update from source repo", or
  "hiivmind-corpus refresh".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch, Task
inputs:
  - name: corpus_name
    type: string
    required: false
    description: Name of the corpus to refresh (uses current directory if not provided)
  - name: mode
    type: string
    required: false
    description: "status" for check-only, "update" to pull changes (prompted if not provided)
  - name: auto_approve
    type: boolean
    required: false
    description: Skip confirmation prompts (for CI/automated runs)
outputs:
  - name: status_report
    type: array
    description: Per-source freshness status
  - name: updated_sources
    type: array
    description: Sources that were updated (empty in status mode)
---

# Corpus Refresh

Check documentation sources for upstream changes and optionally update the index.
Operates in two modes: **status** (check only) and **update** (pull changes and refresh index).

## Precondition

A `config.yaml` must exist with at least one source and a built index (not placeholder).
If not found, suggest running `hiivmind-corpus-init` or `hiivmind-corpus-build`.

---

## Phase 1: Validate

**Inputs:** working directory
**Outputs:** `computed.config`, `computed.sources`, `computed.index_structure`, `computed.index_format`

1. Read and parse `config.yaml`
2. Verify at least one source exists in `config.sources`
3. Read `index.md` and verify it has real content (not the placeholder from init)
4. Detect index format version:
   - Check if `index.yaml` exists → `computed.index_format = "v2"`
   - If only `index.md` → `computed.index_format = "v1"`
5. Detect tiered index structure:
   - Glob for `index-*.md` files
   - If found, set `computed.index_structure.is_tiered = true` and store sub-index paths
6. Display: "Found corpus: {name} — Sources: {count} — Index: {format} {single|tiered ({n} sub-indexes)}"

---

## Phase 2: Choose Mode

**Inputs:** optional `mode` from invocation, optional `auto_approve`
**Outputs:** `computed.command_mode`

If `mode` was provided as input, use it directly.

If `auto_approve` is set:
- With `mode = "status"` → status mode
- Without explicit mode → update mode (auto-approve implies update)

Otherwise ask: "What would you like to do?"
- **Check status** → `computed.command_mode = "status"`
- **Update sources** → `computed.command_mode = "update"`

---

## Phase 3: Check Freshness

**Inputs:** `computed.sources`
**Outputs:** `computed.status_report`

Check each source for upstream changes. For multi-source corpora, use parallel Task agents
when possible.

### Per-source freshness check by type

**Git sources** — See `lib/corpus/patterns/sources/git.md` § "Fetch Upstream SHA":

```pseudocode
upstream_sha = git ls-remote {repo_url} refs/heads/{branch} | cut -f1
status = (upstream_sha == last_commit_sha) ? "current" : "stale"
```

Report: source_id, type, indexed_sha, upstream_sha, status

**Local sources** — See `lib/corpus/patterns/sources/local.md`:

- Count files in `uploads/{source_id}/`
- Compare file modification times against `last_indexed_at`
- Status is always "check_manually" (no automatic change detection)

Report: source_id, type, file_count, last_indexed_at, status

**Web sources** — See `lib/corpus/patterns/sources/web.md` § "Get Cache Age":

- Check cache age of files in `.cache/web/{source_id}/`
- Report age in days

Report: source_id, type, cache_age_days, last_indexed_at, status

**llms-txt sources** — See `lib/corpus/patterns/sources/llms-txt.md` § "Check Freshness":

```pseudocode
current_manifest = fetch {base_url}/llms.txt
current_hash = sha256(current_manifest)
status = (current_hash == manifest.last_hash) ? "current" : "stale"
```

Report: source_id, type, manifest_hash_match, status

**Generated-docs sources** — See `lib/corpus/patterns/sources/generated-docs.md` § "Check Freshness":

- Same as git: compare source_repo SHA against upstream
- Report like git source

**Self sources** — See `lib/corpus/patterns/sources/self.md` § "Freshness Tracking":

```pseudocode
docs_root = source.docs_root (normalize "." to "")
if docs_root:
    current_sha = git log -1 --format=%H -- {docs_root}
else:
    current_sha = git log -1 --format=%H
status = (current_sha == last_commit_sha) ? "current" : "stale"
```

Report: source_id, type, indexed_sha, current_sha, status

---

## Phase 4: Present Status Report

**Inputs:** `computed.status_report`

Display a table:

```
Source Status Report
─────────────────────────────────
| Source ID       | Type   | Status  | Details                    |
|-----------------|--------|---------|----------------------------|
| {id}            | git    | stale   | 5 new commits              |
| {id}            | local  | manual  | 12 files, check timestamps |
| {id}            | web    | ok      | Cache: 3 days old          |
```

### If status mode

If any sources are stale, ask: "Some sources have updates. Would you like to update now?"
- **Yes** → switch to update mode, continue to Phase 5
- **No** → done

If all sources are current: "All sources are up to date." → done

### If update mode

Continue directly to Phase 5 with the status report available.

---

## Phase 5: Update Sources

**Inputs:** `computed.status_report`, `computed.sources`
**Outputs:** `computed.updated_sources`, `computed.all_changes`

### Select sources to update

If `auto_approve` is set, automatically select all stale sources.

Otherwise ask: "Which sources should be updated?"
- **All stale sources** → select all with status != "current"
- **Specific sources** → present list for selection
- **Cancel** → done

### Update loop

For each selected source, execute the type-specific update:

**Git source update** — See `lib/corpus/patterns/sources/git.md`:

1. Check if `.source/{source_id}` clone exists
   - If not, clone: `git clone --depth 1 --branch {branch} {url} .source/{source_id}`
   - If exists, fetch and pull: `git -C .source/{source_id} pull origin`
2. Get commit count between old and new SHA
3. Get file changes (added/modified/deleted) filtered to `docs_root`
4. Store new SHA
5. Collect changes for index update

**Local source update:**

1. Scan `uploads/{source_id}/` for files newer than `last_indexed_at`
2. List new/modified files
3. Collect changes for index update

**Web source update:**

1. If `auto_approve`, re-fetch all cached URLs automatically
2. Otherwise ask: "Re-fetch cached web content? (Yes / No, just re-index existing cache)"
3. If re-fetching: for each URL in source config, WebFetch and overwrite cache file
4. Collect changes for index update

**llms-txt source update** — See `lib/corpus/patterns/sources/llms-txt.md`:

1. Re-fetch manifest
2. Diff old vs new manifest to find added/removed pages
3. Update manifest hash in config
4. Re-cache changed pages per caching strategy
5. Collect changes for index update

**Generated-docs source update** — See `lib/corpus/patterns/sources/generated-docs.md`:

1. Pull source repo for new SHA
2. Re-discover URLs from sitemap if available
3. Compare discovered URLs to stored list
4. Collect changes for index update

**Self source update:**

1. No clone or fetch needed — files are already local
2. Get current scoped SHA: `git log -1 --format=%H -- {docs_root}`
3. Get file changes: `git diff --name-status {old_sha}..{new_sha} -- {docs_root}`
4. Filter changes to `include_patterns` from config
5. Store new SHA
6. Collect changes for index update

---

## Phase 6: Apply Changes to Index

**Inputs:** `computed.all_changes`, `computed.index_structure`, `computed.index_format`, `computed.updated_sources`

### v2 format (index.yaml exists)

If `computed.index_format == "v2"`:

1. **For modified entries**: Set `stale: true` and `stale_since` to current timestamp. Preserve existing summary, tags, keywords.
2. **For added entries**: Add placeholder entries with `stale: true`, `category: "unknown"`, `summary: "Pending re-scan"`. Full metadata populated on next build or LLM re-scan.
3. **For deleted entries**: Remove entry from index.yaml. Remove from graph.yaml concept entries if referenced.
4. Update `meta.generated_at` and `meta.entry_count` in index.yaml.
5. Re-render index.md: `bash ./render-index.sh index.yaml` (render-index.sh is at corpus root, copied from templates/ during build)
6. Show preview of changes (entries added/modified/removed, stale count).

**Note:** `links_from` is NOT updated during refresh — requires a full build to recompute cross-references.

**Pattern reference:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/freshness.md`

### v1 format (index.md only)

#### Single index

If `computed.index_structure.is_tiered` is false:

1. Read `index.md`
2. Apply changes: update existing entries, add new entries, mark removed entries
3. Show preview of changes to user
4. If `auto_approve` or user confirms → save index.md

#### Tiered index

If `computed.index_structure.is_tiered` is true:

1. Map changes to affected sub-indexes (match source sections to `index-*.md` files)
2. Present affected sections to user
3. For each affected sub-index:
   - Read `index-{section}.md`
   - Apply relevant changes
   - Save
4. Update main `index.md` summary section
5. If `auto_approve` or user confirms → save all files

### Update config metadata (both formats)

After index changes are saved (applies to both v1 and v2):

1. Update `index.last_updated_at` in config.yaml
2. For each updated source:
   - Set `last_commit_sha` (git/generated-docs)
   - Set `last_indexed_at` to current timestamp
   - Update `manifest.last_hash` (llms-txt)
3. Save config.yaml

### Completion

Display summary:

```
Refresh complete.
Updated sources: {count}
Index entries: {added} added, {modified} modified, {removed} removed
{if v2: Stale entries: {stale_count} (run build or dispatch LLM re-scan to update)}
```

---

## Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| No config.yaml | "No config.yaml found" | Run hiivmind-corpus-init |
| No sources | "No sources configured" | Run hiivmind-corpus-add-source |
| Index not built | "Index is a placeholder" | Run hiivmind-corpus-build |
| Clone/fetch failed | "Failed to fetch from {url}" | Check network and URL |
| Index update failed | "Failed to update index" | Check file permissions |
| Config save failed | "Failed to save config.yaml" | Check file permissions |

---

## Pattern Documentation

- **Git sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/git.md`
- **Local sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/local.md`
- **Web sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/web.md`
- **llms-txt sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/llms-txt.md`
- **Generated docs:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/generated-docs.md`
- **Self sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/self.md`
- **Shared patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/shared.md`
- **Index v2 schema:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-format-v2.md`
- **Freshness checks:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/freshness.md`
- **Index rendering:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/index-rendering.md`

## Agent

- **Source scanner:** `${CLAUDE_PLUGIN_ROOT}/agents/source-scanner.md`

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented)
