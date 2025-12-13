# Changelog

All notable changes to hiivmind-corpus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
