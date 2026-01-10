---
name: hiivmind-corpus-add-source
description: >
  This skill should be used when the user asks to "add another source to corpus", "include blog posts",
  "add local documents", "add git repo to corpus", "extend corpus with web pages", "add team docs",
  or wants to extend an existing corpus with additional documentation sources. Triggers on
  "add [url/repo] to corpus", "include [source] in my docs", "add another documentation source",
  "combine sources in corpus", or "hiivmind-corpus add-source".
---

# Add Source to Corpus

Add a new documentation source to an existing corpus skill.

## Process

```
1. LOCATE  →  2. TYPE  →  3. COLLECT  →  4. SETUP  →  5. INDEX?
```

## Prerequisites

Run from within a corpus skill directory containing `data/config.yaml`.

---

## Step 1: Locate Corpus

**See:** `lib/corpus/patterns/config-parsing.md` for YAML extraction methods.

Find and read `data/config.yaml`:

Using Claude tools:
```
Read: data/config.yaml
```

Verify:
- File exists
- List existing sources to user

---

## Step 2: Source Type

### Step 2a: Detect llms.txt Manifest (Automatic)

Before asking the user for source type, check if the URL provides an llms.txt manifest:

**Using Claude tools:**
```
WebFetch: {base_url}/llms.txt
If 404: WebFetch: {base_url}/docs/llms.txt
```

If manifest found:
> Found llms.txt manifest at {url}:
> - Title: {title}
> - {N} pages in {M} sections
>
> This site provides structured documentation for LLMs.
> Would you like to use the **llms-txt** source type for automatic discovery?

### Step 2b: Ask for Source Type

If no llms.txt found or user declines, ask which type to add:

| Type | Description | Example Use Case |
|------|-------------|------------------|
| **git** | Git repository | Library docs, framework APIs |
| **local** | User-uploaded files | Team standards, internal docs |
| **web** | Blog posts, articles | Individual web pages to cache |
| **generated-docs** | Auto-generated docs site | MkDocs, Sphinx, gh CLI manual |
| **llms-txt** | Site with llms.txt manifest | Anthropic docs, Vercel docs |

---

## Step 3: Collect Source Information

### For Git Sources

| Input | Source | Example |
|-------|--------|---------|
| Repo URL | Ask user | `https://github.com/TanStack/query` |
| Source ID | Derive from repo name | `tanstack-query` |
| Branch | Ask or default `main` | `main` |
| Docs root | Investigate or ask | `docs/` |

**Generate unique source ID:**
- Derive from repo name (lowercase, hyphenated)
- Check for conflicts with existing sources
- Ask user if ambiguous

### For Local Sources

| Input | Source | Example |
|-------|--------|---------|
| Source ID | Ask user | `team-standards` |
| Description | Ask user | `Internal team documentation` |

### For Web Sources

| Input | Source | Example |
|-------|--------|---------|
| Source ID | Ask user | `kent-testing-blog` |
| Description | Ask user | `Testing best practices articles` |
| URLs | Ask for list | One or more URLs to fetch |

### For Generated-Docs Sources

| Input | Source | Example |
|-------|--------|---------|
| Source ID | Ask user or derive | `gh-cli-manual` |
| Source repo URL | Ask user | `https://github.com/cli/cli` |
| Branch | Ask or default `main` | `trunk` |
| Docs root | Ask (path in repo that generates docs) | `cmd/` |
| Web base URL | Ask user | `https://cli.github.com/manual` |
| Sitemap URL | Check or ask | `https://cli.github.com/sitemap.xml` |

**Key concept:** The source repo contains the code that *generates* the docs. The web URL is where the *rendered* docs are published.

### For llms-txt Sources

| Input | Source | Example |
|-------|--------|---------|
| Source ID | Derive from title or ask | `claude-code-docs` |
| Manifest URL | Auto-detected or ask | `https://code.claude.com/docs/llms.txt` |
| Base URL | Derive from manifest URL or ask | `https://code.claude.com/docs/en` |
| Caching strategy | Ask user | `selective`, `full`, or `on-demand` |
| Sections to cache | Ask if selective | `["skills", "agents"]` |

