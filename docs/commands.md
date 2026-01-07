# Commands Reference

## Overview

| Command | Purpose |
|---------|---------|
| `/codex-bridge:discuss` | Critical analysis with GPT 5.2 (architecture, trade-offs) |
| `/codex-bridge:delegate` | Code implementation with GPT 5.2 Codex |
| `/codex-bridge:codex` | Low-ceremony Codex calls, session operations |
| `/codex-bridge:context` | Recall or checkpoint session context |

---

## /codex-bridge:discuss

Start a critical discussion using GPT 5.2 (base model, NOT Codex) with maximum reasoning.

**Use for**: Architecture decisions, trade-off analysis, risk assessment, planning, second opinions.

**Settings**:
- `model`: `gpt-5.2`
- `reasoningEffort`: `xhigh`
- `sandbox`: `read-only`

**Example**:
```
/codex-bridge:discuss Should we use microservices or monolith for our API?
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
            Yes --> /codex-bridge:discuss
            No  --> /codex-bridge:codex

Continuing something from before?
  --> /codex-bridge:context recall <topic>
```
