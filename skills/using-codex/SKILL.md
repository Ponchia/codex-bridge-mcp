---
name: using-codex
description: |
  Protocol reference for Codex bridge tools and multi-turn conversations.
  Use when: you need direct tool access, session operations, or background execution.
  See critical-discussion for analysis tasks, coding-delegation for implementation.
allowed-tools:
  # Plugin installation (Claude Code extension)
  - mcp__plugin_codex-bridge_codex__codex
  - mcp__plugin_codex-bridge_codex__codex-reply
  - mcp__plugin_codex-bridge_codex__codex-bridge-info
  - mcp__plugin_codex-bridge_codex__codex-bridge-options
  - mcp__plugin_codex-bridge_codex__codex-bridge-sessions
  - mcp__plugin_codex-bridge_codex__codex-bridge-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-name-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-delete-session
  - mcp__plugin_codex-bridge_codex__codex-bridge-read-rollout
  - mcp__plugin_codex-bridge_codex__codex-bridge-export-session
  # Manual MCP server installation
  - mcp__codex__codex
  - mcp__codex__codex-reply
  - mcp__codex__codex-bridge-info
  - mcp__codex__codex-bridge-options
  - mcp__codex__codex-bridge-sessions
  - mcp__codex__codex-bridge-session
  - mcp__codex__codex-bridge-name-session
  - mcp__codex__codex-bridge-delete-session
  - mcp__codex__codex-bridge-read-rollout
  - mcp__codex__codex-bridge-export-session
---

# Codex Bridge Protocol

This is the **protocol reference** for direct Codex tool usage. For guided workflows, see:
- [critical-discussion](../critical-discussion/SKILL.md) - analysis and decisions
- [coding-delegation](../coding-delegation/SKILL.md) - implementation tasks

## Tools

### Core Tools

| Tool | Purpose |
|------|---------|
| `codex` | Start a session, returns `{conversationId, output, session}` |
| `codex-reply` | Continue session by `conversationId` |

### Session Tools

| Tool | Purpose |
|------|---------|
| `codex-bridge-sessions` | List/search sessions (use `query` for name search) |
| `codex-bridge-session` | Get details for a `conversationId` |
| `codex-bridge-name-session` | Set/update session name |
| `codex-bridge-delete-session` | Delete session from index (optionally delete rollout file too) |
| `codex-bridge-read-rollout` | Read session's rollout log for debugging |
| `codex-bridge-export-session` | Export session conversation as markdown or JSON |

### Info Tools

| Tool | Purpose |
|------|---------|
| `codex-bridge-info` | Bridge version, paths, session count |
| `codex-bridge-options` | Available models, enums, policies, auth mode |

## Tool Name Variants

| Installation | Tool prefix |
|--------------|-------------|
| Plugin (recommended) | `mcp__plugin_codex-bridge_codex__*` |
| Manual MCP server | `mcp__codex__*` |

## Response Format

All tools return JSON:

```json
{
  "conversationId": "...",
  "output": "...",
  "session": {
    "conversationId": "...",
    "name": "...",
    "model": "...",
    "sandboxPolicy": {...}
  }
}
```

## Parameters

### codex

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | yes | Task description |
| `model` | string | no | See **Available Models** below |
| `reasoningEffort` | string | no | `xhigh` (recommended), `high`, `medium`, `low` |
| `sandbox` | string | no | `read-only`, `workspace-write`, `danger-full-access` |
| `approval-policy` | string | no | `untrusted`, `on-failure`, `on-request`, `never` |
| `name` | string | no | Session name for later search |
| `timeoutMs` | number | no | Timeout in ms (max 600000) |
| `config` | object | no | Config overrides (see below) |

### Available Models

> **MODEL RESTRICTION (ChatGPT Auth)**: Only `gpt-5.2` and `gpt-5.2-codex` work.
> Do NOT use `o3`, `o4-mini`, `gpt-5.2-mini`, or `gpt-5.2-nano` - they will fail with ChatGPT auth.

| Model | Use Case | Auth Required |
|-------|----------|---------------|
| `gpt-5.2` | General reasoning, discussions, research | ChatGPT or API |
| `gpt-5.2-codex` | Code generation and implementation | ChatGPT or API |
| `gpt-5.2-mini` | Faster, lighter tasks | API key only |
| `gpt-5.2-nano` | Fastest, simplest tasks | API key only |
| `o3`, `o4-mini` | Alternative reasoning models | API key only |

Use `codex-bridge-options` to check your detected auth mode and available models.

### Reasoning Effort

> Use `high` as the default. Use `xhigh` for complex tasks where quality matters most.

| Value | Use Case |
|-------|----------|
| `xhigh` | Complex analysis, critical decisions, thorough implementation |
| `high` | **Recommended default** - good quality-speed balance |
| `medium` | Moderate complexity, faster turnaround |
| `low` | Simple/trivial tasks where speed matters |

### Config Options

Pass additional config via the `config` object:

```json
{
  "config": {
    "web_search_request": true
  }
}
```

| Config Key | Type | Description |
|------------|------|-------------|
| `web_search_request` | boolean | Enable web search during execution |

### codex-reply

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversationId` | string | yes | From previous response |
| `prompt` | string | yes | Follow-up message |
| `timeoutMs` | number | no | Timeout in ms |

### codex-bridge-sessions

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | no | Search by name (substring) |
| `limit` | number | no | Max results (default 50) |
| `cursor` | string | no | Pagination cursor |

### codex-bridge-delete-session

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversationId` | string | yes | Session to delete |
| `deleteRollout` | boolean | no | If true, also delete the underlying Codex rollout file (default: false) |

Useful for cleaning up failed or test sessions. By default, only removes from the bridge index.
Use `deleteRollout: true` for full cleanup including the Codex rollout file.

### codex-bridge-export-session

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversationId` | string | yes | Session to export |
| `format` | string | no | `markdown` (default) or `json` |

Export a session's conversation for documentation or sharing.

### codex-bridge-read-rollout

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversationId` | string | yes | Session to read rollout for |
| `lines` | number | no | Lines from end (default 50, max 500) |

Returns the last N lines from the session's Codex rollout log file.

## Session Naming Convention

| Pattern | Use for |
|---------|---------|
| `arch/<topic> #tags` | Architecture decisions |
| `impl/<topic> #tags` | Implementation |
| `review/<topic> #tags` | Code review |
| `notes/<topic> #notes` | Running memory |
| `research/<topic> #tags` | Web-enabled research |

## Background Execution

Run Codex in background using Claude's Task tool:

```json
{
  "description": "Codex implements feature",
  "subagent_type": "general-purpose",
  "run_in_background": true,
  "prompt": "Use mcp__plugin_codex-bridge_codex__codex with prompt='...', sandbox='workspace-write'"
}
```

Retrieve with `TaskOutput` when ready.

## Error Handling

| Scenario | Action |
|----------|--------|
| Timeout | Increase `timeoutMs`, or continue with `codex-reply` |
| Missing conversationId | Check Codex is installed/authenticated |
| Session not found | Use `codex-bridge-sessions` to list all |

## Storage

| Location | Contents |
|----------|----------|
| `~/.codex/sessions/` | Full Codex rollouts |
| `~/.codex-bridge-mcp/sessions.jsonl` | Bridge metadata |