**Key concept:** The llms.txt manifest provides structured discovery with links to raw markdown. Content is much smaller (10-30x) than HTML pages.

---

## Step 4: Setup Source

**See:** `lib/corpus/patterns/sources/` for source-specific operations (git.md, local.md, web.md, generated-docs.md, llms-txt.md).

### Git Source Setup

```bash
# Clone to source-specific directory
git clone --depth 1 {repo_url} .source/{source_id}

# Get current commit SHA
cd .source/{source_id} && git rev-parse HEAD
```

#### Research the Source

After cloning, analyze the documentation structure:

```bash
# Framework detection
ls .source/{source_id}/

# Find doc framework config
find .source/{source_id} -maxdepth 2 -name "docusaurus.config.js" -o -name "mkdocs.yml" -o -name "conf.py" 2>/dev/null

# Find nav structure
find .source/{source_id} -maxdepth 2 -name "sidebars*" -o -name "_toc.yml" 2>/dev/null

# Count doc files
find .source/{source_id}/{docs_root} -name "*.md" -o -name "*.mdx" 2>/dev/null | wc -l

# Check for i18n
ls .source/{source_id}/i18n/ .source/{source_id}/docs/en/ 2>/dev/null
```

| Finding | Implication |
|---------|-------------|
| `docusaurus.config.js` | Docusaurus site - check `sidebars.js` for structure |
| `mkdocs.yml` | MkDocs site - nav structure in yml file |
| `conf.py` | Sphinx docs - check `toctree` directives |
| `i18n/` or `/en/` dirs | Multilingual - may need language selection |

This research helps inform the build phase but doesn't block source addition.

Add to config.yaml `sources:` array:
```yaml
- id: "{source_id}"
  type: "git"
  repo_url: "{repo_url}"
  repo_owner: "{owner}"
  repo_name: "{name}"
  branch: "{branch}"
  docs_root: "{docs_root}"
  last_commit_sha: "{sha}"
  last_indexed_at: null
```

### Local Source Setup

```bash
# Create uploads directory
mkdir -p data/uploads/{source_id}
```

Instruct user:
> Place your documents in `data/uploads/{source_id}/`
> Supported formats: .md, .mdx
> Let me know when files are in place.

After user confirms, scan directory:
```bash
find data/uploads/{source_id} -name "*.md" -o -name "*.mdx"
```

Add to config.yaml:
```yaml
- id: "{source_id}"
  type: "local"
  path: "uploads/{source_id}/"
  description: "{description}"
  files: []
  last_indexed_at: null
```

### Web Source Setup

```bash
# Create cache directory
mkdir -p .cache/web/{source_id}
```

For each URL provided:

1. **Fetch content** using WebFetch tool
2. **Show user the fetched content** for approval
3. **If approved**, save as markdown to `.cache/web/{source_id}/{slug}.md`
4. **Generate filename** from URL path (e.g., `testing-implementation-details.md`)
5. **Calculate content hash** (SHA-256 of content)

**Important:** Never auto-save web content. User must approve each fetched article before caching.

Add to config.yaml:
```yaml
- id: "{source_id}"
  type: "web"
  description: "{description}"
  urls:
    - url: "{url}"
      title: "{title}"
      cached_file: "{filename}.md"
      fetched_at: "{timestamp}"
      content_hash: "sha256:{hash}"
  cache_dir: ".cache/web/{source_id}/"
  last_indexed_at: null
```

### Generated-Docs Source Setup

**See:** `lib/corpus/patterns/sources/generated-docs.md` for URL discovery operations.

1. **Clone source repo** (for SHA tracking):
```bash
git clone --depth 1 --branch {branch} {source_repo_url} .source/{source_id}
sha=$(git -C .source/{source_id} rev-parse HEAD)
```

2. **Discover URLs** from web output:
   - First, try sitemap: `WebFetch: {sitemap_url}`
   - If no sitemap, crawl from base URL
   - Show discovered URLs to user for confirmation

