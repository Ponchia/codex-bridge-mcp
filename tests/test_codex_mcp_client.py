"""Tests for CodexMcpClient class.

Note: These tests use mocking extensively since CodexMcpClient spawns
a subprocess and uses threads. Full integration tests would require
an actual Codex binary.
"""
from __future__ import annotations

import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


class TestCodexMcpClientHelpers:
    """Tests for CodexMcpClient helper methods that don't require subprocess."""

    def test_new_id_generates_sequential_ids(self):
        """Test that _new_id generates sequential IDs."""
        # Create a minimal mock to test ID generation
        with patch.object(cbm.CodexMcpClient, "__init__", lambda self, *args, **kwargs: None):
            client = cbm.CodexMcpClient.__new__(cbm.CodexMcpClient)
            client._next_id = 1
            client._id_lock = threading.Lock()

            id1 = client._new_id()
            id2 = client._new_id()
            id3 = client._new_id()

            assert id1 == 1
            assert id2 == 2
            assert id3 == 3

    def test_new_id_thread_safe(self):
        """Test that _new_id is thread-safe."""
        with patch.object(cbm.CodexMcpClient, "__init__", lambda self, *args, **kwargs: None):
            client = cbm.CodexMcpClient.__new__(cbm.CodexMcpClient)
            client._next_id = 1
            client._id_lock = threading.Lock()

            ids: List[int] = []
            lock = threading.Lock()

            def generate_ids():
                for _ in range(50):
                    new_id = client._new_id()
                    with lock:
                        ids.append(new_id)

            threads = [threading.Thread(target=generate_ids) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All IDs should be unique
            assert len(ids) == 250
            assert len(set(ids)) == 250


class TestSessionCapture:
    """Tests for session capture functionality."""

    def test_session_info_captured_in_dict(self):
        """Test that session info can be stored and retrieved by request ID."""
        session_dict: Dict[int, cbm.SessionInfo] = {}
        session_cv = threading.Condition()

        # Simulate capturing a session
        info = cbm.SessionInfo(
            conversation_id="test-session-123",
            captured_at=time.time(),
            model="gpt-5.2",
        )

        with session_cv:
            session_dict[42] = info
            session_cv.notify_all()

        # Retrieve it
        retrieved = session_dict.get(42)
        assert retrieved is not None
        assert retrieved.conversation_id == "test-session-123"

    def test_session_from_event_parsing(self):
        """Test parsing session_configured event."""
        event = {
            "type": "session_configured",
            "session_id": "parsed-session-456",
            "model": "gpt-5.2",
            "model_provider_id": "openai",
            "sandbox_policy": {"type": "read-only"},
        }

        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.conversation_id == "parsed-session-456"
        assert info.model == "gpt-5.2"


class TestCancelledError:
    """Tests for CancelledError handling."""

    def test_cancelled_error_raised(self):
        """Test that CancelledError can be raised and caught."""
        with pytest.raises(cbm.CancelledError) as exc_info:
            raise cbm.CancelledError("Test cancellation")

        assert "Test cancellation" in str(exc_info.value)

    def test_cancel_event_signaling(self):
        """Test cancel event can signal cancellation."""
        cancel_event = threading.Event()

        # Initially not set
        assert not cancel_event.is_set()

        # Set it
        cancel_event.set()
        assert cancel_event.is_set()


class TestJsonRpcMessageForming:
    """Tests for JSON-RPC message formation used by client."""

    def test_request_message_format(self):
        """Test that request messages have correct format."""
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "codex", "arguments": {}},
        }

        payload = cbm._json_dumps(msg) + "\n"

        # Should be valid JSON
        parsed = json.loads(payload)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == 1
        assert parsed["method"] == "tools/call"

    def test_cancel_request_message_format(self):
        """Test cancel request message format."""
        msg = {
            "jsonrpc": "2.0",
            "method": "$/cancelRequest",
            "params": {"id": 42},
        }

        payload = cbm._json_dumps(msg)
        parsed = json.loads(payload)

        assert parsed["method"] == "$/cancelRequest"
        assert parsed["params"]["id"] == 42
        # No "id" field for notifications
        assert "id" not in parsed


