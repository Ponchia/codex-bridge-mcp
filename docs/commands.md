# Commands Reference

## Overview

| Command | Purpose |
|---------|---------|
| `/codex-bridge:discuss` | Dual-model discussion: Claude + Codex analyze → shared conclusion |
| `/codex-bridge:delegate` | Code implementation with GPT 5.2 Codex |
| `/codex-bridge:codex` | Low-ceremony Codex calls, session operations |
| `/codex-bridge:context` | Recall or checkpoint session context |
| `/codex-bridge:research` | Dual-model research: Claude + Codex research → merged findings |

---

## /codex-bridge:discuss

Discuss a topic with both Claude and Codex in parallel, then synthesize into a shared conclusion.

**Workflow**:
1. Dispatch Codex with analysis prompt (background)
2. Claude analyzes the same topic in parallel
3. Synthesize both perspectives (agreements, differences, shared conclusion)

**Use for**: Architecture decisions, trade-off analysis, strategic choices, second opinions.

**Output**: Codex Position, Claude Position, Agreements, Shared Conclusion, Risks, Next Steps.

**Example**:
```
/codex-bridge:discuss Should we use microservices or monolith for our API?
```

---

## /codex-bridge:research

Research a topic with both Claude and Codex in parallel, then merge findings.

**Workflow**:
1. Dispatch Codex with web search enabled (background)
2. Claude researches using WebSearch in parallel
3. Merge findings (agreements, unique insights, gaps)

**Use for**: Current best practices, technology comparisons, documentation lookups.

**Output**: Merged Findings, Agreements, Unique Insights, Gaps, Sources.

**Example**:
```
/codex-bridge:research What are the current best practices for JWT token rotation in 2025?
```

---

## /codex-bridge:delegate

Delegate a coding task to GPT 5.2 Codex for autonomous implementation.

**Use for**: Feature implementation, refactoring, test generation, bug fixes.

**Settings**:
- `model`: `gpt-5.2-codex`
- `reasoningEffort`: `xhigh`
- `sandbox`: `workspace-write`
- `approval-policy`: `on-failure`

**Example**:
```
/codex-bridge:delegate Add Redis caching to the users endpoint with tests
```

---

## /codex-bridge:codex

Low-ceremony Codex invocation. Use when you need direct control or session operations.

**Example**:
```
/codex-bridge:codex Review the authentication code for security issues
```

---

## /codex-bridge:context

Recall or checkpoint context from previous sessions.

**Modes**:
- `recall <query>` - Find a session and get a structured summary
- `checkpoint <query>` - Save context to a `notes/*` session for later

**Examples**:
```
/codex-bridge:context recall arch/auth
/codex-bridge:context checkpoint impl/caching
```

See [Sessions](sessions.md) for naming conventions and workflows.

---

## Decision Tree

```
Do you want code changes in the repo?
  Yes --> /codex-bridge:delegate
  No  --> Do you need analysis / trade-offs / a decision?
            Yes --> /codex-bridge:discuss (dual-model)
            No  --> Do you need current/web information?
                      Yes --> /codex-bridge:research (dual-model)
                      No  --> /codex-bridge:codex

Continuing something from before?
  --> /codex-bridge:context recall <topic>
```

---

## Web Search Configuration

Enable web search in any Codex call with:

```json
{
  "config": {
    "web_search_request": true
  }
}
```

This allows Codex to search the web during task execution. Useful for:
- Current best practices
- Recent documentation
- Technology comparisons
- Market research