3. **Add to config.yaml:**
```yaml
- id: "{source_id}"
  type: "generated-docs"

  source_repo:
    url: "{source_repo_url}"
    branch: "{branch}"
    docs_root: "{docs_root}"
    last_commit_sha: "{sha}"

  web_output:
    base_url: "{web_base_url}"
    sitemap_url: "{sitemap_url}"  # if available
    discovered_urls:
      - path: "/path1"
        title: "Page Title 1"
      - path: "/path2"
        title: "Page Title 2"

  cache:
    enabled: false
    dir: ".cache/web/{source_id}/"

  last_indexed_at: null
```

**Important notes:**
- Content is fetched live via WebFetch (no pre-caching needed)
- Source repo clone is shallow and only for SHA tracking
- `discovered_urls` is populated by sitemap/crawl discovery

### llms-txt Source Setup

**See:** `lib/corpus/patterns/sources/llms-txt.md` for manifest parsing and caching operations.

1. **Fetch and parse manifest:**
```
WebFetch: {manifest_url}
Parse: Extract title, summary, sections, URLs
```

2. **Hash manifest for change detection:**
```python
import hashlib
manifest_hash = hashlib.sha256(manifest_content.encode()).hexdigest()
```

3. **Setup cache directory:**
```bash
mkdir -p .cache/llms-txt/{source_id}
```

4. **Cache pages based on strategy:**
   - **full**: Fetch and cache all pages from manifest
   - **selective**: Fetch only specified sections
   - **on-demand**: Skip caching, fetch live when navigating

5. **Add to config.yaml:**
```yaml
- id: "{source_id}"
  type: "llms-txt"

  manifest:
    url: "{manifest_url}"
    last_hash: "sha256:{hash}"
    last_fetched_at: "{timestamp}"

  urls:
    base_url: "{base_url}"
    suffix: ".md"

  cache:
    enabled: true
    dir: ".cache/llms-txt/{source_id}/"
    strategy: "{strategy}"
    sections: ["{section1}", "{section2}"]  # if selective

  structure:
    title: "{title}"
    summary: "{summary}"
    sections:
      - name: "{section_name}"
        urls:
          - path: "{path}"
            title: "{page_title}"

  last_indexed_at: null
```

**Important notes:**
- Raw markdown content requires no HTML extraction
- Manifest hash enables lightweight change detection
- Section structure can inform index organization

---

## Step 5: Index Prompt

Ask user:
> Would you like to add entries from this source to the index now?

### If yes:

1. Scan the new source for available documents
2. **Detect large structured files** (see below)
3. Show document list to user
4. Ask which documents to include
5. Collaboratively add entries to `data/index.md`
6. Use `{source_id}:{path}` format for all entries
7. Update `last_indexed_at` for the source in config

### Detecting Large Structured Files

**See:** `lib/corpus/patterns/scanning.md` for large file detection patterns.

Check for files that are too large to read directly:

Using Claude tools:
```
Read: {source_path}/{file} (check line count)
If > 1000 lines, mark with ⚡ GREP
```

Using bash:
```bash
# Find files over 1000 lines
wc -l {source_path}/*.graphql {source_path}/*.json {source_path}/*.yaml 2>/dev/null | awk '$1 > 1000'
```

**File types to check:**
- GraphQL schemas (`.graphql`, `.gql`)
- OpenAPI/Swagger specs (`.yaml`, `.json`)
- JSON Schema files
- Any file > 1000 lines

**Mark these in the index with `⚡ GREP`:**

```markdown
- **GraphQL Schema** `source-id:schema.graphql` ⚡ GREP - API schema (15k lines). Search with: `grep -n "^type {Name}" ... -A 30`
```

The `⚡ GREP` marker tells the navigator to use Grep instead of Read.

Example entries:
```markdown
## New Section (from {source_id})

- **Document Title** `{source_id}:path/to/file.md` - Brief description
```

### If no:

- Note that source is configured but not yet indexed
- User can run `hiivmind-corpus-build` or `hiivmind-corpus-enhance` later

---

## Example Sessions

### Adding a Git Repository

**User**: "Add TanStack Query docs to this corpus"

