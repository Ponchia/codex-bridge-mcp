# Codex Bridge Examples

## Example 1: Delegate - Implement Feature

**User**: "Implement a rate limiter middleware for our Express API"

**Claude's workflow**:

```
1. Confirm requirements:
   - Max requests: 100/minute per IP
   - Storage: Redis
   - Response on limit: 429 with Retry-After header

2. Call codex tool:
```

```json
{
  "prompt": "TASK: Implement rate limiter middleware for Express API\n\nCONTEXT:\n- Express 4.x app in src/\n- Redis client already configured at src/lib/redis.ts\n- Middleware pattern: src/middleware/*.ts\n\nREQUIREMENTS:\n- 100 requests/minute per IP\n- Use sliding window algorithm\n- Return 429 with Retry-After header\n- Log rate limit hits\n\nACCEPTANCE CRITERIA:\n- Middleware exports from src/middleware/rateLimiter.ts\n- Unit tests in src/middleware/__tests__/rateLimiter.test.ts\n- Integration with existing error handler\n\nCONSTRAINTS:\n- Don't modify existing routes\n- Follow existing TypeScript patterns",
  "model": "gpt-5.2-codex",
  "reasoningEffort": "high",
  "sandbox": "workspace-write",
  "approval-policy": "on-failure",
  "name": "impl/rate-limiter #middleware #redis"
}
```

```
3. Verify:
   git diff
   npm test -- rateLimiter

4. Report implementation summary + test results
```

---

## Example 2: Discuss - Architecture Decision (True Parallel)

**User**: "Should we use microservices or monolith for our e-commerce platform?"

**Claude's workflow**:

```
Step 1: Dispatch Codex in background (Task tool)
```

```json
{
  "description": "Codex analyzes microservices vs monolith",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with these parameters:\n- prompt: 'TOPIC: Microservices vs monolith for e-commerce platform\n\nCONTEXT:\n- Team of 5 developers\n- 10k DAU initially, scaling to 100k\n- Django experience\n- Budget constraints\n\nANALYSIS REQUIRED:\n1. Key considerations\n2. Trade-offs\n3. Risks and mitigations\n4. Your recommendation with rationale\n\nBe thorough and cite your reasoning.'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- name: 'arch/ecommerce-architecture #microservices #monolith'\n\nReturn the full tool response."
}
```

**Response**: `task_id: "abc123"` - Codex now running in background

```
Step 2: Claude analyzes immediately (no waiting!)

Claude's analysis:
- Team size (5) suggests monolith - microservices operational overhead too high
- Django is excellent for monolith with clear module boundaries
- 10k→100k DAU is achievable with monolith + caching
- Budget constraints favor simpler infrastructure
- Recommendation: Modular monolith with event-driven internals
```

```
Step 3: Retrieve Codex result (TaskOutput tool)
```

```json
{ "task_id": "abc123", "block": true, "timeout": 300000 }
```

**Codex response**: Recommends monolith, cites team size as primary factor, suggests clear module boundaries for future extraction.

```
Step 4: Synthesize
```

```markdown
## Discussion: Microservices vs Monolith

### Codex Position
Recommends monolith with clear module boundaries. Primary factor: team of 5 cannot sustain microservices operational overhead. Suggests Django's app structure naturally supports modular design.

### Claude Position
Agrees on monolith. Adds: use event-driven internal communication between modules. This preserves extraction option without current complexity.

### Agreements (High Confidence)
- Start with monolith given team size
- Django is appropriate choice
- Plan for future decomposition via clear boundaries

### Points of Difference
- Codex: Simple Django apps sufficient
- Claude: Add internal event bus for loose coupling
- Resolution: Event bus adds minimal overhead, significantly improves future flexibility

### Shared Conclusion
Build a **modular monolith** using Django. Use internal events between modules (e.g., django-eventtools or simple signals). This preserves the option to extract services later without premature complexity.

### Next Steps
1. Define module boundaries (users, catalog, orders, payments)
2. Set up internal event contracts
3. Document extraction triggers (team size >15, or single module needs independent scaling)

### Session Info
Codex session: arch/ecommerce-architecture (conversationId: xyz789)
```

---

## Example 3: Research - Current Best Practices (True Parallel)

**User**: "What are the current best practices for JWT token rotation?"

**Claude's workflow (Option A: Background Task)**:

```
Step 1: Dispatch Codex research in background
```

