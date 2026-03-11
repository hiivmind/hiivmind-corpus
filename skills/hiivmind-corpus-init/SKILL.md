---
name: hiivmind-corpus-init
description: >
  This skill should be used when the user asks to "create a corpus", "initialize documentation",
  "set up docs for a library", "index this project's docs", "create documentation corpus",
  or mentions wanting to create a new documentation corpus. Also triggers on "new corpus",
  "corpus for [library name]", or "hiivmind-corpus init".
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash
inputs:
  - name: source_url
    type: string
    required: false
    description: GitHub repo URL, docs site URL, or local path (prompted if not provided)
  - name: corpus_name
    type: string
    required: false
    description: Corpus identifier (derived from URL or prompted if not provided)
outputs:
  - name: corpus_root
    type: string
    description: Path to the created corpus directory
  - name: delegated_to_add_source
    type: boolean
    description: Whether the skill delegated to add-source for initial content
---

# Corpus Init

Initialize a new data-only documentation corpus. Collects project info, scaffolds a flat
repository structure, and delegates to `hiivmind-corpus-add-source` for source acquisition.

> **HARD STOP:** This skill MUST NOT fetch, clone, scan, explore, or read any external content.
> It writes local files only. All source acquisition is the exclusive responsibility of
> `hiivmind-corpus-add-source`.

## Corpus Structure

Every corpus created by this skill has this structure:

```
hiivmind-corpus-{name}/
├── config.yaml          # schema_version: 2, corpus metadata, source stub
├── index.md             # Placeholder until build runs
├── CLAUDE.md            # Data-only corpus guidance
├── README.md            # Brief description
├── .gitignore           # .source/, .cache/, OS files
├── LICENSE              # MIT
└── uploads/             # For local document uploads
```

---

## Phase 1: Collect Project Name

**Inputs:** invocation arguments (optional `source_url`, optional `corpus_name`)
**Outputs:** `computed.corpus_name`, `computed.display_name`

If `corpus_name` was provided as an input argument, use it directly.

If `source_url` was provided, derive the name:

```pseudocode
DERIVE_NAME(url):
  IF url contains "github.com":
    name = url, remove trailing ".git", take last path segment, lowercase
  ELSE IF url starts with "http":
    name = url, strip protocol, take first domain segment,
           remove "docs." prefix, take before first ".", lowercase
  ELSE:
    # Local path
    name = basename of path, lowercase
  RETURN name
```

Confirm with user: "Corpus name derived as '{name}'. Is this correct?"

If neither argument was provided, ask: "What project are you creating a corpus for?"

Derive `display_name` by capitalizing the first letter of each word in the name.

---

## Phase 2: Collect Source URL

**Inputs:** invocation arguments (optional `source_url`)
**Outputs:** `computed.source_url`, `computed.source_type`

If `source_url` was provided as an input argument, skip the prompt.

Otherwise ask: "Where are the docs? (GitHub repo URL, docs site URL, or local path)"

Determine source type from URL shape:

| URL Pattern | Source Type |
|-------------|-------------|
| Contains `github.com` | `git` |
| Starts with `http` | `web` |
| Filesystem path | `local` |

For git sources, also extract `repo_owner` and `repo_name` from the URL path segments.

Store the URL string and type. **Do not fetch, clone, or read the source.**

---

## Phase 3: Collect Keywords

**Inputs:** `computed.corpus_name`
**Outputs:** `computed.keywords`

Suggest default keywords based on the project name. Ask: "What keywords should route
documentation questions to this corpus? (comma-separated, or press enter for defaults)"

Default keywords: the corpus name itself plus common variations (e.g., for "flyio":
`flyio, fly.io, fly`).

---

## Phase 4: Scaffold

**Inputs:** `computed.corpus_name`, `computed.display_name`, `computed.source_url`,
`computed.source_type`, `computed.keywords`
**Outputs:** `computed.corpus_root`, files on disk

Create the corpus directory and all files at `./hiivmind-corpus-{name}/`.

```bash
mkdir -p ./hiivmind-corpus-{name}/uploads
```

### 4a: config.yaml

**For git sources:**

```yaml
schema_version: 2

corpus:
  name: "{name}"
  display_name: "{Display Name}"
  keywords:
    - "{keyword1}"
    - "{keyword2}"

sources:
  - id: "{name}"
    type: "git"
    repo_url: "{url}"
    repo_owner: "{owner}"
    repo_name: "{repo}"
    branch: "main"
    docs_root: "."
    last_commit_sha: null
    last_indexed_at: null

index:
  format: "markdown"
  last_updated_at: null

settings:
  include_patterns:
    - "**/*.md"
    - "**/*.mdx"
  exclude_patterns:
    - "**/_*.md"
    - "**/_snippets/**"
```

**For web sources:** Use `type: "web"` and `base_url` field instead of repo fields.

**For local sources:** Use `type: "local"` and `path` field instead of repo fields.

### 4b: index.md

```markdown
# {Display Name} Documentation Corpus

> Run `/hiivmind-corpus build` to build this index.

This corpus is not yet populated. Add documentation sources and build the index.
```

### 4c: CLAUDE.md

Write a CLAUDE.md parameterized with the corpus name and keywords. Content should match
the data-only corpus pattern:

- State that this is a data-only documentation corpus (not a plugin)
- Show how to register it (`/hiivmind-corpus register github:hiivmind/hiivmind-corpus-{name}`)
- Show how to navigate it
- Document the directory structure
- List key files and their purposes
- List maintenance skills (build, refresh, enhance, add-source)
- List the routing keywords from `computed.keywords`

Use `hiivmind-corpus-flyio/CLAUDE.md` as the reference template, substituting the project
name and keywords.

### 4d: README.md

```markdown
# hiivmind-corpus-{name}

Documentation corpus for {Display Name}.

## Usage

Register this corpus with your project:

```
/hiivmind-corpus register github:hiivmind/hiivmind-corpus-{name}
```

Then ask questions about {Display Name} — the navigate skill will find relevant documentation.

## Maintenance

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-build` | Build the documentation index |
| `hiivmind-corpus-refresh` | Update from upstream changes |
| `hiivmind-corpus-enhance` | Deepen coverage on topics |
| `hiivmind-corpus-add-source` | Add documentation sources |
```

### 4e: .gitignore

```
# Cloned documentation repositories
.source/

# Cached web content
.cache/

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*.swo
*~
```

### 4f: LICENSE

MIT License with `Copyright (c) {current_year} hiivmind`. Use the standard MIT text.

### 4g: Verify Scaffold

After writing all files, verify these exist:
- `{root}/config.yaml`
- `{root}/index.md`
- `{root}/CLAUDE.md`
- `{root}/README.md`
- `{root}/.gitignore`
- `{root}/LICENSE`
- `{root}/uploads/` (directory)

If any file is missing, report it and check file system permissions.

---

## Phase 5: Delegate to add-source

**Inputs:** `computed.source_url`, `computed.corpus_root`
**Outputs:** `computed.delegated_to_add_source`

Display a summary of what was created:

```
Corpus '{name}' initialized at {corpus_root}

Files created:
  config.yaml, index.md, CLAUDE.md, README.md, .gitignore, LICENSE, uploads/

Delegating to add-source for source acquisition...
```

Immediately invoke `hiivmind-corpus-add-source` with:
- `source_url`: `computed.source_url`
- `working_directory`: `computed.corpus_root`

Set `computed.delegated_to_add_source = true`. Init is complete.

---

## Related Skills

- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
