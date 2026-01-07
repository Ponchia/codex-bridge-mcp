# Codex Usage Examples

## Example 1: Implementing a New Feature

**Scenario**: User asks to add a caching layer to an API.

```json
{
  "prompt": "Add Redis caching to the /api/users endpoint. The endpoint is in src/api/users.ts. Cache user data for 5 minutes. Use the existing Redis connection from src/lib/redis.ts.",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "reasoningEffort": "medium"
}
```

**Follow-up to add cache invalidation:**
```json
{
  "conversationId": "abc123",
  "prompt": "Add cache invalidation when a user is updated or deleted"
}
```

## Example 2: Complex Refactoring

**Scenario**: Migrate from callbacks to async/await.

```json
{
  "prompt": "Refactor src/services/database.js from callback-based functions to async/await. Maintain the same public API. Update all 15 functions in the file.",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "timeoutMs": 300000,
  "reasoningEffort": "high"
}
```

## Example 3: Generating Tests

**Scenario**: Add comprehensive tests for a module.

```json
{
  "prompt": "Generate unit tests for src/utils/validation.ts. Use Jest. Cover all exported functions with edge cases. The test file should go in src/utils/__tests__/validation.test.ts.",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure"
}
```

## Example 4: Exploration First, Then Implementation

**Step 1: Explore (read-only)**
```json
{
  "prompt": "Analyze the authentication flow in this codebase. Identify all files involved and explain how login/logout works.",
  "sandbox": "read-only"
}
```

**Step 2: Plan (read-only, continue conversation)**
```json
{
  "conversationId": "abc123",
  "prompt": "Create a plan to add OAuth2 support. List the files that need to be modified and the new files needed."
}
```

**Step 3: Implement (workspace-write, new session)**
```json
{
  "prompt": "Implement OAuth2 support following this plan: [paste plan from previous session]. Files to modify: src/auth/login.ts, src/auth/middleware.ts. New files: src/auth/oauth.ts, src/auth/providers/google.ts.",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure"
}
```

## Example 5: Handling Long-Running Tasks

For tasks that might take longer than 10 minutes:

```json
{
  "prompt": "Migrate the entire codebase from JavaScript to TypeScript. Start with the src/utils folder.",
  "sandbox": "workspace-write",
  "timeoutMs": 600000,
  "reasoningEffort": "high"
}
```

If it times out, continue:
```json
{
  "conversationId": "abc123",
  "prompt": "Continue the migration. What's left to do?",
  "timeoutMs": 600000
}
```

## Example 6: Using Different Models

For simpler tasks, use a faster model:
```json
{
  "prompt": "Add JSDoc comments to all exported functions in src/api/handlers.ts",
  "model": "gpt-5.2-mini",
  "sandbox": "workspace-write"
}
```

For complex architectural work:
```json
{
  "prompt": "Design and implement a plugin system for this application...",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write"
}
```

## Example 7: Debugging with Codex

```json
{
  "prompt": "The tests in src/services/__tests__/payment.test.ts are failing with 'TypeError: Cannot read property of undefined'. Debug and fix the issue. Run the tests after fixing.",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure"
}
```

---

## Background Execution Examples

### Example 8: Background Code Review While Implementing

**Scenario**: User asks to add a payment webhook handler. Spawn Codex to review existing payment code while you implement.

**Step 1: Spawn background review**
```json
// Task tool call
{
  "description": "Codex reviews payment code",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters: prompt='Review the payment processing code in src/services/payment/ and src/api/payments/. Look for: 1) Security issues (input validation, authentication), 2) Error handling gaps, 3) Code quality issues, 4) Missing edge cases. Provide specific findings with file:line references.', sandbox='read-only'. Return the full response."
}
```
Returns: `agent_id: "task_abc123"`

**Step 2: Implement the webhook handler yourself** (using Edit/Write tools)

**Step 3: Retrieve review before finishing**
```json
// TaskOutput tool call
{
  "task_id": "task_abc123",
  "block": true
}
```

**Step 4**: Incorporate relevant findings into your implementation or mention them to the user.

---

### Example 9: Parallel Approach Exploration

**Scenario**: User wants to optimize database queries but isn't sure of best approach. Explore multiple options in parallel.

**Spawn three parallel tasks in a single message:**

```json
// Task 1: Codex explores query optimization
{
  "description": "Codex query optimization",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex with: prompt='Analyze src/db/queries.ts and suggest query optimizations. Focus on N+1 problems, missing indexes, and inefficient joins. Provide before/after code.', sandbox='read-only'"
}

// Task 2: Codex explores caching strategy
{
  "description": "Codex caching strategy",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex with: prompt='Design a caching strategy for the queries in src/db/queries.ts. Suggest what to cache, TTLs, and invalidation strategies. Show implementation code.', sandbox='read-only'"
}

// Task 3: Codex explores denormalization
{
  "description": "Codex denormalization analysis",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex with: prompt='Analyze if denormalization would help the queries in src/db/queries.ts. Show potential schema changes and trade-offs.', sandbox='read-only'"
}
```

**Retrieve all results:**
```json
{"task_id": "task_query_opt", "block": true}
{"task_id": "task_caching", "block": true}
{"task_id": "task_denorm", "block": true}
```

