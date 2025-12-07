---
name: generate-docs-plugin
description: Generate a documentation skill plugin for any open source project. Use when setting up documentation access for a new project.
---

# Documentation Plugin Generator

Generate a documentation skill plugin structure for any open source project.

## Process

```
1. DISCOVER  →  2. RESEARCH  →  3. GENERATE
   (clone)       (analyze)      (files)
```

**Note:** After generating, run `docs-init` to build the index collaboratively.

## Phase 1: Discover

Clone the target documentation repository temporarily.

```bash
git clone --depth 1 {repo_url} .temp-source
```

Identify:
- Documentation location (`docs/`, `documentation/`, root)
- File count and types (`.md`, `.mdx`, `.rst`)

## Phase 2: Research

Analyze the existing structure. **Do not assume** - investigate.

### Questions to Answer

| Question | How to Find |
|----------|-------------|
| Doc framework? | Look for `docusaurus.config.js`, `mkdocs.yml`, `conf.py` |
| Existing nav structure? | Check `sidebars.js`, `mkdocs.yml` nav, toctree |
| Frontmatter schema? | Sample 5-10 files, check YAML frontmatter |
| Multiple languages? | Look for `i18n/`, `/en/`, `/zh/` directories |
| External doc sources? | Check build scripts for git clones |

### Research Commands

```bash
# Framework detection
ls .temp-source/

# Find nav structure
find .temp-source -name "sidebars*" -o -name "mkdocs.yml" -o -name "conf.py"

# Sample frontmatter
head -30 .temp-source/docs/some-file.md

# Check for external sources
grep -r "git clone" .temp-source/scripts/ .temp-source/package.json
```

## Phase 3: Generate

Create the plugin structure:

```
{project}-docs/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── navigate/
│       └── SKILL.md      # Per-project (for discoverability)
├── data/
│   ├── config.yaml
│   └── index.md          # Placeholder - built by docs-init
├── .gitignore
└── README.md
```

### Files to Create

**plugin.json**
```json
{
  "name": "{project}-docs",
  "description": "Always-current {Project} documentation",
  "version": "1.0.0"
}
```

**config.yaml**
```yaml
source:
  repo_url: "{repo_url}"
  branch: "{branch}"
  docs_root: "{docs_path}"

index:
  last_commit_sha: null
  last_indexed_at: null
  format: "markdown"

settings:
  include_patterns:
    - "**/*.md"
  exclude_patterns:
    - "**/_*.md"
```

**index.md** (placeholder)
```markdown
# {Project} Documentation Index

> Run `docs-init` to build this index.
```

**navigate/SKILL.md** - Per-project, with specific description for discoverability.

### Cleanup

Remove temporary clone after generating:
```bash
rm -rf .temp-source
```

## Example

**User**: "Create a docs plugin for Prisma"

**Phase 1**: Clone `https://github.com/prisma/docs` to `.temp-source`

**Phase 2**:
- Framework: Docusaurus
- Nav: `sidebars.js`
- 450 MDX files
- Docs root: `docs/`

**Phase 3**: Generate `prisma-docs/` structure

**Next step**: Run `docs-init` from within `prisma-docs/` to build the index.

## Reference

- Initialize index: `skills/docs-init/SKILL.md`
- Update index: `skills/docs-maintain/SKILL.md`
- Example implementation: `clickhouse-docs/`
- Original spec: `docs/doc-skill-plugin-spec.md`