```json
{
  "description": "Codex researches JWT rotation",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use the mcp__codex__codex tool with:\n- prompt: 'RESEARCH TOPIC: JWT token rotation best practices 2025\n\nCONTEXT:\n- Building auth for web API\n- Need balance of security and UX\n\nINSTRUCTIONS:\nResearch thoroughly. For each finding, note source and confidence.\n\nOUTPUT:\n- Key findings with sources\n- Confidence levels\n- Gaps/unknowns'\n- model: 'gpt-5.2'\n- reasoningEffort: 'xhigh'\n- sandbox: 'read-only'\n- config: {\"web_search_request\": true}\n- name: 'research/jwt-rotation #security #auth'\n\nReturn the full response."
}
```

**Response**: `task_id: "def456"` - Codex researching in background

```
Step 2: Claude researches immediately with WebSearch
```

```json
{ "query": "JWT token rotation best practices 2025" }
{ "query": "refresh token rotation security OWASP" }
{ "query": "auth0 okta token lifetime recommendations" }
```

**Claude's findings**:
- OWASP recommends 5-15 min access token lifetime for high-security
- Refresh token rotation on every use (rotate refresh tokens)
- Reuse detection: invalidate entire family if old token reused
- Sources: OWASP ASVS, Auth0 docs, RFC 6749 bis

```
Step 3: Retrieve Codex result
```

```json
{ "task_id": "def456", "block": true, "timeout": 600000 }
```

**Codex's findings**:
- 15-60 min access token recommended (Auth0)
- Sliding window refresh for UX
- Bound refresh tokens to device fingerprint
- Sources: Auth0, Okta, recent security blogs

```
Step 4: Merge findings
```

```markdown
## Research: JWT Token Rotation

### Merged Findings

#### Access Token Lifetime
- **Codex**: 15-60 minutes (Auth0 docs)
- **Claude**: 5-15 minutes for high-security (OWASP ASVS)
- **Confidence**: High (both agree on short lifetimes, OWASP more conservative)

#### Refresh Token Rotation
- **Codex**: Rotate on every use
- **Claude**: Same + reuse detection (invalidate family)
- **Confidence**: High

#### Device Binding
- **Codex**: Bind to device fingerprint
- **Claude**: Not explicitly found
- **Confidence**: Medium (Codex-only finding)

### Agreements
- Short access token lifetimes (under 60 min)
- Refresh token rotation mandatory
- Consider sliding window for UX

### Unique Insights
- **From Codex**: Device fingerprint binding, sliding window UX pattern
- **From Claude**: Reuse detection + family invalidation, RFC 6749 bis updates

### Gaps
- Specific guidance for mobile vs web differs by source
- Token binding (DPoP) adoption unclear

### Sources
- OWASP ASVS, Auth0 docs, Okta best practices, RFC 6749 bis

### Session Info
Codex session: research/jwt-rotation (conversationId: uvw012)
```

---

## Example 4: Research (Option B: Parallel Tool Calls)

**User**: "What's new in React 19?"

**Claude's workflow**: Make BOTH calls in a single message:

```
Both tools called in parallel (single message):
```

**Tool call 1**:
```json
// mcp__codex__codex
{
  "prompt": "RESEARCH: What's new in React 19?\n\nFind: new features, breaking changes, migration considerations.\nInclude sources.",
  "model": "gpt-5.2",
  "reasoningEffort": "high",
  "sandbox": "read-only",
  "config": { "web_search_request": true },
  "name": "research/react-19 #react #frontend"
}
```

**Tool call 2**:
```json
// WebSearch
{ "query": "React 19 new features release notes 2025" }
```

**Both return simultaneously**, then merge findings.

---

## Example 5: Direct - Continue Session

**User**: "Continue my auth architecture discussion"

```json
// codex-bridge-sessions - find the session
{ "query": "auth", "limit": 5 }
```

**Response**: Found `arch/auth-tokens #jwt #security` (conversationId: abc789)

```json
// codex-reply - continue the conversation
{
  "conversationId": "abc789",
  "prompt": "Based on our shared conclusion to use JWT with refresh rotation, detail:\n1. Specific implementation steps\n2. Token storage strategy (httpOnly cookies vs memory)\n3. Logout/revocation approach"
}
```

---

## Example 6: Multi-turn with Context Recall

**User**: "What did we decide about the database architecture?"

```
Step 1: Search sessions
```

```json
{ "query": "database", "limit": 10 }
```

**Found**: `arch/database-schema #postgres #scaling`

```
Step 2: Request structured recall
```

```json
{
  "conversationId": "<found id>",
  "prompt": "RECALL\n\nSummarize our discussion and decisions.\n\nOutput:\n1) Recap (2-4 sentences)\n2) Key Decisions\n3) Open Questions\n4) Next Steps"
}
```

**Return**: Structured summary to user with session reference.
