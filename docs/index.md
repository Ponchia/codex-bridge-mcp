# Codex Bridge Documentation

## Start Here

| Guide | What you'll learn |
|-------|-------------------|
| [Commands](commands.md) | All slash commands: `/discuss`, `/delegate`, `/codex`, `/context` |
| [Sessions](sessions.md) | Naming, finding, recalling, and checkpointing conversations |
| [Verification](verification.md) | How to avoid "diffusion of responsibility" with AI handoffs |
| [Hooks](../hooks/README.md) | Optional logging and validation hooks |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

## Core Concepts

### Tool Names

Depending on how you installed the plugin:

| Installation | Tool prefix |
|--------------|-------------|
| Plugin (recommended) | `mcp__plugin_codex-bridge_codex__*` |
| Manual MCP server | `mcp__codex__*` |

### Sessions

Every Codex interaction creates a **session** with a `conversationId`. Sessions are:
- **Continuable**: Use `codex-reply` to pick up where you left off
- **Searchable**: Name sessions well and find them with `codex-bridge-sessions`
- **Persistent**: Metadata stored in `~/.codex-bridge-mcp/sessions.jsonl`

### Safety Knobs

| Setting | Options | Default |
|---------|---------|---------|
| `sandbox` | `read-only`, `workspace-write`, `danger-full-access` | varies by skill |
| `approval-policy` | `untrusted`, `on-failure`, `on-request`, `never` | `on-failure` |
| `reasoningEffort` | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` | `xhigh` for skills |

## Quick Links

- [GitHub Repository](https://github.com/Ponchia/codex-bridge-mcp)
- [Examples Catalog](../examples/README.md)
- [Changelog](../CHANGELOG.md)
