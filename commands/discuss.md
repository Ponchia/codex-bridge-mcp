---
description: Start a critical discussion with GPT 5.2 (analysis, architecture, trade-offs)
argument-hint: <topic to discuss>
---

# Critical Discussion

Start a critical discussion with GPT 5.2 using maximum reasoning effort.

## Topic

$ARGUMENTS

## Instructions

Use the `mcp__plugin_codex-bridge_codex__codex` tool with these **required settings**:

1. **Model**: `gpt-5.2` (NOT gpt-5.2-codex - we want reasoning, not coding)
2. **Reasoning Effort**: `xhigh` (maximum analysis depth)
3. **Sandbox**: `read-only` (discussions don't modify files)
4. **Name**: A descriptive session name for later reference

## Prompt Structure

Structure the discussion prompt with:
- **TOPIC**: Clear statement of what to discuss
- **CONTEXT**: Relevant background information
- **QUESTIONS**: Specific aspects to analyze
- **DESIRED OUTPUT**: Format preferences (pros/cons, recommendations, etc.)

## Example Tool Call

```json
{
  "prompt": "TOPIC: $ARGUMENTS\n\nCONTEXT:\n- [Add relevant background]\n\nQUESTIONS:\n1. What are the key trade-offs?\n2. What are the risks?\n3. What's your recommendation?\n\nDESIRED OUTPUT:\n- Pros/cons analysis\n- Risk assessment\n- Clear recommendation with justification",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/<topic> #tags"
}
```

## After the Discussion

1. Save the `conversationId` if you want to continue the discussion later
2. Present the analysis in markdown format
3. Use `mcp__plugin_codex-bridge_codex__codex-reply` for follow-up questions
