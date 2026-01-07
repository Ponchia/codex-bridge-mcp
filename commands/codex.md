---
description: Start a Codex session to delegate a coding task to OpenAI Codex
argument-hint: [task description]
---

# Start Codex Session

Delegate this coding task to OpenAI Codex using the `mcp__codex__codex` tool.

## Task

$ARGUMENTS

## Instructions

1. Use the `mcp__codex__codex` tool with the task above as the prompt
2. Set appropriate options:
   - `sandbox`: Use `workspace-write` for implementation tasks, `read-only` for exploration
   - `approval-policy`: Use `on-failure` for most tasks
3. Save the `conversationId` from the response for potential follow-ups
4. Review and summarize what Codex accomplished

## Example Tool Call

```json
{
  "prompt": "<the task description>",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure"
}
```
