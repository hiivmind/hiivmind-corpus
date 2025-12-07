# Future Enhancements

Potential improvements to the documentation navigation skill suite.

## Current limitations

### What this doesn't cover

1. **External knowledge** - Stack Overflow, blog posts, GitHub issues, release notes
2. **Cross-project queries** - "How do I use ClickHouse with dbt?" spans two doc sets
3. **Version awareness** - User on v23.8 shouldn't see v24.x docs
4. **API reference vs. guides** - Different retrieval patterns (exact lookup vs. conceptual)

---

## Proposed enhancements

### Staleness warning on navigate

**Complexity:** Low
**Value:** High

When the navigate skill runs and `.source/` exists, compare the local HEAD to `last_commit_sha` in config. If the clone is newer than the index:

```
Note: The documentation source is 47 commits ahead of the index.
Consider running docs-maintain to update.
```

This is passive - doesn't block navigation, just informs.

---

### Curated external links

**Complexity:** Low
**Value:** Medium

Add an optional section to `index.md` for authoritative external resources:

```markdown
## External Resources

- **Performance Tuning Guide** [blog.clickhouse.com/...] - Official deep-dive
- **ClickHouse at Scale** [YouTube] - Architecture talk from maintainer
- **Common Pitfalls** [GitHub Discussion #1234] - Frequently asked questions
```

These would be manually curated during `docs-init` or added later.

---

### Version tags in config

**Complexity:** Medium
**Value:** High (for fast-moving projects)

Extend `config.yaml` to track version:

```yaml
source:
  repo_url: "https://github.com/ClickHouse/clickhouse-docs"
  branch: "main"
  version: "24.8"  # Optional: docs version
  version_selector: "frontmatter.version"  # How to detect version in docs
```

The navigate skill could then:
- Warn when docs version doesn't match user's installed version
- Filter results to version-appropriate content

**Challenge:** Most doc repos don't tag versions cleanly. May need per-project logic.

---

### Cross-project index linking

**Complexity:** Medium
**Value:** Situational

For common tool combinations (ClickHouse + dbt, Prisma + Next.js), allow index entries to reference other doc plugins:

```markdown
## Integrations

- **dbt Integration** `docs/integrations/dbt.md`
- **See also:** `dbt-docs:clickhouse-adapter` (cross-reference)
```

The navigate skill would resolve cross-references by looking up the other plugin's index.

**Challenge:** Requires convention for cross-plugin references. May add complexity without proportional value.

---

### Proactive index refresh

**Complexity:** Medium
**Value:** Medium

Add a `docs-status-all` skill that checks all doc plugins for staleness:

```
Documentation Status:
- clickhouse-docs: 47 commits behind (last updated 2025-11-15)
- prisma-docs: up to date
- dbt-docs: 12 commits behind (last updated 2025-12-01)
```

Could be run periodically or on session start.

---

### Semantic search over index

**Complexity:** High
**Value:** Diminishing returns

Embed index entries for semantic similarity search rather than keyword matching.

**Assessment:** For a well-organized markdown index with clear headings, semantic search adds complexity without proportional benefit. The current approach (read index, find relevant section, fetch doc) works well for curated indexes.

May be worth revisiting if indexes grow very large (500+ entries).

---

### Auto-suggested index updates

**Complexity:** High
**Value:** Medium

During `docs-maintain update`, analyze the diff and suggest index changes:

```
Detected changes:
- New file: docs/guides/materialized-views-v2.md
  Suggested: Add to "Data Modeling > Materialized Views" section?

- Deleted file: docs/deprecated/old-syntax.md
  Action: Remove from index (currently in "SQL Reference")

- Renamed: docs/engines/mergetree.md → docs/engines/mergetree-family/overview.md
  Action: Update path in index
```

**Challenge:** Requires understanding index structure to suggest appropriate placement. Risk of noisy suggestions.

---

## Not planned

### Automatic index generation

Building the index without user collaboration would defeat the purpose. The value comes from:
- User-specific curation ("I care about X, skip Y")
- Human-readable organization
- Descriptions that reflect user's mental model

Auto-generated indexes would be comprehensive but noisy.

### Full-text search over docs

Fetching and indexing all doc content would:
- Bloat the plugin significantly
- Duplicate what web search already does
- Require constant re-indexing

The curated index approach intentionally trades comprehensiveness for relevance.

---

## Contributing

To propose an enhancement:
1. Consider complexity vs. value tradeoff
2. Check if it aligns with design principles (human-in-the-loop, simplicity)
3. Add to this document with assessment
