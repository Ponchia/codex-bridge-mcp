# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-01-08

### Changed
- **MCP Protocol upgrade**: Updated from 2024-11-05 to 2025-11-25 (latest spec)
- **Skill documentation improvements**:
  - Added explicit model constraints (only GPT 5.2 family available, not o3/o4-mini)
  - Made `xhigh` reasoning effort the recommended default across all skills
  - Added complete tool call examples with all required parameters
  - Added CRITICAL note about `web_search_request` config for research skill

## [0.6.0] - 2026-01-07

### Added
- **Dual-Model Pattern**: Both `/codex-bridge:discuss` and `/codex-bridge:research` now run Claude and Codex in parallel, then synthesize results
- **Web Research**: `/codex-bridge:research` command and `research` skill for dual-model research with web search enabled
- **Research session naming**: New `research/<topic> #tags` naming convention for research sessions
- **Web search documentation**: Documented `config.web_search_request` option in skills and commands

### Changed
- `/codex-bridge:discuss` now uses dual-model workflow: dispatch Codex → Claude analyzes in parallel → synthesize to shared conclusion
- `/codex-bridge:research` uses dual-model workflow: both models research → merge findings with agreements/unique insights
- `critical-discussion` skill updated for dual-model pattern
- `research` skill created with dual-model pattern
- Updated decision tree in README and docs
- Added new keywords: `research`, `dual-model`, `web-search`

## [0.5.0] - 2026-01-07

### Added
- **Critical Discussion skill** (`critical-discussion`): Uses GPT 5.2 (base model) with `xhigh` reasoning for architecture decisions, trade-off analysis, and technical planning
- **Coding Delegation skill** (`coding-delegation`): Uses GPT 5.2 Codex with `xhigh` reasoning for autonomous code implementation
- **New slash commands**:
  - `/codex-bridge:discuss` - Start a critical discussion with GPT 5.2
  - `/codex-bridge:delegate` - Delegate coding task to GPT 5.2 Codex
- **Hooks documentation** (`hooks/README.md`): Installation guide for optional hooks
  - PostToolUse session logger (logs to `~/.codex-bridge-mcp/logs/`)
  - PreToolUse configuration validator (warns about dangerous settings)
- `allowed-tools` frontmatter in skills for cleaner permissions

### Changed
- Updated plugin description to highlight new capabilities
- Added new keywords: `gpt-5.2`, `delegation`, `discussion`
- Reorganized README with skills and commands tables

## [0.4.2] - 2026-01-07

### Fixed
- Marketplace name now uses a valid slug to avoid plugin ID validation errors

## [0.4.1] - 2026-01-07

### Fixed
- Marketplace install compatibility (normalize `.mcp.json` layout and marketplace source metadata)

## [0.4.0] - 2026-01-07

### Added
- **Named sessions**: Assign names/topics to Codex sessions for easier reference
  - New `name` parameter on `codex` tool to name sessions at creation
  - New `codex-bridge-name-session` tool to name/rename existing sessions
  - New `query` parameter on `codex-bridge-sessions` to search by name
  - Session names are persisted and included in all session payloads
- Enables workflows like "remember that auth security review discussion with Codex"

## [0.3.1] - 2026-01-07

### Fixed
- Plugin MCP server startup reliability (avoid non-expanded `${CLAUDE_PLUGIN_ROOT}` in `.mcp.json`)
- MCP `initialize` compatibility by echoing the client-requested `protocolVersion` when provided

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
