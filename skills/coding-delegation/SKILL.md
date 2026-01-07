---
name: coding-delegation
description: |
  Delegate coding tasks to GPT 5.2 Codex for autonomous implementation. Use when:
  implementing features, writing code, generating tests, refactoring, creating boilerplate,
  fixing bugs, or any task requiring actual code changes. Triggers: "implement", "code",
  "write", "generate", "create", "build", "fix", "refactor", "delegate to codex",
  "have codex", "let codex handle". Uses GPT 5.2 Codex with maximum reasoning for coding.
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Coding Delegation with GPT 5.2 Codex

Delegate practical coding tasks to GPT 5.2 Codex for autonomous implementation. This skill is for **code generation and implementation** - not analysis or discussion.

## When to Use This Skill

**Good candidates:**
- Implementing new features
- Writing unit/integration tests
- Refactoring code
- Generating boilerplate (APIs, models, utilities)
- Fixing bugs with clear reproduction steps
- Code transformations (e.g., JS to TS, callbacks to async/await)
- Creating API endpoints, database models, utilities

**Use critical-discussion skill instead for:**
- Architecture decisions
- Design trade-off analysis
- Planning and strategy discussions

---

## How to Delegate a Coding Task

Use the `mcp__plugin_codex-bridge_codex__codex` tool with these **required settings**:

```json
{
  "prompt": "<detailed task description>",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "<descriptive-session-name>"
}
```

**Critical Configuration:**
| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2-codex` | Optimized for code generation |
| `reasoningEffort` | `xhigh` | Complex implementations |
| `sandbox` | `workspace-write` | Needs to modify files |
| `approval-policy` | `on-failure` | Safety with autonomy |
| `name` | descriptive | For later reference |

---

## Task Description Structure

Structure your coding tasks for best results:

```
TASK: [Clear statement of what to implement]

CONTEXT:
- [Relevant files and their locations]
- [Existing patterns to follow]
- [Dependencies available]

REQUIREMENTS:
- [Specific functionality needed]
- [Edge cases to handle]
- [Performance considerations]

ACCEPTANCE CRITERIA:
- [How to verify the implementation works]
- [Tests that should pass]
- [Documentation needed]

CONSTRAINTS:
- [What NOT to modify]
- [Style guidelines]
- [Compatibility requirements]
```

---

## Sandbox Modes

| Mode | When to Use |
|------|-------------|
| `read-only` | Code review, generating plans, analyzing code |
| `workspace-write` | Most implementation tasks (recommended default) |
| `danger-full-access` | Only when needing system operations (rare) |

---

## Approval Policies

| Policy | Behavior |
|--------|----------|
| `untrusted` | Maximum safety - approval before any action |
| `on-failure` | Approval only when something fails (recommended) |
| `on-request` | Codex asks when unsure |
| `never` | Full autonomy (use with caution) |

---

## Continuing Implementation

Use `mcp__plugin_codex-bridge_codex__codex-reply` to continue:

```json
{
  "conversationId": "<from previous response>",
  "prompt": "Now add unit tests for the functions you just created"
}
```

The session maintains full context of what was implemented.

---

## Background Delegation

For long-running tasks, delegate in background using the Task tool:

```json
{
  "description": "Codex implements feature",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__plugin_codex-bridge_codex__codex with: prompt='<task>', model='gpt-5.2-codex', reasoningEffort='xhigh', sandbox='workspace-write', approval-policy='on-failure', name='<session-name>'"
}
```

Continue your own work while Codex runs, then retrieve with TaskOutput.

---

## Review Codex Output

**Always review what Codex implemented:**

1. Check the output summary for what was done
2. Review modified files: `git diff`
3. Run tests to verify functionality
4. Run linters/type checks
5. Commit only after verification

---

## Example: Feature Implementation

```json
{
  "prompt": "TASK: Add Redis caching to the /api/users endpoint\n\nCONTEXT:\n- Endpoint: src/api/users.ts\n- Redis client: src/lib/redis.ts\n- Follow caching pattern in src/api/products.ts\n\nREQUIREMENTS:\n- Cache user data for 5 minutes\n- Cache key: user:{id}\n- Handle cache misses gracefully\n- Invalidate on user update/delete\n\nACCEPTANCE CRITERIA:\n- GET /api/users/:id uses cache when available\n- Cache invalidates on PUT/DELETE\n- Add tests for caching behavior\n\nCONSTRAINTS:\n- Don't modify User model schema\n- Keep existing response format",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "users-caching-impl"
}
```

See [EXAMPLES.md](EXAMPLES.md) for more detailed usage examples.
