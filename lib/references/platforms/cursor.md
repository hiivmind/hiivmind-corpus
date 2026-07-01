# Cursor Platform Notes

Cursor can consume the root `skills/`, `agents/`, and `commands/` directories through `.cursor-plugin/plugin.json`.

## Tool Mapping

Cursor generally follows Claude Code tool names:

| Claude Code term | Cursor equivalent |
| --- | --- |
| `Read` | `Read` |
| `Write` | `Write` |
| `Edit` | `Edit` |
| `Bash` | `Bash` |
| `Grep` | `Grep` |
| `Glob` | `Glob` |
| `Task` | `Agent` or `Task` where available |
| `TodoWrite` | `TodoWrite` |
| `AskUserQuestion` | `AskUserQuestion` |
| `WebFetch` | `WebFetch` |

## Hooks

This plugin does not currently ship Cursor hook handlers. If hooks are added, use `hooks/hooks-cursor.json` with Cursor camelCase event names such as `sessionStart`, `preToolUse`, `postToolUse`, and `beforeSubmitPrompt`.
