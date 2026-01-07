# Verification

When Claude delegates work to Codex, there's a risk of **diffusion of responsibility**: humans assume "the other AI checked it" and stop verifying.

This document defines the verification contract to prevent shipping unreviewed code.

## The Problem

```
User asks Claude --> Claude delegates to Codex --> Codex produces code
                                                         |
                                              Who verified this?
```

Without explicit verification, you get "unreviewed code with a reviewed vibe."

## The Contract

### Implementer (Codex) Must Return

1. **What changed**: Files modified, functions added/changed
2. **How to verify**: Commands to run (tests, lints, type checks)
3. **Results**: Output of verification commands, or why they couldn't run
4. **Assumptions**: What was assumed about requirements

### Reviewer (Claude or Human) Must Check

1. **API contracts**: Do changes match expected interfaces?
2. **Edge cases**: Are error paths handled?
3. **Security**: Input validation, auth, data exposure?
4. **Backwards compatibility**: Will existing code break?
5. **Evidence**: Did tests actually pass? (Don't trust "tests pass" without output)

## Verification Checklist

Use this for any delegated implementation:

```markdown
## Verification

- [ ] Reviewed `git diff` output
- [ ] Tests pass: `npm test` / `pytest` / etc.
- [ ] Type check passes: `tsc --noEmit` / `mypy` / etc.
- [ ] Linter passes: `eslint` / `ruff` / etc.
- [ ] No new security issues (auth, validation, data exposure)
- [ ] Backwards compatible (or breaking changes documented)
- [ ] Assumptions validated with user
```

## When to Be Extra Careful

Require explicit human review for:

- Authentication/authorization changes
- Payment/financial code
- Data deletion or migration
- External API integrations
- Security-sensitive operations
- Changes to CI/CD or deployment

## The Independence Illusion

Two AIs agreeing doesn't mean correctness. Model errors are **correlated**, not independent.

Real independence comes from:
- Automated tests with good coverage
- Type systems and linters
- Human review of critical paths
- Evidence (command output), not narration ("I verified it works")

## Test-Driven Verification

When feasible, the implementer should:

1. **Add or modify a test that fails before the change and passes after**
2. Include the test output in the response
3. This provides concrete evidence, not just "I think it works"

## Using Hook Logs as Evidence

If you've enabled the PostToolUse logger hook (see [hooks/README.md](../hooks/README.md)):

- Session logs are written to `~/.codex-bridge-mcp/logs/<date>.jsonl`
- Include relevant log entries in PR descriptions
- Logs show: timestamp, tool called, session ID, success/failure

Example PR description:

```markdown
## Codex Session Evidence

Session: `impl/users-caching` (019b9868-...)
Log: `~/.codex-bridge-mcp/logs/2026-01-07.jsonl`

Verification:
- Tests: PASS (output attached)
- Lint: PASS
- Type check: PASS
```

This ties "evidence over narration" to concrete, auditable artifacts.
