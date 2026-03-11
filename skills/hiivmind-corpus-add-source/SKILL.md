---
name: hiivmind-corpus-add-source
description: >
  Add documentation source to corpus. Triggers: "add source", "add git repo",
  "include blog posts", "add local documents", "extend corpus with web pages",
  "add team docs", "add PDF to corpus", "import PDF book", "split PDF into chapters".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash, WebFetch
inputs:
  - name: source_url
    type: string
    required: false
    description: URL or path to documentation source (prompted if not provided)
  - name: working_directory
    type: string
    required: false
    description: Corpus root directory (defaults to current directory)
outputs:
  - name: source_id
    type: string
    description: Identifier of the added source
  - name: source_type
    type: string
    description: Type of source added (git, local, web, llms-txt, generated-docs)
---

# Add Source

Add a documentation source to an existing corpus. Detects source type, collects
configuration, executes acquisition, and updates config.yaml.

## Precondition

A `config.yaml` must exist in the working directory. If not found, display:

```
No config.yaml found. Run hiivmind-corpus-init first.
```

---

## Phase 1: Locate Corpus

**Inputs:** working directory
**Outputs:** `computed.config`, `computed.is_first_source`

1. Read `config.yaml` and parse it
2. Check if `sources` array is empty → set `computed.is_first_source`
3. Display: "Found corpus: {config.corpus.name} — Existing sources: {count}"

---

## Phase 2: Determine Source Type

**Inputs:** optional `source_url` from invocation
**Outputs:** `computed.source_url`, `computed.source_type`

### If source_url was provided

Check the URL to auto-detect type:

1. If URL ends with `.pdf` or `.PDF` → go to **PDF Detection** (below)
2. Otherwise, try llms.txt detection:
   - Fetch `{base_url}/llms.txt` (then `{base_url}/docs/llms.txt` if 404)
   - If manifest found, ask user: "Found llms.txt manifest! Use llms-txt source type? (Recommended) / Choose different type"
   - If user accepts → `source_type = llms-txt`
3. If no manifest found, ask: "What type of source is {url}?"
   - Git repository → `source_type = git`
   - Web page → `source_type = web`
   - Generated docs (MkDocs, Sphinx, ReadTheDocs) → `source_type = generated-docs`

### If source_url was NOT provided

Ask: "What documentation would you like to add?"

| Option | Sets |
|--------|------|
| Git repository | `source_type = git` |
| Local files | `source_type = local` |
| Web pages | `source_type = web` |
| llms.txt site | `source_type = llms-txt` |

If user types a URL instead of selecting an option, store it as `source_url` and
re-enter the detection flow above.

### PDF Detection

If the URL/path ends with `.pdf`:

1. Check if `pymupdf` is installed (`python -c "import pymupdf"`)
2. If available:
   - Run chapter detection per `lib/corpus/patterns/sources/pdf.md` § "Detect Chapters"
   - If chapters found, ask: "Split into chapters? (Recommended for large PDFs) / Keep as single file"
   - If user wants split → execute split per pdf.md § "Split PDF"
3. If pymupdf missing:
   - Ask: "PDF splitting requires pymupdf. Add as single file? / Cancel (I'll install pymupdf first)"
4. After split (or if no split), configure as a `local` source

---

## Phase 3: Collect Source Details

Branch based on `computed.source_type`. Each path collects what's needed and updates config.yaml.

### Git Source

**See:** `lib/corpus/patterns/sources/git.md`

1. If `source_url` not set, ask: "What's the git repository URL?"
2. Parse URL to extract `owner` and `repo_name`
3. Derive `source_id` from repo name (lowercase, alphanumeric + hyphens)
4. Ask branch (default: main) and docs root (default: docs/)
5. Validate:
   - `source_url` is set
   - `source_id` is not already in config.sources
6. Clone: `git clone --depth 1 --branch {branch} {url} .source/{source_id}`
7. Get SHA: `git -C .source/{source_id} rev-parse HEAD`
8. Add to config.yaml per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "Git Source Entry"

   Substitute collected values: `source_id`, `url`, `owner`, `repo_name`, `branch`, `docs_root`, `sha`.

