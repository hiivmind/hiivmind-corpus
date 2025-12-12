---
name: hiivmind-corpus-refresh
description: Refresh corpus index by comparing with upstream changes. Checks each source independently and updates based on diffs.
---

# Corpus Index Refresh

Compare index against upstream changes and refresh based on diffs. Handles each source type independently.

## Prerequisites

Run from within a corpus skill directory. Valid locations:

| Destination Type | Location |
|------------------|----------|
| User-level skill | `~/.claude/skills/{skill-name}/` |
| Repo-local skill | `{repo}/.claude-plugin/skills/{skill-name}/` |
| Single-corpus plugin | `{plugin-root}/` (with `.claude-plugin/plugin.json`) |
| Multi-corpus plugin | `{marketplace}/{plugin-name}/` |

Requires:
- `data/config.yaml` with at least one source configured (with tracking metadata like `last_commit_sha`, `last_indexed_at`)
- `data/index.md` with real entries (not placeholder)

**Note:** This skill updates index *freshness* from upstream. Use `hiivmind-corpus-enhance` to add depth to topics.

## When to Use vs Other Skills

| Situation | Use This Skill? | Instead Use |
|-----------|-----------------|-------------|
| Upstream docs have changed | ✅ Yes | - |
| Web cache is stale | ✅ Yes | - |
| Local files were modified | ✅ Yes | - |
| Need more detail on a topic | ❌ No | `hiivmind-corpus-enhance` |
| Want to add a new source | ❌ No | `hiivmind-corpus-add-source` |
| Corpus has no sources yet | ❌ No | `hiivmind-corpus-add-source` |
| First-time index building | ❌ No | `hiivmind-corpus-build` |
| Index only has placeholder | ❌ No | `hiivmind-corpus-build` |

## Commands

- **status**: Check if sources are current
- **update**: Refresh selected sources

---

## Status

Check currency of all sources.

### Step 1: Validate and Read config

```bash
cat data/config.yaml
```

**Check 1: Sources exist**
- If `sources:` array is empty → **STOP**: Run `hiivmind-corpus-add-source` to add sources first
- If sources exist → Continue

**Check 2: Index exists**
```bash
cat data/index.md
```
- If only placeholder text ("Run hiivmind-corpus-build...") → **STOP**: Run `hiivmind-corpus-build` first
- If index has real entries → Continue

### Step 2: Detect Index Structure

Check if this is a **tiered index** (for large corpora):

```bash
# Check for sub-index files
ls data/index-*.md 2>/dev/null
```

**Single index:** Only `data/index.md` exists - changes update one file
**Tiered index:** Multiple files exist - need to track which sub-indexes are affected by changes

For tiered indexes, note which sections/sub-indexes exist for change mapping later.

### Step 3: Check each source

**For git sources:**
```bash
# If .source/{source_id}/ exists
cd .source/{source_id} && git fetch origin
git rev-parse origin/{branch}
# Compare to last_commit_sha in config

# If no local clone
git ls-remote {repo_url} refs/heads/{branch}
```

**For local sources:**
```bash
# Find files modified after last_indexed_at
find data/uploads/{source_id} -type f -name "*.md" -newer {timestamp_reference}
```

**For web sources:**
- Report cache age (days since `fetched_at`)
- Note: Re-fetching requires user approval

### Step 4: Report status

Present per-source status:

```
Index Structure: Tiered (index.md + 4 sub-indexes)

Source Status:

1. react (git)
   - Indexed: abc123 (2025-12-01)
   - Upstream: def456
   - Changes: 47 commits, 12 files changed
   - Affected sections: reference/, learn/
   - Status: UPDATES AVAILABLE

2. team-standards (local)
   - Last indexed: 2025-12-05
   - Modified files: 2 (coding-guidelines.md, pr-process.md)
   - Status: UPDATES AVAILABLE

3. kent-testing-blog (web)
   - Cache age: 7 days
   - Status: Consider refreshing (URLs may have changed)

4. tanstack-query (git)
   - Indexed: xyz789 (2025-12-07)
   - Upstream: xyz789
   - Status: UP TO DATE
```

