---
adr: 3
title: "Generated-Docs Source Type for Auto-Generated Documentation"
status: Proposed
date: 2025-12-18
deciders: [nathanielramm]
---

# 3. Generated-Docs Source Type for Auto-Generated Documentation

## Status

Proposed

## Context

Many documentation sites are auto-generated from source code in git repositories:

| Project | Source Repo | Generated Site |
|---------|-------------|----------------|
| GitHub CLI | `cli/cli` (Go) | cli.github.com/manual |
| MkDocs projects | markdown in repo | rendered HTML |
| Sphinx/ReadTheDocs | RST/MD in repo | docs.project.io |
| API docs | OpenAPI/code | generated reference |

**Current source types cannot handle this pattern well:**

- **git source**: Can clone the source repo, but it contains code, not rendered docs
- **web source**: Can fetch rendered docs, but has no change detection mechanism

The web source requires:
1. Pre-listing all URLs manually (brittle, high maintenance)
2. Pre-caching all content (storage overhead)
3. No way to know if content has changed without re-fetching everything

**Real example**: Adding the GitHub CLI manual required manually listing 165+ URLs in config.yaml with no way to detect when cli/cli releases update the docs.

## Decision

Add a new source type: `generated-docs`

### Core Concept: Git-Tracked URL Directory

Use git for change detection, web for content fetching:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Source Repo    │     │  generated-docs  │     │  Web Output     │
│  (cli/cli)      │────▶│  config entry    │────▶│  (cli.github.com)│
│                 │     │                  │     │                 │
│  • Track SHA    │     │  • URL directory │     │  • Live fetch   │
│  • docs_root    │     │  • Freshness     │     │  • WebFetch     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Config Schema

```yaml
- id: "gh-cli-manual"
  type: "generated-docs"

  # Git tracking (for change detection)
  source_repo:
    url: "https://github.com/cli/cli"
    branch: "trunk"
    docs_root: "cmd/"
    last_commit_sha: "abc123"

  # Web output (for live fetching)
  web_output:
    base_url: "https://cli.github.com/manual"
    sitemap_url: "https://cli.github.com/sitemap.xml"
    discovered_urls: []

  # Optional caching (default: live fetch)
  cache:
    enabled: false
    dir: ".cache/web/gh-cli-manual/"

  last_indexed_at: "2025-12-18T..."
```

### Design Choices

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Content access** | Live fetch (WebFetch) by default | Always fresh, no storage overhead |
| **Caching** | Optional, user-enabled | Support offline use when needed |
| **URL discovery** | Auto-discover (sitemap/crawl) | Reduce manual maintenance |
| **Change detection** | Git SHA tracking | Reliable, same as git sources |

### URL Discovery Strategies

1. **Sitemap** (preferred): Parse sitemap.xml for all URLs
2. **Pattern**: Template-based URL construction from repo structure
3. **Crawl**: Follow links from base_url (fallback)
4. **Manual**: Explicit URL list (last resort)

### Navigation Flow

```
User: "How do I use gh pr create?"

1. Navigate finds gh-cli-manual in index
2. Index entry has path: gh_pr_create
3. Construct URL: base_url + "/gh_pr_create"
4. WebFetch retrieves content live
5. Answer from fresh content
```

### Refresh Flow

```
1. Fetch upstream SHA from source_repo.url
2. Compare to last_commit_sha
3. If different:
   - Re-run URL discovery (sitemap may have new pages)
   - Report: "Source has N new commits"
   - Update last_commit_sha
4. If same: "Source unchanged"
```

## Consequences

### Positive

- **Change detection for generated docs**: Know when upstream source changed
- **Reduced maintenance**: Auto-discover URLs instead of manual lists
- **No storage overhead**: Default to live fetch, no mandatory caching
- **Always fresh**: Content fetched on demand, never stale from cache
- **Flexible caching**: Optional offline support when needed

### Negative

- **Network dependency**: Live fetch requires internet access
- **Latency**: Each navigation incurs WebFetch time
- **Build lag**: Source may update before docs site rebuilds (CI/CD pipeline time)
- **Sitemap dependency**: Best experience requires site to have sitemap.xml

### Neutral

- **New source type to document**: Extends existing pattern library
- **Git clone optional**: Only needed if tracking specific docs_root changes

## Implementation

**Files to modify (7):**

| File | Changes |
|------|---------|
| `lib/corpus/patterns/sources/generated-docs.md` | Generated-docs operations (now split per ADR-0004) |
| `lib/corpus/patterns/status.md` | Add freshness check for generated-docs |
| `lib/corpus/patterns/config-parsing.md` | Document new schema fields |
| `skills/hiivmind-corpus-add-source/SKILL.md` | Add generated-docs setup flow |
| `skills/hiivmind-corpus-refresh/SKILL.md` | Add SHA checking, URL re-discovery |
| `skills/hiivmind-corpus-navigate/SKILL.md` | Add live fetch integration |

**New file (1):**
| `docs/adr/0003-generated-docs-source-type.md` | This ADR |

**Estimated effort:** 6-8 hours

## References

- [Plan file](/home/nathanielramm/.claude/plans/compressed-roaming-horizon.md)
- [GitHub CLI manual source discussion](conversation context)
- [Source patterns](lib/corpus/patterns/sources/) (split per ADR-0004)
