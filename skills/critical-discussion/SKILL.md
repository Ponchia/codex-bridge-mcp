---
name: critical-discussion
description: |
  Critically discuss architecture/technical decisions with GPT 5.2 (base model, not Codex).
  Use when: evaluating trade-offs, architecture decisions, risk analysis, planning, second opinions.
  Avoid when: you need code changes (use coding-delegation).
  Triggers: "discuss", "analyze", "evaluate", "trade-offs", "architecture", "ADR", "second opinion".
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Critical Discussion (GPT 5.2)

## Purpose

- Produce decision-quality analysis: recommendation + rationale + risks + next steps
- Keep discussions resumable via named sessions

## Use When / Avoid When

**Use when:**
- Architecture or API design decisions
- Trade-off evaluation (options, risks, mitigations)
- Planning + defining scope for implementation
- Reviewing proposals at a conceptual level
- Getting a "second opinion" on technical decisions

**Avoid when:**
- User wants code changes now (use `coding-delegation`)
- Problem needs product/legal decisions (ask first)

## Required Inputs (ask if missing)

- Goal: what outcome are we optimizing for?
- Constraints: performance, cost, security, compatibility, team size
- Options: known alternatives (if any)
- Verification: what evidence would change our mind?

## Tool Settings

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2` | Base model for reasoning (NOT codex) |
| `reasoningEffort` | `xhigh` | Maximum analysis depth |
| `sandbox` | `read-only` | Discussions don't modify files |
| `name` | required | Use `arch/<topic> #tag1 #tag2` |

## Prompt Skeleton

```
TOPIC: <what we're deciding>

CONTEXT:
- <current system / constraints>
- <stakeholders>
- <non-goals>

OPTIONS (if known):
A) ...
B) ...

QUESTIONS:
1) ...
2) ...

DESIRED OUTPUT:
- Recommendation + rationale
- Risks + mitigations
- Open questions
- Next steps
```

## Workflow

1. If continuing an older topic, search by name (`codex-bridge-sessions`) or use `/codex-bridge:context recall`
2. Start discussion session (or continue with `codex-reply`) using settings above
3. If session is unnamed, set a better name (`codex-bridge-name-session`)
4. Return output per contract below; be explicit about assumptions
5. Consider checkpointing (`/codex-bridge:context checkpoint`) for easy recall later

## Output Contract

- **Recommendation** (one paragraph)
- **Options considered** (short bullets)
- **Key trade-offs** (pros/cons)
- **Risks** (with mitigations)
- **Assumptions / unknowns**
- **Next steps** (ordered)
- **Session**: name + `conversationId`

## Stop Conditions (ask the user)

- Missing constraints that materially change the recommendation
- Security/identity decisions without threat model assumptions
- Decisions requiring product/legal/compliance input
