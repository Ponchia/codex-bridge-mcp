# codex-bridge-mcp

A Claude Code plugin that wraps the official `codex mcp-server` and **returns `conversationId` in the tool result** so Claude can do multi-turn Codex conversations.

## Features

- **Multi-turn conversations**: Returns `conversationId` in-band for seamless follow-ups
- **Proactive skill**: Claude automatically considers using Codex for complex coding tasks
- **Slash command**: Quick `/codex-bridge:codex` command to delegate tasks
- **Session persistence**: Tracks all sessions in `~/.codex-bridge-mcp/sessions.jsonl`
- **Non-blocking**: Worker threads prevent long Codex runs from blocking
- **Cancellation support**: `$/cancelRequest` for aborting long-running tasks

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
# Add the marketplace (one-time setup)
/plugin marketplace add Ponchia/codex-bridge-mcp

# Install the plugin
/plugin install codex-bridge@ponchia-codex-bridge-mcp
```

### Option 2: Install from Local Clone

```bash
# Clone the repository
git clone https://github.com/Ponchia/codex-bridge-mcp.git

# Install as user-scoped plugin
/plugin install /path/to/codex-bridge-mcp --scope user
```

### Option 3: Development Mode

```bash
# Run Claude Code with the plugin directory
claude --plugin-dir /path/to/codex-bridge-mcp
```

### Option 4: Manual MCP Server (Without Plugin Features)

```bash
claude mcp add -s user codex -- python3 /path/to/codex_bridge_mcp.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CODEX_BINARY` | Path to codex CLI (auto-detected if on PATH) |
| `CODEX_BIN` | Alias for `CODEX_BINARY` (for compatibility) |
| `CODEX_BRIDGE_STATE_DIR` | Override state directory (default: `~/.codex-bridge-mcp`) |

## Why this exists

The official Codex MCP server exposes two tools:

- `codex` (start a session)
- `codex-reply` (continue via `conversationId`)

However, the official server emits the `conversationId` as a `codex/event` notification (`session_configured.session_id`), not as part of the `codex` tool’s final result. Some MCP clients (including Claude Code’s VS Code extension) don’t make it easy to capture that notification, which makes conversations hard.

This bridge listens for `codex/event` notifications, captures `session_id`, and returns it in-band as JSON.

It also:
- Runs tool calls in worker threads so one long Codex run doesn’t block the MCP server.
- Supports `$/cancelRequest` (best-effort upstream cancellation + fast local abort).
- Persists lightweight session metadata to `~/.codex-bridge-mcp/sessions.jsonl` (configurable via `CODEX_BRIDGE_STATE_DIR`).

## Prerequisites

- **Python 3.9+** (macOS system Python works)
- **OpenAI Codex CLI** installed and authenticated
  - The plugin auto-detects Codex in common locations (PATH, Homebrew, VS Code extension)
  - Or set `CODEX_BINARY` environment variable to specify the path

## Usage

### Start a conversation

Call the `codex` tool. The tool result is a JSON string:

```json
{"conversationId":"...","output":"...","session":{...}}
```

### Continue the conversation

Call `codex-reply` with the `conversationId` and a new prompt. The result is the same JSON shape.

### Extra tools (discovery / persistence)

- `codex-bridge-info` — versions, paths, state dir, session count
- `codex-bridge-options` — common enums (reasoning effort/summary, sandbox, approval policy) and known `gpt-5.2*` model ids
- `codex-bridge-sessions` — list captured sessions (`{data,nextCursor}`)
- `codex-bridge-session` — get captured metadata for a `conversationId`

### Resources

- `codex-bridge://info`
- `codex-bridge://options`
- `codex-bridge://sessions`
- `codex-bridge://session/{conversationId}`

## Plugin Components

### Skill: `using-codex`

A proactive skill that teaches Claude when and how to delegate tasks to Codex. Claude will automatically consider using Codex for:
- Multi-file feature implementations
- Complex refactoring tasks
- Boilerplate code generation
- Tasks that benefit from autonomous execution

### Slash Command: `/codex-bridge:codex`

Quick way to explicitly delegate a task:
```
/codex-bridge:codex implement a REST API for user management
```

## Notes

- This uses the **official** Codex MCP server (`codex mcp-server`) under the hood.
- Transport is **newline-delimited JSON over stdio** (the format used by Claude Code for stdio MCP servers).
- Privacy: Codex itself writes rollouts under `~/.codex/sessions/...`; this bridge additionally writes session metadata to `~/.codex-bridge-mcp/sessions.jsonl` by default.

## License

MIT
