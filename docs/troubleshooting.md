# Troubleshooting

## conversationId Missing

**Symptom**: Tool returns output but no `conversationId`.

**Causes**:
1. Codex session didn't start properly
2. Notification was lost before bridge captured it

**Solutions**:
- Check Codex is installed: `codex --version`
- Check Codex is authenticated: `codex auth status`
- Try again - transient issue
- Check `~/.codex-bridge-mcp/sessions.jsonl` for recent sessions

## Tool Name Confusion

**Symptom**: "Tool not found" errors.

**Cause**: Using wrong tool prefix for your installation method.

| Installation | Correct prefix |
|--------------|----------------|
| Plugin (`/plugin install`) | `mcp__plugin_codex-bridge_codex__*` |
| Manual MCP server (`claude mcp add`) | `mcp__codex__*` |

## Codex Binary Not Found

**Symptom**: "Could not find codex binary" error.

**Solutions**:
1. Ensure Codex is installed: `npm install -g @openai/codex` or `brew install codex`
2. Check it's on PATH: `which codex`
3. Set explicitly: `export CODEX_BINARY=/path/to/codex`

Common locations auto-detected:
- Anywhere on PATH
- `/opt/homebrew/bin/codex` (Homebrew on macOS)
- `/usr/local/bin/codex`
- VS Code extension paths

## Session Search Returns Nothing

**Symptom**: `codex-bridge-sessions` with `query` returns empty.

**Causes**:
- Session wasn't named (uses conversationId as name)
- Query doesn't match session name (substring search)
- Session is in Codex storage but not bridge metadata

**Solutions**:
- Use `codex-bridge-sessions` without query to list all
- Name sessions when creating them: `"name": "arch/my-topic"`
- Rename existing sessions: `codex-bridge-name-session`

## Timeout on Long Tasks

**Symptom**: Codex times out before completing.

**Solutions**:
- Increase timeout: `"timeoutMs": 600000` (up to 1 hour supported)
- Break task into smaller pieces
- Use `codex-reply` to continue from where it left off
- Check partial output in the response

## conversationId Missing on Startup

**Symptom**: First call returns output but no `conversationId`.

**Cause**: Session metadata notification arrived after tool completed.

**Solution**: Increase `startupTimeoutMs` to wait longer for session metadata:

```json
{
  "prompt": "...",
  "startupTimeoutMs": 10000
}
```

Default is 5000ms. Increase if you consistently miss `conversationId` on first calls.

## Hooks Not Running

**Symptom**: Configured hooks don't execute.

**Solutions**:
1. Verify JSON syntax: `cat ~/.claude/settings.json | jq`
2. Check hook matcher matches tool names exactly
3. Ensure Python 3 is available: `python3 --version`
4. Run Claude Code with `--debug` to see hook execution
5. Check hook exit codes (0 = success, 2 = block)

## Permission Errors

**Symptom**: Can't write to state directory.

**Solutions**:
- Check permissions: `ls -la ~/.codex-bridge-mcp/`
- Override location: `export CODEX_BRIDGE_STATE_DIR=/path/with/permissions`
- Create directory manually: `mkdir -p ~/.codex-bridge-mcp`
