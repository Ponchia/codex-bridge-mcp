# Codex Protocol Examples

Tool usage examples. For workflow examples, see [examples/](../../examples/README.md).

---

## Start a Session

```json
{
  "prompt": "Analyze the authentication flow in this codebase",
  "sandbox": "read-only",
  "name": "explore/auth-flow"
}
```

**Response:**
```json
{
  "conversationId": "abc123",
  "output": "The authentication flow works as follows...",
  "session": {
    "conversationId": "abc123",
    "name": "explore/auth-flow",
    "model": "gpt-5.2-codex"
  }
}
```

---

## Continue a Session

```json
{
  "conversationId": "abc123",
  "prompt": "Now explain how session refresh works"
}
```

---

## Search Sessions

```json
{
  "query": "auth",
  "limit": 10
}
```

**Response:**
```json
{
  "data": [
    {"conversationId": "abc123", "name": "arch/auth-tokens #jwt", "capturedAt": "..."},
    {"conversationId": "def456", "name": "impl/auth-middleware", "capturedAt": "..."}
  ],
  "nextCursor": null
}
```

---

## Rename a Session

```json
{
  "conversationId": "abc123",
  "name": "arch/auth-tokens #jwt #security"
}
```

---

## Background Execution

Using Claude's Task tool:

```json
{
  "description": "Codex reviews payment code",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__plugin_codex-bridge_codex__codex with: prompt='Review src/services/payment.ts for security issues', sandbox='read-only', name='review/payment-security'"
}
```

Retrieve later:
```json
{
  "task_id": "<agent_id>",
  "block": true
}
```
