# Codex Platform Notes

Codex loads repository guidance from `AGENTS.md` and plugin skills from the enabled plugin package.

## Tool Mapping

| Claude Code term | Codex equivalent |
| --- | --- |
| `Read` | file read through local context/tools |
| `Write` | file creation through patch/write tools |
| `Edit` | `apply_patch` |
| `Bash` | sandboxed shell command |
| `Grep` | `rg` or content search |
| `Glob` | `rg --files` or file listing |
| `Task` | `spawn_agent` when multi-agent tools are available |
| `TodoWrite` | `update_plan` |
| `AskUserQuestion` | `request_user_input` when available, otherwise ask directly |
| `WebFetch` | web/MCP fetch capability when available |

## Installation

The Codex marketplace manifest is `.agents/plugins/marketplace.json`. For this single-plugin repository, the plugin source path must be `"./"` so the installed package includes `skills/`, `commands/`, `agents/`, and `lib/`.

## Runtime

The source skills use Claude Code frontmatter fields such as `allowed-tools`, `inputs`, and `outputs`. Codex should use `name` and `description` for discovery and treat unsupported frontmatter keys as advisory metadata.
