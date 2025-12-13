---
description: Discover and interact with installed hiivmind-corpus documentation corpora
argument-hint: [corpus-name] [optional query]
allowed-tools: ["Read", "Glob", "Bash", "AskUserQuestion", "Skill"]
---

# Corpus Gateway

Interactive gateway for discovering and navigating installed hiivmind-corpus documentation corpora.

## Arguments

**Input**: $ARGUMENTS

Parse the input to determine mode:

| Pattern | Mode | Action |
|---------|------|--------|
| (empty) | Discovery | List all corpora → interactive selection → corpus menu |
| `polars` | Corpus menu | Show actions for specified corpus |
| `polars "lazy api"` | Direct query | Navigate directly with the query |

## Mode: Discovery (No Arguments)

When invoked without arguments, discover all installed corpora and present an interactive selection.

### Step 1: Discover Corpora

Find all installed hiivmind-corpus plugins:

```bash
# User-level corpora
ls -d ~/.claude/skills/hiivmind-corpus-*/ 2>/dev/null | while read d; do
  echo "user-level|$(basename "$d")|$d"
done

# Repo-local corpora
ls -d .claude-plugin/skills/hiivmind-corpus-*/ 2>/dev/null | while read d; do
  echo "repo-local|$(basename "$d")|$d"
done

# Marketplace single-corpus
ls -d ~/.claude/plugins/marketplaces/hiivmind-corpus-*/.claude-plugin 2>/dev/null | while read d; do
  dir=$(dirname "$d")
  echo "marketplace|$(basename "$dir")|$dir"
done

# Marketplace multi-corpus children
ls -d ~/.claude/plugins/marketplaces/*/hiivmind-corpus-*/.claude-plugin 2>/dev/null | while read d; do
  dir=$(dirname "$d")
  echo "marketplace|$(basename "$dir")|$dir"
done
```

### Step 2: Check Status

For each corpus found, check if it's built:

```bash
# Check if index has real content (not placeholder)
if grep -q "Run.*hiivmind-corpus-build" "$corpus_path/data/index.md" 2>/dev/null; then
  echo "placeholder"
elif [ -f "$corpus_path/data/index.md" ]; then
  echo "built"
else
  echo "missing"
fi
```

### Step 3: Present Selection

If corpora found, use AskUserQuestion to present interactive list:

```
Which corpus would you like to use?

Options:
- hiivmind-corpus-polars (built) - Polars DataFrame documentation
- hiivmind-corpus-ibis (built) - Ibis SQL expression documentation
- hiivmind-corpus-github (stale) - GitHub API and Actions documentation
```

Include status indicators:
- ✓ built - Index is ready
- ⚠ stale - Source updated since last index
- ○ placeholder - Needs `hiivmind-corpus-build`

### Step 4: Route to Corpus Menu

After user selects a corpus, proceed to **Mode: Corpus Menu**.

---

## Mode: Corpus Menu (With Corpus Name)

When a corpus name is provided (or selected), show the action menu for that corpus.

### Step 1: Validate Corpus

Verify the corpus exists and resolve its path:

```bash
# Try each location
CORPUS_PATH=""
for path in \
  ~/.claude/skills/$CORPUS_NAME \
  .claude-plugin/skills/$CORPUS_NAME \
  ~/.claude/plugins/marketplaces/$CORPUS_NAME \
  ~/.claude/plugins/marketplaces/*/$CORPUS_NAME
do
  if [ -d "$path" ]; then
    CORPUS_PATH="$path"
    break
  fi
done
```

If not found:
> Corpus `{name}` not found. Run `/hiivmind-corpus` to see available corpora.

### Step 2: Check Status

Determine corpus status:

```bash
# Check build status
if grep -q "Run.*hiivmind-corpus-build" "$CORPUS_PATH/data/index.md" 2>/dev/null; then
  STATUS="placeholder"
elif [ -f "$CORPUS_PATH/data/index.md" ]; then
  STATUS="built"
else
  STATUS="missing"
fi

# Check staleness for built corpora
if [ "$STATUS" = "built" ]; then
  INDEXED_SHA=$(yq '.sources[0].last_commit_sha' "$CORPUS_PATH/data/config.yaml" 2>/dev/null)
  SOURCE_ID=$(yq '.sources[0].id' "$CORPUS_PATH/data/config.yaml" 2>/dev/null)
  CURRENT_SHA=$(git -C "$CORPUS_PATH/.source/$SOURCE_ID" rev-parse HEAD 2>/dev/null)
  if [ -n "$CURRENT_SHA" ] && [ "$CURRENT_SHA" != "$INDEXED_SHA" ]; then
    STATUS="stale"
  fi
fi
```

### Step 3: Present Action Menu

Use AskUserQuestion to show available actions:

**For built/stale corpora:**
```
What would you like to do with {corpus_name}?

- Navigate - Ask questions about this documentation
- Check freshness - See if the source has updates
- Enhance - Add more depth to specific topics
- Refresh - Sync index with upstream changes
```

**For placeholder corpora:**
```
The {corpus_name} corpus hasn't been built yet.

- Build now - Run hiivmind-corpus-build to create the index
- Add sources - Add more documentation sources first
```

### Step 4: Dispatch to Skill

Based on selection, invoke the appropriate skill:

| Action | Dispatch To |
|--------|-------------|
| Navigate | Load `hiivmind-corpus-navigate` skill with corpus context |
| Check freshness | Load `hiivmind-corpus-refresh` skill (dry-run mode) |
| Enhance | Load `hiivmind-corpus-enhance` skill |
| Refresh | Load `hiivmind-corpus-refresh` skill |
| Build now | Load `hiivmind-corpus-build` skill |
| Add sources | Load `hiivmind-corpus-add-source` skill |

When dispatching, provide corpus context:
> Working with corpus: {corpus_name}
> Location: {corpus_path}
> Status: {status}

---

## Mode: Direct Query (With Corpus + Query)

When both corpus name and query are provided, navigate directly.

### Parse Arguments

Split arguments into corpus name and query:

```
/hiivmind-corpus polars "how do I filter a dataframe"
             ^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
             corpus   query
```

### Dispatch to Navigate

1. Resolve corpus path (as in Corpus Menu Step 1)
2. Read the corpus's `data/index.md`
3. Find relevant entries matching the query
4. Fetch and present documentation

Invoke the per-corpus navigate skill with the query:
> **Corpus**: {corpus_name}
> **Query**: {query}
> **Location**: {corpus_path}

---

## Error Handling

**No corpora installed:**
```
No hiivmind-corpus documentation corpora are installed.

To get started:
- Create a new corpus: Use `hiivmind-corpus-init`
- Install from marketplace: `/plugin install hiivmind-corpus-polars@hiivmind`
```

**Invalid corpus name:**
```
Corpus `{name}` not found.

Available corpora:
- hiivmind-corpus-polars
- hiivmind-corpus-ibis

Did you mean one of these?
```

**Query on placeholder corpus:**
```
Cannot navigate `{corpus}` - the index hasn't been built yet.

Would you like to build it now? (This requires collaborative review)
```

---

## Examples

**List all corpora:**
```
/hiivmind-corpus
```

**Open menu for specific corpus:**
```
/hiivmind-corpus polars
```

**Query directly:**
```
/hiivmind-corpus polars "lazy evaluation"
/hiivmind-corpus github "create a workflow"
```

---

## Notes

- This command is the primary entry point for corpus interaction
- Uses `hiivmind-corpus-discover` logic for finding corpora
- Routes to per-corpus navigate skills for actual documentation fetching
- All corpus names use the `hiivmind-corpus-` prefix for consistency
