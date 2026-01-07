"""Tests for SessionStore class."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


class TestSessionStoreInit:
    """Tests for SessionStore initialization."""

    def test_creates_state_dir_if_not_exists(self, temp_state_dir: Path):
        new_dir = temp_state_dir / "subdir" / "sessions"
        store = cbm.SessionStore(new_dir)

        assert new_dir.exists()
        assert store.count() == 0

    def test_loads_existing_sessions(self, temp_state_dir: Path):
        # Pre-populate sessions file
        sessions_file = temp_state_dir / "sessions.jsonl"
        sessions_file.parent.mkdir(parents=True, exist_ok=True)

        session_data = {
            "conversation_id": "existing-123",
            "captured_at": 1234567890.0,
            "model": "gpt-5.2",
        }
        sessions_file.write_text(json.dumps(session_data) + "\n")

        store = cbm.SessionStore(temp_state_dir)

        assert store.count() == 1
        info = store.get("existing-123")
        assert info is not None
        assert info.model == "gpt-5.2"

    def test_handles_corrupted_lines_gracefully(self, temp_state_dir: Path):
        sessions_file = temp_state_dir / "sessions.jsonl"
        sessions_file.parent.mkdir(parents=True, exist_ok=True)

        # Mix of valid and invalid lines
        content = (
            '{"conversation_id": "valid-1", "captured_at": 100.0}\n'
            "not valid json\n"
            '{"conversation_id": "valid-2", "captured_at": 200.0}\n'
            '{"missing_conversation_id": true}\n'  # Missing required field
        )
        sessions_file.write_text(content)

        store = cbm.SessionStore(temp_state_dir)

        # Should load valid sessions, skip invalid ones
        assert store.count() == 2
        assert store.get("valid-1") is not None
        assert store.get("valid-2") is not None


class TestSessionStoreAdd:
    """Tests for SessionStore.add method."""

    def test_add_session(self, session_store: cbm.SessionStore, sample_session_info: cbm.SessionInfo):
        session_store.add(sample_session_info)

        assert session_store.count() == 1
        retrieved = session_store.get(sample_session_info.conversation_id)
        assert retrieved == sample_session_info

    def test_add_persists_to_file(self, temp_state_dir: Path, sample_session_info: cbm.SessionInfo):
        store = cbm.SessionStore(temp_state_dir)
        store.add(sample_session_info)

        # Check file contents
        sessions_file = temp_state_dir / "sessions.jsonl"
        assert sessions_file.exists()

        lines = sessions_file.read_text().strip().split("\n")
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["conversation_id"] == sample_session_info.conversation_id

    def test_add_multiple_sessions(self, session_store: cbm.SessionStore):
        for i in range(5):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i * 100),
            )
            session_store.add(info)

        assert session_store.count() == 5

        for i in range(5):
            assert session_store.get(f"session-{i}") is not None

    def test_add_ignores_duplicate_session(self, session_store: cbm.SessionStore):
        """Adding a session with the same ID does not replace - it's ignored."""
        info1 = cbm.SessionInfo(
            conversation_id="same-id",
            captured_at=100.0,
            model="model-v1",
        )
        info2 = cbm.SessionInfo(
            conversation_id="same-id",
            captured_at=200.0,
            model="model-v2",
        )

        session_store.add(info1)
        session_store.add(info2)

        # Count should still be 1 (duplicate ignored)
        assert session_store.count() == 1

        # Original session is kept
        retrieved = session_store.get("same-id")
        assert retrieved is not None
        assert retrieved.model == "model-v1"  # First one wins
        assert retrieved.captured_at == 100.0


class TestSessionStoreGet:
    """Tests for SessionStore.get method."""

    def test_get_existing_session(self, session_store: cbm.SessionStore, sample_session_info: cbm.SessionInfo):
        session_store.add(sample_session_info)
        retrieved = session_store.get(sample_session_info.conversation_id)

        assert retrieved == sample_session_info

    def test_get_nonexistent_session_returns_none(self, session_store: cbm.SessionStore):
        result = session_store.get("nonexistent-id")
        assert result is None

    def test_get_with_empty_store(self, session_store: cbm.SessionStore):
        result = session_store.get("any-id")
        assert result is None


