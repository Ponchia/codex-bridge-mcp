---
description: Discuss a topic with both Claude and Codex to reach a shared conclusion
argument-hint: <topic to discuss>
---

# Critical Discussion (Dual-Model)

Discuss this topic with both Claude and Codex, then synthesize into a shared conclusion.

## Topic

$ARGUMENTS

## Workflow

### Step 1: Dispatch Codex Analysis (Background)

Start Codex analyzing the topic:

```json
// mcp__plugin_codex-bridge_codex__codex
{
  "prompt": "TOPIC: $ARGUMENTS\n\nCONTEXT:\n- [Relevant background]\n- [Constraints and requirements]\n\nANALYSIS REQUIRED:\nProvide your independent analysis:\n1. Key considerations and factors\n2. Trade-offs between approaches\n3. Risks and mitigations\n4. Your recommendation with rationale\n\nBe thorough, cite your reasoning, and flag assumptions.",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/<topic> #tags"
}
```

**Important**: After calling this tool, immediately proceed to Step 2 while Codex works.

### Step 2: Claude Analyzes (Parallel)

While Codex works, Claude analyzes the same topic:

1. Consider the key trade-offs and constraints
2. Evaluate different approaches
3. Identify risks and edge cases
4. Form your own recommendation

Document your analysis with reasoning.

### Step 3: Synthesize to Shared Conclusion

Once both complete, compare analyses and synthesize:
- Identify where both agree (high confidence)
- Identify where they differ (needs discussion)
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
