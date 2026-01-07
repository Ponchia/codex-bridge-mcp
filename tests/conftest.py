"""Shared pytest fixtures for codex-bridge-mcp tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path so we can import codex_bridge_mcp
sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


@pytest.fixture
def temp_state_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for session state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def session_store(temp_state_dir: Path) -> cbm.SessionStore:
    """Create a SessionStore with a temporary state directory."""
    return cbm.SessionStore(temp_state_dir)


@pytest.fixture
def sample_session_info() -> cbm.SessionInfo:
    """Create a sample SessionInfo for testing."""
    return cbm.SessionInfo(
        conversation_id="test-conv-123",
        captured_at=1704067200.0,  # 2024-01-01 00:00:00 UTC
        model="gpt-5.2",
        model_provider_id="openai",
        approval_policy="on-failure",
        sandbox_policy={"type": "read-only"},
        cwd="/home/user/project",
        reasoning_effort="high",
        rollout_path="/home/user/.codex/sessions/rollout.jsonl",
        history_log_id=42,
        history_entry_count=5,
    )


@pytest.fixture
def sample_session_event() -> Dict[str, Any]:
    """Create a sample session_configured event payload."""
    return {
        "type": "session_configured",
        "session_id": "event-conv-456",
        "model": "gpt-5.2",
        "model_provider_id": "openai",
        "approval_policy": "never",
        "sandbox_policy": {"type": "workspace-write"},
        "cwd": "/tmp/test",
        "reasoning_effort": "medium",
        "rollout_path": "/tmp/rollout.jsonl",
        "history_log_id": 1,
        "history_entry_count": 0,
    }


@pytest.fixture
def mock_codex_binary(temp_state_dir: Path) -> Generator[str, None, None]:
    """Create a mock codex binary script for testing."""
    mock_binary = temp_state_dir / "mock_codex"
    mock_binary.write_text(
        '#!/bin/bash\necho "mock codex"\n'
    )
    mock_binary.chmod(0o755)
    yield str(mock_binary)


@pytest.fixture
def jsonrpc_request() -> Dict[str, Any]:
    """Create a sample JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "codex",
            "arguments": {"prompt": "Hello, world!"},
        },
    }


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    """Mock subprocess.Popen for CodexMcpClient tests."""
    with patch("codex_bridge_mcp.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        mock_proc.stdin = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_popen.return_value = mock_proc
        yield mock_popen
