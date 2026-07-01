# Gemini CLI Platform Notes

Gemini CLI loads this extension through `gemini-extension.json`, then reads `GEMINI.md`.

## Tool Mapping

| Claude Code term | Gemini CLI equivalent |
| --- | --- |
| `Read` | `read_file` |
| `Write` | `write_file` |
| `Edit` | `replace` |
| `Bash` | `run_shell_command` |
| `Grep` | `grep_search` |
| `Glob` | `glob` |
| `Task` | `@agent-name` routing or automatic subagent routing |
| `TodoWrite` | `write_todos` |
| `AskUserQuestion` | `ask_user` |
| `WebFetch` | `web_fetch` |

## Installation

Use `gemini extensions install https://github.com/hiivmind/hiivmind-corpus` or link a local checkout with `gemini extensions link /path/to/hiivmind-corpus`.

## Hooks

This plugin does not currently ship Gemini hook handlers. If hooks are added later, configure them through Gemini settings using Gemini event names such as `SessionStart`, `BeforeTool`, `AfterTool`, `PreCompress`, and `AfterAgent`.
