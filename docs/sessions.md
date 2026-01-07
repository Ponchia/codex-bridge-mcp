# Sessions

Sessions let you continue Codex conversations and recall context from previous work.

## Naming Convention

Name sessions so they're easy to find later:

| Pattern | Use for |
|---------|---------|
| `arch/<topic> #tag1 #tag2` | Architecture decisions, ADRs |
| `impl/<topic> #tag1 #tag2` | Implementation work |
| `review/<topic> #tag1` | Code reviews |
| `notes/<topic> #notes` | Running memory summaries |

**Examples**:
- `arch/auth-tokens #jwt #security`
- `impl/user-caching #redis #perf`
- `notes/payment-system #notes`

## Session Tools

| Tool | Purpose |
|------|---------|
| `codex` | Start a new session (returns `conversationId`) |
| `codex-reply` | Continue a session by `conversationId` |
| `codex-bridge-sessions` | List/search sessions by name |
| `codex-bridge-session` | Get details for a `conversationId` |
| `codex-bridge-name-session` | Rename a session |

## Workflows

### Find and Continue a Session

```json
// 1. Search by name
{ "query": "auth" }  // codex-bridge-sessions

// 2. Continue with the conversationId
{
  "conversationId": "<from search>",
  "prompt": "Let's continue. What were the open questions?"
}
```

### Structured Recall

Use `/codex-bridge:context recall <query>` to get a formatted summary:

```
/codex-bridge:context recall arch/auth
```

Returns:
- Recap
- Decisions made
- Constraints/invariants
- Open questions
- Next steps
- File/path pointers

### Checkpoint to Notes

Save important context to a `notes/*` session for reliable recall later:

```
/codex-bridge:context checkpoint arch/auth
```

This:
1. Generates a structured checkpoint from the session
2. Persists it into `notes/auth #notes` session
3. Creates a rolling "memory" you can query later

### The Notes Pattern

For long-running topics, maintain a dedicated notes session:

1. **Primary session**: `arch/auth-tokens` (the actual discussion)
2. **Notes session**: `notes/auth-tokens #notes` (compact, rolling summary)

When you checkpoint, the summary goes into the notes session. Next week, recall from notes for a clean, condensed view.

## Storage

Sessions are stored in two places:

| Location | Contents |
|----------|----------|
| `~/.codex/sessions/...` | Full Codex rollouts (Codex's own storage) |
| `~/.codex-bridge-mcp/sessions.jsonl` | Bridge metadata (name, conversationId, timestamps) |

## Limitations

- **Search is name-only**: The `query` parameter matches session names, not content
- **Context window**: Very old sessions may have truncated context
- **Recall is generated**: Asking "what did we decide?" produces a summary, not a verbatim record
