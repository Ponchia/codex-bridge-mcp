# Critical Discussion Examples (Dual-Model)

These examples show the dual-model discussion workflow where both Claude and Codex analyze in parallel, then synthesize to a shared conclusion.

---

## Example 1: Architecture Decision

**User request**: "Should we use microservices or monolith for our e-commerce platform?"

**Step 1 - Dispatch Codex** (then proceed to Step 2 immediately):
```json
{
  "prompt": "TOPIC: Microservices vs monolith for e-commerce platform\n\nCONTEXT:\n- Team of 5 developers\n- 10k DAU initially, scaling to 100k\n- Django experience\n- Budget constraints\n\nANALYSIS REQUIRED:\n1. Key considerations\n2. Trade-offs\n3. Risks and mitigations\n4. Your recommendation with rationale",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/ecommerce-platform #architecture"
}
```

**Step 2 - Claude analyzes** (parallel):
- Consider team size vs operational complexity
- Evaluate Django's strengths for monolith
- Assess scaling requirements
- Form recommendation

**Step 3 - Synthesized output**:
```markdown
## Discussion: Microservices vs Monolith

### Codex Position
Recommends monolith with clear module boundaries. Cites team size (5) as
primary factor - microservices operational overhead too high.

### Claude Position
Agrees on monolith start. Suggests "modular monolith" pattern with
event-driven internal communication for future extraction.

### Agreements (High Confidence)
- Start with monolith given team size
- Django is appropriate choice
- Plan for future decomposition

### Points of Difference
- Codex: Simple monolith is fine
- Claude: Modular monolith with events
- Resolution: Modular approach adds minimal overhead, preserves options

### Shared Conclusion
Build a modular monolith using Django. Use internal events between modules.
This preserves the option to extract services later without premature complexity.
```

---

## Example 2: Security Trade-off

**User request**: "JWT vs session tokens for our new auth system?"

**Step 1 - Dispatch Codex**:
```json
{
  "prompt": "TOPIC: JWT vs opaque session tokens\n\nCONTEXT:\n- API serving web + mobile\n- Requirement for immediate session revocation\n- 100k DAU\n\nANALYSIS REQUIRED:\n1. Security implications\n2. Scalability trade-offs\n3. Revocation strategies\n4. Your recommendation",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/auth-tokens #jwt #security"
}
```

**Step 2 - Claude analyzes**:
- Evaluate JWT statelessness vs revocation requirement conflict
- Consider hybrid approaches
- Assess Redis session store scalability

---

## Example 3: Multi-turn Discussion

**Start with dual analysis**, then continue the Codex session:

**Initial dual analysis** (Steps 1-3 as above)

**Continue Codex session for deeper dive**:
```json
{
  "conversationId": "<from initial discussion>",
  "prompt": "Based on our shared conclusion, elaborate on:\n1. Specific implementation steps\n2. Migration path from current system\n3. Testing strategy for the transition"
}
```
