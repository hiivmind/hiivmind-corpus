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

## Embedded Mode Detection

Before collecting project info, check if the user wants an embedded corpus:

**Detection heuristic:** If the current working directory is a git repo with documentation-like content, offer embedded mode:

1. Check: is this a git repo? (`git rev-parse --show-toplevel`)
2. Check for doc indicators: `.obsidian/` directory, `docs/` folder, or 10+ `.md` files at root
3. If indicators found, ask:

> "This looks like a documentation repository. Would you like to:
> (A) Create an embedded corpus at `.hiivmind/corpus/` that indexes this repo's own content
> (B) Create a standalone corpus in a new repository"

If user chooses (A), skip to Phase 4-embedded below.
If user chooses (B), continue with standard flow.

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

**See:** `${CLAUDE_PLUGIN_ROOT}/lib/corpus/patterns/config-yaml-formatting.md` § "Full Config Schema"

Write config.yaml using the full schema from the pattern doc. Substitute:

| Placeholder | Value |
|-------------|-------|
| `{name}` | `computed.corpus_name` |
| `{Display Name}` | `computed.display_name` |
| `{keyword1}`, `{keyword2}`, ... | `computed.keywords` |

Leave `sources: []` empty — add-source populates this.

### 4b: index.md

**Template:** `${CLAUDE_PLUGIN_ROOT}/templates/index.md.template`

Substitute `{{project_display_name}}` with `computed.display_name`.

### 4c: CLAUDE.md

**Template:** `${CLAUDE_PLUGIN_ROOT}/templates/claude-data-only.md.template`

Substitute placeholders:

| Placeholder | Value |
|-------------|-------|
| `{{project_display_name}}` | `computed.display_name` |
| `{{project_name}}` | `computed.corpus_name` |
| `{{author_name}}` | `"hiivmind"` (default) |
| `{{example_questions}}` | Generate 2-3 example questions based on the corpus topic |
| `{{keywords_list}}` | Bullet list from `computed.keywords` |

### 4d: README.md

**Template:** `${CLAUDE_PLUGIN_ROOT}/templates/readme-data-only.md.template`

Substitute placeholders:

| Placeholder | Value |
|-------------|-------|
| `{{project_display_name}}` | `computed.display_name` |
| `{{project_name}}` | `computed.corpus_name` |
| `{{author_name}}` | `"hiivmind"` (default) |
| `{{example_questions}}` | Same as CLAUDE.md |
| `{{keywords}}` | Mustache loop from `computed.keywords` |

### 4e: .gitignore

**Template:** `${CLAUDE_PLUGIN_ROOT}/templates/gitignore.template`

No placeholders — copy verbatim.

### 4f: LICENSE

**Template:** `${CLAUDE_PLUGIN_ROOT}/templates/license.template`

Substitute placeholders:

| Placeholder | Value |
|-------------|-------|
| `{{year}}` | Current year |
| `{{author_name}}` | `"hiivmind"` |

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

## Phase 4-embedded: Scaffold Embedded Corpus

**Inputs:** `computed.corpus_name`, `computed.display_name`, `computed.keywords`
**Outputs:** `computed.corpus_root`, files on disk

Create the embedded corpus at `.hiivmind/corpus/`:

```bash
mkdir -p .hiivmind/corpus
```

### 4e-1: Detect docs_root

Suggest `docs_root` based on repo structure:
- If `docs/` directory exists → suggest `"docs"`
- If `.obsidian/` exists (Obsidian vault) → suggest `"."`
- Otherwise → suggest `"."`

Confirm with user: "What directory contains the documentation? (default: {suggestion})"

### 4e-2: config.yaml

Write `.hiivmind/corpus/config.yaml` using the full schema from `config-yaml-formatting.md`, with these differences:
- `sources` is pre-populated with a `type: self` entry (NOT empty)
- `settings.exclude_patterns` includes `.hiivmind/**`

```yaml
schema_version: 2

corpus:
  name: "{name}"
  display_name: "{Display Name}"
  keywords:
    - "{keyword1}"
    - "{keyword2}"
  created_at: null

sources:
  - id: "{source_id}"
    type: "self"
    docs_root: "{docs_root}"
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
    - ".hiivmind/**"
```

### 4e-3: index.md

Write `.hiivmind/corpus/index.md` using the same placeholder template as standard init.

### 4e-4: .gitignore

Minimal or empty — embedded corpora commit everything (no `.source/`, `.cache/`, `uploads/`).

### 4e-5: Verify

Verify these exist:
- `.hiivmind/corpus/config.yaml`
- `.hiivmind/corpus/index.md`

### 4e-6: Skip add-source delegation

Embedded corpora do NOT delegate to add-source. The `type: self` source is already configured. Display:

```
Embedded corpus '{name}' initialized at .hiivmind/corpus/

Files created:
  .hiivmind/corpus/config.yaml
  .hiivmind/corpus/index.md

Source: this repository (docs_root: {docs_root})

Next: Run hiivmind-corpus-build to create the index.
```

Done — do NOT invoke add-source.

---

## Related Skills

- Add sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-add-source/SKILL.md`
- Build index: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-build/SKILL.md`
- Refresh sources: `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-refresh/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-graph/SKILL.md` — View, validate, edit concept graphs
- `${CLAUDE_PLUGIN_ROOT}/skills/hiivmind-corpus-bridge/SKILL.md` — Cross-corpus concept bridges and aliases
