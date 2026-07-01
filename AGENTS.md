# hiivmind-corpus

Meta-plugin for creating documentation corpus skills: index, register, navigate, refresh, enhance, and bridge documentation corpora.

When starting work in this repository, also read `CLAUDE.md` in the repo root and treat it as repository guidance unless it conflicts with higher-priority instructions.

## Project Context

This is a portable skill plugin. The canonical source skills live in `skills/*/SKILL.md`; platform manifests and context files adapt that same skill surface for Claude Code, Codex, Cursor, Gemini CLI, Antigravity, and OpenClaw.

## Skills

Read the relevant `SKILL.md` before acting:

- `skills/hiivmind-corpus-init/SKILL.md` - scaffold a new data-only corpus repository.
- `skills/hiivmind-corpus-add-source/SKILL.md` - add git, local, web, llms.txt, generated-docs, PDF, or Obsidian sources.
- `skills/hiivmind-corpus-build/SKILL.md` - scan sources and build `index.yaml`, `index.md`, optional graph, and embeddings.
- `skills/hiivmind-corpus-refresh/SKILL.md` - compare upstream sources and refresh stale entries.
- `skills/hiivmind-corpus-enhance/SKILL.md` - deepen coverage for specific topics in an existing corpus.
- `skills/hiivmind-corpus-discover/SKILL.md` - find registered or installed corpora.
- `skills/hiivmind-corpus-navigate/SKILL.md` - query registered corpora and fetch source documentation.
- `skills/hiivmind-corpus-register/SKILL.md` - add a corpus to `.hiivmind/corpus/registry.yaml`.
- `skills/hiivmind-corpus-status/SKILL.md` - inspect corpus health, freshness, and cache state.
- `skills/hiivmind-corpus-graph/SKILL.md` - view, validate, and edit `graph.yaml`.
- `skills/hiivmind-corpus-bridge/SKILL.md` - create cross-corpus bridges in `registry-graph.yaml`.

## Commands

- `commands/hiivmind-corpus.md` - gateway command that routes natural-language requests to the appropriate skill.

## Agents

- `agents/source-scanner.md` - internal scanner used by build and refresh workflows for parallel source analysis.

## Tool Name Mapping

Skills use Claude Code tool names. Platform equivalents are documented in `lib/references/platforms/`:

- `Read` maps to file-read tools such as Codex file reads, Gemini `read_file`, and Antigravity `view_file`.
- `Write` maps to file-write tools such as Gemini `write_file` and Antigravity `write_to_file`.
- `Edit` maps to edit/patch tools such as Codex `apply_patch`, Gemini `replace`, and Antigravity `replace_file_content`.
- `Bash` maps to shell execution tools such as Gemini `run_shell_command` and Antigravity `run_command`.
- `Grep` maps to content search tools such as Gemini/Antigravity `grep_search`.
- `Glob` maps to file search tools such as Gemini `glob` and Antigravity `find_by_name`.
- `Task`/agent dispatch maps to platform subagent mechanisms where supported; see `lib/references/platforms/codex.md`, `gemini-cli.md`, `openclaw.md`, and `antigravity.md`.

## Portability Notes

Some source skills include Claude Code frontmatter such as `allowed-tools` or `inputs`/`outputs`. Platforms that do not consume those fields should ignore unknown frontmatter keys and use `name` plus `description` for activation.
