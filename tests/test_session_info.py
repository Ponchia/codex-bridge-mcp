"""Tests for SessionInfo dataclass."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


class TestSessionInfoDataclass:
    """Tests for SessionInfo dataclass attributes and behavior."""

    def test_required_fields(self):
        info = cbm.SessionInfo(
            conversation_id="test-123",
            captured_at=1234567890.0,
        )
        assert info.conversation_id == "test-123"
        assert info.captured_at == 1234567890.0

    def test_optional_fields_default_to_none(self):
        info = cbm.SessionInfo(
            conversation_id="test-123",
            captured_at=1234567890.0,
        )
        assert info.model is None
        assert info.model_provider_id is None
        assert info.approval_policy is None
        assert info.sandbox_policy is None
        assert info.cwd is None
        assert info.reasoning_effort is None
        assert info.rollout_path is None
        assert info.history_log_id is None
        assert info.history_entry_count is None

    def test_all_fields_populated(self, sample_session_info: cbm.SessionInfo):
        assert sample_session_info.conversation_id == "test-conv-123"
        assert sample_session_info.model == "gpt-5.2"
        assert sample_session_info.model_provider_id == "openai"
        assert sample_session_info.approval_policy == "on-failure"
        assert sample_session_info.sandbox_policy == {"type": "read-only"}
        assert sample_session_info.cwd == "/home/user/project"
        assert sample_session_info.reasoning_effort == "high"
        assert sample_session_info.rollout_path == "/home/user/.codex/sessions/rollout.jsonl"
        assert sample_session_info.history_log_id == 42
        assert sample_session_info.history_entry_count == 5

    def test_frozen_dataclass(self, sample_session_info: cbm.SessionInfo):
        """SessionInfo should be immutable (frozen=True)."""
        with pytest.raises(AttributeError):
            sample_session_info.conversation_id = "changed"  # type: ignore

    def test_equality(self):
        info1 = cbm.SessionInfo(conversation_id="abc", captured_at=100.0)
        info2 = cbm.SessionInfo(conversation_id="abc", captured_at=100.0)
        info3 = cbm.SessionInfo(conversation_id="xyz", captured_at=100.0)

        assert info1 == info2
        assert info1 != info3

    def test_hashable_without_dict_fields(self):
        """Frozen dataclass without dict fields should be hashable."""
        # SessionInfo with sandbox_policy=None (no dict) is hashable
        info = cbm.SessionInfo(
            conversation_id="hashable-test",
            captured_at=100.0,
            model="gpt-5.2",
            # No sandbox_policy (which is a dict)
        )
        # This should not raise
        hash_value = hash(info)
        assert isinstance(hash_value, int)

        # Can be used in sets/dicts
        session_set = {info}
        assert info in session_set

    def test_not_hashable_with_dict_fields(self, sample_session_info: cbm.SessionInfo):
        """SessionInfo with dict fields (sandbox_policy) is not hashable."""
        # sample_session_info has sandbox_policy={"type": "read-only"}
        # dicts are not hashable, so this should raise TypeError
        with pytest.raises(TypeError):
            hash(sample_session_info)


class TestSessionInfoFromEvent:
    """Tests for SessionInfo.from_session_configured_event static method."""

    def test_valid_event(self, sample_session_event: Dict[str, Any]):
        info = cbm.SessionInfo.from_session_configured_event(sample_session_event)

        assert info is not None
        assert info.conversation_id == "event-conv-456"
        assert info.model == "gpt-5.2"
        assert info.model_provider_id == "openai"
        assert info.approval_policy == "never"
        assert info.sandbox_policy == {"type": "workspace-write"}
        assert info.cwd == "/tmp/test"
        assert info.reasoning_effort == "medium"
        assert info.rollout_path == "/tmp/rollout.jsonl"
        assert info.history_log_id == 1
        assert info.history_entry_count == 0

    def test_captured_at_is_current_time(self, sample_session_event: Dict[str, Any]):
        before = time.time()
        info = cbm.SessionInfo.from_session_configured_event(sample_session_event)
        after = time.time()

        assert info is not None
        assert before <= info.captured_at <= after

    def test_missing_session_id_returns_none(self):
        event = {"type": "session_configured", "model": "gpt-5.2"}
        info = cbm.SessionInfo.from_session_configured_event(event)
        assert info is None

    def test_empty_session_id_returns_none(self):
        event = {"type": "session_configured", "session_id": ""}
        info = cbm.SessionInfo.from_session_configured_event(event)
        assert info is None

    def test_non_string_session_id_returns_none(self):
        event = {"type": "session_configured", "session_id": 12345}
        info = cbm.SessionInfo.from_session_configured_event(event)
        assert info is None

    def test_minimal_valid_event(self):
        event = {"session_id": "minimal-123"}
        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.conversation_id == "minimal-123"
        assert info.model is None
        assert info.sandbox_policy is None

    def test_invalid_model_type_ignored(self):
        event = {
            "session_id": "test-123",
            "model": 12345,  # Should be string
        }
        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.model is None

    def test_invalid_sandbox_policy_type_ignored(self):
        event = {
            "session_id": "test-123",
            "sandbox_policy": "should-be-dict",  # Should be dict
        }
        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.sandbox_policy is None

    def test_invalid_history_log_id_type_ignored(self):
        event = {
            "session_id": "test-123",
            "history_log_id": "not-an-int",  # Should be int
        }
        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.history_log_id is None

    def test_extra_fields_ignored(self):
        event = {
            "session_id": "test-123",
            "unknown_field": "should be ignored",
            "another_unknown": {"nested": "data"},
        }
        info = cbm.SessionInfo.from_session_configured_event(event)

        assert info is not None
        assert info.conversation_id == "test-123"
        # No AttributeError for unknown fields


class TestSessionInfoSerialization:
    """Tests for SessionInfo to_dict method (if exists) or dict conversion."""

    def test_can_convert_to_dict(self, sample_session_info: cbm.SessionInfo):
        """Test conversion to dict for JSON serialization."""
        from dataclasses import asdict

        d = asdict(sample_session_info)

        assert d["conversation_id"] == "test-conv-123"
        assert d["captured_at"] == 1704067200.0
        assert d["model"] == "gpt-5.2"
        assert d["sandbox_policy"] == {"type": "read-only"}

    def test_dict_is_json_serializable(self, sample_session_info: cbm.SessionInfo):
        """Ensure the dict can be serialized to JSON."""
        import json
        from dataclasses import asdict

        d = asdict(sample_session_info)
        json_str = json.dumps(d)

        assert isinstance(json_str, str)
        assert "test-conv-123" in json_str
