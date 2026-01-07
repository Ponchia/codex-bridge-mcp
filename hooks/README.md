# Codex Bridge Hooks

This directory contains hook configurations for the Codex Bridge plugin.

**Note**: Hooks must be manually installed in your Claude Code settings - they are not automatically installed by the plugin.

---

## Available Hooks

| Hook | Type | Purpose |
|------|------|---------|
| Session Logger | PostToolUse | Log all Codex tool calls for audit/debugging |
| Config Validator | PreToolUse | Warn about potentially dangerous configurations |

---

## Installation

Add these hooks to your Claude Code settings file:

| Scope | File Location |
|-------|---------------|
| User (all projects) | `~/.claude/settings.json` |
| Project (this project) | `.claude/settings.json` |

---

## Hook 1: PostToolUse Session Logger

Logs all Codex tool calls to `~/.codex-bridge-mcp/logs/<date>.jsonl`.

**What it captures:**
- Timestamp of each call
- Tool name (`codex` or `codex-reply`)
- Session/conversation ID
- Success/failure status

### Configuration

Add to your `settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__plugin_codex-bridge_codex__codex|mcp__plugin_codex-bridge_codex__codex-reply",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys, os, datetime; data=json.load(sys.stdin); log_dir=os.path.expanduser('~/.codex-bridge-mcp/logs'); os.makedirs(log_dir, exist_ok=True); log_file=os.path.join(log_dir, datetime.date.today().isoformat()+'.jsonl'); entry={'timestamp': datetime.datetime.now().isoformat(), 'tool': data.get('tool_name'), 'session': data.get('tool_output',{}).get('conversationId') if isinstance(data.get('tool_output'), dict) else None, 'success': not (isinstance(data.get('tool_output'), dict) and data.get('tool_output',{}).get('isError', False))}; open(log_file,'a').write(json.dumps(entry)+'\\n')\""
          }
        ]
      }
    ]
  }
}
```

### Viewing Logs

```bash
# View today's log
cat ~/.codex-bridge-mcp/logs/$(date +%Y-%m-%d).jsonl | jq

# Count sessions by date
wc -l ~/.codex-bridge-mcp/logs/*.jsonl

# Find failed calls
grep '"success": false' ~/.codex-bridge-mcp/logs/*.jsonl

# View all sessions from today
cat ~/.codex-bridge-mcp/logs/$(date +%Y-%m-%d).jsonl | jq -r '.session' | sort -u
```

---

## Hook 2: PreToolUse Configuration Validator

Warns about potentially dangerous Codex configurations before execution.

**What it validates:**
- Warns when using `danger-full-access` sandbox mode
- Warns when using `approval-policy: never` with write access

**Behavior**: Warning only (does NOT block execution)

### Configuration

Add to your `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_codex-bridge_codex__codex",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); args=data.get('tool_input',{}); sandbox=args.get('sandbox',''); approval=args.get('approval-policy',''); warnings=[]; (sandbox=='danger-full-access') and warnings.append('WARNING: Using danger-full-access sandbox'); (approval=='never' and sandbox not in ['', 'read-only']) and warnings.append('WARNING: approval-policy=never with write access'); warnings and print('\\n'.join(warnings), file=sys.stderr); sys.exit(0)\""
          }
        ]
      }
    ]
  }
}
```

---

## Hook 2b: Blocking Validator (Optional)

If you want to **block** dangerous configurations instead of just warning:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_codex-bridge_codex__codex",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); args=data.get('tool_input',{}); sandbox=args.get('sandbox',''); approval=args.get('approval-policy',''); (sandbox=='danger-full-access') and (print('BLOCKED: danger-full-access sandbox not allowed', file=sys.stderr) or sys.exit(2)); (approval=='never' and sandbox not in ['', 'read-only']) and (print('BLOCKED: approval-policy=never requires read-only sandbox', file=sys.stderr) or sys.exit(2)); sys.exit(0)\""
          }
        ]
      }
    ]
  }
}
```

**Note**: Exit code 2 blocks execution and sends the error message to Claude.

---

## Complete Example

Full `settings.json` with both hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_codex-bridge_codex__codex",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); args=data.get('tool_input',{}); sandbox=args.get('sandbox',''); approval=args.get('approval-policy',''); warnings=[]; (sandbox=='danger-full-access') and warnings.append('WARNING: Using danger-full-access sandbox'); (approval=='never' and sandbox not in ['', 'read-only']) and warnings.append('WARNING: approval-policy=never with write access'); warnings and print('\\n'.join(warnings), file=sys.stderr); sys.exit(0)\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__plugin_codex-bridge_codex__codex|mcp__plugin_codex-bridge_codex__codex-reply",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys, os, datetime; data=json.load(sys.stdin); log_dir=os.path.expanduser('~/.codex-bridge-mcp/logs'); os.makedirs(log_dir, exist_ok=True); log_file=os.path.join(log_dir, datetime.date.today().isoformat()+'.jsonl'); entry={'timestamp': datetime.datetime.now().isoformat(), 'tool': data.get('tool_name'), 'session': data.get('tool_output',{}).get('conversationId') if isinstance(data.get('tool_output'), dict) else None, 'success': not (isinstance(data.get('tool_output'), dict) and data.get('tool_output',{}).get('isError', False))}; open(log_file,'a').write(json.dumps(entry)+'\\n')\""
          }
        ]
      }
    ]
  }
}
```

---

## Troubleshooting

### Hooks not running?

1. Check Claude Code is using the correct settings file
2. Verify JSON syntax is valid: `cat ~/.claude/settings.json | jq`
3. Run Claude Code with `--debug` to see hook execution

### Python errors?

The hooks require Python 3 to be available as `python3`. Test with:

```bash
python3 --version
```

### Logs not appearing?

1. Check the log directory exists: `ls ~/.codex-bridge-mcp/logs/`
2. Verify write permissions to the directory
3. Check if any Codex tools were actually called

---

## Hook Development

### Input Format (stdin)

PreToolUse receives:
```json
{
  "tool_name": "mcp__plugin_codex-bridge_codex__codex",
  "tool_input": {
    "prompt": "...",
    "model": "gpt-5.2-codex",
    "sandbox": "workspace-write"
  }
}
```

PostToolUse receives:
```json
{
  "tool_name": "mcp__plugin_codex-bridge_codex__codex",
  "tool_input": { ... },
  "tool_output": {
    "conversationId": "abc123",
    "output": "...",
    "session": { ... }
  }
}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - continue execution |
| 2 | Block - stop execution, show stderr as error |
| Other | Error - may affect execution depending on hook type |
