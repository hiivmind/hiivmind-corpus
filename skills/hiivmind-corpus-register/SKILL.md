---
name: hiivmind-corpus-register
description: >
  Register a documentation corpus with the current project. Use when users want to add
  a corpus to their project, connect documentation sources, or set up corpus access.
  Triggers: register corpus, add corpus, connect docs, add documentation, setup corpus.
allowed-tools: Read, Write, Edit, Bash, WebFetch, AskUserQuestion
---

# Corpus Register Skill

Add a documentation corpus to the project's registry. This creates or updates
`.hiivmind/corpus/registry.yaml` with the corpus source information.

## When to Use

- User wants to add a corpus to their project
- User says "register", "add", or "connect" with a corpus reference
- Gateway routes a registration request to this skill

## Workflow

### Phase 1: Parse Source Reference

Parse the source argument to determine type and location:

**GitHub format:**
```
github:owner/repo                    → full repo
github:owner/repo@ref                → specific branch/tag/commit
github:owner/repo/path               → subdirectory in repo
github:owner/repo/path@ref           → subdirectory with ref
```

**Local format:**
```
local:/path/to/corpus                → absolute path
local:./relative/path                → relative path
```

**URL format:**
```
https://github.com/owner/repo        → GitHub repo URL
```

### Phase 2: Validate Corpus

Fetch and validate the corpus has required files:

**For GitHub sources:**
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path?}/config.yaml
prompt: "Check if this is a valid YAML file with corpus.name field"
```

Required files:
- `config.yaml` - Corpus configuration with keywords
- `index.md` - Documentation index

If validation fails:
```
The specified location doesn't appear to be a valid corpus.
Missing required file: config.yaml

A valid corpus has:
  config.yaml    - Source definitions and keywords
  index.md       - Documentation index

To create a new corpus, use:
  /hiivmind-corpus init
```

### Phase 3: Extract Corpus Metadata

From config.yaml, extract:
- `corpus.name` - Corpus identifier
- `corpus.display_name` - Human-readable name
- `corpus.keywords` - Routing keywords

```yaml
# Example config.yaml
corpus:
  name: "flyio"
  display_name: "Fly.io"
  keywords:
    - flyio
    - fly.io
    - deployment
```

### Phase 4: Create/Update Registry

**If `.hiivmind/corpus/registry.yaml` doesn't exist:**

Create the directory and file:

```bash
mkdir -p .hiivmind/corpus
```

```yaml
# .hiivmind/corpus/registry.yaml
schema_version: 1

corpora:
  - id: flyio
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main
      path: null
    cache:
      strategy: fetch      # clone | fetch | none
      path: null           # .corpus-cache/flyio for clone strategy
      ttl: 7d
```

**If registry exists:**

Add or update the corpus entry:

```yaml
# Updated registry
corpora:
  - id: existing-corpus
    ...
  - id: flyio              # New entry
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main
```

### Phase 5: Confirm Registration

Display confirmation:

```
Registered corpus: Fly.io (flyio)

Source: github:hiivmind/hiivmind-corpus-flyio@main
Keywords: flyio, fly.io, deployment, hosting, edge, cloud

You can now navigate this corpus:
  "How do I deploy to Fly.io?"
  /hiivmind-corpus navigate flyio "postgres setup"

Registry updated: .hiivmind/corpus/registry.yaml
```

## Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `{source}` | Corpus source reference | `github:hiivmind/hiivmind-corpus-flyio` |

**Source formats:**
```
github:hiivmind/hiivmind-corpus-flyio
github:hiivmind/hiivmind-corpus-flyio@v2.0
github:hiivmind/hiivmind-corpus-data/hiivmind-corpus-polars
local:./docs/corpus
https://github.com/hiivmind/hiivmind-corpus-flyio
```

## Cache Strategy Options

When registering, the user can optionally specify caching:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `fetch` | Always fetch from source (default) | Small corpora, always-fresh |
| `clone` | Clone repo locally | Large corpora, offline access |
| `none` | No caching | Local sources |

**Specifying cache strategy:**
```
/hiivmind-corpus register --cache=clone github:hiivmind/hiivmind-corpus-flyio
```

## Interactive Mode

If source is not provided, prompt the user:

```
What corpus would you like to register?

1. **From GitHub** - Enter a GitHub repository
2. **From local path** - Use a local directory
3. **Browse available** - See published corpora
```

For GitHub:
```
Enter the GitHub repository (e.g., hiivmind/hiivmind-corpus-flyio):
```

## Error Handling

**Invalid source format:**
```
Could not parse source reference: {input}

Expected formats:
  github:owner/repo
  github:owner/repo@ref
  local:/path/to/corpus
  https://github.com/owner/repo
```

**Corpus not found:**
```
Could not find corpus at: github:owner/nonexistent

Verify the repository exists and contains:
  - config.yaml
  - index.md
```

**Corpus already registered:**
```
Corpus 'flyio' is already registered.

Current source: github:hiivmind/hiivmind-corpus-flyio@main

Would you like to update the source?
  1. Yes, update to new source
  2. No, keep existing
```

**Permission denied:**
```
Cannot write to .hiivmind/corpus/registry.yaml

Check file permissions or run with appropriate access.
```

## Registry Schema

Full registry schema for reference:

```yaml
schema_version: 1

corpora:
  - id: flyio                          # Unique identifier (from config.yaml)
    source:
      type: github                     # github | local
      repo: hiivmind/hiivmind-corpus-flyio  # owner/repo
      ref: main                        # branch, tag, or commit SHA
      path: null                       # subdirectory for mono-repos
    cache:
      strategy: fetch                  # clone | fetch | none
      path: null                       # local cache path (for clone)
      ttl: 7d                          # cache validity period
    registered_at: "2026-01-26T12:00:00Z"
```

## Related Skills

- **Navigate:** `hiivmind-corpus-navigate` - Query registered corpora
- **Status:** `hiivmind-corpus-status` - Check corpus health
- **Discover:** `hiivmind-corpus-discover` - Find available corpora
