# Pattern: Sources (Overview)

Manage documentation sources: git repositories, local uploads, web content, and generated docs.

## When to Use

- Adding new sources to a corpus
- Cloning git repositories for local access
- Updating sources to get latest content
- Comparing indexed content with upstream changes
- Managing local file uploads
- Caching web content

## Prerequisites

- **Tool detection** (see `../tool-detection.md`) - Git required for git sources
- **Config parsing** (see `../config-parsing.md`) - Reading source configuration
- **Paths** (see `../paths.md`) - Resolving source locations

## Source Type Taxonomy

| Type | Storage Location | Change Detection | Content Access | Use Case |
|------|------------------|------------------|----------------|----------|
| `git` | `.source/{id}/` | SHA comparison | Local files | Full repos with docs |
| `local` | `data/uploads/{id}/` | Timestamp | Local files | User-uploaded docs |
| `web` | `.cache/web/{id}/` | Manual refresh | Cached files | Blog posts, articles |
| `generated-docs` | `.source/{id}/` + `.cache/web/{id}/` | Git SHA | Live WebFetch | CLI manuals, API docs |
| `llms-txt` | `.cache/llms-txt/{id}/` | Manifest hash | Cached markdown | Sites with llms.txt |

## When to Use Each Type

```
Is the documentation in a git repository?
├─ Yes: Is the repo the actual docs (markdown files)?
│       ├─ Yes → git source
│       └─ No (code generates docs) → generated-docs source
└─ No: Is it a web page/article?
        ├─ Yes: Does the site provide llms.txt manifest?
        │       ├─ Yes → llms-txt source
        │       └─ No → web source
        └─ No (local files) → local source
```

## File Organization

| File | Content | Lines* |
|------|---------|--------|
| `git.md` | Clone, fetch, SHA tracking, change comparison | ~260 |
| `local.md` | Upload directory setup, file listing | ~60 |
| `web.md` | Cache setup, URL slugification, cache age | ~90 |
| `generated-docs.md` | Hybrid git+web, URL discovery, live fetch | ~220 |
| `llms-txt.md` | Manifest parsing, hash detection, raw markdown caching | ~280 |
| `shared.md` | URL parsing, existence checks, errors | ~160 |

*Approximate line counts

## Quick Reference

### Most Common Operations

| Operation | File | Function |
|-----------|------|----------|
| Clone a repo | `git.md` | `clone_source()` |
| Get current SHA | `git.md` | `get_source_sha()` |
| Check for upstream changes | `git.md` | `fetch_upstream_sha()` |
| Compare clone to indexed | `git.md` | `compare_clone_to_indexed()` |
| Setup local uploads | `local.md` | `setup_local_source()` |
| Setup web cache | `web.md` | `setup_web_source()` |
| Discover URLs from sitemap | `generated-docs.md` | `discover_urls_from_sitemap()` |
| Fetch llms.txt manifest | `llms-txt.md` | `fetch_manifest()` |
| Parse manifest structure | `llms-txt.md` | `parse_manifest()` |
| Check manifest freshness | `llms-txt.md` | `check_freshness()` |
| Check if source exists | `shared.md` | `exists_git_source()`, etc. |

---

## Examples

### Example 1: Adding a Git Source

**User request:** "Add the polars docs"

**Process:**
1. Parse URL: `https://github.com/pola-rs/polars`
2. Generate source_id: `polars` (see `shared.md#generate-source-id-from-url`)
3. Clone: `git clone --depth 1 ... .source/polars` (see `git.md#clone-a-git-repository`)
4. Get SHA: `git -C .source/polars rev-parse HEAD` (see `git.md#get-clone-sha`)
5. Update config.yaml with source entry

### Example 2: Checking for Updates

**User request:** "Are there updates to the polars docs?"

**Process:**
1. Get indexed SHA from config
2. Fetch upstream SHA (see `git.md#fetch-upstream-sha`)
3. Compare SHAs (see `git.md#compare-clone-to-indexed-sha`)
4. If different, count commits and show file changes

**Sample output:**
```
polars source has updates:
- Indexed at: abc123 (2025-01-10)
- Upstream: def456
- 15 new commits
- Files changed: 8 added, 12 modified, 2 deleted

Run refresh to update the index.
```

### Example 3: Caching Web Content

**User request:** "Add Kent's testing article"

**Process:**
1. Setup cache directory (see `web.md#setup-web-cache-directory`)
2. Fetch URL content with WebFetch
3. Save to cache with slugified filename (see `web.md#generate-cache-filename-from-url`)
4. Add source entry to config.yaml
5. Add entry to index.md

### Example 4: Adding llms.txt Source

**User request:** "Add Claude Code documentation"

**Process:**
1. Detect llms.txt at `https://code.claude.com/docs/llms.txt`
2. Parse manifest to discover 47 pages in structured sections
3. Setup cache directory (see `llms-txt.md#setup-cache-directory`)
4. Hash manifest for change detection (see `llms-txt.md#hash-manifest`)
5. Add source entry to config.yaml with structure
6. Cache pages based on selected strategy (full/selective/on-demand)

**Sample output:**
```
Found llms.txt manifest:
- Title: Claude Code
- 47 pages in 8 sections
- Sections: Getting Started, Core Features, Skills, Agents, ...

Using llms-txt source type with selective caching.
```

---

## Related Patterns

- **tool-detection.md** - Git availability check
- **config-parsing.md** - Reading/writing source configuration
- **paths.md** - Resolving source locations
- **status.md** - Freshness checking using source operations
