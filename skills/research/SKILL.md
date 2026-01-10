---
name: research
description: |
  DEPRECATED: Use codex-bridge skill instead (`/codex research <query>`).
  Dual-model research: Claude and Codex both research in parallel, then merge findings.
  Use when: you need current/up-to-date information, best practices research, technology comparisons.
  Avoid when: Codex's training data is sufficient, speed matters more than thoroughness.
  Triggers: "research", "look up", "find current", "what's the latest", "best practices for"
allowed-tools:
  # Task tool for true parallel execution
  - Task
  - TaskOutput
  # Claude's web search
  - WebSearch
  # Plugin installation (Claude Code extension)
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-delete-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-export-session
  # Manual MCP server installation
  - mcp__codex__codex
  - mcp__codex__codex-reply
  - mcp__codex__codex-bridge-sessions
  - mcp__codex__codex-bridge-session
  - mcp__codex__codex-bridge-name-session
  - mcp__codex__codex-bridge-delete-session
  - mcp__codex__codex-bridge-export-session
---

# Research Skill (Dual-Model)

> **DEPRECATED**: This skill is superseded by the unified `codex-bridge` skill.
> Use `/codex research <query>` instead for true parallel execution.

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

## Workflow (True Parallel Execution)

### Option A: Background Task (Recommended)

1. **Dispatch Codex in background** using Task tool:
   ```json
   {
     "description": "Codex researches topic",
     "subagent_type": "general-purpose",
     "run_in_background": true,
     "prompt": "Use mcp__codex__codex with prompt='RESEARCH: ...' config={\"web_search_request\": true} model='gpt-5.2' sandbox='read-only' name='research/<topic>'"
   }
   ```
   Save the `task_id`.

2. **Claude researches immediately** using WebSearch (no waiting)

3. **Retrieve Codex result** using TaskOutput:
   ```json
   { "task_id": "<saved task_id>", "block": true, "timeout": 600000 }
   ```

4. **Merge findings** from both sources

### Option B: Parallel Tool Calls

Make BOTH calls in a single message for parallel execution:
- Call 1: `mcp__codex__codex` with `config: { "web_search_request": true }`
- Call 2: `WebSearch` with the same query

Both execute simultaneously. Merge when both return.

## Tool Settings for Codex

> **MODEL RESTRICTION**: Only `gpt-5.2` and `gpt-5.2-codex` work with ChatGPT auth.
> Do NOT use `o3`, `o4-mini`, `gpt-5.2-mini`, or `gpt-5.2-nano` - they will fail.

> **CRITICAL**: You MUST pass `config: { "web_search_request": true }` or Codex won't search the web!

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2` | Reasoning model |
| `reasoningEffort` | `high` | Good quality-speed balance |
| `sandbox` | `read-only` | Research only |
| `config.web_search_request` | `true` | **REQUIRED** - Enable web search |
| `name` | required | Use `research/<topic> #tags` |

### Complete Tool Call Example

```json
{
  "prompt": "Research best practices for...",
  "model": "gpt-5.2",
  "reasoningEffort": "high",
  "sandbox": "read-only",
  "name": "research/topic-name #tags",
  "config": {
    "web_search_request": true
  }
}
```

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

## Timeout Recommendations

Web search tasks take longer than local operations. Use appropriate timeouts:

| Task Type | Recommended `timeoutMs` |
|-----------|------------------------|
| Simple lookup (no web) | `120000` (2 min) |
| Web search research | Omit (use default 600s) |
| Complex multi-source | `300000`-`600000` (5-10 min) |

> **TIP**: Omit `timeoutMs` for research tasks to use the default 10-minute timeout.
> Passing a short timeout (e.g., 120000ms) will cause web search tasks to fail.

### Why Timeouts Matter

Web search + reasoning is slower than local operations:
1. Codex must perform web searches (network latency)
2. Process and synthesize multiple sources
3. Generate reasoned output with citations

A 2-minute timeout is **insufficient** for most research tasks. When in doubt, omit `timeoutMs`.

## Stop Conditions

Ask user before proceeding if:
- Topic is ambiguous (need to narrow scope)
- Models found conflicting authoritative sources
- Research reveals the question should be reframed
