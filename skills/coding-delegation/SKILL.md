---
name: coding-delegation
description: |
  Delegate coding tasks to GPT 5.2 Codex for autonomous implementation.
  Use when: implementing features, writing tests, refactoring, fixing bugs, generating boilerplate.
  Avoid when: requirements are unclear (use critical-discussion first).
  Triggers: "implement", "code", "write", "generate", "build", "fix", "refactor", "delegate".
allowed-tools:
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
---

# Coding Delegation (GPT 5.2 Codex)

## Purpose

- Delegate implementation tasks to Codex for autonomous execution
- Get code changes with verification evidence

## Use When / Avoid When

**Use when:**
- Implementing features with clear requirements
- Writing tests for existing code
- Refactoring with defined goals
- Bug fixes with clear reproduction steps
- Generating boilerplate (APIs, models, utilities)

**Avoid when:**
- Requirements are ambiguous (use `critical-discussion` first)
- High-risk changes without verification strategy
- User wants step-by-step visibility

## Required Inputs (ask if missing)

- Task: what to implement
- Context: relevant files, patterns to follow
- Acceptance criteria: how to verify success
- Constraints: what NOT to modify

## Tool Settings

> **IMPORTANT**: Only GPT 5.2 models are available. Do NOT use `o3`, `o4-mini`, or other model names.

| Setting | Value | Why |
|---------|-------|-----|
| `model` | `gpt-5.2-codex` | Optimized for code generation |
| `reasoningEffort` | `xhigh` | **Always use xhigh** |
| `sandbox` | `workspace-write` | Needs to modify files |
| `approval-policy` | `on-failure` | Safety with autonomy |
| `name` | required | Use `impl/<topic> #tag1 #tag2` |

### Complete Tool Call Example

```json
{
  "prompt": "TASK: Implement...\n\nCONTEXT:\n- ...\n\nREQUIREMENTS:\n- ...",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/feature-name #tags"
}
```

## Prompt Skeleton

```
TASK: <what to implement>

CONTEXT:
- <relevant files and locations>
- <existing patterns to follow>
- <dependencies available>

REQUIREMENTS:
- <specific functionality>
- <edge cases to handle>

ACCEPTANCE CRITERIA:
- <how to verify it works>
- <tests that should pass>

CONSTRAINTS:
- <what NOT to modify>
- <style guidelines>
```

## Workflow

1. Confirm inputs are complete; don't guess requirements
2. Start implementation session with settings above
3. Name the session (`impl/<topic> #tags`)
4. Return output per contract below with verification evidence
5. **Always review** before committing: `git diff`, run tests

## Output Contract

- **Summary**: what was implemented (files changed, functions added)
- **Verification**: commands run + results (or why not run)
- **Assumptions**: what was assumed about requirements
- **Next steps**: follow-up work if any
- **Session**: name + `conversationId`

## Stop Conditions (ask the user)

- Ambiguous requirements affecting correctness
- Security-sensitive changes without explicit constraints
- Large refactors without clear "done" definition
- Breaking changes to public APIs

## Verification Reminder

Always verify Codex output before committing:

```bash
git diff              # Review changes
npm test              # Run tests
tsc --noEmit          # Type check
npm run lint          # Lint check
```

See [docs/verification.md](../../docs/verification.md) for the full contract.
