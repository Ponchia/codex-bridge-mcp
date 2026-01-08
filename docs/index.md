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

### Available Models

> **Only GPT 5.2 models are available.** Do NOT use `o3`, `o4-mini`, or other model names.

| Model | Use Case |
|-------|----------|
| `gpt-5.2` | General reasoning, discussions, research |
| `gpt-5.2-codex` | Code generation and implementation |

### Reasoning Effort

> **Always use `xhigh`** for best results.

```json
{ "reasoningEffort": "xhigh" }
```

### Web Search

For research tasks, you MUST enable web search in the config:

```json
{
  "config": { "web_search_request": true }
}
```

### Safety Knobs

| Setting | Options | Default |
|---------|---------|---------|
| `sandbox` | `read-only`, `workspace-write`, `danger-full-access` | varies by skill |
| `approval-policy` | `untrusted`, `on-failure`, `on-request`, `never` | `on-failure` |
| `reasoningEffort` | `xhigh`, `high`, `medium`, `low` | **`xhigh` (always recommended)** |

## Quick Links

- [GitHub Repository](https://github.com/Ponchia/codex-bridge-mcp)
- [Examples Catalog](../examples/README.md)
- [Changelog](../CHANGELOG.md)
