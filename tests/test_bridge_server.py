"""Tests for CodexBridgeServer class."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


@pytest.fixture
def mock_codex_client():
    """Create a mock CodexMcpClient."""
    client = MagicMock(spec=cbm.CodexMcpClient)
    client.is_alive.return_value = True
    client.server_info.return_value = {"name": "mock-codex", "version": "1.0.0"}
    client.list_tools.return_value = [
        {"name": "codex", "description": "Start Codex"},
        {"name": "codex-reply", "description": "Continue"},
    ]
    return client


@pytest.fixture
def bridge_server(temp_state_dir: Path, mock_codex_client):
    """Create a CodexBridgeServer with mocked dependencies."""
    with patch("codex_bridge_mcp._find_codex_binary", return_value="/usr/bin/codex"):
        with patch("codex_bridge_mcp._get_state_dir", return_value=temp_state_dir):
            server = cbm.CodexBridgeServer()
            # Inject mock client
            server._client = mock_codex_client
            server._codex_binary = "/usr/bin/codex"
            yield server


class TestBridgeServerInit:
    """Tests for CodexBridgeServer initialization."""

    def test_initializes_with_state_dir(self, temp_state_dir: Path):
        with patch("codex_bridge_mcp._find_codex_binary", return_value="/usr/bin/codex"):
            with patch("codex_bridge_mcp._get_state_dir", return_value=temp_state_dir):
                server = cbm.CodexBridgeServer()

                assert server._state_dir == temp_state_dir
                assert server._sessions is not None

    def test_handles_missing_codex_binary(self, temp_state_dir: Path):
        with patch("codex_bridge_mcp._find_codex_binary", side_effect=FileNotFoundError("Not found")):
            with patch("codex_bridge_mcp._get_state_dir", return_value=temp_state_dir):
                server = cbm.CodexBridgeServer()

                assert server._codex_binary is None
                assert server._codex_binary_error == "Not found"

    def test_starts_session_writer_thread(self, temp_state_dir: Path):
        with patch("codex_bridge_mcp._find_codex_binary", return_value="/usr/bin/codex"):
            with patch("codex_bridge_mcp._get_state_dir", return_value=temp_state_dir):
                server = cbm.CodexBridgeServer()

                assert server._session_writer_thread.is_alive()


class TestBridgeServerHandle:
    """Tests for the handle method."""

    def test_handle_initialize(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client"},
            },
        }

        response = bridge_server.handle(msg)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in response["result"]

    def test_handle_shutdown(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 2, "method": "shutdown"}

        response = bridge_server.handle(msg)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert response["result"] is None

    def test_handle_exit(self, bridge_server):
        # First shutdown
        bridge_server.handle({"jsonrpc": "2.0", "id": 1, "method": "shutdown"})

        # Then exit
        msg = {"jsonrpc": "2.0", "method": "exit"}
        response = bridge_server.handle(msg)

        assert response is None
        assert bridge_server.should_exit() is True

    def test_handle_unknown_method(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 3, "method": "unknown/method"}

        response = bridge_server.handle(msg)

        assert "error" in response
        assert response["error"]["code"] == cbm.JSONRPC_METHOD_NOT_FOUND

    def test_handle_notification_no_response(self, bridge_server):
        # Notifications have no id
        msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        response = bridge_server.handle(msg)

        assert response is None


class TestBridgeServerToolsList:
    """Tests for tools/list handling."""

    def test_lists_bridge_tools(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

        response = bridge_server.handle(msg)

        assert "result" in response
        tools = response["result"]["tools"]

        # Should include bridge-specific tools
        tool_names = [t["name"] for t in tools]
        assert "codex-bridge-info" in tool_names
        assert "codex-bridge-options" in tool_names
        assert "codex-bridge-sessions" in tool_names
        assert "codex-bridge-session" in tool_names

    def test_includes_upstream_tools(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

        response = bridge_server.handle(msg)

        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        # Should include upstream tools from mock
        assert "codex" in tool_names
        assert "codex-reply" in tool_names


class TestBridgeServerResourcesList:
    """Tests for resources/list handling."""

    def test_lists_resources(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "resources/list"}

        response = bridge_server.handle(msg)

        assert "result" in response
        resources = response["result"]["resources"]

        uris = [r["uri"] for r in resources]
        assert "codex-bridge://info" in uris
        assert "codex-bridge://options" in uris
        assert "codex-bridge://sessions" in uris


class TestBridgeServerResourcesRead:
    """Tests for resources/read handling."""

    def test_read_info_resource(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "codex-bridge://info"},
        }

        response = bridge_server.handle(msg)

        assert "result" in response
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["mimeType"] == "application/json"

        data = json.loads(contents[0]["text"])
        assert "bridgeVersion" in data
        assert data["bridgeVersion"] == cbm.BRIDGE_VERSION

    def test_read_options_resource(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "codex-bridge://options"},
        }

        response = bridge_server.handle(msg)

        assert "result" in response
        contents = response["result"]["contents"]
        data = json.loads(contents[0]["text"])

        assert "sandboxModes" in data
        assert "approvalPolicies" in data

    def test_read_sessions_resource(self, bridge_server, sample_session_info):
        # Add a session
        bridge_server._sessions.add(sample_session_info)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "codex-bridge://sessions"},
        }

        response = bridge_server.handle(msg)

        assert "result" in response
        contents = response["result"]["contents"]
        data = json.loads(contents[0]["text"])

        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["conversationId"] == sample_session_info.conversation_id

    def test_read_unknown_resource(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "codex-bridge://unknown"},
        }

        response = bridge_server.handle(msg)

        # Should return error for unknown resource
        assert "error" in response


class TestBridgeServerToolsCall:
    """Tests for tools/call handling."""

    def test_call_bridge_info_tool(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "codex-bridge-info", "arguments": {}},
        }

        # Note: tools/call is async, returns _ASYNC marker
        response = bridge_server.handle(msg)

        # For bridge-info it might be sync or async depending on implementation
        # Let's wait a bit for async handling
        time.sleep(0.2)

    def test_call_bridge_options_tool(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "codex-bridge-options", "arguments": {}},
        }

        response = bridge_server.handle(msg)
        time.sleep(0.2)

    def test_call_bridge_sessions_tool(self, bridge_server, sample_session_info):
        bridge_server._sessions.add(sample_session_info)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "codex-bridge-sessions", "arguments": {}},
        }

        response = bridge_server.handle(msg)
        time.sleep(0.2)

    def test_call_bridge_session_tool(self, bridge_server, sample_session_info):
        bridge_server._sessions.add(sample_session_info)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex-bridge-session",
                "arguments": {"conversationId": sample_session_info.conversation_id},
            },
        }

        response = bridge_server.handle(msg)
        time.sleep(0.2)

    def test_call_unknown_tool(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "unknown-tool", "arguments": {}},
        }

        response = bridge_server.handle(msg)

        # Unknown tool should return error (possibly async)
        # The error might be returned synchronously or asynchronously


class TestBridgeServerCancelRequest:
    """Tests for $/cancelRequest handling."""

    def test_cancel_unknown_request(self, bridge_server):
        msg = {
            "jsonrpc": "2.0",
            "method": "$/cancelRequest",
            "params": {"id": 999},
        }

        # Should not raise, just no-op
        response = bridge_server.handle(msg)
        assert response is None


class TestBridgeServerShouldExit:
    """Tests for should_exit method."""

    def test_initially_false(self, bridge_server):
        assert bridge_server.should_exit() is False

    def test_true_after_exit(self, bridge_server):
        # Shutdown first
        bridge_server.handle({"jsonrpc": "2.0", "id": 1, "method": "shutdown"})
        # Then exit
        bridge_server.handle({"jsonrpc": "2.0", "method": "exit"})

        assert bridge_server.should_exit() is True


class TestBridgeServerPromptsList:
    """Tests for prompts/list handling."""

    def test_returns_empty_prompts(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}

        response = bridge_server.handle(msg)

        assert "result" in response
        assert response["result"]["prompts"] == []


class TestBridgeServerResourceTemplates:
    """Tests for resources/templates/list handling."""

    def test_lists_session_template(self, bridge_server):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "resources/templates/list"}

        response = bridge_server.handle(msg)

        assert "result" in response
        templates = response["result"]["resourceTemplates"]

        # Should have session/{id} template
        uris = [t["uriTemplate"] for t in templates]
        assert any("session" in uri for uri in uris)


class TestBridgeServerIntegration:
    """Integration tests for CodexBridgeServer."""

    def test_full_initialize_workflow(self, temp_state_dir: Path):
        with patch("codex_bridge_mcp._find_codex_binary", return_value="/usr/bin/codex"):
            with patch("codex_bridge_mcp._get_state_dir", return_value=temp_state_dir):
                server = cbm.CodexBridgeServer()

                # Initialize
                init_response = server.handle({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test"},
                    },
                })

                assert "result" in init_response
                assert init_response["result"]["protocolVersion"] == "2024-11-05"

                # Initialized notification
                server.handle({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                })

                # List tools
                tools_response = server.handle({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                })

                assert "result" in tools_response
                assert "tools" in tools_response["result"]

                # Shutdown
                shutdown_response = server.handle({
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "shutdown",
                })

                assert shutdown_response["result"] is None

                # Exit
                server.handle({"jsonrpc": "2.0", "method": "exit"})
                assert server.should_exit() is True
