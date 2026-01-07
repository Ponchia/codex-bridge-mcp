---
name: critical-discussion
description: |
  Critically discuss topics with GPT 5.2 for solution-oriented analysis. Use when:
  evaluating architecture decisions, analyzing trade-offs, planning complex features,
  discussing design patterns, debating implementation approaches, or needing a second
  opinion on technical decisions. Triggers: "discuss", "analyze", "evaluate", "debate",
  "think through", "architecture", "trade-offs", "critical analysis", "second opinion".
  Uses GPT 5.2 (NOT Codex) with maximum reasoning effort for thoughtful discourse.
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Critical Discussion with GPT 5.2

Use GPT 5.2 (base model, NOT Codex) with maximum reasoning effort to critically analyze and discuss topics. This skill is for **thinking, analysis, and planning** - not code generation.

## When to Use This Skill

**Good candidates:**
- Architecture decisions and trade-off analysis
- Design pattern evaluation and selection
- Technical planning and roadmap discussions
- Evaluating multiple implementation approaches
- Getting a critical "second opinion" on decisions
- Analyzing risks and mitigation strategies
- Discussing best practices and conventions
- Complex problem decomposition

**Use coding-delegation skill instead for:**
- Actual code implementation
- Writing tests
- Refactoring code
- Bug fixes

---

## How to Start a Discussion

Use the `mcp__plugin_codex-bridge_codex__codex` tool with these **required settings**:

```json
{
  "prompt": "<your discussion topic with context>",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "<descriptive-session-name>"
}
```

**Critical Configuration:**
| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2` | Base model for reasoning (NOT gpt-5.2-codex) |
| `reasoningEffort` | `xhigh` | Maximum analysis depth |
| `sandbox` | `read-only` | Discussions don't modify files |
| `name` | descriptive | For later reference and search |

---

## Prompt Structure for Discussions

Structure your discussion prompts for best results:

```
TOPIC: [Clear statement of what you want to discuss]

CONTEXT:
- [Relevant background information]
- [Current state/constraints]
- [Stakeholders affected]

SPECIFIC QUESTIONS:
1. [First aspect to analyze]
2. [Second aspect to evaluate]
3. [Trade-offs to consider]

DESIRED OUTPUT:
- [What kind of analysis you want]
- [Format preferences: pros/cons, recommendations, etc.]
```

---

## Continuing a Discussion

Use `mcp__plugin_codex-bridge_codex__codex-reply` to continue with the same `conversationId`:

```json
{
  "conversationId": "<from previous response>",
  "prompt": "Let's explore the second option further. What are the long-term maintenance implications?"
}
```

The discussion maintains full context from previous exchanges.

---

## Output Format

Discussion results should be presented in markdown:
- Clear headers for organization
- Pros/cons tables where appropriate
- Numbered recommendations
- Summary of key insights
- Areas requiring further investigation

---

## Named Sessions

Always name discussion sessions for later reference:

```json
{
  "name": "auth-architecture-discussion"
}
```

Find past discussions with `mcp__plugin_codex-bridge_codex__codex-bridge-sessions`:

```json
{
  "query": "architecture"
}
```

---

## Example: Architecture Decision

```json
{
  "prompt": "TOPIC: Should we use microservices or monolith for our new platform?\n\nCONTEXT:\n- Team of 5 developers\n- Expected 10k DAU initially, scaling to 100k\n- Need to integrate with 3 payment providers\n- Budget constraints\n\nQUESTIONS:\n1. Operational complexity trade-offs?\n2. Time-to-market impact?\n3. Scaling implications?\n\nOUTPUT: Pros/cons comparison with recommendation",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "platform-architecture-decision"
}
```

See [EXAMPLES.md](EXAMPLES.md) for more detailed usage examples.
