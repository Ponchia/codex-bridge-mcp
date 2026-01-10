---
description: Research a topic using both Claude (web) and Codex (web+reasoning) in parallel
argument-hint: <research topic or question>
---

# Research (Dual-Model)

Research this topic using both Claude and Codex **in true parallel**, then merge findings.

## Topic

$ARGUMENTS

## Workflow Options

Choose the approach based on research complexity:

### Option A: Background Task (Recommended for thorough research)

#### Step 1: Dispatch Codex Research in Background

Use the Task tool to run Codex without blocking:

```json
// Task tool
{
  "description": "Codex researches topic",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters:\n- prompt: 'RESEARCH TOPIC: $ARGUMENTS\n\nCONTEXT:\n- [Why this research matters]\n- [Current understanding]\n\nINSTRUCTIONS:\nResearch thoroughly. For each finding:\n1. State the finding clearly\n2. Note the source/basis\n3. Rate confidence (High/Medium/Low)\n4. Flag caveats\n\nOUTPUT:\n- Key findings with sources\n- Confidence levels\n- Gaps/unknowns'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- config: {\"web_search_request\": true}\n- name: 'research/<topic> #tags'\n\nReturn the full tool response."
}
```

**Save the `task_id`**. Codex is now researching in background with web search.

#### Step 2: Claude Researches Immediately (No Waiting)

While Codex works in background, use WebSearch:

1. Search for current best practices and recent developments
2. Search for authoritative sources (official docs, expert blogs)
3. Search for case studies or real-world examples
4. Apply your own reasoning to evaluate findings

Document findings with sources and confidence levels.

#### Step 3: Retrieve Codex Result

When Claude's research is complete, get Codex's result:

```json
// TaskOutput tool
{ "task_id": "<saved task_id>", "block": true, "timeout": 600000 }
```

#### Step 4: Merge Findings

Combine both research outputs into unified findings.

---

### Option B: Parallel Tool Calls (Faster for simple queries)

Make BOTH calls in a **single message** for simultaneous execution:

**In the same response**, call both tools in parallel:

**Tool call 1** - Codex with web search:
```json
// mcp__codex__codex
{
  "prompt": "RESEARCH: $ARGUMENTS\n\nFind key findings with sources. Rate confidence.",
  "model": "gpt-5.2",
  "reasoningEffort": "high",
  "sandbox": "read-only",
  "config": { "web_search_request": true },
  "name": "research/<topic> #tags"
}
```

**Tool call 2** - Claude's WebSearch:
```json
// WebSearch
{ "query": "$ARGUMENTS best practices 2025" }
```

Both execute simultaneously. Merge results when both return.

---

## Output Contract

Present merged research in this format:

```markdown
## Research: <topic>

### Merged Findings

#### <Finding 1>
- **Codex**: <what Codex found + source>
- **Claude**: <what Claude found + source>
- **Confidence**: <High/Medium/Low based on agreement>

#### <Finding 2>
...

### Agreements
- <Findings where both sources align>

### Unique Insights
- **From Codex**: <findings only Codex surfaced>
- **From Claude**: <findings only Claude surfaced>

### Gaps & Unknowns
- <What neither could determine>
- <Conflicting information>

### Recommended Next Steps
1. <Verification action>
2. <Follow-up research>

### Sources
- <List of sources consulted>

### Session Info
Codex session: `research/<topic>` (conversationId: ...)
```

## When to Use

- Need current/up-to-date information
- Best practices that evolve over time
- Technology comparisons with recent developments
- Documentation lookups where completeness matters

## Tool Name Note

If you installed as a manual MCP server (not plugin), use `mcp__codex__*` instead of `mcp__plugin_codex-bridge_codex__*`.
