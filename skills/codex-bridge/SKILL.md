---
name: codex-bridge
description: |
  Unified Codex Bridge skill for coding delegation, dual-model discussions, and parallel research.
  Modes: delegate (code), discuss (architecture), research (web search).
  Features true parallel execution using Claude Code's Task tool for background dispatch.
allowed-tools:
  # Task tool for true parallel execution
  - Task
  - TaskOutput
  # Plugin installation (Claude Code extension)
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-info
  - mcp__plugin_codex-bridge_codex__codex-bridge-options
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-delete-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-export-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-read-rollout
  # Manual MCP server installation
  - mcp__codex__codex
  - mcp__codex__codex-reply
  - mcp__codex__codex-bridge-info
  - mcp__codex__codex-bridge-options
  - mcp__codex__codex-bridge-sessions
  - mcp__codex__codex-bridge-session
  - mcp__codex__codex-bridge-name-session
  - mcp__codex__codex-bridge-delete-session
  - mcp__codex__codex-bridge-export-session
  - mcp__codex__codex-bridge-read-rollout
  # Claude's web search for dual-model research
  - WebSearch
---

# Codex Bridge (Unified Skill)

A unified interface to GPT 5.2 Codex with **true parallel execution** for dual-model workflows.

## Modes

| Mode | Command | Pattern | Use For |
|------|---------|---------|---------|
| **delegate** | `/codex delegate <task>` | Single-model | Code implementation, tests, refactoring |
| **discuss** | `/codex discuss <topic>` | Dual-model parallel | Architecture decisions, trade-offs |
| **research** | `/codex research <query>` | Dual-model parallel | Web research, best practices |
| **direct** | `/codex <prompt>` | Single-model | Direct Codex access |

## Model Restrictions

> **ChatGPT Auth**: Only `gpt-5.2` and `gpt-5.2-codex` work.
> Do NOT use `o3`, `o4-mini`, `gpt-5.2-mini`, or `gpt-5.2-nano` - they require API key auth.

---

# Mode: delegate

Delegate coding tasks to GPT 5.2 Codex for autonomous implementation.

## When to Use

- Implementing features with clear requirements
- Writing tests for existing code
- Refactoring with defined goals
- Bug fixes with clear reproduction steps

## When NOT to Use

- Requirements are ambiguous (use `discuss` first)
- Need real-time visibility into changes
- High-risk changes without verification strategy

## Required Inputs (ask if missing)

1. **Task**: What to implement
2. **Context**: Relevant files, patterns to follow
3. **Acceptance criteria**: How to verify success
4. **Constraints**: What NOT to modify

## Tool Settings

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2-codex` | Optimized for code generation |
| `reasoningEffort` | `high` | Good quality-speed balance |
| `sandbox` | `workspace-write` | Needs to modify files |
| `approval-policy` | `on-failure` | Safety with autonomy |
| `name` | required | Use `impl/<topic> #tags` |

## Workflow

