---
name: research
description: |
  Dual-model research: Claude and Codex both research in parallel, then merge findings.
  Use when: you need current/up-to-date information, best practices research, technology comparisons.
  Avoid when: Codex's training data is sufficient, speed matters more than thoroughness.
  Triggers: "research", "look up", "find current", "what's the latest", "best practices for"
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Research Skill (Dual-Model)

## Purpose

Both Claude and Codex research the topic in parallel using web search, then Claude merges findings into a unified output with higher confidence.

## Why Dual-Model?

- **Coverage**: Two models may find different sources
- **Confidence**: Agreement = higher confidence; unique findings = broader coverage
- **Validation**: Cross-check findings between models

## Use When

- Need current/up-to-date information beyond training data
- Researching best practices that evolve over time
- Technology comparisons with recent developments
- Documentation lookups where completeness matters

## Avoid When

- Speed matters more than thoroughness (just use one model)
- Topic is purely code-specific (use coding-delegation)
- Need architectural analysis (use critical-discussion)

## Required Inputs

Ask if not provided:
1. **Topic**: What to research
2. **Context**: Why this research matters
3. **Scope**: Breadth vs depth preference

## Workflow

1. **Dispatch Codex** with web search enabled (don't wait)
2. **Claude researches** the same topic using WebSearch in parallel
3. **Merge findings** when both complete

## Tool Settings for Codex

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2` | Reasoning model, not code-optimized |
| `reasoningEffort` | `xhigh` | Thorough research |
| `sandbox` | `read-only` | Research only |
| `config.web_search_request` | `true` | Enable web search |
| `name` | required | Use `research/<topic> #tags` |

## Codex Prompt Skeleton

```
RESEARCH TOPIC: <topic>

CONTEXT:
- <why this matters>
- <current understanding>

INSTRUCTIONS:
Research this topic thoroughly. For each finding:
1. State the finding clearly
2. Note the source/basis
3. Rate confidence (High/Medium/Low)
4. Flag any caveats

OUTPUT FORMAT:
- Key findings (with sources)
- Confidence level per finding
- Gaps/unknowns
- Suggested follow-ups
```

## Output Contract

Present merged research:
1. **Merged Findings**: Each finding with what both models found + confidence
2. **Agreements**: Where both align (high confidence)
3. **Unique Insights**: Findings from only one model
4. **Gaps**: What neither could determine
5. **Sources**: List of sources consulted
6. **Session info**: Name + conversationId

## Stop Conditions

Ask user before proceeding if:
- Topic is ambiguous (need to narrow scope)
- Models found conflicting authoritative sources
- Research reveals the question should be reframed
