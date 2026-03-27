# Pattern: SHA-Gated Freshness Checks and Stale Flagging

## Purpose

Detect whether a corpus index is current with its upstream sources. Operates at two points in the workflow: read-time (navigate warns if stale) and write-time (CI refresh flags changed entries and dispatches re-scan requests).

## When to Use

- **Navigate (read-time):** Before serving query results, to warn users when the index may lag behind the source
- **CI refresh (write-time):** On schedule or webhook trigger, to detect changes and update index.yaml without LLM inference
- **`hiivmind-corpus refresh` (write-time):** Manual differential refresh
- **`hiivmind-corpus status`:** Show staleness summary

## Prerequisites

- `config.yaml` with `sources[].last_commit_sha`
  - For `git`/`generated-docs`: also needs `repo_owner`, `repo_name`, `branch`
  - For `self`: uses local `git log` (no remote needed)
- `gh` CLI authenticated (not required for self sources)
- `yq` 4.0+ (mikefarah/yq)

---

## Navigate Freshness Check (Read-Time)

Navigate performs a lightweight SHA comparison as Step 0, before yq pre-filtering. `config.yaml` is already fetched as part of navigate's standard flow, so this adds only one `gh api` call.

### Algorithm

```bash
# Source coordinates from config.yaml (already fetched for navigate)
SOURCE_REPO=$(yq '.sources[0].repo_owner + "/" + .sources[0].repo_name' config.yaml)
SOURCE_BRANCH=$(yq '.sources[0].branch' config.yaml)
INDEXED_SHA=$(yq '.sources[0].last_commit_sha' config.yaml)

CURRENT_SHA=$(gh api "repos/${SOURCE_REPO}/commits/${SOURCE_BRANCH}" --jq '.sha')

if [ "$CURRENT_SHA" != "$INDEXED_SHA" ]; then
  # Warn: "Note: {corpus} was indexed at {short_sha}, source is now at {current_short_sha}. Consider running refresh."
fi
```

### Behavior

| Condition | Behavior |
|-----------|----------|
| SHAs match | Proceed silently — index is current |
| SHAs differ | Warn user: corpus indexed at `{short_sha}`, source now at `{current_short_sha}`. Suggest refresh. Proceed with cached index |
| Check fails (network, permissions) | Skip silently — do not block navigate |

### Self Source Navigate Freshness Check

Self sources use local `git log` instead of `gh api` since the source is the current repo:

```bash
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
```

| Condition | Behavior |
|-----------|----------|
| SHAs match | Proceed silently |
| SHAs differ | Warn user, suggest refresh |
| Not a git repo | Skip silently |

### What Navigate Does NOT Do

- Does not trigger refresh — only suggests it
- Does not modify `index.yaml`, `config.yaml`, or `graph.yaml` — read-only
- Does not require the check to succeed — graceful degradation on failure

---

## CI Freshness Check (Write-Time)

The CI workflow performs a full differential refresh when the source has changed. No LLM inference — structural updates only.

### Algorithm

```
1. Read source coordinates from config.yaml (repo, branch, last_commit_sha)
2. Compare config.yaml last_commit_sha against current source SHA via gh api
3. If unchanged → exit (no work)
4. If changed → compute file diff between old and new SHA
   > **Self sources:** Replace `gh api` SHA lookup with `git log -1 --format=%H -- {docs_root}`. File diff uses `git diff {old_sha}..{new_sha} -- {docs_root}`.
5. For each added file:
   - Add entry to index.yaml with stale: true and placeholder metadata:
     - id: "{source_id}:{path}"
     - source: source ID, path: file path
     - title: derived from filename (hyphens/underscores → spaces)
     - summary: "Pending re-scan"
     - tags: [], keywords: []
     - category: "unknown", content_type: "markdown", size: "standard"
     - grep_hint: null, headings: [], links_to: [], links_from: []
     - frontmatter: {}, stale: true, stale_since: now
6. For each deleted file:
   - Remove entry from index.yaml
   - Remove from graph.yaml concept entries (if referenced)
7. For each modified file:
   - Set stale: true and stale_since on existing entry
   - Preserve existing summary, tags, keywords (may be outdated but better than nothing)
8. Update config.yaml: last_commit_sha and last_indexed_at
9. Update index.yaml: meta.generated_at and meta.entry_count
10. Re-render index.md from index.yaml
11. Commit and push (config.yaml + index.yaml + index.md)
12. (Optional) Dispatch LLM re-scan request
```

### Stale Flagging Rules

| File Status | Action |
|-------------|--------|
| Modified | Set `stale: true` and `stale_since: now` on existing entry. Preserve metadata |
| Added | Add placeholder entry with `stale: true`, `category: unknown`, `summary: "Pending re-scan"` |
| Deleted | Remove entry from `index.yaml`. Remove from `graph.yaml` concept entries if referenced |

---

## LLM Re-scan Dispatch

CI does not run LLM inference. Instead, it creates a signal for an external agent (OpenClaw, ZeroClaw, PaperClip, or any system with LLM access) to pick up:

### Option A: GitHub Issue

```bash
gh issue create \
  --title "Corpus refresh: ${STALE_COUNT} stale entries" \
  --body "$(cat <<EOF
## Stale Entries

The following entries need LLM re-scanning:

$(yq '.entries[] | select(.stale == true) | "- \(.id) (stale since \(.stale_since))"' index.yaml)

## Instructions

1. For each stale entry, fetch the source file and regenerate: summary, tags, keywords, category
2. Update index.yaml with new metadata
3. Set stale: false on updated entries
4. Re-render index.md
5. Commit and close this issue
EOF
)" \
  --label "corpus-refresh"
```

### Option B: Repository Dispatch

```bash
gh api repos/{owner}/{corpus-repo}/dispatches \
  -f event_type="rescan-stale" \
  -f client_payload[stale_count]="$STALE_COUNT" \
  -f client_payload[source_sha]="$NEW_SHA"
```

The consuming agent picks up the issue or event, runs LLM re-scan on stale entries, updates `index.yaml` with fresh metadata, sets `stale: false`, re-renders `index.md`, and commits the results.

---

## Embedding Freshness

When `index-embeddings.lance/` exists alongside `index.yaml`, check staleness by comparing timestamps:

```bash
# Extract generated_at from Lance dataset metadata sidecar
python3 -c "
import json, sys
from pathlib import Path
meta_path = Path(sys.argv[1]) / '_meta.json'
if meta_path.exists():
    print(json.loads(meta_path.read_text()).get('generated_at', 'none'))
else:
    print('none')
" index-embeddings.lance
```

Compare against `meta.generated_at` in `index.yaml`. If index.yaml timestamp is newer,
embeddings are stale.

| State | Meaning | Action |
|-------|---------|--------|
| Current | Lance generated_at >= index.yaml generated_at | Use normally |
| Stale | Lance generated_at < index.yaml generated_at | Use anyway, note in output |
| Missing | No index-embeddings.lance/ | Skip embedding retrieval |

**See:** `embeddings.md` for full embedding patterns including graph-boost and graceful degradation.

---

## Related Patterns

- `index-format-v2.md` — `index.yaml` schema including the `stale` and `stale_since` fields
- `index-rendering.md` — deterministic render algorithm that surfaces stale markers in `index.md`
- `status.md` — how `hiivmind-corpus status` presents freshness information
- `config-parsing.md` — reading source coordinates from `config.yaml`
