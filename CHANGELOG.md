# Changelog

All notable changes to hiivmind-corpus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-11

### Removed

- **All workflow.yaml files** — Skills are now self-contained phased prose SKILL.md files (~6,000 lines of workflow YAML deleted)
- **Blueprint-lib dependency** — No longer requires `hiivmind/hiivmind-blueprint-lib@v2.0.0` execution engine
- **Gateway intent-mapping.yaml** — 3VL intent detection replaced with simple keyword routing table
- **`hiivmind-corpus-upgrade` skill** — Obsolete with data-only corpus format (no legacy formats to migrate)
- **`hiivmind-corpus-awareness` skill** — Removed along with capability-awareness pattern
- **`hiivmind-corpus-init` references/** — Legacy implementation-examples, marketplace-templates, template-placeholders
- **`hiivmind-corpus-build` diagrams/** — Workflow diagram for deleted workflow
- **Four destination types** — Corpora are now always data-only repositories

### Changed

- **`hiivmind-corpus-init`** — Simplified to scaffold flat data-only corpus repos (config.yaml, index.md, README, CLAUDE.md, .gitignore, LICENSE)
- **`hiivmind-corpus-add-source`** — Rewritten as 4-phase prose skill supporting 6 source types (git, local, web, llms-txt, generated-docs, PDF)
- **`hiivmind-corpus-build`** — Rewritten as 6-phase prose skill with parallel agent scanning for multi-source corpora
- **`hiivmind-corpus-refresh`** — Rewritten as 6-phase prose skill with status/update modes and per-source-type freshness checks
- **Gateway command** (`/hiivmind-corpus`) — Simplified to keyword routing table with interactive menu fallback
- **CLAUDE.md** — Updated architecture docs to reflect data-only corpus format and removed all blueprint-lib/upgrade references

### Unchanged

- All `lib/corpus/patterns/` files (contain the actual source-type operations)
- `agents/source-scanner.md` (parallel scanning protocol)
- Pattern delegation model (skills reference pattern docs for operations)

## [1.0.0] - 2025-12-13

### Added

- **Gateway command** (`/hiivmind-corpus`) — Natural language entry point for all corpus operations
- **Eight core skills:**
  - `discover` — Find all installed corpora across user-level, repo-local, and marketplace locations
  - `navigate` — Query across all corpora, routing to per-corpus navigate skills
  - `init` — Create corpus structure from GitHub repos
  - `add-source` — Add git repos, local documents, or web pages to existing corpora
  - `build` — Collaboratively create indexes with user guidance
  - `enhance` — Deepen coverage on specific topics
  - `refresh` — Sync with upstream changes
  - `upgrade` — Update existing corpora to latest template standards
- **Four corpus destination types:** user-level, repo-local, single-corpus plugin, multi-corpus marketplace
- **Three source types:** git repositories, local documents, web pages
- **Tiered indexes** for large documentation sets (500+ files)
- **Large file markers** (`⚡ GREP`) for files too large to read directly
- **Project awareness snippets** for CLAUDE.md injection
- **Shell function library** (`lib/corpus/`) for composable discovery and status operations
- **Templates** for generating new corpus skills
- **User documentation:** README with quick start, skills guide with workflows and troubleshooting
