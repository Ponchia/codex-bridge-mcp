---
name: using-codex
description: |
  Delegate complex coding tasks to OpenAI Codex. Use when: implementing multi-file features,
  complex refactoring, generating boilerplate code, or when a task benefits from Codex's
  specialized code generation capabilities. Codex excels at autonomous coding tasks.

  KEY CAPABILITY: Run Codex as a background subagent using the Task tool with run_in_background: true.
  This allows parallel work - spawn Codex for code review or alternative implementation while
  continuing your own work. Use TaskOutput to retrieve results later.
---

# Using Codex as an Agent

Codex is OpenAI's coding agent that can autonomously execute multi-step coding tasks. Use it when the task would benefit from autonomous execution rather than step-by-step guidance.

## When to Use Codex

**Good candidates for Codex:**
- Implementing features that span multiple files
- Complex refactoring or code transformations
- Generating boilerplate code (tests, API endpoints, models)
- Tasks with clear specifications that need autonomous execution
- When you want a "second opinion" implementation approach

**Keep in Claude:**
- Simple single-file edits
- Tasks requiring interactive discussion
- Code review and explanation
- When the user wants step-by-step visibility

## Starting a Codex Session

Use the `mcp__codex__codex` tool:

```json
{
  "prompt": "Implement a user authentication system with login, logout, and session management",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure"
}
```

**Key parameters:**
- `prompt` (required): Clear task description with context
- `sandbox`: `read-only` | `workspace-write` | `danger-full-access`
- `approval-policy`: `untrusted` | `on-failure` | `on-request` | `never`
- `model`: Override the model (e.g., `gpt-5.2`, `gpt-5.2-mini`)
- `reasoningEffort`: `none` | `minimal` | `low` | `medium` | `high` | `xhigh`
- `timeoutMs`: Timeout in milliseconds (default: 600000 = 10 min)

**Response format:**
```json
{
  "conversationId": "abc123",
  "output": "I've implemented the authentication system...",
  "session": {
    "conversationId": "abc123",
    "model": "gpt-5.2",
    "sandboxPolicy": {...}
  }
}
```

## Continuing a Conversation

Use `mcp__codex__codex-reply` to continue with the same `conversationId`:

```json
{
  "conversationId": "abc123",
  "prompt": "Now add password reset functionality"
}
```

The conversation maintains context, so Codex remembers what it implemented.

## Configuration Guidelines

### Sandbox Policies

| Policy | Use When |
|--------|----------|
| `read-only` | Exploring, analyzing, generating plans |
| `workspace-write` | Most implementation tasks (recommended) |
| `danger-full-access` | Only when explicitly needed for system operations |

### Approval Policies

| Policy | Behavior |
|--------|----------|
| `untrusted` | Maximum safety, approval before any action |
| `on-failure` | Approval only when something fails |
| `on-request` | Codex asks when unsure |
| `never` | Full autonomy (use with `workspace-write` sandbox) |

### Reasoning Effort

For complex tasks, increase reasoning effort:
```json
{
  "prompt": "...",
  "reasoningEffort": "high"
}
```

## Error Handling

If Codex times out or fails:
1. Check the `output` field for partial progress
2. Use `codex-reply` to continue from where it left off
3. Increase `timeoutMs` for long-running tasks
4. Consider breaking the task into smaller pieces

## Best Practices

1. **Provide context**: Include relevant file paths, existing patterns, constraints
2. **Be specific**: Clear acceptance criteria help Codex deliver better results
3. **Start with read-only**: Explore/plan first, then switch to `workspace-write`
4. **Save the conversationId**: Essential for follow-up messages
5. **Review output**: Always review what Codex implemented before committing

---

## Running Codex as a Background Subagent

Codex tasks can take several minutes. Instead of waiting, spawn Codex as a **background subagent** using Claude Code's Task tool, then continue working on other things.

### The Pattern

