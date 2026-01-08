---
name: critical-discussion
description: |
  Dual-model discussion: Claude and Codex both analyze, then synthesize to a shared conclusion.
  Use when: evaluating trade-offs, architecture decisions, risk analysis, strategic choices.
  Avoid when: you need code changes (use coding-delegation), simple factual questions.
  Triggers: "discuss", "analyze", "evaluate", "trade-offs", "architecture", "ADR", "second opinion".
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Critical Discussion (Dual-Model)

## Purpose

Both Claude and Codex analyze the topic independently, then synthesize into a shared conclusion with higher confidence.

## Why Dual-Model?

- **Different perspectives**: Each model may weight factors differently
- **Confidence**: Agreement = high confidence; differences = important nuances to resolve
- **Blind spot reduction**: Two analyses catch more edge cases

## Use When

- Architecture or API design decisions
- Trade-off evaluation (options, risks, mitigations)
- Technology choices (library A vs B)
- Strategic decisions needing validation
- Getting a "second opinion" on technical decisions

## Avoid When

- User wants code changes now (use `coding-delegation`)
- Simple factual questions (just ask one model)
- Current events research (use `research`)

## Required Inputs (ask if missing)

- **Goal**: What outcome are we optimizing for?
- **Constraints**: Performance, cost, security, compatibility
- **Options**: Known alternatives (if any)
- **Stakes**: Why this decision matters

## Workflow

1. **Dispatch Codex** with analysis prompt (don't wait)
2. **Claude analyzes** the same topic in parallel
3. **Synthesize** when both complete: agreements, differences, shared conclusion

## Tool Settings for Codex

> **IMPORTANT**: Only GPT 5.2 models are available. Do NOT use `o3`, `o4-mini`, or other model names.

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2` | Reasoning model (NOT `gpt-5.2-codex` for discussions) |
| `reasoningEffort` | `xhigh` | **Always use xhigh** |
| `sandbox` | `read-only` | Discussions don't modify files |
| `name` | required | Use `arch/<topic> #tag1 #tag2` |

### Complete Tool Call Example

```json
{
  "prompt": "TOPIC: Architecture decision for...\n\nCONTEXT:\n- ...\n\nANALYSIS REQUIRED:\n...",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/topic-name #tags"
}
```

## Codex Prompt Skeleton

```
TOPIC: <what we're deciding>

CONTEXT:
- <current system / constraints>
- <stakeholders>
- <non-goals>

ANALYSIS REQUIRED:
Provide your independent analysis:
1. Key considerations and factors
2. Trade-offs between approaches
3. Risks and mitigations
4. Your recommendation with rationale

Be thorough, cite your reasoning, and flag assumptions.
```

## Output Contract

Present synthesized discussion:
1. **Codex Position**: Summary of Codex's analysis
2. **Claude Position**: Summary of Claude's analysis
3. **Agreements**: Where both align (high confidence)
4. **Points of Difference**: Where they differ + resolution
5. **Shared Conclusion**: The synthesized recommendation
6. **Key Trade-offs**: Main considerations
7. **Risks & Mitigations**
8. **Next Steps**: Action items
9. **Session info**: Name + conversationId

## Stop Conditions (ask the user)

- Models fundamentally disagree with no clear resolution
- Missing constraints that materially change the recommendation
- Security/identity decisions without threat model assumptions
- Decisions requiring product/legal/compliance input