For tiered indexes, also show which sub-indexes may need updates based on changed file paths.

---

## Update

Refresh selected sources and update index.

### Step 1: Select sources

Ask user:
> Which sources would you like to update?
> - All sources with updates
> - Specific sources: [list source IDs]
> - All sources (including up-to-date)

### Step 2: Update by source type

#### Git Sources

```bash
# Ensure clone exists
ls .source/{source_id} || git clone --depth 1 {repo_url} .source/{source_id}

# Fetch and show changes
cd .source/{source_id}
git fetch origin

# Show commit log since last index
git log --oneline {last_commit_sha}..origin/{branch} -- {docs_root} | head -20

# Show file changes
git diff --name-status {last_commit_sha}..origin/{branch} -- {docs_root}

# Pull changes
git pull origin {branch}

# Get new SHA
git rev-parse HEAD
```

Show user:
- Number of commits since last index
- Files: Added (A), Modified (M), Deleted (D), Renamed (R)

#### Local Sources

```bash
# Find new/modified files since last index
find data/uploads/{source_id} -type f -name "*.md" -newer /tmp/timestamp_marker
```

Compare file list against `files:` array in config to detect:
- New files (not in config)
- Modified files (mtime > config timestamp)
- Deleted files (in config but not on disk)

#### Web Sources

**Important:** Web content requires user approval before updating cache.

For each URL in the source:
1. Show current cache age
2. Offer to re-fetch
3. If user agrees:
   - Fetch URL with WebFetch
   - Show fetched content to user
   - Compare with cached version (show diff if changed)
   - **Only save if user approves**
4. If URL fails to fetch, warn but preserve existing cache

### Step 3: Update index collaboratively

For changes detected in each source:

**Added files:**
- Show file list to user
- Ask: "Which new files should be added to the index?"
- Add selected entries with `{source_id}:{path}` format

**Modified files:**
- Check if content significantly changed
- Ask: "Should I update the description for {file}?"
- Update entries as needed

**Deleted files:**
- Show which indexed files were deleted
- Remove corresponding entries from index

**Renamed files:**
- Update path in index (keep same description)

### Tiered Index Updates

For tiered indexes, determine which file(s) to update based on changed paths:

| Changed Path | Update Target |
|--------------|---------------|
| `docs/reference/...` | `data/index-reference.md` |
| `docs/guides/...` | `data/index-guides.md` |
| New top-level section | `data/index.md` (main index) |

If a change affects the main index structure (e.g., new major section), also update `data/index.md` summary and links.

Ask user: "These changes affect `index-reference.md`. Should I also update the main index summary?"

### Step 4: Update config metadata

For each updated source:

**Git sources:**
```yaml
- id: "react"
  # ... other fields ...
  last_commit_sha: "{new_sha}"
  last_indexed_at: "{timestamp}"
```

**Local sources:**
```yaml
- id: "team-standards"
  # ... other fields ...
  files:
    - path: "coding-guidelines.md"
      last_modified: "{new_mtime}"
    - path: "new-file.md"
      last_modified: "{mtime}"
  last_indexed_at: "{timestamp}"
```

**Web sources:**
```yaml
- id: "kent-testing-blog"
  # ... other fields ...
  urls:
    - url: "..."
      fetched_at: "{new_timestamp}"
      content_hash: "{new_hash}"
  last_indexed_at: "{timestamp}"
```

### Step 5: Commit reminder

**For single index:**
```bash
git add data/index.md data/config.yaml
git commit -m "Refresh docs index"
```

**For tiered index:**
```bash
# Include any updated sub-indexes
git add data/index.md data/index-*.md data/config.yaml
git commit -m "Refresh docs index ({sources_updated})"
```

---

## File Locations

- **Config**: `data/config.yaml`
- **Main index**: `data/index.md`
- **Sub-indexes** (tiered): `data/index-{section}.md`
- **Git sources**: `.source/{source_id}/` (gitignored)
- **Local sources**: `data/uploads/{source_id}/`
- **Web cache**: `.cache/web/{source_id}/` (gitignored)

---

## Next Steps Guidance

After refresh, suggest appropriate next actions:

| Situation | Recommend |
|-----------|-----------|
| Many new docs added, index feels shallow | `hiivmind-corpus-enhance` on expanded sections |
| User mentions wanting to add external resources | `hiivmind-corpus-add-source` |
| User wants deeper coverage of new topic | `hiivmind-corpus-enhance` |
| Large corpus grew significantly | Consider tiered indexing (see `hiivmind-corpus-build`) |

---

## Example Sessions

### Refreshing a Single Git Source

**User**: "refresh status"

```
Source Status:

1. polars (git)
   - Indexed: abc123 (2025-12-01)
   - Upstream: def456
   - Changes: 15 commits, 8 files changed
   - Status: UPDATES AVAILABLE
```

**User**: "refresh update"

```
Updating polars (git)...

Changes since last index:
A  docs/guides/new-feature.md
M  docs/reference/expressions.md
M  docs/reference/io.md
D  docs/deprecated/old-api.md

Added files:
- docs/guides/new-feature.md

Would you like to add "new-feature.md" to the index?
```

User: "Yes, add it to the Guides section"

```
Updated index:
- Added: **New Feature Guide** `polars:guides/new-feature.md`
- Removed: `polars:deprecated/old-api.md`

Updated config with new SHA: def456
```

---

### Refreshing Web Sources

**User**: "refresh update kent-testing-blog"

```
Checking kent-testing-blog (web)...

1. testing-implementation-details.md
   - Cached: 14 days ago
   - Re-fetch? [y/n]
```

User: "y"

```
Fetching https://kentcdodds.com/blog/testing-implementation-details...

Content has changed since last fetch.
[Shows diff or summary of changes]

Save updated content? [y/n]
```

User: "y"

```
Saved updated content.
Updated cache timestamp and content hash.
```

---

### Refreshing Local Sources

**User**: "refresh status team-standards"

```
team-standards (local):
- Last indexed: 2025-12-05
- Modified files:
  - coding-guidelines.md (modified 2025-12-07)
- New files:
  - deployment-process.md
- Status: UPDATES AVAILABLE
```

**User**: "refresh update"

```
Updating team-standards (local)...

New file found: deployment-process.md
Add to index? [y/n]
```

User: "Yes, create a new Deployment section"

```
Updated index:
- Added section: ## Deployment
- Added: **Deployment Process** `local:team-standards/deployment-process.md`
```

---

### Refreshing Tiered Index

**User**: "refresh status"

```
Index Structure: Tiered (index.md + index-reference.md + index-guides.md)

Source Status:

1. github (git)
   - Indexed: abc123 (2025-12-01)
   - Upstream: def456
   - Changes: 23 commits, 15 files changed
   - Affected sections:
     - actions/using-workflows/ → index-actions.md
     - rest/reference/ → index-rest-api.md
   - Status: UPDATES AVAILABLE
```

**User**: "refresh update"

```
Updating github (git)...

Changes affecting index-actions.md:
A  actions/using-workflows/reusing-workflows.md
M  actions/using-workflows/workflow-syntax.md

Changes affecting index-rest-api.md:
A  rest/reference/repos/autolinks.md
D  rest/reference/deprecated/legacy-auth.md

Would you like to update both sub-indexes?
```

User: "Yes"

```
Updated index-actions.md:
- Added: **Reusing Workflows** `github:actions/using-workflows/reusing-workflows.md`

Updated index-rest-api.md:
- Added: **Repository Autolinks** `github:rest/reference/repos/autolinks.md`
- Removed: `github:rest/reference/deprecated/legacy-auth.md`

Main index.md: No structural changes needed (section counts unchanged)

Updated config with new SHA: def456
```

---

### Blocked: No Index Built

**User**: "refresh status"

**Step 1**: Validate prerequisites
- Config: schema_version 2, sources exist ✓
- Index: Only placeholder text ("Run hiivmind-corpus-build...")

**Response**: "The index hasn't been built yet - it only contains placeholder text.

**Recommended next step:** Run `hiivmind-corpus-build` to create the initial index, then use refresh for future updates."

---

## Reference

- Add sources: `skills/hiivmind-corpus-add-source/SKILL.md`
- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build index: `skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
