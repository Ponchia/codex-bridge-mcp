# Critical Discussion Examples

Examples of using GPT 5.2 (base model) with maximum reasoning effort for analysis and discussion tasks.

---

## Example 1: Architecture Decision

**Scenario**: Deciding between microservices and monolith for a new project.

```json
{
  "prompt": "TOPIC: Should we use microservices or monolith architecture for our new e-commerce platform?\n\nCONTEXT:\n- Team of 5 developers\n- Expected 10k daily active users initially, scaling to 100k in 2 years\n- Need to integrate with 3 payment providers\n- Budget constraints require cost-effective infrastructure\n- Team has Django experience\n\nSPECIFIC QUESTIONS:\n1. What are the operational complexity trade-offs?\n2. How does each approach affect time-to-market?\n3. What are the scaling implications?\n4. Which approach better handles payment provider integrations?\n5. What's the cost comparison for infrastructure?\n\nDESIRED OUTPUT:\n- Detailed pros/cons comparison table\n- Recommendation with justification\n- Risk assessment for each option\n- Suggested hybrid approaches if applicable",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "ecommerce-architecture-decision"
}
```

---

## Example 2: Design Pattern Evaluation

**Scenario**: Choosing between Repository and Active Record patterns for data access.

```json
{
  "prompt": "TOPIC: Repository pattern vs Active Record for our data access layer\n\nCONTEXT:\n- Python/FastAPI application\n- PostgreSQL database\n- Complex domain with 15+ entities\n- Need extensive unit testing\n- Team familiar with Django (Active Record style)\n- Planning to add GraphQL in 6 months\n\nSPECIFIC QUESTIONS:\n1. How does each pattern affect testability?\n2. What are the maintenance implications as the domain grows?\n3. How does each handle complex queries and joins?\n4. Learning curve considerations for the team?\n5. How does each pattern work with GraphQL resolvers?\n\nDESIRED OUTPUT:\n- Pattern comparison matrix\n- Code structure examples for each approach\n- Testing strategy implications\n- Migration path recommendations",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "data-access-pattern-evaluation"
}
```

---

## Example 3: Security Trade-off Analysis

**Scenario**: Evaluating authentication approaches for a multi-platform API.

```json
{
  "prompt": "TOPIC: JWT vs Session-based authentication trade-offs\n\nCONTEXT:\n- API serving both web app and mobile apps\n- Users may be on unreliable networks (frequent disconnects)\n- Regulatory requirement for immediate session revocation capability\n- Performance is critical (high-traffic endpoints)\n- Users sometimes share devices\n\nANALYZE:\n1. Security implications of each approach\n2. Scalability and performance considerations\n3. Token/session revocation strategies and their trade-offs\n4. Network reliability handling\n5. Compliance with session revocation requirements\n\nDESIRED OUTPUT:\n- Security comparison matrix\n- Implementation complexity assessment\n- Hybrid approach recommendations\n- Compliance checklist",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "auth-security-analysis"
}
```

---

## Example 4: API Design Discussion

**Scenario**: Choosing between REST and GraphQL for a new API.

```json
{
  "prompt": "TOPIC: REST vs GraphQL for our customer-facing API\n\nCONTEXT:\n- Building API for web dashboard and mobile app\n- 50+ endpoints planned\n- Multiple frontend teams with different data needs\n- Some endpoints need real-time updates\n- Team has REST experience, limited GraphQL\n\nQUESTIONS:\n1. How do over-fetching/under-fetching compare?\n2. What's the caching story for each?\n3. How do subscriptions/real-time work?\n4. What are the tooling and debugging differences?\n5. How does each affect API versioning?\n\nOUTPUT:\n- Feature comparison table\n- Team adoption considerations\n- Suggested approach with timeline",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "api-design-discussion"
}
```

---

## Example 5: Multi-turn Discussion

**Scenario**: Deep dive into a complex topic across multiple exchanges.

### Step 1: Initial discussion
```json
{
  "prompt": "TOPIC: Event sourcing vs traditional CRUD for our order management system\n\nCONTEXT:\n- E-commerce platform processing 10k orders/day\n- Need complete audit trail\n- Complex order state machine\n- Multiple systems consume order events\n\nStart with: What are the fundamental trade-offs?",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "order-system-architecture"
}
```

### Step 2: Deep dive on specific aspect
```json
{
  "conversationId": "abc123",
  "prompt": "You mentioned eventual consistency challenges with event sourcing. Can you elaborate on:\n1. Specific scenarios where this causes problems in order management?\n2. Mitigation strategies and their trade-offs?\n3. How do other e-commerce platforms handle this?"
}
```

### Step 3: Explore implementation details
```json
{
  "conversationId": "abc123",
  "prompt": "Let's focus on the event store implementation:\n1. Should we use a dedicated event store (EventStoreDB) or build on PostgreSQL?\n2. What are the operational implications of each?\n3. How do we handle schema evolution for events?"
}
```

