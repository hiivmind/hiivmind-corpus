---
name: clickhouse-navigate
description: Find relevant ClickHouse documentation. Use when working with ClickHouse data modeling, ETL, query optimization, or operations.
---

# ClickHouse Documentation Navigator

Find and retrieve relevant documentation from the ClickHouse docs.

## Process

1. **Read the index**: `data/index.md`
2. **Find relevant file path** from index entries
3. **Get content** (see Source Access below)
4. **Answer** with citation to file path

## Source Access

### If `.source/` exists (local clone)
Read directly from `.source/{path}`

### If `.source/` doesn't exist

**Option A: Fetch on demand**
```
https://raw.githubusercontent.com/ClickHouse/clickhouse-docs/main/{path}
```
Use WebFetch to retrieve content. No clone needed.

**Option B: Clone locally**
```bash
git clone --depth 1 https://github.com/ClickHouse/clickhouse-docs.git .source
```

After cloning, compare commits:
```bash
cd .source && git rev-parse HEAD
```

Compare this to `last_commit_sha` in `data/config.yaml`:
- If clone is **newer** → warn user: "The docs have been updated since the index was built. Consider running maintenance to update the index."
- Continue answering regardless

## File Locations

- **Index**: `data/index.md`
- **Config**: `data/config.yaml` (has `last_commit_sha`)
- **Local source**: `.source/docs/` (if cloned)
- **Remote source**: `https://raw.githubusercontent.com/ClickHouse/clickhouse-docs/main/docs/`

## Index Structure

```markdown
## Section Name
*Brief description*

- **Doc Title** `docs/path/to/file.md` - Description
```

## Example

User: "How do I choose a primary key?"

1. Read `data/index.md`
2. Find: `**Choosing a Primary Key** docs/best-practices/choosing_a_primary_key.md`
3. Check if `.source/` exists:
   - Yes → read `.source/docs/best-practices/choosing_a_primary_key.md`
   - No → fetch from `raw.githubusercontent.com/.../docs/best-practices/choosing_a_primary_key.md`
4. Extract relevant content
5. Answer with citation: `docs/best-practices/choosing_a_primary_key.md`

## Output

- Cite the file path for reference
- Include code examples from the docs
- Suggest related docs from the same index section
- If source is newer than index, note this to user
