# Coding Delegation Examples

Examples of using GPT 5.2 Codex with maximum reasoning effort for autonomous code implementation.

---

## Example 1: Feature Implementation

**Scenario**: Adding caching to an API endpoint.

```json
{
  "prompt": "TASK: Add Redis caching to the /api/users endpoint\n\nCONTEXT:\n- Endpoint location: src/api/users.ts\n- Redis connection: src/lib/redis.ts (already configured)\n- Follow caching patterns in src/api/products.ts (already has caching)\n\nREQUIREMENTS:\n- Cache user data for 5 minutes (TTL: 300s)\n- Cache key format: user:{id}\n- Handle cache misses gracefully (fall back to DB)\n- Add cache invalidation on user update/delete\n- Log cache hits/misses for monitoring\n\nACCEPTANCE CRITERIA:\n- GET /api/users/:id returns cached data when available\n- Cache invalidates on PUT /api/users/:id\n- Cache invalidates on DELETE /api/users/:id\n- Existing tests still pass\n- Add new tests for caching behavior\n\nCONSTRAINTS:\n- Don't modify the User model schema\n- Keep existing response format unchanged\n- Don't break existing API consumers",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "users-caching-impl"
}
```

---

## Example 2: Writing Tests

**Scenario**: Generating comprehensive unit tests for a utility module.

```json
{
  "prompt": "TASK: Generate comprehensive unit tests for src/utils/validation.ts\n\nCONTEXT:\n- Test framework: Jest\n- Test file location: src/utils/__tests__/validation.test.ts\n- Follow test patterns in src/utils/__tests__/formatting.test.ts\n- Module exports: validateEmail, validatePhone, validatePassword, validateUsername\n\nREQUIREMENTS:\n- Test all exported functions\n- Cover edge cases: null, undefined, empty strings, whitespace\n- Cover boundary conditions (min/max lengths)\n- Test error cases and error messages\n- Test valid inputs return expected results\n- Use descriptive test names\n\nACCEPTANCE CRITERIA:\n- 100% function coverage\n- All tests pass\n- Tests are readable and maintainable\n- Each function has at least 5 test cases",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "validation-tests"
}
```

---

## Example 3: Refactoring

**Scenario**: Converting callback-based code to async/await.

```json
{
  "prompt": "TASK: Refactor src/services/payment.js from callbacks to async/await\n\nCONTEXT:\n- 12 functions currently use callbacks\n- Some functions chain multiple callbacks (3-4 deep)\n- Module is imported by: src/api/checkout.js, src/api/subscriptions.js\n- No TypeScript, staying with JavaScript\n\nREQUIREMENTS:\n- Convert all callback-based functions to async/await\n- Maintain the same public API (exported function names)\n- Preserve all existing functionality\n- Add proper try/catch error handling\n- Replace callback error patterns with thrown errors\n\nACCEPTANCE CRITERIA:\n- All functions use async/await\n- No nested callbacks remain\n- All existing tests pass (may need updates for async)\n- Error handling is consistent\n\nCONSTRAINTS:\n- Don't change function names in the public API\n- Don't add TypeScript\n- Keep backward compatibility where possible",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "timeoutMs": 300000,
  "name": "payment-async-refactor"
}
```

---

## Example 4: Bug Fix

**Scenario**: Fixing an authentication timeout issue.

```json
{
  "prompt": "TASK: Fix the authentication bug in src/auth/middleware.ts\n\nBUG DESCRIPTION:\n- Users get logged out randomly after 10-15 minutes\n- Error in logs: 'TokenExpiredError: jwt expired'\n- Expected behavior: Sessions should last 24 hours\n- Started happening after recent deployment\n\nCONTEXT:\n- Token generation: src/auth/tokens.ts\n- Middleware: src/auth/middleware.ts\n- Config: src/config/auth.ts\n- Recent changes: Updated jsonwebtoken library version\n\nREQUIREMENTS:\n- Identify the root cause\n- Fix the issue so tokens last 24 hours\n- Add a regression test\n- Document the fix in code comments\n\nACCEPTANCE CRITERIA:\n- Tokens correctly expire after 24 hours\n- No more random logouts\n- Test verifies token expiration behavior",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "auth-timeout-bugfix"
}
```

