# codex-bridge-mcp

A Claude Code plugin that wraps the official `codex mcp-server` and **returns `conversationId` in the tool result**, enabling reliable multi-turn Codex conversations from Claude.

## 60-Second Quick Start

**1) Install:**

```bash
/plugin marketplace add Ponchia/codex-bridge-mcp
/plugin install codex-bridge@ponchia-codex-bridge-mcp
```

**2) Verify Codex CLI:**

```bash
codex --version
```

**3) Run a critical discussion** (architecture, trade-offs):

```
/codex-bridge:discuss Should we use JWT or opaque sessions for auth?
```

**4) Delegate coding work** (implementation):

```
/codex-bridge:delegate Add caching to the users endpoint with tests
```

## Which Command Should I Use?

```
Do you want code changes in the repo?
  Yes --> /codex-bridge:delegate
  No  --> Do you need analysis / trade-offs / a decision?
            Yes --> /codex-bridge:discuss
            No  --> /codex-bridge:codex (direct calls, session ops)

Continuing something from before?
  --> /codex-bridge:context recall <topic>
```

## Sessions (Name, Find, Recall)

This plugin stores session metadata for easy retrieval.

**Naming convention:**
- `arch/<topic> #tag1 #tag2` - decisions, ADRs
- `impl/<topic> #tag1 #tag2` - implementation work
- `notes/<topic> #notes` - running memory summaries

**Key commands:**
- `/codex-bridge:context recall <query>` - structured recall from past sessions
- `/codex-bridge:context checkpoint <query>` - save to `notes/*` for later

**Useful tools:**
| Tool | Purpose |
|------|---------|
| `codex` | Start session (returns `conversationId`) |
| `codex-reply` | Continue by `conversationId` |
| `codex-bridge-sessions` | Search sessions by name |
| `codex-bridge-name-session` | Rename a session |

See [docs/sessions.md](docs/sessions.md) for workflows.

## What This Plugin Adds

The official Codex MCP server emits `conversationId` via notification, not in the tool result. Some MCP clients don't capture notifications reliably.

This bridge:
- Returns `conversationId` in-band in the tool result
- Runs tool calls in worker threads (non-blocking)
- Supports cancellation (`$/cancelRequest`)
- Persists session metadata to `~/.codex-bridge-mcp/`

## Installation Options

### Option 1: Plugin (Recommended)

```bash
/plugin marketplace add Ponchia/codex-bridge-mcp
/plugin install codex-bridge@ponchia-codex-bridge-mcp
```

### Option 2: Local Clone

```bash
git clone https://github.com/Ponchia/codex-bridge-mcp.git
/plugin install /path/to/codex-bridge-mcp --scope user
```

### Option 3: Manual MCP Server

```bash
claude mcp add -s user codex -- python3 /path/to/codex_bridge_mcp.py
```

Note: Tool names differ by installation method. See [docs/troubleshooting.md](docs/troubleshooting.md).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CODEX_BINARY` / `CODEX_BIN` | Path to `codex` CLI (auto-detected if on PATH) |
| `CODEX_BRIDGE_STATE_DIR` | Override state directory (default: `~/.codex-bridge-mcp`) |

## Hooks (Optional)

See [hooks/README.md](hooks/README.md) for:
- PostToolUse logger (audit/debug)
- PreToolUse validator (warn/block risky configs)

## Documentation

| Guide | Contents |
|-------|----------|
| [docs/index.md](docs/index.md) | Start here - concepts and links |
| [docs/commands.md](docs/commands.md) | All commands reference |
| [docs/sessions.md](docs/sessions.md) | Session workflows |
| [docs/verification.md](docs/verification.md) | Verification contract |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues |
| [examples/](examples/README.md) | Canonical examples |

## Privacy

- Codex writes rollouts to `~/.codex/sessions/...`
- This bridge stores session *metadata* in `~/.codex-bridge-mcp/sessions.jsonl`

## License

MIT
