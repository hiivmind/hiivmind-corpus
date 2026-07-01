# Antigravity Platform Notes

Antigravity uses `AGENTS.md` plus skill discovery from `.agents/skills/` or plugin-provided skill directories.

## Tool Mapping

| Claude Code term | Antigravity equivalent |
| --- | --- |
| `Read` | `view_file` |
| `Write` | `write_to_file` |
| `Edit` | `replace_file_content` |
| `Bash` | `run_command` |
| `Grep` | `grep_search` |
| `Glob` | `find_by_name` |
| `Task` | no general equivalent; browser-only subagent support exists |
| `TodoWrite` | no direct equivalent |
| `AskUserQuestion` | ask the user directly |
| `WebFetch` | `read_url_content` |

## Installation

Antigravity can use the repository as a skill-bearing plugin or copy individual skill directories into `.agents/skills/`. The `package.json` at the repository root carries extension metadata for OpenVSX-style distribution.

## Runtime

Antigravity should ignore unsupported Claude-specific frontmatter fields such as `allowed-tools`.