**Step 1**: Read config, list existing sources
**Step 2**: Source type: **git**
**Step 3**: Collect:
- Repo: `https://github.com/TanStack/query`
- Source ID: `tanstack-query`
- Branch: `main`
- Docs root: `docs/`
**Step 4**: Clone to `.source/tanstack-query/`, add to config
**Step 5**: Ask about indexing

---

### Adding Local Documents

**User**: "I want to add our team's API documentation"

**Step 1**: Read config, list existing sources
**Step 2**: Source type: **local**
**Step 3**: Collect:
- Source ID: `team-api-docs`
- Description: `Internal API documentation`
**Step 4**: Create `data/uploads/team-api-docs/`, wait for files
**Step 5**: Offer to index

---

### Adding Web Articles

**User**: "Add these testing blog posts to my corpus"

**Step 1**: Read config, list existing sources
**Step 2**: Source type: **web**
**Step 3**: Collect:
- Source ID: `kent-testing-blog`
- Description: `Testing best practices from Kent C. Dodds`
- URLs:
  - `https://kentcdodds.com/blog/testing-implementation-details`
  - `https://kentcdodds.com/blog/common-mistakes-with-react-testing-library`
**Step 4**:
- Fetch first URL, show content to user
- User approves → save to `.cache/web/kent-testing-blog/testing-implementation-details.md`
- Repeat for each URL
- Add to config
**Step 5**: Offer to index

---

### Adding Generated-Docs (Auto-Generated Documentation)

**User**: "Add the GitHub CLI manual - it's generated from the cli/cli repo"

**Step 1**: Read config, list existing sources
**Step 2**: Source type: **generated-docs**
**Step 3**: Collect:
- Source ID: `gh-cli-manual`
- Source repo: `https://github.com/cli/cli`
- Branch: `trunk`
- Docs root: `cmd/` (where command definitions live)
- Web base URL: `https://cli.github.com/manual`
- Sitemap URL: `https://cli.github.com/sitemap.xml`
**Step 4**:
- Clone source repo (shallow): `git clone --depth 1 https://github.com/cli/cli .source/gh-cli-manual`
- Get SHA for tracking
- Fetch sitemap, discover 165 URLs
- Show discovered URLs to user: "Found 165 command pages. Add all?"
- Add to config with discovered_urls
**Step 5**: Offer to index (add entries to index.md pointing to discovered URLs)

**Key difference from web source**: No pre-caching. Content is fetched live when navigating.

---

### Adding llms.txt Source

**User**: "Add the Claude Code documentation"

**Step 1**: Read config, list existing sources
**Step 2**: Detect llms.txt at `https://code.claude.com/docs/llms.txt`
- Parse manifest: "Claude Code", 47 pages, 8 sections
- User confirms llms-txt source type
**Step 3**: Collect:
- Source ID: `claude-code-docs`
- Manifest URL: `https://code.claude.com/docs/llms.txt`
- Base URL: `https://code.claude.com/docs/en`
- Caching strategy: `selective`
- Sections to cache: `["skills", "agents"]`
**Step 4**:
- Hash manifest for change detection
- Setup cache directory
- Fetch and cache selected sections (raw markdown)
- Add to config with structure
**Step 5**: Offer to index

**Key difference from web source**: Structured discovery via manifest, raw markdown access (10-30x smaller), hash-based change detection.

---

## Reference

**Pattern documentation:**
- `lib/corpus/patterns/config-parsing.md` - YAML config extraction
- `lib/corpus/patterns/sources/` - Source type operations (git, local, web, generated-docs, llms-txt)
- `lib/corpus/patterns/scanning.md` - File discovery and large file detection
- `lib/corpus/patterns/paths.md` - Path resolution

**Related skills:**
- Initialize corpus: `skills/hiivmind-corpus-init/SKILL.md`
- Build full index: `skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `skills/hiivmind-corpus-refresh/SKILL.md`
- Upgrade to latest standards: `skills/hiivmind-corpus-upgrade/SKILL.md`
- Discover corpora: `skills/hiivmind-corpus-discover/SKILL.md`
- Global navigation: `skills/hiivmind-corpus-navigate/SKILL.md`
- Gateway command: `commands/hiivmind-corpus.md`
