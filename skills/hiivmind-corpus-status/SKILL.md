---
name: hiivmind-corpus-status
description: >
  Check the health and status of registered corpora. Use when users want to see corpus
  freshness, verify configurations, check for upstream updates, or diagnose issues.
  Triggers: corpus status, check corpus, corpus health, is corpus up to date, corpus info.
allowed-tools: Read, Glob, Bash, WebFetch, AskUserQuestion
---

# Corpus Status Skill

Check the health and freshness of registered documentation corpora. Reports on
index status, source availability, and cache state.

## When to Use

- User asks about corpus status or health
- User wants to know if corpora need updating
- Diagnosing navigation or fetch issues
- Before bulk operations (upgrade, refresh)

## Workflow

### Phase 1: Load Registry

Read `.hiivmind/corpus/registry.yaml`:

```
Read: .hiivmind/corpus/registry.yaml
```

If not found:
```
No corpus registry found at .hiivmind/corpus/registry.yaml

No corpora are registered for this project.

Register a corpus with:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

### Phase 2: Check Each Corpus

For each registered corpus, gather status information:

#### 2a. Fetch Corpus Config

**From GitHub (using gh api - preferred):**
```bash
gh api repos/{owner}/{repo}/contents/config.yaml?ref={ref} --jq '.content' | base64 -d
```

Then parse the YAML to extract: schema_version, corpus.name, corpus.keywords, sources[].last_commit_sha, index.last_updated_at

**Fallback (WebFetch):**
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/{ref}/config.yaml
prompt: "Extract schema_version, corpus.name, corpus.keywords, sources[].last_commit_sha, index.last_updated_at"
```

**From local:**
```
Read: {source.path}/config.yaml
```

#### 2b. Check Index Exists

**From GitHub (using gh api - preferred):**
```bash
# Check if file exists (will error if not found)
gh api repos/{owner}/{repo}/contents/index.md?ref={ref} --jq '.name' 2>/dev/null && echo "exists"

# Or fetch first portion to verify content
gh api repos/{owner}/{repo}/contents/index.md?ref={ref} --jq '.content' | base64 -d | head -10
```

**Fallback (WebFetch):**
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/{ref}/index.md
prompt: "Return just the first 10 lines to verify file exists"
```

**From local:**
```
Read: {source.path}/index.md (limit: 10 lines)
```

#### 2c. Check Source Freshness (Git sources)

For git-based documentation sources, compare tracked commit to latest:

```bash
# Get latest commit from GitHub API
gh api repos/{owner}/{repo}/commits/{branch} --jq '.sha'
```

Compare with `sources[].last_commit_sha` in config.yaml.

#### 2d. Check Cache Status

If `cache.strategy: clone`:
```bash
# Check if cache exists
if [ -d ".corpus-cache/{corpus_id}" ]; then
    # Check last modified time
    stat -c %Y ".corpus-cache/{corpus_id}/index.md"
fi
```

### Phase 3: Build Status Report

Compile status for all corpora:

```yaml
corpora_status:
  - id: flyio
    display_name: "Fly.io"
    source: github:hiivmind/hiivmind-corpus-flyio@main
    status: healthy          # healthy | stale | error
    index:
      exists: true
      last_updated: "2026-01-08T12:00:00Z"
      entry_count: 747
    sources:
      - id: flyio
        type: git
        upstream: current    # current | behind | error
        tracked_sha: "e353a1b..."
        latest_sha: "e353a1b..."
    cache:
      strategy: fetch
      cached: false
    keywords: ["flyio", "fly.io", "deployment"]

  - id: polars
    status: stale
    ...
```

### Phase 4: Present Report

**Summary view (default):**

```markdown
## Corpus Status

| Corpus | Status | Last Updated | Sources | Keywords |
|--------|--------|--------------|---------|----------|
| Fly.io | healthy | 2026-01-08 | 1 current | flyio, fly.io |
| Polars | stale | 2025-12-01 | 1 behind | polars, dataframe |