```
1. Spawn Task agent with run_in_background: true
   → Task agent calls mcp__codex__codex
   → Returns immediately with agent_id

2. Continue your own work (edits, other tasks, etc.)

3. Use TaskOutput to retrieve Codex results when needed
```

### Starting a Background Codex Task

Use the **Task tool** to spawn a background agent that calls Codex:

```json
{
  "description": "Codex code review",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool to review the authentication implementation in src/auth/. Call the tool with: prompt='Review the authentication code in src/auth/ for security issues, code quality, and potential improvements. List specific findings with file:line references.', sandbox='read-only'. Return the full Codex response including conversationId."
}
```

This returns immediately with an `agent_id`. Continue working, then retrieve results:

```json
// TaskOutput tool
{
  "task_id": "<agent_id from above>",
  "block": true  // wait for completion, or false to check status
}
```

### When to Use Background Execution

**Good use cases:**
- **Code review while implementing**: Spawn Codex to review existing code while you implement new features
- **Second opinion**: Get Codex's implementation approach while you work on your own
- **Parallel exploration**: Have Codex explore one approach while you explore another
- **Long-running tasks**: Don't block on tasks that might take 5-10 minutes

**Keep synchronous when:**
- Task is quick (< 1 minute)
- You need the result immediately to continue
- User explicitly wants to wait and see the result

---

## Parallel Codex Tasks

Spawn **multiple Codex tasks simultaneously** for different purposes. Send multiple Task tool calls in a single message:

### Example: Review + Alternative Implementation

```json
// First Task call - background review
{
  "description": "Codex reviews current code",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex to review src/services/payment.ts for issues. Use sandbox='read-only'."
}

// Second Task call - alternative implementation (same message)
{
  "description": "Codex alternative approach",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex to implement an alternative payment processing approach. Use sandbox='read-only' to just generate the code without writing files."
}
```

Both run in parallel. Retrieve results as needed with TaskOutput.

---

## Workflow Patterns

### Pattern 1: Review While Implementing

**Scenario**: User asks to add a feature. You want Codex to review existing related code while you implement.

```
1. Spawn background Codex task:
   Task(run_in_background=true, prompt="Use mcp__codex__codex to review
   src/api/users.ts for patterns, issues, and improvement suggestions...")

2. Implement the feature yourself using Edit/Write tools

3. Before finishing, retrieve Codex review:
   TaskOutput(task_id=<agent_id>)

4. Incorporate relevant feedback from Codex review

5. Present both your implementation and Codex's review findings to user
```

### Pattern 2: Codex Implements, You Review

**Scenario**: Delegate implementation to Codex while you review other code.

```
1. Spawn background Codex implementation:
   Task(run_in_background=true, prompt="Use mcp__codex__codex to implement
   the caching layer in src/api/... with sandbox='workspace-write'")

2. While Codex works, review related code or tests yourself

3. Retrieve Codex results:
   TaskOutput(task_id=<agent_id>)

4. Review what Codex implemented, suggest improvements to user
```

### Pattern 3: Parallel Exploration

**Scenario**: Uncertain about best approach. Explore multiple options in parallel.

```
1. Spawn Codex to explore approach A (background)
2. Spawn Codex to explore approach B (background)
3. You explore approach C yourself

4. Gather all results:
   TaskOutput for approach A
   TaskOutput for approach B
   Your findings for approach C

5. Compare and recommend best approach to user
```

### Pattern 4: Continuous Background Review

**Scenario**: Long implementation session. Have Codex periodically review your work.

```
After completing each major component:

1. Spawn background Codex review of what you just implemented
2. Continue to next component
3. Check previous review results before moving to third component
4. Incorporate feedback as you go
```

---

## Helper Tools

- `mcp__codex__codex-bridge-info`: Get bridge status and configuration
- `mcp__codex__codex-bridge-options`: List available options (models, enums)
- `mcp__codex__codex-bridge-sessions`: List previous sessions
- `mcp__codex__codex-bridge-session`: Get details for a specific session

See [EXAMPLES.md](EXAMPLES.md) for concrete usage examples.