class TestSessionStoreList:
    """Tests for SessionStore.list method (returns dict, not tuple)."""

    def test_list_empty_store(self, session_store: cbm.SessionStore):
        result = session_store.list()

        assert result["data"] == []
        assert result["nextCursor"] is None

    def test_list_all_sessions(self, session_store: cbm.SessionStore):
        for i in range(3):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i),
            )
            session_store.add(info)

        result = session_store.list()

        assert len(result["data"]) == 3
        assert result["nextCursor"] is None  # All sessions returned

    def test_list_with_limit(self, session_store: cbm.SessionStore):
        for i in range(10):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i),
            )
            session_store.add(info)

        result = session_store.list(limit=3)

        assert len(result["data"]) == 3
        assert result["nextCursor"] is not None  # More sessions available

    def test_pagination_with_cursor(self, session_store: cbm.SessionStore):
        # Add 10 sessions
        for i in range(10):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i:02d}",  # Zero-padded for consistent ordering
                captured_at=float(i),
            )
            session_store.add(info)

        # Get first page
        page1 = session_store.list(limit=4)
        assert len(page1["data"]) == 4
        cursor1 = page1["nextCursor"]
        assert cursor1 is not None

        # Get second page
        page2 = session_store.list(limit=4, cursor=cursor1)
        assert len(page2["data"]) == 4
        cursor2 = page2["nextCursor"]
        assert cursor2 is not None

        # Get third page (last 2)
        page3 = session_store.list(limit=4, cursor=cursor2)
        assert len(page3["data"]) == 2
        assert page3["nextCursor"] is None  # No more pages

        # Verify no duplicates across pages
        all_ids = [s["conversationId"] for s in page1["data"] + page2["data"] + page3["data"]]
        assert len(all_ids) == len(set(all_ids))

    def test_invalid_cursor_starts_from_beginning(self, session_store: cbm.SessionStore):
        for i in range(5):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i),
            )
            session_store.add(info)

        # Invalid non-numeric cursor - should start from 0
        result = session_store.list(cursor="invalid")

        assert len(result["data"]) == 5


class TestSessionStoreThreadSafety:
    """Tests for SessionStore thread safety."""

    def test_concurrent_adds(self, temp_state_dir: Path):
        store = cbm.SessionStore(temp_state_dir)
        num_threads = 10
        sessions_per_thread = 20

        def add_sessions(thread_id: int):
            for i in range(sessions_per_thread):
                info = cbm.SessionInfo(
                    conversation_id=f"thread-{thread_id}-session-{i}",
                    captured_at=time.time(),
                )
                store.add(info)

        threads = [
            threading.Thread(target=add_sessions, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All sessions should be added
        assert store.count() == num_threads * sessions_per_thread

    def test_concurrent_reads_and_writes(self, temp_state_dir: Path):
        store = cbm.SessionStore(temp_state_dir)
        stop_event = threading.Event()
        errors: List[Exception] = []

        # Pre-populate some sessions
        for i in range(10):
            info = cbm.SessionInfo(
                conversation_id=f"initial-{i}",
                captured_at=float(i),
            )
            store.add(info)

        def writer():
            counter = 0
            while not stop_event.is_set():
                try:
                    info = cbm.SessionInfo(
                        conversation_id=f"new-{counter}",
                        captured_at=time.time(),
                    )
                    store.add(info)
                    counter += 1
                except Exception as e:
                    errors.append(e)

        def reader():
            while not stop_event.is_set():
                try:
                    store.list(limit=5)
                    store.get("initial-5")
                    store.count()
                except Exception as e:
                    errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()

        time.sleep(0.3)  # Let threads run
        stop_event.set()

        for t in threads:
            t.join(timeout=1.0)

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"


class TestSessionStoreCount:
    """Tests for SessionStore.count method."""

    def test_count_empty_store(self, session_store: cbm.SessionStore):
        assert session_store.count() == 0

    def test_count_after_adds(self, session_store: cbm.SessionStore):
        for i in range(7):
            info = cbm.SessionInfo(
                conversation_id=f"session-{i}",
                captured_at=float(i),
            )
            session_store.add(info)

        assert session_store.count() == 7


class TestSessionStorePersistence:
    """Tests for SessionStore file persistence."""

    def test_sessions_survive_reload(self, temp_state_dir: Path, sample_session_info: cbm.SessionInfo):
        # Create store and add session
        store1 = cbm.SessionStore(temp_state_dir)
        store1.add(sample_session_info)

        # Create new store instance (simulates restart)
        store2 = cbm.SessionStore(temp_state_dir)

        assert store2.count() == 1
        retrieved = store2.get(sample_session_info.conversation_id)
        assert retrieved is not None
        assert retrieved.model == sample_session_info.model

    def test_append_mode_preserves_existing(self, temp_state_dir: Path):
        # First store instance
        store1 = cbm.SessionStore(temp_state_dir)
        store1.add(cbm.SessionInfo(conversation_id="first", captured_at=100.0))

        # Second store instance adds more
        store2 = cbm.SessionStore(temp_state_dir)
        store2.add(cbm.SessionInfo(conversation_id="second", captured_at=200.0))

        # Third instance should see both
        store3 = cbm.SessionStore(temp_state_dir)
        assert store3.count() == 2
        assert store3.get("first") is not None
        assert store3.get("second") is not None