### Step 4: Get final recommendations
```json
{
  "conversationId": "abc123",
  "prompt": "Given our constraints (small team, need rapid iteration, existing PostgreSQL infrastructure), what's your final recommendation?\n\nProvide:\n1. Recommended approach\n2. Implementation phases\n3. Key risks and mitigations\n4. Success metrics"
}
```

---

## Example 6: Database Selection

**Scenario**: Choosing a database for a new feature.

```json
{
  "prompt": "TOPIC: Database selection for real-time analytics feature\n\nCONTEXT:\n- Need to store and query user behavior events\n- 100M+ events per day expected\n- Queries: time-series aggregations, funnel analysis, user segmentation\n- Need sub-second query response for dashboards\n- Current stack: PostgreSQL, Redis\n\nOPTIONS TO EVALUATE:\n1. PostgreSQL with TimescaleDB extension\n2. ClickHouse\n3. Apache Druid\n4. Elasticsearch\n\nEVALUATE:\n- Query performance for our use cases\n- Operational complexity\n- Integration with existing stack\n- Cost at our scale\n- Team learning curve",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "analytics-database-selection"
}
```

---

## Example 7: Finding and Resuming Past Discussions

**Search by topic:**
```json
// mcp__plugin_codex-bridge_codex__codex-bridge-sessions
{
  "query": "architecture"
}
```

**View session details:**
```json
// mcp__plugin_codex-bridge_codex__codex-bridge-session
{
  "conversationId": "abc123"
}
```

**Resume a past discussion:**
```json
// mcp__plugin_codex-bridge_codex__codex-reply
{
  "conversationId": "abc123",
  "prompt": "We're revisiting this decision 3 months later. Given what we've learned:\n- The team grew to 8 developers\n- Traffic is 3x higher than expected\n\nShould we reconsider our original choice?"
}
```

---

## Example 8: Risk Assessment

**Scenario**: Evaluating risks of a major refactoring effort.

```json
{
  "prompt": "TOPIC: Risk assessment for migrating from JavaScript to TypeScript\n\nCONTEXT:\n- 150k lines of JavaScript code\n- 5 developers, 2 with TypeScript experience\n- Active development (20+ PRs/week)\n- No comprehensive test suite (30% coverage)\n- Customer-facing product, high availability requirements\n\nASSESS:\n1. What could go wrong during migration?\n2. What's the realistic timeline?\n3. How do we minimize production risk?\n4. Should we do big-bang or incremental?\n5. What's the opportunity cost?\n\nOUTPUT:\n- Risk matrix (likelihood vs impact)\n- Mitigation strategies for top risks\n- Go/no-go recommendation\n- If go: phased approach with milestones",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "typescript-migration-risk"
}
```

---

## Example 9: Technical Debt Prioritization

**Scenario**: Deciding which technical debt to address first.

```json
{
  "prompt": "TOPIC: Technical debt prioritization for Q1\n\nTECHNICAL DEBT INVENTORY:\n1. Legacy authentication system (security concerns, hard to extend)\n2. Monolithic frontend (slow builds, difficult testing)\n3. Manual deployment process (error-prone, slow)\n4. Outdated dependencies (some with known CVEs)\n5. No API documentation (onboarding friction)\n6. Inconsistent error handling (poor debugging)\n\nCONSTRAINTS:\n- 1 developer can be allocated to tech debt\n- Q1 = 12 weeks\n- Need to show measurable impact to stakeholders\n\nHELP ME:\n1. Prioritize these items\n2. Estimate effort for each\n3. Identify quick wins\n4. Create a Q1 roadmap\n5. Define success metrics for each item",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "q1-tech-debt-planning"
}
```

---

## Example 10: Testing Strategy Discussion

**Scenario**: Designing a testing strategy for a new project.

```json
{
  "prompt": "TOPIC: Testing strategy for our new microservices platform\n\nCONTEXT:\n- 5 microservices communicating via REST and events\n- Each service has its own database\n- Services: User, Order, Inventory, Payment, Notification\n- CI/CD pipeline with GitHub Actions\n- Team of 8, mixed testing experience\n\nQUESTIONS:\n1. What's the right balance of unit/integration/e2e tests?\n2. How do we test inter-service communication?\n3. Contract testing: do we need it? Which tool?\n4. How do we handle test data across services?\n5. What should block deployments vs run async?\n\nOUTPUT:\n- Testing pyramid recommendation\n- Tool recommendations for each layer\n- CI pipeline design\n- Test data strategy",
  "model": "gpt-5.2",
  "reasoningEffort": "xhigh",
  "sandbox": "read-only",
  "name": "microservices-testing-strategy"
}
```
