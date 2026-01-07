# Examples Catalog

Canonical examples for codex-bridge-mcp. Each example shows: goal, command/tool call, expected outcome.

## Quick Reference

| Example | Type | Description |
|---------|------|-------------|
| [Architecture Decision](#architecture-decision) | discuss | Microservices vs monolith |
| [Trade-off Analysis](#trade-off-analysis) | discuss | JWT vs sessions |
| [Feature Implementation](#feature-implementation) | delegate | Add caching to endpoint |
| [Test Generation](#test-generation) | delegate | Generate unit tests |
| [Refactoring](#refactoring) | delegate | Callbacks to async/await |
| [Code Review](#code-review) | delegate | Security review (read-only) |
| [Session Recall](#session-recall) | context | Resume previous discussion |
| [Session Checkpoint](#session-checkpoint) | context | Save to notes |

---

## Discussion Examples

### Architecture Decision

**Goal**: Decide between microservices and monolith.

```
/codex-bridge:discuss Should we use microservices or monolith for our e-commerce platform?
```

Or direct tool call:

```json
{
  "prompt": "TOPIC: Microservices vs monolith for e-commerce platform\n\nCONTEXT:\n- Team of 5 developers\n- 10k DAU initially, scaling to 100k\n- Django experience\n\nQUESTIONS:\n1. Operational complexity trade-offs?\n2. Time-to-market impact?\n3. Scaling implications?\n\nDESIRED OUTPUT:\n- Pros/cons comparison\n- Recommendation with justification",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/ecommerce-platform #architecture"
}
```

### Trade-off Analysis

**Goal**: Evaluate authentication approaches.

```json
{
  "prompt": "TOPIC: JWT vs opaque session tokens\n\nCONTEXT:\n- API serving web + mobile\n- Need immediate session revocation\n- High-traffic endpoints\n\nQUESTIONS:\n1. Security implications?\n2. Scalability trade-offs?\n3. Token revocation strategies?",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/auth-tokens #jwt #security"
}
```

---

## Delegation Examples

### Feature Implementation

**Goal**: Add Redis caching to an API endpoint.

```
/codex-bridge:delegate Add Redis caching to the /api/users endpoint with 5-minute TTL
```

Or direct tool call:

```json
{
  "prompt": "TASK: Add Redis caching to /api/users endpoint\n\nCONTEXT:\n- Endpoint: src/api/users.ts\n- Redis client: src/lib/redis.ts\n- Follow pattern in src/api/products.ts\n\nREQUIREMENTS:\n- Cache for 5 minutes (TTL: 300s)\n- Cache key: user:{id}\n- Invalidate on update/delete\n\nACCEPTANCE CRITERIA:\n- GET uses cache when available\n- PUT/DELETE invalidate cache\n- Tests for caching behavior",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/users-caching #redis #perf"
}
```

### Test Generation

**Goal**: Generate comprehensive tests for a module.

```json
{
  "prompt": "TASK: Generate unit tests for src/utils/validation.ts\n\nCONTEXT:\n- Framework: Jest\n- Output: src/utils/__tests__/validation.test.ts\n- Follow patterns in formatting.test.ts\n\nREQUIREMENTS:\n- Test all exported functions\n- Cover edge cases: null, undefined, empty, whitespace\n- Test error messages\n\nACCEPTANCE CRITERIA:\n- 100% function coverage\n- Each function has 5+ test cases",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/validation-tests #testing"
}
```

### Refactoring

**Goal**: Convert callback-based code to async/await.

```json
{
  "prompt": "TASK: Refactor src/services/payment.js from callbacks to async/await\n\nCONTEXT:\n- 12 functions use callbacks\n- Some chain 3-4 callbacks deep\n- Keep JavaScript (no TypeScript)\n\nREQUIREMENTS:\n- All functions use async/await\n- Maintain same public API\n- Add proper try/catch\n\nCONSTRAINTS:\n- Don't change exported function names\n- Keep backward compatibility",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "timeoutMs": 300000,
  "name": "impl/payment-async #refactor"
}
```

### Code Review

**Goal**: Security review (read-only, no changes).

```json
{
  "prompt": "TASK: Review src/services/payment.ts for security issues\n\nREVIEW FOR:\n1. Input validation gaps\n2. Authentication/authorization issues\n3. Error handling that leaks info\n4. SQL injection / XSS risks\n\nOUTPUT:\n- Findings by severity: CRITICAL, HIGH, MEDIUM, LOW\n- File:line references\n- Specific fix suggestions",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "review/payment-security #security"
}
```

---

## Session Examples

### Session Recall

**Goal**: Resume a previous architecture discussion.

```
/codex-bridge:context recall arch/auth
```

This searches for sessions matching "arch/auth" and produces a structured summary:
- Recap
- Decisions made
- Open questions
- Next steps

### Session Checkpoint

**Goal**: Save discussion context to notes for later.

```
/codex-bridge:context checkpoint arch/auth-tokens
```

This:
1. Generates a checkpoint from the session
2. Persists to `notes/auth-tokens #notes`
3. Creates searchable, resumable memory

### Continue a Session

**Goal**: Pick up where you left off.

```json
{
  "conversationId": "<from previous response or search>",
  "prompt": "Let's continue. What were the open questions?"
}
```

### Search Sessions

**Goal**: Find sessions by topic.

```json
{
  "query": "auth",
  "limit": 10
}
```

Returns all sessions with "auth" in the name.

---

## More Examples

See the skill-specific example files for additional scenarios:
- [critical-discussion EXAMPLES.md](../skills/critical-discussion/EXAMPLES.md)
- [coding-delegation EXAMPLES.md](../skills/coding-delegation/EXAMPLES.md)
- [using-codex EXAMPLES.md](../skills/using-codex/EXAMPLES.md)