---

## Example 5: API Endpoint Creation

**Scenario**: Creating a new REST API endpoint.

```json
{
  "prompt": "TASK: Create POST /api/orders endpoint for order creation\n\nCONTEXT:\n- Router: src/api/index.ts\n- Existing patterns: src/api/users.ts, src/api/products.ts\n- Database: src/db/models/Order.ts (already exists)\n- Validation: use zod schemas in src/schemas/\n\nREQUIREMENTS:\n- Accept JSON body with: userId, items[], shippingAddress\n- Validate all inputs with zod schema\n- Calculate total from item prices\n- Create order in database\n- Return created order with 201 status\n- Handle validation errors with 400\n- Handle not found (user, products) with 404\n\nACCEPTANCE CRITERIA:\n- Endpoint accessible at POST /api/orders\n- Input validation works correctly\n- Order is persisted to database\n- Response matches existing API patterns\n- Add integration tests\n\nCONSTRAINTS:\n- Follow existing error handling patterns\n- Use existing middleware for auth\n- Match response format of other endpoints",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "orders-endpoint-impl"
}
```

---

## Example 6: Code Review (Read-Only Mode)

**Scenario**: Getting a code review without modifications.

```json
{
  "prompt": "TASK: Review src/services/payment.ts for issues\n\nREVIEW FOR:\n1. Security issues (input validation, authentication, authorization)\n2. Error handling gaps (unhandled exceptions, missing try/catch)\n3. Performance concerns (N+1 queries, unnecessary loops)\n4. Code quality issues (complexity, duplication, naming)\n5. Potential bugs (race conditions, null references)\n\nOUTPUT FORMAT:\n- List findings by severity: CRITICAL, HIGH, MEDIUM, LOW\n- Include file:line references for each finding\n- Suggest specific fixes for each issue\n- Prioritize findings by impact",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "payment-code-review"
}
```

---

## Example 7: Background Delegation with Review

**Scenario**: Running a long implementation task while continuing other work.

### Step 1: Spawn background implementation
```json
// Use the Task tool
{
  "description": "Codex implements email service",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__plugin_codex-bridge_codex__codex tool with these parameters:\n- prompt: 'TASK: Implement email service in src/services/email.ts\n\nREQUIREMENTS:\n- sendWelcome(userId): Send welcome email to new users\n- sendPasswordReset(userId, token): Send password reset link\n- sendNotification(userId, message): Send general notification\n- Use nodemailer with SMTP config from env vars\n- Include retry logic (3 attempts with exponential backoff)\n- Add proper error handling and logging\n\nCONTEXT:\n- Config: src/config/email.ts\n- Templates: src/templates/email/\n\nACCEPTANCE CRITERIA:\n- All three functions implemented\n- Retry logic works correctly\n- Unit tests for each function'\n- model: 'gpt-5.2-codex'\n- reasoningEffort: 'xhigh'\n- sandbox: 'workspace-write'\n- approval-policy: 'on-failure'\n- name: 'email-service-impl'"
}
```

### Step 2: Continue working on other tasks while Codex runs

### Step 3: Retrieve results when needed
```json
// Use TaskOutput tool
{
  "task_id": "<agent_id from step 1>",
  "block": true
}
```

### Step 4: Review the implementation
```bash
git diff
npm test
```

---

## Example 8: Multi-turn Implementation

**Scenario**: Building a feature incrementally across multiple interactions.

### Step 1: Create the basic structure
```json
{
  "prompt": "TASK: Create the foundation for a notification system\n\nCREATE:\n1. src/services/notifications/NotificationService.ts - main service class\n2. src/services/notifications/types.ts - TypeScript interfaces\n3. src/services/notifications/index.ts - exports\n\nSTRUCTURE:\n- NotificationService class with constructor taking config\n- Methods: send(), sendBatch(), getHistory()\n- Types: Notification, NotificationConfig, NotificationResult",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "notification-system"
}
```

