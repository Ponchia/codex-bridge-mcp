---
description: Research a topic using both Claude (web) and Codex (web+reasoning) in parallel
argument-hint: <research topic or question>
---

# Research (Dual-Model)

Research this topic using both Claude and Codex in parallel, then merge findings.

## Topic

$ARGUMENTS

## Workflow

### Step 1: Dispatch Codex Research (Background)

Start Codex researching with web search enabled:

```json
// mcp__plugin_codex-bridge_codex__codex
{
  "prompt": "RESEARCH TOPIC: $ARGUMENTS\n\nCONTEXT:\n- [Why this research matters]\n- [Current understanding]\n\nINSTRUCTIONS:\nResearch this topic thoroughly. For each finding:\n1. State the finding clearly\n2. Note the source/basis\n3. Rate confidence (High/Medium/Low)\n4. Flag any caveats or uncertainties\n\nOUTPUT FORMAT:\n- Key findings (with sources where available)\n- Confidence level per finding\n- Gaps/unknowns\n- Suggested follow-ups",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "config": {
    "web_search_request": true
  },
  "name": "research/<topic> #tags"
}
```

**Important**: After calling this tool, immediately proceed to Step 2 while Codex works.

### Step 2: Claude Researches (Parallel)

While Codex works, use Claude's WebSearch to research the same topic:

1. Search for current best practices and recent developments
2. Search for authoritative sources (official docs, expert blogs)
3. Search for case studies or real-world examples
4. Apply your own reasoning to evaluate findings

Document findings with sources and confidence levels.

### Step 3: Merge Findings

Once both complete, merge the research into a unified output.

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

If you installed as a manual MCP server (not plugin), use `mcp__codex__codex` instead of `mcp__plugin_codex-bridge_codex__codex`.
