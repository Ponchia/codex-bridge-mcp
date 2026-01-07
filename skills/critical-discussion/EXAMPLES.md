# Critical Discussion Examples

Top 3 canonical examples. For more, see [examples/](../../examples/README.md).

---

## Example 1: Architecture Decision

```json
{
  "prompt": "TOPIC: Microservices vs monolith for e-commerce platform\n\nCONTEXT:\n- Team of 5 developers\n- 10k DAU initially, scaling to 100k\n- Django experience\n- Budget constraints\n\nQUESTIONS:\n1. Operational complexity trade-offs?\n2. Time-to-market impact?\n3. Scaling implications?\n\nDESIRED OUTPUT:\n- Pros/cons comparison\n- Recommendation with justification\n- Risk assessment",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/ecommerce-platform #architecture"
}
```

---

## Example 2: Security Trade-off Analysis

```json
{
  "prompt": "TOPIC: JWT vs opaque session tokens\n\nCONTEXT:\n- API serving web + mobile apps\n- Regulatory requirement for immediate session revocation\n- High-traffic endpoints\n- Users sometimes share devices\n\nANALYZE:\n1. Security implications\n2. Scalability/performance\n3. Token revocation strategies\n4. Compliance with revocation requirements\n\nDESIRED OUTPUT:\n- Security comparison matrix\n- Hybrid approach recommendations\n- Compliance checklist",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/auth-tokens #jwt #security"
}
```

---

## Example 3: Multi-turn Discussion

**Start:**
```json
{
  "prompt": "TOPIC: Event sourcing vs CRUD for order management\n\nCONTEXT:\n- 10k orders/day\n- Need complete audit trail\n- Multiple systems consume order events\n\nStart with: fundamental trade-offs?",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "arch/order-system #eventsourcing"
}
```

**Continue:**
```json
{
  "conversationId": "<from above>",
  "prompt": "You mentioned eventual consistency challenges. Elaborate on:\n1. Specific problem scenarios?\n2. Mitigation strategies?\n3. How do other e-commerce platforms handle this?"
}
```

**Get recommendation:**
```json
{
  "conversationId": "<same>",
  "prompt": "Given our constraints (small team, PostgreSQL, need rapid iteration), what's your final recommendation with implementation phases?"
}
```