**Present comparison** to user with pros/cons of each approach.

---

### Example 10: Second Opinion Implementation

**Scenario**: User asks to implement a feature. Get Codex's implementation while you do your own, then compare.

**Spawn background Codex implementation:**
```json
{
  "description": "Codex implements rate limiter",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex with: prompt='Implement a rate limiter middleware for Express in src/middleware/rateLimit.ts. Requirements: 100 requests per minute per IP, return 429 on limit, use Redis for distributed state. Write the implementation.', sandbox='read-only'. Return the generated code and explanation."
}
```

**Implement your own version** using Edit/Write tools.

**Retrieve Codex version:**
```json
{"task_id": "task_rate_limiter", "block": true}
```

**Compare and present** both implementations to user:
- Your approach: [advantages/disadvantages]
- Codex approach: [advantages/disadvantages]
- Recommendation: [which to use or hybrid]

---

### Example 11: Continuous Review During Long Implementation

**Scenario**: Implementing a large feature across multiple files. Have Codex review completed parts while you continue.

**After completing auth module:**
```json
{
  "description": "Codex reviews auth module",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex to review the authentication module I just implemented in src/auth/. Check for security issues and suggest improvements. sandbox='read-only'"
}
```
Save: `auth_review_id`

**Continue implementing user module...**

**After completing user module, check auth review:**
```json
{"task_id": "auth_review_id", "block": false}  // non-blocking check
```

If complete, incorporate feedback. If not, continue and check later.

**Spawn user module review:**
```json
{
  "description": "Codex reviews user module",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex to review src/users/. sandbox='read-only'"
}
```

**Continue this pattern** throughout the implementation session.

---

### Example 12: Codex Implements While You Write Tests

**Scenario**: Parallel workflow - Codex implements the feature while you write tests for it.

**Spawn Codex implementation:**
```json
{
  "description": "Codex implements email service",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__codex__codex with: prompt='Implement an email service in src/services/email.ts with: sendWelcomeEmail, sendPasswordReset, sendNotification. Use nodemailer. Include retry logic and logging.', sandbox='workspace-write', approval-policy='on-failure'"
}
```

**Write tests yourself:**
```typescript
// src/services/__tests__/email.test.ts
describe('EmailService', () => {
  it('should send welcome email with correct template', ...);
  it('should retry on transient failures', ...);
  it('should log all email attempts', ...);
});
```

**Retrieve Codex implementation:**
```json
{"task_id": "task_email_impl", "block": true}
```

**Verify tests pass** with Codex's implementation. Fix any mismatches.

---

## Prompt Structure Tips

**Good prompt structure:**
```
[TASK]: What you want done
[CONTEXT]: Relevant files, patterns, constraints
[ACCEPTANCE CRITERIA]: How to know it's done
[CONSTRAINTS]: What NOT to do
```

**Example:**
```
TASK: Add input validation to the user registration endpoint

CONTEXT:
- Endpoint: src/api/auth/register.ts
- Use zod for validation (already installed)
- Follow the pattern in src/api/auth/login.ts

ACCEPTANCE CRITERIA:
- Validate email format
- Password min 8 chars, must include number and special char
- Username alphanumeric only, 3-20 chars
- Return 400 with clear error messages on validation failure

CONSTRAINTS:
- Don't modify the database schema
- Keep the existing response format
```

---

## Named Sessions Examples

### Example 13: Named Session for Later Reference

**Scenario**: Start a security review session that you'll want to reference later.

```json
{
  "prompt": "Perform a comprehensive security review of the authentication and authorization code in src/auth/. Focus on: OWASP Top 10 vulnerabilities, session management, password handling, and access control. Document all findings.",
  "sandbox": "read-only",
  "name": "auth-security-audit-jan2026",
  "reasoningEffort": "high"
}
```

**Later, when user asks**: "What did Codex find in that security review?"

**Search by name:**
```json
// mcp__codex__codex-bridge-sessions
{
  "query": "security-audit"
}
```

**Continue the conversation:**
```json
{
  "conversationId": "<from search results>",
  "prompt": "What were the most critical findings from your review?"
}
```

---

### Example 14: Naming Sessions After Creation

**Scenario**: You started a productive session but forgot to name it.

**Name the session retroactively:**
```json
// mcp__codex__codex-bridge-name-session
{
  "conversationId": "abc123",
  "name": "payment-refactor-discussion"
}
```

---

### Example 15: Multiple Named Sessions for a Project

**Scenario**: Working on a major feature with several Codex discussions.

**Architecture discussion:**
```json
{
  "prompt": "Let's discuss the architecture for the new notification system...",
  "sandbox": "read-only",
  "name": "notifications-architecture"
}
```

**Implementation session:**
```json
{
  "prompt": "Implement the notification system based on our architecture discussion...",
  "sandbox": "workspace-write",
  "name": "notifications-implementation"
}
```

**Review session:**
```json
{
  "prompt": "Review the notification system implementation for issues...",
  "sandbox": "read-only",
  "name": "notifications-review"
}
```

**Search all related sessions:**
```json
{
  "query": "notifications"
}
```

Returns all three sessions for easy reference and continuation.
