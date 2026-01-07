---
description: Start a Codex session to delegate a coding task to OpenAI Codex
argument-hint: [task description]
---

# Start Codex Session

Delegate this coding task to OpenAI Codex.

## Task

$ARGUMENTS

## Instructions

Use the `mcp__plugin_codex-bridge_codex__codex` tool (or `mcp__codex__codex` if installed manually):

1. Set the task above as the `prompt`
2. Set appropriate options:
   - `sandbox`: Use `workspace-write` for implementation, `read-only` for exploration
   - `approval-policy`: Use `on-failure` for most tasks
   - `name`: Use naming convention `impl/<topic> #tags` or `explore/<topic>`
3. Save the `conversationId` for potential follow-ups
4. Review and summarize what Codex accomplished

## Example Tool Call

```json
{
  "prompt": "<the task description>",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/<topic> #tags"
}
```
