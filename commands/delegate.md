---
description: Delegate a coding task to GPT 5.2 Codex for autonomous implementation
argument-hint: <coding task description>
---

# Delegate to Codex

Delegate this coding task to GPT 5.2 Codex for autonomous implementation.

## Task

$ARGUMENTS

## Instructions

Use the `mcp__plugin_codex-bridge_codex__codex` tool with these **required settings**:

1. **Model**: `gpt-5.2-codex` (optimized for code generation)
2. **Reasoning Effort**: `xhigh` (for complex implementations)
3. **Sandbox**: `workspace-write` (to modify files) or `read-only` (for review)
4. **Approval Policy**: `on-failure` (safe default with autonomy)
5. **Name**: A descriptive session name for later reference

## Prompt Structure

Structure the task prompt with:
- **TASK**: Clear statement of what to implement
- **CONTEXT**: Relevant files, patterns to follow
- **REQUIREMENTS**: Specific functionality needed
- **ACCEPTANCE CRITERIA**: How to verify success
- **CONSTRAINTS**: What NOT to modify

## Example Tool Call

```json
{
  "prompt": "TASK: $ARGUMENTS\n\nCONTEXT:\n- [Relevant files and locations]\n- [Existing patterns to follow]\n\nREQUIREMENTS:\n- [Specific functionality]\n- [Edge cases to handle]\n\nACCEPTANCE CRITERIA:\n- [How to verify it works]\n- [Tests that should pass]\n\nCONSTRAINTS:\n- [What not to modify]\n- [Style guidelines]",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "coding-task-session"
}
```

## After Delegation

1. Save the `conversationId` for follow-up instructions
2. **Review the output** before committing
3. Run `git diff` to see changes
4. Run tests to verify functionality
5. Use `mcp__plugin_codex-bridge_codex__codex-reply` to request adjustments