**Healthy:** 1 corpus
**Stale:** 1 corpus (upstream has changes)
**Errors:** 0

To update stale corpora:
  /hiivmind-corpus refresh polars
```

**Detailed view (with --verbose or specific corpus):**

```markdown
## Fly.io Corpus Status

**Source:** github:hiivmind/hiivmind-corpus-flyio@main
**Status:** healthy

### Index
- **Exists:** Yes
- **Last Updated:** 2026-01-08T12:00:00Z
- **Entry Count:** 747 files indexed

### Sources
| Source ID | Type | Status | Tracked | Latest |
|-----------|------|--------|---------|--------|
| flyio | git | current | e353a1b... | e353a1b... |

### Cache
- **Strategy:** fetch (no local cache)

### Keywords
flyio, fly.io, deployment, hosting, edge, cloud
```

## Status Classifications

| Status | Meaning | Action |
|--------|---------|--------|
| `healthy` | Index exists, sources current | None needed |
| `stale` | Upstream has new commits | Run `/hiivmind-corpus refresh` |
| `outdated` | Schema version is old | Run `/hiivmind-corpus upgrade` |
| `no-index` | Config exists but no index | Run `/hiivmind-corpus build` |
| `unreachable` | Cannot fetch from source | Check network/URL |
| `invalid` | Config is malformed | Check config.yaml |

## Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `{corpus}` | Optional specific corpus | `flyio` |
| `--verbose` | Detailed output | |
| `--json` | JSON output for scripts | |

**Usage examples:**
```
/hiivmind-corpus status              # All corpora summary
/hiivmind-corpus status flyio        # Specific corpus detail
/hiivmind-corpus status --verbose    # All corpora detailed
```

## Checking Upstream Freshness

For git sources, check if upstream has new commits:

### Using GitHub API

```bash
# Get latest commit SHA
latest=$(gh api repos/superfly/docs/commits/main --jq '.sha')

# Compare with tracked SHA from config
tracked=$(yq -r '.sources[] | select(.id == "flyio") | .last_commit_sha' config.yaml)

if [ "$latest" = "$tracked" ]; then
    echo "current"
else
    echo "behind"
fi
```

### Using WebFetch

```
WebFetch: https://api.github.com/repos/superfly/docs/commits/main
prompt: "Extract just the SHA value from the response"
```

Compare with tracked commit in corpus config.

## Error Handling

**Registry not found:**
```
No corpus registry found.

Register a corpus first:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio
```

**Corpus not in registry:**
```
Corpus 'unknown' is not registered.

Registered corpora: flyio, polars

Register with: /hiivmind-corpus register github:owner/repo
```

**Cannot fetch corpus:**
```
Cannot reach corpus 'flyio' at github:hiivmind/hiivmind-corpus-flyio

Network error or repository may have moved.

Last known good state:
- Index updated: 2026-01-08
- Sources tracked: e353a1b...
```

**Invalid corpus config:**
```
Corpus 'flyio' has invalid configuration.

Missing required fields in config.yaml:
- corpus.name
- sources[]

Try rebuilding: /hiivmind-corpus build flyio
```

## Integration with Other Skills

**Before refresh:**
```
/hiivmind-corpus status flyio

Corpus 'flyio' is stale:
- Upstream has 3 new commits since last index

Run refresh to update:
  /hiivmind-corpus refresh flyio
```

**Before navigate (if stale):**
```
Note: Corpus 'flyio' is 5 days behind upstream.
Documentation may be outdated.

[Proceed with current index] [Refresh first]
```

## Related Skills

- **Navigate:** `hiivmind-corpus-navigate` - Query corpus documentation
- **Register:** `hiivmind-corpus-register` - Add new corpora
- **Refresh:** `hiivmind-corpus-refresh` - Update stale corpora
- **Discover:** `hiivmind-corpus-discover` - Find available corpora