1. **Confirm inputs** are complete (don't guess requirements)
2. **Call codex tool** with settings above
3. **Review output** and verify:
   ```bash
   git diff              # Review changes
   npm test              # Run tests
   ```
4. **Report** what was implemented + verification results

## Output Contract

- **Summary**: Files changed, functions added
- **Verification**: Commands run + results
- **Assumptions**: What was assumed
- **Next steps**: Follow-up work if any
- **Session**: name + conversationId

---

# Mode: discuss (Dual-Model Parallel)

Both Claude and Codex analyze the topic **in parallel**, then synthesize to a shared conclusion.

## Why Dual-Model?

- **Different perspectives**: Each model weighs factors differently
- **Confidence**: Agreement = high confidence; differences = important nuances
- **Blind spot reduction**: Two analyses catch more edge cases

## When to Use

- Architecture decisions (microservices vs monolith)
- Technology choices (library A vs B)
- Trade-off analysis (security vs usability)
- Getting a "second opinion"

## When NOT to Use

- Need code changes (use `delegate`)
- Simple factual questions
- Current events (use `research`)

## Required Inputs (ask if missing)

1. **Goal**: What outcome are we optimizing for?
2. **Constraints**: Performance, cost, security, compatibility
3. **Options**: Known alternatives (if any)
4. **Stakes**: Why this decision matters

## Workflow (True Parallel Execution)

### Step 1: Dispatch Codex in Background

Use Claude Code's Task tool to run Codex without blocking:

```json
{
  "description": "Codex analyzes architecture",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters:\n- prompt: 'TOPIC: <topic>\n\nCONTEXT:\n- <relevant background>\n- <constraints>\n\nANALYSIS REQUIRED:\n1. Key considerations and factors\n2. Trade-offs between approaches\n3. Risks and mitigations\n4. Your recommendation with rationale'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- name: 'arch/<topic> #tags'\n\nReturn the full tool response."
}
```

**Save the `task_id`** from the response.

### Step 2: Claude Analyzes Immediately (No Waiting)

While Codex works in background, Claude analyzes:

1. Consider the key trade-offs and constraints
2. Evaluate different approaches
3. Identify risks and edge cases
4. Form your own recommendation with reasoning

Document your analysis thoroughly.

### Step 3: Retrieve Codex Result

When Claude's analysis is complete, get Codex's result:

```json
// TaskOutput tool
{ "task_id": "<saved task_id>", "block": true, "timeout": 300000 }
```

### Step 4: Synthesize to Shared Conclusion

Compare both analyses:
- Identify agreements (high confidence)
- Identify differences (needs resolution)
- Resolve through reasoning
- Produce shared recommendation

## Output Contract

```markdown
## Discussion: <topic>

### Codex Position
<Summary of Codex's analysis>

### Claude Position
<Summary of Claude's analysis>

### Agreements (High Confidence)
- <Point where both align>

### Points of Difference
- <Difference>: Codex says X, Claude says Y
- <Resolution>: After considering both, <conclusion>

### Shared Conclusion
<The synthesized recommendation>

### Key Trade-offs
- <Trade-off 1>
- <Trade-off 2>

### Risks & Mitigations
- <Risk 1>: <Mitigation>

### Next Steps
1. <Action item>

### Session Info
Codex session: arch/<topic> (conversationId: ...)
```

---

# Mode: research (Dual-Model Parallel)

Both Claude and Codex research the topic **in parallel** using web search, then merge findings.

## Why Dual-Model Research?

- **Coverage**: Two models may find different sources
- **Confidence**: Agreement = higher confidence
- **Validation**: Cross-check findings between models

## When to Use

- Need current/up-to-date information
- Best practices that evolve over time
- Technology comparisons with recent developments
- Documentation lookups where completeness matters

## When NOT to Use

- Speed matters more than thoroughness
- Topic is purely code-specific (use `delegate`)
- Need architectural analysis (use `discuss`)

## Required Inputs (ask if missing)

1. **Topic**: What to research
2. **Context**: Why this research matters
3. **Scope**: Breadth vs depth preference

## Workflow (True Parallel Execution)

### Step 1: Dispatch Codex Research in Background

```json
{
  "description": "Codex researches topic",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters:\n- prompt: 'RESEARCH TOPIC: <topic>\n\nINSTRUCTIONS:\nResearch thoroughly. For each finding:\n1. State the finding clearly\n2. Note the source/basis\n3. Rate confidence (High/Medium/Low)\n4. Flag caveats\n\nOUTPUT:\n- Key findings with sources\n- Confidence levels\n- Gaps/unknowns'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- config: {\"web_search_request\": true}\n- name: 'research/<topic> #tags'\n\nReturn the full tool response."
}
```

**Save the `task_id`** from the response. Codex is now researching in background.

### Step 2: Claude Researches Immediately (No Waiting)

**IMMEDIATELY** after dispatching Codex, Claude researches the same topic using WebSearch:

```json
// WebSearch tool - make multiple searches
{ "query": "<topic> best practices 2025" }
{ "query": "<topic> official documentation" }
{ "query": "<topic> real-world examples" }
```

Document your findings with sources and confidence levels thoroughly.

**DO NOT WAIT** for Codex - start your WebSearch calls right away.

### Step 3: Retrieve Codex Result

When Claude's research is complete, get Codex's result:

```json
// TaskOutput tool
{ "task_id": "<saved task_id>", "block": true, "timeout": 600000 }
```

### Step 4: Merge Findings

Combine both research outputs into unified findings:
- Identify where both found the same information (high confidence)
- Note unique insights from each source
- Flag any conflicting information
- List gaps neither could fill

## Output Contract

```markdown
## Research: <topic>

### Merged Findings

#### <Finding 1>
- **Codex**: <what Codex found + source>
- **Claude**: <what Claude found + source>
- **Confidence**: <High/Medium/Low based on agreement>

### Agreements
- <Findings where both align>

### Unique Insights
- **From Codex**: <findings only Codex surfaced>
- **From Claude**: <findings only Claude surfaced>

### Gaps & Unknowns
- <What neither could determine>

### Sources
- <List of all sources consulted>

### Session Info
Codex session: research/<topic> (conversationId: ...)
```

---

# Mode: direct

Direct Codex access for custom workflows.

## Tool Reference

| Tool | Purpose |
|------|---------|
| `codex` | Start a session |
| `codex-reply` | Continue by conversationId |
| `codex-bridge-sessions` | List/search sessions |
| `codex-bridge-session` | Get session details |
| `codex-bridge-name-session` | Rename session |
| `codex-bridge-delete-session` | Delete session |
| `codex-bridge-export-session` | Export as markdown/JSON |
| `codex-bridge-read-rollout` | Debug session history |
| `codex-bridge-info` | Bridge version and status |
| `codex-bridge-options` | Available models and settings |

## Session Naming Convention

| Pattern | Use for |
|---------|---------|
| `arch/<topic> #tags` | Architecture decisions |
| `impl/<topic> #tags` | Implementation |
| `research/<topic> #tags` | Research |
| `notes/<topic> #notes` | Running memory |

---

# Parallel Execution Summary

| Mode | Pattern | Mechanism |
|------|---------|-----------|
| delegate | Sequential | Direct codex tool call |
| discuss | **True Parallel** | Task tool with `run_in_background: true` |
| research | **True Parallel** | Task tool OR parallel tool calls in single message |

The key insight: Claude Code's Task tool enables **actual parallel execution** where Codex runs in background while Claude continues working.