### Step 2: Add specific channel implementations
```json
{
  "conversationId": "abc123",
  "prompt": "Now add channel implementations:\n1. src/services/notifications/channels/EmailChannel.ts\n2. src/services/notifications/channels/SlackChannel.ts\n3. src/services/notifications/channels/SMSChannel.ts\n\nEach channel should:\n- Implement a common NotificationChannel interface\n- Handle channel-specific configuration\n- Include retry logic"
}
```

### Step 3: Add tests
```json
{
  "conversationId": "abc123",
  "prompt": "Add comprehensive tests:\n1. src/services/notifications/__tests__/NotificationService.test.ts\n2. src/services/notifications/__tests__/channels.test.ts\n\nTest:\n- Service initialization\n- Each channel independently\n- Error handling and retries\n- Batch sending"
}
```

---

## Example 9: Database Migration

**Scenario**: Creating a database schema change.

```json
{
  "prompt": "TASK: Add soft delete to the users table\n\nCONTEXT:\n- Database: PostgreSQL\n- ORM: Prisma\n- Schema: prisma/schema.prisma\n- Existing User model has: id, email, name, createdAt, updatedAt\n\nREQUIREMENTS:\n1. Add deletedAt column (nullable timestamp)\n2. Create migration file\n3. Update User model queries to filter out deleted users by default\n4. Add soft delete method to user service\n5. Add restore method to recover deleted users\n\nFILES TO MODIFY:\n- prisma/schema.prisma\n- src/services/userService.ts\n- src/db/queries/users.ts\n\nACCEPTANCE CRITERIA:\n- Migration runs without errors\n- Existing queries exclude soft-deleted users\n- Admin can still query deleted users explicitly\n- Tests cover soft delete and restore",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "users-soft-delete"
}
```

---

## Example 10: TypeScript Migration

**Scenario**: Converting a JavaScript file to TypeScript.

```json
{
  "prompt": "TASK: Convert src/utils/helpers.js to TypeScript\n\nCONTEXT:\n- Target file: src/utils/helpers.js -> src/utils/helpers.ts\n- tsconfig.json is already configured with strict mode\n- Other utils in the folder are already TypeScript\n\nREQUIREMENTS:\n1. Add proper type annotations to all functions\n2. Add interfaces for complex parameter/return types\n3. Fix any type errors that strict mode reveals\n4. Add JSDoc comments for public functions\n5. Export types that consumers might need\n\nACCEPTANCE CRITERIA:\n- No TypeScript errors (tsc --noEmit passes)\n- No 'any' types used\n- All existing tests pass\n- Types are exported for external use",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "helpers-ts-migration"
}
```

---

## Example 11: Finding and Resuming Past Sessions

**Search by name:**
```json
// mcp__plugin_codex-bridge_codex__codex-bridge-sessions
{
  "query": "impl"
}
```

**Continue a previous implementation:**
```json
// mcp__plugin_codex-bridge_codex__codex-reply
{
  "conversationId": "abc123",
  "prompt": "The tests are failing with this error:\n\nError: Cannot find module './channels/EmailChannel'\n\nPlease fix the import paths."
}
```

---

## Example 12: Component Generation

**Scenario**: Creating a React component with all supporting files.

```json
{
  "prompt": "TASK: Create a UserProfile React component\n\nCONTEXT:\n- Location: src/components/UserProfile/\n- Use existing patterns from src/components/ProductCard/\n- Styling: Tailwind CSS\n- State: React Query for data fetching\n\nCREATE FILES:\n1. src/components/UserProfile/UserProfile.tsx - main component\n2. src/components/UserProfile/UserProfile.types.ts - TypeScript types\n3. src/components/UserProfile/UserProfile.test.tsx - tests\n4. src/components/UserProfile/index.ts - exports\n\nCOMPONENT REQUIREMENTS:\n- Display user avatar, name, email, bio\n- Loading skeleton while fetching\n- Error state with retry button\n- Edit button that opens modal (just the button, modal is separate)\n\nACCEPTANCE CRITERIA:\n- Component renders correctly with mock data\n- Loading state shows skeleton\n- Error state is testable\n- All tests pass",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "xhigh",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "user-profile-component"
}
```
