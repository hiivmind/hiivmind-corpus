# Pattern: Config YAML Formatting

## Purpose

Canonical schemas for **writing** config.yaml content. Used by `hiivmind-corpus-init` (full schema)
and `hiivmind-corpus-add-source` (per-source entries).

For **reading** config.yaml, see `config-parsing.md`.

## When to Use

- Creating a new corpus (init writes the full config.yaml)
- Adding a source (add-source appends an entry to the `sources` array)
- Any skill that needs to write or update config.yaml structure

---

## Full Config Schema

The complete config.yaml structure for a new corpus. Init writes this with `sources: []`;
add-source populates the sources array later.

```yaml
schema_version: 2

corpus:
  name: "{name}"
  display_name: "{Display Name}"
  keywords:
    - "{keyword1}"
    - "{keyword2}"
  created_at: null

sources: []

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

| Field | Source | Notes |
|-------|--------|-------|
| `schema_version` | Always `2` | Current schema version |
| `corpus.name` | `computed.corpus_name` | Lowercase, alphanumeric + hyphens |
| `corpus.display_name` | `computed.display_name` | Title-cased name |
| `corpus.keywords` | `computed.keywords` | Routing keywords for discovery |
| `corpus.created_at` | Set to `null` | Updated by build skill |
| `sources` | Empty array `[]` | Populated by add-source |
| `index.format` | Always `"markdown"` | Only format currently supported |
| `settings.include_patterns` | Default glob patterns | Markdown files |
| `settings.exclude_patterns` | Default exclusions | Internal/snippet files |

---

## Source Entry Schemas

Each source type has a specific schema. Add-source appends one of these to the `sources` array.
Tracking fields (`last_commit_sha`, `last_indexed_at`, etc.) are set to `null` on initial creation
and updated by build/refresh skills.

### Git Source Entry

```yaml
- id: "{source_id}"
  type: "git"
  repo_url: "{url}"
  repo_owner: "{owner}"
  repo_name: "{repo_name}"
  branch: "{branch}"
  docs_root: "{docs_root}"
  last_commit_sha: "{sha}"
  last_indexed_at: null
```

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Derived from repo name | Lowercase, alphanumeric + hyphens |
| `repo_url` | User input or `computed.source_url` | Full HTTPS URL |
| `repo_owner` | Parsed from URL | GitHub owner/org |
| `repo_name` | Parsed from URL | Repository name |
| `branch` | User input, default `"main"` | |
| `docs_root` | User input, default `"docs/"` | Relative path within repo |
| `last_commit_sha` | From `git rev-parse HEAD` after clone | Set during add-source |
| `last_indexed_at` | `null` | Set by build/refresh |

### Local Source Entry

```yaml
- id: "{source_id}"
  type: "local"
  path: "uploads/{source_id}/"
  description: "{description}"
  files: []
  last_indexed_at: null
```

| Field | Source | Notes |
|-------|--------|-------|
| `id` | User input | Descriptive name |
| `path` | `"uploads/{source_id}/"` | Always under uploads/ |
| `description` | User input | Brief description |
| `files` | Empty array `[]` | Populated by build when scanning |
| `last_indexed_at` | `null` | Set by build/refresh |

### Web Source Entry

```yaml
- id: "{source_id}"
  type: "web"
  description: "{description}"
  cache_dir: ".cache/web/{source_id}/"
  urls:
    - url: "{url}"
      title: "Fetched article"
      cached_file: "{filename}"
      fetched_at: "{timestamp}"
  last_indexed_at: null
```

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Derived from URL or user input | |
| `description` | User input | Brief description |
| `cache_dir` | `".cache/web/{source_id}/"` | Always under .cache/web/ |
| `urls` | First URL from user input | Array, more can be added later |
| `urls[].fetched_at` | ISO timestamp at fetch time | |
| `last_indexed_at` | `null` | Set by build/refresh |

### llms-txt Source Entry

```yaml
- id: "{source_id}"
  type: "llms-txt"
  manifest:
    url: "{manifest_url}"
    last_hash: "{sha256_hash}"
    last_fetched_at: "{timestamp}"
  urls:
    base_url: "{base_url}"
    suffix: ".md"
  cache:
    enabled: true
    dir: ".cache/llms-txt/{source_id}/"
    strategy: "{strategy}"
  last_indexed_at: null
```

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Derived from manifest title | |
| `manifest.url` | Auto-detected or user input | URL to llms.txt file |
| `manifest.last_hash` | SHA-256 of manifest content | For change detection |
| `manifest.last_fetched_at` | ISO timestamp | |
| `urls.base_url` | Derived from manifest URL | Base for page URLs |
| `urls.suffix` | `".md"` | Default suffix for page URLs |
| `cache.strategy` | User choice | `"selective"`, `"full"`, or `"on-demand"` |
| `last_indexed_at` | `null` | Set by build/refresh |

### Generated-Docs Source Entry

```yaml
- id: "{source_id}"
  type: "generated-docs"
  source_repo:
    url: "{source_repo_url}"
    branch: "main"
    docs_root: "docs"
    last_commit_sha: "{sha}"
  web_output:
    base_url: "{web_base_url}"
    discovered_urls: []
  cache:
    enabled: false
    dir: ".cache/web/{source_id}/"
  last_indexed_at: null
```

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Derived from repo name | |
| `source_repo.url` | User input | Source repository URL |
| `source_repo.branch` | Default `"main"` | |
| `source_repo.docs_root` | Default `"docs"` | |
| `source_repo.last_commit_sha` | From `git rev-parse HEAD` | Set during add-source |
| `web_output.base_url` | User input | Published docs URL |
| `web_output.discovered_urls` | Empty `[]` | Populated by discovery |
| `cache.enabled` | Default `false` | Live fetch by default |
| `last_indexed_at` | `null` | Set by build/refresh |

---

## Related Patterns

- **Reading config:** `config-parsing.md` (extraction patterns with yq/python/grep)
- **Source operations:** `sources/git.md`, `sources/local.md`, `sources/web.md`, `sources/llms-txt.md`, `sources/generated-docs.md`
- **Template file:** `${CLAUDE_PLUGIN_ROOT}/templates/config.yaml.template` (mustache-syntax template for tooling)
