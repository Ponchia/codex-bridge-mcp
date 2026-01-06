# codex-bridge-mcp

Small MCP (stdio) server that wraps the official `codex mcp-server` and **returns `conversationId` in the tool result** so clients that don’t surface MCP notifications can still do multi-turn Codex conversations.

## Why this exists

The official Codex MCP server exposes two tools:

- `codex` (start a session)
- `codex-reply` (continue via `conversationId`)

However, the official server emits the `conversationId` as a `codex/event` notification (`session_configured.session_id`), not as part of the `codex` tool’s final result. Some MCP clients (including Claude Code’s VS Code extension) don’t make it easy to capture that notification, which makes conversations hard.

This bridge listens for `codex/event` notifications, captures `session_id`, and returns it in-band as JSON.

## Requirements

- `python3` (works with macOS system Python 3.9+)
- OpenAI Codex CLI installed and logged in
  - If `codex` is on your `PATH`, you’re good.
  - Otherwise set `CODEX_BINARY` to an absolute `codex` path.

## Install / Configure (Claude Code)

Add as a user-scoped MCP server:

```bash
claude mcp add -s user -t stdio codex \\
  --env CODEX_BINARY=/absolute/path/to/codex \\
  -- /usr/bin/env python3 /absolute/path/to/codex_bridge_mcp.py
```

If `codex` is on your `PATH`, you can omit `CODEX_BINARY`.

## Usage

### Start a conversation

Call the `codex` tool. The tool result is a JSON string:

```json
{"conversationId":"...","output":"..."}
```

### Continue the conversation

Call `codex-reply` with the `conversationId` and a new prompt. The result is the same JSON shape.

## Notes

- This uses the **official** Codex MCP server (`codex mcp-server`) under the hood.
- Transport is **newline-delimited JSON over stdio** (the format used by Claude Code for stdio MCP servers).

