# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-06

### Added
- **Background/parallel execution patterns**: Skill now teaches Claude to run Codex as a background subagent
- **Task tool integration**: Use `run_in_background: true` to spawn Codex tasks and continue working
- **Workflow patterns**: Review-while-implementing, parallel exploration, second opinion, continuous review
- **5 new examples**: Background code review, parallel approach exploration, second opinion implementation, continuous review, parallel tests+implementation

### Changed
- Updated skill description to highlight background execution capability
- Reorganized SKILL.md with dedicated sections for background and parallel execution

## [0.2.0] - 2025-01-06

### Added
- **Claude Code Plugin support**: Can now be installed as a plugin with `--plugin-dir`
- **Proactive skill** (`using-codex`): Claude automatically considers using Codex for complex coding tasks
- **Slash command** (`/codex-bridge:codex`): Quick way to delegate tasks to Codex
- **Plugin manifest** (`.claude-plugin/plugin.json`): Standard plugin structure
- **MCP configuration** (`.mcp.json`): Plugin-compatible server configuration
- **Skill examples** (`EXAMPLES.md`): Concrete usage patterns and prompts

### Changed
- Updated README with plugin installation instructions
- Reorganized project structure for plugin compatibility

## [0.1.0] - 2025-01-05

### Added
- Initial release
- MCP bridge server (`codex_bridge_mcp.py`)
- In-band `conversationId` return for multi-turn conversations
- Worker thread execution for non-blocking tool calls
- `$/cancelRequest` support
- Session persistence to `sessions.jsonl`
- Discovery tools: `codex-bridge-info`, `codex-bridge-options`, `codex-bridge-sessions`, `codex-bridge-session`
- MCP resources for session data
