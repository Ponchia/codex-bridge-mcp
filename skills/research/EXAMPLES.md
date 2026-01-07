# Research Skill Examples (Dual-Model)

These examples show the dual-model research workflow where both Claude and Codex research in parallel.

---

## Example 1: Best Practices Research

**User request**: "What are the current best practices for JWT token rotation?"

**Step 1 - Dispatch Codex** (then proceed to Step 2 immediately):
```json
{
  "prompt": "RESEARCH TOPIC: JWT token rotation best practices in 2025\n\nCONTEXT:\n- Building authentication system for web API\n- Need to balance security with user experience\n\nINSTRUCTIONS:\nResearch thoroughly. For each finding, note source and confidence.\n\nOUTPUT:\n- Key findings with sources\n- Confidence levels\n- Gaps/unknowns",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "config": { "web_search_request": true },
  "name": "research/jwt-rotation #security #auth"
}
```

**Step 2 - Claude researches** (parallel):
- Search: "JWT token rotation best practices 2025"
- Search: "auth0 okta token lifetime recommendations"
- Search: "refresh token rotation security"

**Step 3 - Merged output**:
```markdown
## Research: JWT Token Rotation

### Merged Findings

#### Access Token Lifetime
- **Codex**: 15-60 minutes recommended (Auth0 docs)
- **Claude**: 5-15 minutes for high-security (OWASP)
- **Confidence**: High (both agree on short lifetimes)

#### Refresh Token Rotation
- **Codex**: Rotate on every use (refresh token rotation)
- **Claude**: Same finding + reuse detection pattern
- **Confidence**: High

### Unique Insights
- **From Codex**: Sliding window approach for UX
- **From Claude**: Recent RFC 6749 bis updates

### Sources
- Auth0 documentation, OWASP guidelines, RFC 6749
```

---

## Example 2: Technology Comparison

**User request**: "Compare Bun vs Node.js for production backend in 2025"

**Step 1 - Dispatch Codex**:
```json
{
  "prompt": "RESEARCH TOPIC: Bun vs Node.js for production backend 2025\n\nCONTEXT:\n- Evaluating runtime for new microservice\n- Team has Node.js experience\n\nINSTRUCTIONS:\nResearch production readiness, performance, ecosystem.\n\nOUTPUT:\n- Findings with sources and confidence\n- Gaps/unknowns",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "config": { "web_search_request": true },
  "name": "research/bun-vs-node #runtime #performance"
}
```

**Step 2 - Claude researches**:
- Search: "Bun production ready 2025"
- Search: "Bun vs Node.js benchmarks real world"
- Search: "companies using Bun production"

---

## Example 3: Documentation Lookup

**User request**: "What's the current way to do streaming responses in Next.js 15?"

**Step 1 - Dispatch Codex**:
```json
{
  "prompt": "RESEARCH TOPIC: Streaming responses in Next.js 15\n\nCONTEXT:\n- Building AI chat interface\n- Using App Router\n\nFOCUS ON:\n- Official API for streaming\n- Server Actions streaming\n- Edge vs Node runtime\n\nOUTPUT:\n- Findings with official doc links\n- Code patterns\n- Gotchas",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "config": { "web_search_request": true },
  "name": "research/nextjs-streaming #nextjs #streaming"
}
```

**Step 2 - Claude researches**:
- Search: "Next.js 15 streaming response API"
- Search: "Next.js App Router streaming server actions"
