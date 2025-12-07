---
name: docs-maintain
description: Check status and update documentation indexes after upstream changes. Use when refreshing an existing docs plugin.
---

# Documentation Index Maintenance

Check for upstream changes and update the index.

## Prerequisites

Run from within a docs plugin directory (e.g., `clickhouse-docs/`).

Requires initialized plugin with `data/config.yaml`:
```yaml
source:
  repo_url: "https://github.com/..."
  branch: "main"
  docs_root: "docs/"

index:
  last_commit_sha: "abc123"
  last_indexed_at: "2025-01-01T00:00:00Z"
```

**Note:** For first-time setup, use `docs-init` instead.

## Commands

- **status**: Check if index is current with upstream
- **update**: Pull changes and update index

---

## Status

Check if index is current with upstream.

1. Read `data/config.yaml` for `last_commit_sha` and `repo_url`

2. Get remote HEAD:

   **If `.source/` exists:**
   ```bash
   cd .source && git fetch origin
   git rev-parse origin/{branch}
   ```

   **If `.source/` doesn't exist:**
   ```bash
   git ls-remote {repo_url} HEAD
   ```

3. Compare and report:
   - Current index: `{last_commit_sha}` from {last_indexed_at}
   - Upstream HEAD: `{remote_sha}`
   - Status: "Up to date" or "Updates available"

---

## Update

Pull latest changes and update index.

### Step 1: Read config
```yaml
# data/config.yaml
source:
  repo_url: "..."
  branch: "..."
  docs_root: "..."
index:
  last_commit_sha: "..."
```

### Step 2: Get current state

**If `.source/` exists:**
```bash
cd .source && git fetch origin
```

**If `.source/` doesn't exist:**
```bash
git clone --depth 1 {repo_url} .source
```

### Step 3: Find what changed

```bash
cd .source
git log --oneline {last_commit_sha}..origin/{branch} -- {docs_root} | head -20
git diff --name-status {last_commit_sha}..origin/{branch} -- {docs_root}
```

Show user:
- Number of commits since last index
- Files added (A), modified (M), deleted (D), renamed (R)

### Step 4: Pull changes

```bash
cd .source && git pull origin {branch}
```

### Step 5: Update index collaboratively

For each change type:
- **Added files**: Ask user if they should be in index
- **Modified files**: Check if title/description changed
- **Deleted files**: Remove from index
- **Renamed files**: Update path in index

### Step 6: Update metadata

Update `data/config.yaml`:
```yaml
index:
  last_commit_sha: "{new_sha}"
  last_indexed_at: "{timestamp}"
```

### Step 7: Commit

Remind user:
```bash
git add data/index.md data/config.yaml
git commit -m "Update docs index to {short_sha}"
```

---

## File Locations (relative to plugin directory)

- **Config**: `data/config.yaml`
- **Index**: `data/index.md`
- **Source**: `.source/` (gitignored)

## Index Format

```markdown
# {Project} Documentation Index

> Source: {repo_url}
> Last updated: {date}
> Commit: {sha}

---

## Section Name
*Brief description*

- **Doc Title** `path/to/file.md` - Description
```

---

## Reference

- Generate plugin structure: `skills/generate-docs-plugin/SKILL.md`
- Initialize index: `skills/docs-init/SKILL.md`
- Example implementation: `clickhouse-docs/`