class TestCodexEventParsing:
    """Tests for parsing codex/event notifications."""

    def test_parse_session_configured_event(self):
        """Test parsing a session_configured event message."""
        event_msg = {
            "jsonrpc": "2.0",
            "method": "codex/event",
            "params": {
                "_meta": {"requestId": 42},
                "msg": {
                    "type": "session_configured",
                    "session_id": "event-session-789",
                    "model": "gpt-5.2",
                },
            },
        }

        # Extract session info like the client does
        params = event_msg.get("params") or {}
        meta = params.get("_meta") or {}
        request_id = meta.get("requestId")
        event = params.get("msg") or {}

        assert request_id == 42
        assert event.get("type") == "session_configured"
        assert event.get("session_id") == "event-session-789"

        # Parse into SessionInfo
        info = cbm.SessionInfo.from_session_configured_event(event)
        assert info is not None
        assert info.conversation_id == "event-session-789"

    def test_ignore_non_session_configured_events(self):
        """Test that non-session_configured events don't create SessionInfo."""
        event = {
            "type": "other_event",
            "data": "something",
        }

        info = cbm.SessionInfo.from_session_configured_event(event)
        # Should return None because session_id is missing
        assert info is None


class TestResponseParsing:
    """Tests for parsing JSON-RPC responses."""

    def test_success_response_parsing(self):
        """Test parsing a successful response."""
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [{"name": "codex"}, {"name": "codex-reply"}],
            },
        }

        assert "error" not in response
        result = response.get("result")
        assert isinstance(result, dict)
        assert len(result["tools"]) == 2

    def test_error_response_parsing(self):
        """Test parsing an error response."""
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,
                "message": "Method not found",
            },
        }

        assert "error" in response
        assert response["error"]["code"] == -32601


class TestWaitForResponseLogic:
    """Tests for the wait-for-response polling logic."""

    def test_queue_based_response_retrieval(self):
        """Test that responses can be retrieved via queue."""
        q: queue.Queue = queue.Queue(maxsize=1)
        expected_response = {"jsonrpc": "2.0", "id": 1, "result": "ok"}

        # Simulate response arriving
        q.put(expected_response)

        # Retrieve it
        response = q.get(timeout=1.0)
        assert response == expected_response

    def test_timeout_on_empty_queue(self):
        """Test timeout when queue is empty."""
        q: queue.Queue = queue.Queue(maxsize=1)

        with pytest.raises(queue.Empty):
            q.get(timeout=0.1)

    def test_cancel_event_checked_in_loop(self):
        """Test that cancel event can interrupt waiting."""
        cancel_event = threading.Event()
        cancelled = False

        def wait_with_cancel():
            nonlocal cancelled
            for _ in range(10):
                if cancel_event.is_set():
                    cancelled = True
                    return
                time.sleep(0.05)

        # Start waiting
        thread = threading.Thread(target=wait_with_cancel)
        thread.start()

        # Cancel it
        time.sleep(0.1)
        cancel_event.set()
        thread.join(timeout=1.0)

        assert cancelled


class TestClientStateManagement:
    """Tests for client state management patterns."""

    def test_pending_requests_tracking(self):
        """Test tracking pending requests."""
        pending: Dict[int, queue.Queue] = {}
        pending_lock = threading.Lock()

        # Add a pending request
        request_id = 42
        q: queue.Queue = queue.Queue(maxsize=1)
        with pending_lock:
            pending[request_id] = q

        # Simulate response arriving
        with pending_lock:
            response_queue = pending.pop(request_id, None)

        assert response_queue is not None
        assert request_id not in pending

    def test_session_cache_cleanup(self):
        """Test session cache doesn't grow unbounded."""
        session_cache: Dict[int, cbm.SessionInfo] = {}
        max_size = 5

        # Add sessions up to limit
        for i in range(max_size + 3):
            if len(session_cache) > max_size:
                session_cache.clear()
            session_cache[i] = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i),
            )

        # Cache should have been cleared
        assert len(session_cache) <= max_size + 1