### Local Source

**See:** `lib/corpus/patterns/sources/local.md`

1. Ask: "What should this local source be called? (used as ID)"
2. Ask: "Brief description of this source:"
3. Create directory: `mkdir -p uploads/{source_id}`
4. Add to config.yaml per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "Local Source Entry"

   Substitute collected values: `source_id`, `description`.

5. Display: "Place your documents in uploads/{source_id}/. Supported formats: .md, .mdx, .pdf"

### Web Source

**See:** `lib/corpus/patterns/sources/web.md`

1. If `source_url` not set, ask: "What should this web source be called?"
   Otherwise derive source_id from URL
2. Ask: "Brief description of this web source:"
3. Ask: "Enter the first URL to cache (you can add more later):"
4. Create directory: `mkdir -p .cache/web/{source_id}`
5. Fetch the URL content using WebFetch
6. Show preview (first ~500 chars) and ask: "Save this content to cache?"
7. If yes, save to `.cache/web/{source_id}/{filename}.md`
8. Add to config.yaml per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "Web Source Entry"

   Substitute collected values: `source_id`, `description`, `url`, `filename`, `timestamp`.

### llms-txt Source

**See:** `lib/corpus/patterns/sources/llms-txt.md`

1. If `source_url` not set, ask: "Enter the base URL for the llms.txt site:"
   Then fetch manifest per llms-txt.md § "Fetch Manifest"
2. Parse manifest to extract title, sections, page count
3. Derive `source_id` from manifest title (or ask user if parsing fails)
4. Ask caching strategy: Selective (recommended) / Full / On-demand
5. Create directory: `mkdir -p .cache/llms-txt/{source_id}`
6. Hash manifest content for change detection
7. Add to config.yaml per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "llms-txt Source Entry"

   Substitute collected values: `source_id`, `manifest_url`, `sha256_hash`, `timestamp`, `base_url`, `strategy`.

### Generated-Docs Source

**See:** `lib/corpus/patterns/sources/generated-docs.md`

1. Ask: "What's the source repository URL (where docs are generated from)?"
2. Ask: "What's the published docs URL?"
3. Derive `source_id` from repo name
4. Clone source repo for SHA tracking: `git clone --depth 1 {url} .source/{source_id}`
5. Get SHA: `git -C .source/{source_id} rev-parse HEAD`
6. Add to config.yaml per `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "Generated-Docs Source Entry"

   Substitute collected values: `source_id`, `source_repo_url`, `sha`, `web_base_url`.

---

## Phase 4: Post-Setup

**Inputs:** `computed.source_id`, `computed.is_first_source`

### First-source navigate update

If `computed.is_first_source` is true, update navigate skill examples per
`lib/corpus/patterns/sources/shared.md` § "Update Navigate Skill Examples".

### Offer indexing

Ask: "Would you like to add entries from this source to the index now?"

- **Yes** → Display: "Run `/hiivmind-corpus-build` to analyze the source and create index entries."
- **No** → Continue

### Success

Display:

```
Source '{source_id}' added successfully.
Type: {source_type}
Location: {.source/ or uploads/ or .cache/}{source_id}
```

---

## Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| No config.yaml | "No config.yaml found" | Run hiivmind-corpus-init |
| Invalid git URL | "Could not parse repository URL" | Check URL format |
| Clone failed | "Failed to clone repository" | Check URL and access |
| Config update failed | "Failed to update config.yaml" | Check file permissions |
| Web fetch failed | "Failed to fetch URL content" | Check URL accessibility |
| Source ID exists | "Source ID '{id}' already exists" | Choose different name |

---

## Pattern Documentation

Source-specific operations referenced by this skill:

- **Config formatting:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md`
- **Git sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/git.md`
- **Local sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/local.md`
- **Web sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/web.md`
- **llms-txt sources:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/llms-txt.md`
- **Generated docs:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/generated-docs.md`
- **PDF processing:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/pdf.md`
- **Shared patterns:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/sources/shared.md`

## Related Skills

- Initialize corpus: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-init/SKILL.md`
- Build full index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Enhance topics: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-enhance/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
