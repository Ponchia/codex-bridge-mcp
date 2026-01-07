# Coding Delegation Examples

Top 3 canonical examples. For more, see [examples/](../../examples/README.md).

---

## Example 1: Feature Implementation

```json
{
  "prompt": "TASK: Add Redis caching to /api/users endpoint\n\nCONTEXT:\n- Endpoint: src/api/users.ts\n- Redis client: src/lib/redis.ts\n- Follow pattern in src/api/products.ts\n\nREQUIREMENTS:\n- Cache for 5 minutes (TTL: 300s)\n- Cache key: user:{id}\n- Handle cache misses gracefully\n- Invalidate on update/delete\n\nACCEPTANCE CRITERIA:\n- GET /api/users/:id uses cache when available\n- PUT/DELETE invalidate cache\n- Tests for caching behavior\n\nCONSTRAINTS:\n- Don't modify User model schema\n- Keep existing response format",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/users-caching #redis #perf"
}
```

---

## Example 2: Test Generation

```json
{
  "prompt": "TASK: Generate unit tests for src/utils/validation.ts\n\nCONTEXT:\n- Framework: Jest\n- Output: src/utils/__tests__/validation.test.ts\n- Follow patterns in formatting.test.ts\n- Exports: validateEmail, validatePhone, validatePassword, validateUsername\n\nREQUIREMENTS:\n- Test all exported functions\n- Cover edge cases: null, undefined, empty, whitespace\n- Cover boundary conditions (min/max lengths)\n- Test error cases and messages\n\nACCEPTANCE CRITERIA:\n- 100% function coverage\n- All tests pass\n- Each function has 5+ test cases",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/validation-tests #testing"
}
```

---

## Example 3: Bug Fix

```json
{
  "prompt": "TASK: Fix authentication timeout bug\n\nBUG DESCRIPTION:\n- Users logged out randomly after 10-15 minutes\n- Error: 'TokenExpiredError: jwt expired'\n- Expected: Sessions last 24 hours\n- Started after recent jsonwebtoken upgrade\n\nCONTEXT:\n- Token generation: src/auth/tokens.ts\n- Middleware: src/auth/middleware.ts\n- Config: src/config/auth.ts\n\nREQUIREMENTS:\n- Identify root cause\n- Fix so tokens last 24 hours\n- Add regression test\n- Document fix in code comments\n\nACCEPTANCE CRITERIA:\n- Tokens expire after 24 hours\n- No random logouts\n- Test verifies expiration behavior",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/auth-timeout-fix #bugfix #auth"
}
```
