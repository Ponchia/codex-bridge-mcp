---
description: Recall or checkpoint context from a previous Codex session
argument-hint: recall <query|conversationId> | checkpoint <query|conversationId>
---

# Context (Recall / Checkpoint)

Find a previous Codex session and either recall its context or save a checkpoint for later.

## Input

$ARGUMENTS

## Modes

### recall `<query>`

Find a session and get a structured summary to continue from.

### checkpoint `<query>`

Generate a checkpoint and persist it to a `notes/*` session.

---

## Naming Convention

Name sessions so they're findable:

- `arch/<topic> #tag1 #tag2` - architecture decisions
- `impl/<topic> #tag1 #tag2` - implementation work
- `notes/<topic> #notes` - running memory summaries

---

## Mode: recall

### Step 1: Find the session

If a `conversationId` was provided, use it directly.

Otherwise, search by name:

```json
// mcp__plugin_codex-bridge_codex__codex-bridge-sessions
{ "query": "<query>", "limit": 10 }
```

If multiple matches, show candidates (name + conversationId + date) and ask which one.

### Step 2: Request structured recall

```json
// mcp__plugin_codex-bridge_codex__codex-reply
{
  "conversationId": "<chosen conversationId>",
  "prompt": "RECALL\n\nSummarize our prior context so we can continue.\n\nOutput sections:\n1) Recap (2-4 sentences)\n2) Decisions (bullets)\n3) Constraints / Invariants\n4) Open Questions\n5) Next Steps\n6) Pointers (files/paths mentioned)\n\nRules:\n- Do NOT invent details. If unsure, write 'unknown'.\n- Be specific and concise."
}
```

### Step 3: Return to user

- Session used: name + `conversationId`
- The structured recall summary

---

## Mode: checkpoint

### Step 1: Find the session

Same as recall.

### Step 2: Generate checkpoint

```json
// mcp__plugin_codex-bridge_codex__codex-reply
{
  "conversationId": "<chosen conversationId>",
  "prompt": "CHECKPOINT\n\nCreate a self-contained checkpoint for later reference.\n\nOutput sections:\n1) Recap (2-6 bullets)\n2) Decisions (with rationale)\n3) Constraints / Invariants\n4) Open Questions\n5) Next Steps (ordered)\n6) Pointers (files/paths)\n\nRules:\n- Do NOT invent details. If unsure, write 'unknown'.\n- Keep it compact (<200 lines).\n- Write as if pasting into a notes log."
}
```

### Step 3: Find or create notes session

**Derive `<topic>` from the session name:**
- If session is `arch/auth-tokens #jwt`, topic is `auth-tokens`
- If session is `impl/user-caching #redis`, topic is `user-caching`
- Extract the part after `arch/`, `impl/`, etc., up to the first space or `#`
- If unclear, ask the user what topic name to use

Search for existing notes session:

```json
// mcp__plugin_codex-bridge_codex__codex-bridge-sessions
{ "query": "notes/<topic>", "limit": 5 }
```

If none exists, create one:

```json
// mcp__plugin_codex-bridge_codex__codex
{
  "prompt": "You are a running memory log for: <topic>.\n\nMaintain a single CURRENT MEMORY block we can rely on.\n\nRules:\n- Do not invent. If unsure, write 'unknown'.\n- Keep compact (target <100 lines).\n- Prefer durable facts: decisions, constraints, pointers.\n\nOutput:\nCURRENT MEMORY:\n- (initialized, awaiting first checkpoint)",
  "model": "gpt-5.2",
  "reasoningEffort": "medium",
  "sandbox": "read-only",
  "name": "notes/<topic> #notes"
}
```

### Step 4: Append checkpoint to notes

Use the checkpoint output from Step 2 directly (don't ask user to paste):

```json
// mcp__plugin_codex-bridge_codex__codex-reply
{
  "conversationId": "<notes conversationId>",
  "prompt": "Update CURRENT MEMORY using the checkpoint below.\n\nOutput ONLY the updated CURRENT MEMORY block.\n\nCHECKPOINT:\n<checkpoint output from Step 2>"
}
```

### Step 5: Return to user

- Primary session: name + `conversationId`
- Notes session: name + `conversationId`
- The checkpoint summary

---

## Optional: Rename unnamed sessions

If the session has no meaningful name:

```json
// mcp__plugin_codex-bridge_codex__codex-bridge-name-session
{
  "conversationId": "<conversationId>",
  "name": "arch/<topic> #tag1 #tag2"
}
```

---

## Tool Name Note

If you installed as a manual MCP server (not plugin), use `mcp__codex__*` instead of `mcp__plugin_codex-bridge_codex__*`.
