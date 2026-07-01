# OpenClaw Platform Notes

OpenClaw reads `openclaw.plugin.json` for native plugin metadata and can consume the standard `skills/` directory.

## Tool Mapping

| Claude Code term | OpenClaw equivalent |
| --- | --- |
| `Read` | `Read` |
| `Write` | `Write` |
| `Edit` | `Edit` |
| `Bash` | `Bash` |
| `Grep` | `Grep` |
| `Glob` | `Glob` |
| `Task` | configure agents through `agents.list[]` or plugin runtime config |
| `TodoWrite` | no direct equivalent |
| `AskUserQuestion` | `AskUserQuestion` where available |
| `WebFetch` | `WebFetch` |

## Hooks

This plugin does not currently ship OpenClaw SDK hook handlers. If hooks are added, register them in TypeScript with OpenClaw event names such as `gateway:startup`, `before_tool_call`, `after_tool_call`, `before_compaction`, `after_compaction`, and `command`.

## Runtime

OpenClaw uses provider/model format for model-specific agent metadata. This repository's only agent is `agents/source-scanner.md`; if porting it to OpenClaw-specific agent config, translate its `model: haiku` hint to the platform's configured lightweight model.
