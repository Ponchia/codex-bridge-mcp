---
description: Discuss a topic with both Claude and Codex to reach a shared conclusion
argument-hint: <topic to discuss>
---

# Critical Discussion (Dual-Model)

Discuss this topic with both Claude and Codex **in true parallel**, then synthesize into a shared conclusion.

## Topic

$ARGUMENTS

## Workflow (True Parallel Execution)

### Step 1: Dispatch Codex in Background

Use the Task tool to run Codex without blocking:

```json
// Task tool
{
  "description": "Codex analyzes topic",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters:\n- prompt: 'TOPIC: $ARGUMENTS\n\nCONTEXT:\n- [Relevant background]\n- [Constraints and requirements]\n\nANALYSIS REQUIRED:\n1. Key considerations and factors\n2. Trade-offs between approaches\n3. Risks and mitigations\n4. Your recommendation with rationale\n\nBe thorough, cite your reasoning, and flag assumptions.'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- name: 'arch/<topic> #tags'\n\nReturn the full tool response."
}
```

**Save the `task_id`** from the response. Codex is now running in background.

### Step 2: Claude Analyzes Immediately (No Waiting)

While Codex works in background, Claude analyzes the same topic:

1. Consider the key trade-offs and constraints
2. Evaluate different approaches
3. Identify risks and edge cases
4. Form your own recommendation

Document your analysis with reasoning thoroughly.

### Step 3: Retrieve Codex Result

When Claude's analysis is complete, get Codex's result:

```json
// TaskOutput tool
{ "task_id": "<saved task_id>", "block": true, "timeout": 300000 }
```

### Step 4: Synthesize to Shared Conclusion

Compare both analyses and synthesize:
- Identify where both agree (high confidence)
- Identify where they differ (needs resolution)
- Resolve differences through reasoning
- Produce a shared recommendation

## Output Contract

Present the synthesized discussion in this format:

```markdown
## Discussion: <topic>

### Codex Position
<Summary of Codex's analysis and recommendation>

### Claude Position
<Summary of Claude's analysis and recommendation>

### Agreements (High Confidence)
- <Point where both align>
- <Another shared conclusion>

### Points of Difference
- <Where they differ>: Codex says X, Claude says Y
- <Resolution>: After considering both, <conclusion>

### Shared Conclusion
<The synthesized recommendation both perspectives support>

### Key Trade-offs
- <Trade-off 1>
- <Trade-off 2>

### Risks & Mitigations
- <Risk 1>: <Mitigation>

### Next Steps
1. <Action item>
2. <Verification step>

### Session Info
Codex session: `arch/<topic>` (conversationId: ...)
```

## When to Use

- Architecture decisions (microservices vs monolith, etc.)
- Technology choices (library A vs B)
- Trade-off analysis (security vs usability)
- Strategic decisions needing multiple perspectives

## When NOT to Use

- Simple factual questions (just ask one model)
- Code implementation (use `/delegate`)
- Current events research (use `/research`)

## Tool Name Note

If you installed as a manual MCP server (not plugin), use `mcp__codex__codex` instead of `mcp__plugin_codex-bridge_codex__codex`.
