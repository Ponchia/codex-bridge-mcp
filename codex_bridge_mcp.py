#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MCP_PROTOCOL_VERSION = "2025-11-25"
BRIDGE_VERSION = "0.9.1"

# Models available for different auth modes
# ChatGPT auth has limited model access compared to API key auth
CHATGPT_AUTH_MODELS = ["gpt-5.2", "gpt-5.2-codex"]
API_AUTH_MODELS = ["gpt-5.2", "gpt-5.2-codex", "gpt-5.2-mini", "gpt-5.2-nano", "o3", "o4-mini"]

# Task types for automatic model selection
TASK_TYPES = ["coding", "discussion", "research"]
DEFAULT_TASK_TYPE = "coding"

# Model defaults by task type (matches recommended in _discover_gpt52_models)
TASK_MODEL_DEFAULTS = {
    "coding": "gpt-5.2-codex",
    "discussion": "gpt-5.2",
    "research": "gpt-5.2",
}

DEFAULT_REASONING_EFFORT = "xhigh"
DEFAULT_SANDBOX = "danger-full-access"

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603

_ASYNC = object()


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr, flush=True)


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _try_parse_json(line: str) -> Tuple[Optional[dict], Optional[int], Optional[str]]:
    line = line.strip()
    if not line:
        return None, None, None
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return None, JSONRPC_PARSE_ERROR, "Parse error"
    if isinstance(msg, dict):
        return msg, None, None
    return None, JSONRPC_INVALID_REQUEST, "Invalid Request"


def _jsonrpc_response(msg_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _jsonrpc_error(msg_id: Any, code: int, message: str, data: Any = None) -> dict:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": err}


def _tool_text_result(text: str, is_error: bool) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": bool(is_error)}


class CancelledError(RuntimeError):
    pass


def _find_codex_binary() -> str:
    env_path = os.environ.get("CODEX_BINARY") or os.environ.get("CODEX_BIN")
    if env_path and Path(env_path).exists():
        return env_path

    for candidate in ("/opt/homebrew/bin/codex", "/usr/local/bin/codex"):
        if Path(candidate).exists():
            return candidate

    which = shutil.which("codex")
    if which:
        return which

    # Fall back to common VS Code extension locations.
    home = Path.home()
    candidates = []
    for base in (
        home / ".vscode-insiders" / "extensions",
        home / ".vscode" / "extensions",
    ):
        if not base.exists():
            continue
        for ext_dir in base.glob("openai.chatgpt-*"):
            # Known layout: bin/<platform>/codex
            for codex_path in ext_dir.glob("bin/**/codex"):
                if codex_path.is_file():
                    candidates.append(codex_path)
    if candidates:
        # Pick the most recently modified candidate.
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(candidates[0])

    raise FileNotFoundError(
        "Could not locate the Codex CLI binary. Set CODEX_BINARY to an absolute path."
    )


@dataclass(frozen=True)
class SessionInfo:
    conversation_id: str
    captured_at: float
    model: Optional[str] = None
    model_provider_id: Optional[str] = None
    approval_policy: Optional[str] = None
    sandbox_policy: Optional[dict] = None
    cwd: Optional[str] = None
    reasoning_effort: Optional[str] = None
    rollout_path: Optional[str] = None
    history_log_id: Optional[int] = None
    history_entry_count: Optional[int] = None
    name: Optional[str] = None

    def with_name(self, name: str) -> "SessionInfo":
        """Return a new SessionInfo with the given name."""
        return SessionInfo(
            conversation_id=self.conversation_id,
            captured_at=self.captured_at,
            model=self.model,
            model_provider_id=self.model_provider_id,
            approval_policy=self.approval_policy,
            sandbox_policy=self.sandbox_policy,
            cwd=self.cwd,
            reasoning_effort=self.reasoning_effort,
            rollout_path=self.rollout_path,
            history_log_id=self.history_log_id,
            history_entry_count=self.history_entry_count,
            name=name,
        )

    def with_incremented_history(self) -> "SessionInfo":
        """Return a new SessionInfo with history_entry_count incremented by 1."""
        current = self.history_entry_count or 0
        return SessionInfo(
            conversation_id=self.conversation_id,
            captured_at=self.captured_at,
            model=self.model,
            model_provider_id=self.model_provider_id,
            approval_policy=self.approval_policy,
            sandbox_policy=self.sandbox_policy,
            cwd=self.cwd,
            reasoning_effort=self.reasoning_effort,
            rollout_path=self.rollout_path,
            history_log_id=self.history_log_id,
            history_entry_count=current + 1,
            name=self.name,
        )

    @staticmethod
    def from_session_configured_event(event: dict, name: Optional[str] = None) -> Optional["SessionInfo"]:
        session_id = event.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return None
        sandbox_policy = event.get("sandbox_policy")
        if sandbox_policy is not None and not isinstance(sandbox_policy, dict):
            sandbox_policy = None
        return SessionInfo(
            conversation_id=session_id,
            captured_at=time.time(),
            model=event.get("model") if isinstance(event.get("model"), str) else None,
            model_provider_id=event.get("model_provider_id")
            if isinstance(event.get("model_provider_id"), str)
            else None,
            approval_policy=event.get("approval_policy")
            if isinstance(event.get("approval_policy"), str)
            else None,
            sandbox_policy=sandbox_policy,
            cwd=event.get("cwd") if isinstance(event.get("cwd"), str) else None,
            reasoning_effort=event.get("reasoning_effort")
            if isinstance(event.get("reasoning_effort"), str)
            else None,
            rollout_path=event.get("rollout_path")
            if isinstance(event.get("rollout_path"), str)
            else None,
            history_log_id=event.get("history_log_id")
            if isinstance(event.get("history_log_id"), int)
            else None,
            history_entry_count=event.get("history_entry_count")
            if isinstance(event.get("history_entry_count"), int)
            else None,
            name=name,
        )


class SessionStore:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._state_dir / "sessions.jsonl"
        self._lock = threading.Lock()
        self._by_id: Dict[str, SessionInfo] = {}
        self._order: List[str] = []
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    conversation_id = obj.get("conversation_id")
                    if not isinstance(conversation_id, str) or not conversation_id:
                        continue
                    try:
                        info = SessionInfo(
                            conversation_id=conversation_id,
                            captured_at=float(obj.get("captured_at") or time.time()),
                            model=obj.get("model") if isinstance(obj.get("model"), str) else None,
                            model_provider_id=obj.get("model_provider_id")
                            if isinstance(obj.get("model_provider_id"), str)
                            else None,
                            approval_policy=obj.get("approval_policy")
                            if isinstance(obj.get("approval_policy"), str)
                            else None,
                            sandbox_policy=obj.get("sandbox_policy")
                            if isinstance(obj.get("sandbox_policy"), dict)
                            else None,
                            cwd=obj.get("cwd") if isinstance(obj.get("cwd"), str) else None,
                            reasoning_effort=obj.get("reasoning_effort")
                            if isinstance(obj.get("reasoning_effort"), str)
                            else None,
                            rollout_path=obj.get("rollout_path")
                            if isinstance(obj.get("rollout_path"), str)
                            else None,
                            history_log_id=obj.get("history_log_id")
                            if isinstance(obj.get("history_log_id"), int)
                            else None,
                            history_entry_count=obj.get("history_entry_count")
                            if isinstance(obj.get("history_entry_count"), int)
                            else None,
                            name=obj.get("name") if isinstance(obj.get("name"), str) else None,
                        )
                    except Exception:
                        continue
                    if conversation_id not in self._by_id:
                        self._order.append(conversation_id)
                    self._by_id[conversation_id] = info
        except OSError:
            return

    def _session_to_record(self, info: SessionInfo) -> dict:
        """Convert a SessionInfo to a JSON-serializable record."""
        return {
            "conversation_id": info.conversation_id,
            "captured_at": info.captured_at,
            "model": info.model,
            "model_provider_id": info.model_provider_id,
            "approval_policy": info.approval_policy,
            "sandbox_policy": info.sandbox_policy,
            "cwd": info.cwd,
            "reasoning_effort": info.reasoning_effort,
            "rollout_path": info.rollout_path,
            "history_log_id": info.history_log_id,
            "history_entry_count": info.history_entry_count,
            "name": info.name,
        }

    def _rewrite_file(self) -> None:
        """Rewrite the entire sessions file from memory (caller must hold lock)."""
        try:
            with self._path.open("w", encoding="utf-8") as f:
                for cid in self._order:
                    info = self._by_id.get(cid)
                    if info is not None:
                        f.write(_json_dumps(self._session_to_record(info)) + "\n")
        except OSError:
            pass

    def add(self, info: SessionInfo) -> None:
        with self._lock:
            if info.conversation_id in self._by_id:
                return
            self._by_id[info.conversation_id] = info
            self._order.append(info.conversation_id)
            try:
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(_json_dumps(self._session_to_record(info)) + "\n")
            except OSError:
                pass

    def update(self, conversation_id: str, name: Optional[str] = None) -> Optional[SessionInfo]:
        """Update a session's name. Returns the updated SessionInfo or None if not found."""
        with self._lock:
            existing = self._by_id.get(conversation_id)
            if existing is None:
                return None
            if name is not None:
                updated = existing.with_name(name)
                self._by_id[conversation_id] = updated
                self._rewrite_file()
                return updated
            return existing

    def search(self, query: str, limit: int = 50) -> List[SessionInfo]:
        """Search sessions by name (case-insensitive substring match)."""
        query_lower = query.lower()
        with self._lock:
            results = []
            for cid in reversed(self._order):
                info = self._by_id.get(cid)
                if info is None:
                    continue
                if info.name and query_lower in info.name.lower():
                    results.append(info)
                    if len(results) >= limit:
                        break
            return results

    def delete(self, conversation_id: str) -> bool:
        """Delete a session by conversation_id. Returns True if deleted."""
        with self._lock:
            if conversation_id not in self._by_id:
                return False
            del self._by_id[conversation_id]
            self._order = [cid for cid in self._order if cid != conversation_id]
            self._rewrite_file()
            return True

    def increment_history(self, conversation_id: str) -> Optional[SessionInfo]:
        """Increment the history_entry_count for a session. Returns updated session or None."""
        with self._lock:
            existing = self._by_id.get(conversation_id)
            if existing is None:
                return None
            updated = existing.with_incremented_history()
            self._by_id[conversation_id] = updated
            self._rewrite_file()
            return updated

    def get(self, conversation_id: str) -> Optional[SessionInfo]:
        with self._lock:
            return self._by_id.get(conversation_id)

    def list(self, limit: int = 50, cursor: Optional[str] = None) -> dict:
        with self._lock:
            start = 0
            if cursor is not None:
                try:
                    start = int(cursor)
                except ValueError:
                    start = 0
            start = max(0, start)
            ids = list(reversed(self._order))
            end = min(len(ids), start + max(1, limit))
            items = []
            for cid in ids[start:end]:
                info = self._by_id.get(cid)
                if info is None:
                    continue
                items.append(_session_info_payload(info))
            next_cursor = str(end) if end < len(ids) else None
            return {"data": items, "nextCursor": next_cursor}

    def count(self) -> int:
        with self._lock:
            return len(self._by_id)


class CodexMcpClient:
    def __init__(self, codex_binary: str, on_session_configured: Optional[callable] = None) -> None:
        self._codex_binary = codex_binary
        self._on_session_configured = on_session_configured
        self._proc = subprocess.Popen(
            [codex_binary, "mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 1
        self._id_lock = threading.Lock()
        self._pending: Dict[int, queue.Queue] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._session_by_request_id: Dict[int, SessionInfo] = {}
        self._session_lock = threading.Lock()
        self._session_cv = threading.Condition(self._session_lock)
        self._server_info: Optional[dict] = None

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

        self._initialize()

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass

    def is_alive(self) -> bool:
        return self._proc.poll() is None

    def server_info(self) -> Optional[dict]:
        return self._server_info

    def _read_stderr(self) -> None:
        assert self._proc.stderr is not None
        for line in self._proc.stderr:
            _eprint("[codex] " + line.rstrip("\n"))

    def _read_stdout(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            msg, err_code, _ = _try_parse_json(line)
            if err_code is not None or not msg:
                continue

            method = msg.get("method")
            if method == "codex/event":
                params = msg.get("params") or {}
                meta = params.get("_meta") or {}
                request_id = meta.get("requestId")
                event = params.get("msg") or {}
                if (
                    isinstance(request_id, int)
                    and event.get("type") == "session_configured"
                    and isinstance(event.get("session_id"), str)
                ):
                    info = SessionInfo.from_session_configured_event(event)
                    if info is not None:
                        with self._session_cv:
                            self._session_by_request_id[request_id] = info
                            if len(self._session_by_request_id) > 2048:
                                # Prevent unbounded growth on long-running bridges.
                                self._session_by_request_id.clear()
                            self._session_cv.notify_all()
                        if self._on_session_configured is not None:
                            try:
                                self._on_session_configured(info)
                            except Exception:
                                pass
                continue

            if "id" in msg:
                msg_id = msg.get("id")
                if isinstance(msg_id, int):
                    with self._pending_lock:
                        q = self._pending.pop(msg_id, None)
                    if q is not None:
                        q.put(msg)
                continue

    def _new_id(self) -> int:
        with self._id_lock:
            rid = self._next_id
            self._next_id += 1
            return rid

    def _send(self, msg: dict) -> None:
        if not self._proc.stdin:
            raise RuntimeError("Codex MCP stdin is closed")
        if self._proc.poll() is not None:
            raise RuntimeError("Codex MCP process has exited")
        payload = _json_dumps(msg) + "\n"
        with self._write_lock:
            self._proc.stdin.write(payload)
            self._proc.stdin.flush()

    def cancel_request(self, request_id: int) -> None:
        # Best-effort: Codex MCP server may ignore this.
        try:
            self._send({"jsonrpc": "2.0", "method": "$/cancelRequest", "params": {"id": request_id}})
        except Exception:
            pass

    def _wait_for_response(
        self,
        request_id: int,
        q: queue.Queue,
        timeout_s: float,
        cancel_event: Optional[threading.Event],
    ) -> dict:
        deadline = time.monotonic() + timeout_s
        while True:
            if cancel_event is not None and cancel_event.is_set():
                with self._pending_lock:
                    self._pending.pop(request_id, None)
                self.cancel_request(request_id)
                raise CancelledError("Request cancelled")
            if self._proc.poll() is not None:
                with self._pending_lock:
                    self._pending.pop(request_id, None)
                raise RuntimeError("Codex MCP process exited")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                with self._pending_lock:
                    self._pending.pop(request_id, None)
                raise TimeoutError(f"Timed out waiting for Codex MCP response to request {request_id}")
            try:
                return q.get(timeout=min(0.25, remaining))
            except queue.Empty:
                continue

    def _request(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout_s: float = 120.0,
        cancel_event: Optional[threading.Event] = None,
    ) -> dict:
        rid = self._new_id()
        q: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[rid] = q

        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        return self._wait_for_response(rid, q, timeout_s=timeout_s, cancel_event=cancel_event)

    def _request_with_id(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout_s: float = 120.0,
        cancel_event: Optional[threading.Event] = None,
    ) -> Tuple[int, dict]:
        rid = self._new_id()
        q: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[rid] = q
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        resp = self._wait_for_response(rid, q, timeout_s=timeout_s, cancel_event=cancel_event)
        return rid, resp

    def _initialize(self) -> None:
        resp = self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "codex-bridge", "version": BRIDGE_VERSION},
            },
            timeout_s=15.0,
        )
        result = resp.get("result") or {}
        if isinstance(result, dict):
            info = result.get("serverInfo")
            if isinstance(info, dict):
                self._server_info = info
        # Codex MCP server (currently) doesn't implement notifications/initialized; skip it.

    def list_tools(self, timeout_s: float = 5.0) -> list:
        resp = self._request("tools/list", {}, timeout_s=timeout_s)
        result = resp.get("result") or {}
        tools = result.get("tools") if isinstance(result, dict) else None
        if isinstance(tools, list):
            return tools
        return []

    def call_tool(
        self,
        name: str,
        arguments: dict,
        timeout_s: float,
        cancel_event: Optional[threading.Event],
    ) -> Tuple[int, dict]:
        rid, resp = self._request_with_id(
            "tools/call",
            {"name": name, "arguments": arguments},
            timeout_s=timeout_s,
            cancel_event=cancel_event,
        )
        return rid, resp

    def get_session_for_request(
        self, request_id: int, timeout_s: float, cancel_event: Optional[threading.Event]
    ) -> Optional[SessionInfo]:
        deadline = time.monotonic() + timeout_s
        with self._session_cv:
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    raise CancelledError("Request cancelled")
                info = self._session_by_request_id.get(request_id)
                if info is not None:
                    return info
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._session_cv.wait(timeout=min(0.25, remaining))


def _extract_text(result: dict) -> str:
    if not isinstance(result, dict):
        return _json_dumps(result)
    content = result.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "\n".join(parts)
    if isinstance(content, str):
        return content
    err = result.get("error")
    if isinstance(err, str):
        return err
    return _json_dumps(result)


def _session_info_payload(info: SessionInfo) -> dict:
    return {
        "conversationId": info.conversation_id,
        "name": info.name,
        "capturedAt": info.captured_at,
        "model": info.model,
        "modelProviderId": info.model_provider_id,
        "approvalPolicy": info.approval_policy,
        "sandboxPolicy": info.sandbox_policy,
        "cwd": info.cwd,
        "reasoningEffort": info.reasoning_effort,
        "rolloutPath": info.rollout_path,
        "historyLogId": info.history_log_id,
        "historyEntryCount": info.history_entry_count,
    }


def _get_state_dir() -> Path:
    override = os.environ.get("CODEX_BRIDGE_STATE_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex-bridge-mcp"


def _run_cmd(argv: List[str], timeout_s: float) -> Tuple[int, str, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
    return proc.returncode, proc.stdout, proc.stderr


def _get_codex_version(codex_binary: str) -> Optional[str]:
    try:
        code, out, _ = _run_cmd([codex_binary, "--version"], timeout_s=5.0)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if code != 0:
        return None
    v = out.strip()
    return v or None


def _ensure_schema_cache(codex_binary: str, state_dir: Path) -> Optional[Path]:
    version = _get_codex_version(codex_binary) or "unknown"
    cache_dir = state_dir / "schema-cache" / version.replace(os.sep, "_")
    schema_path = cache_dir / "codex_app_server_protocol.schemas.json"
    if schema_path.exists():
        return schema_path
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    try:
        subprocess.run(
            [codex_binary, "app-server", "generate-json-schema", "--out", str(cache_dir)],
            capture_output=True,
            text=True,
            timeout=60.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if schema_path.exists():
        return schema_path
    return None


def _extract_enums_from_schema(schema_path: Path) -> dict:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    defs = schema.get("definitions")
    if not isinstance(defs, dict):
        return {}
    v2 = defs.get("v2")
    if not isinstance(v2, dict):
        return {}

    def _enum_for(name: str) -> List[str]:
        d = v2.get(name)
        if not isinstance(d, dict):
            return []
        vals = d.get("enum")
        if isinstance(vals, list) and all(isinstance(x, str) for x in vals):
            return list(vals)
        # Some enums are represented as oneOf[...] enum blocks.
        vals_out: List[str] = []
        one_of = d.get("oneOf") or d.get("anyOf")
        if isinstance(one_of, list):
            for item in one_of:
                if not isinstance(item, dict):
                    continue
                enum_vals = item.get("enum")
                if isinstance(enum_vals, list) and all(isinstance(x, str) for x in enum_vals):
                    vals_out.extend(enum_vals)
        dedup: List[str] = []
        seen = set()
        for v in vals_out:
            if v not in seen:
                seen.add(v)
                dedup.append(v)
        return dedup

    return {
        "reasoningEffort": _enum_for("ReasoningEffort"),
        "reasoningSummary": _enum_for("ReasoningSummary"),
        "networkAccess": _enum_for("NetworkAccess"),
    }


def _detect_auth_mode(sessions: SessionStore) -> str:
    """Detect auth mode based on session history.

    Returns 'chatgpt' if we've seen model errors typical of ChatGPT auth,
    'api' if we've seen API-only models work, or 'unknown' otherwise.
    """
    # Check if we've successfully used any API-only models
    api_only_models = {"gpt-5.2-mini", "gpt-5.2-nano", "o3", "o4-mini"}
    try:
        with sessions._lock:
            for info in sessions._by_id.values():
                if info.model in api_only_models:
                    # If we have a session with an API-only model, user has API auth
                    return "api"
    except Exception:
        pass
    # Default to ChatGPT since it's more common and restrictive
    return "chatgpt"


def _discover_gpt52_models(codex_binary: str, sessions: SessionStore) -> dict:
    auth_mode = _detect_auth_mode(sessions)

    # Base available models depend on auth mode
    if auth_mode == "api":
        available = list(API_AUTH_MODELS)
        notes = [
            "API key auth detected - all models available.",
            "If a model hangs, cancel the request or lower timeoutMs.",
        ]
    else:
        available = list(CHATGPT_AUTH_MODELS)
        notes = [
            "ChatGPT auth detected - only gpt-5.2 and gpt-5.2-codex available.",
            "Models like o3, o4-mini, gpt-5.2-mini, gpt-5.2-nano require API key auth.",
            "If a model hangs, cancel the request or lower timeoutMs.",
        ]

    # Also include anything we have actually seen work in session_configured events
    seen = set(available)
    try:
        with sessions._lock:
            for info in sessions._by_id.values():
                if info.model and info.model not in seen:
                    # Only add models that have successfully been used
                    seen.add(info.model)
                    available.append(info.model)
    except Exception:
        pass

    return {
        "authMode": auth_mode,
        "available": available,
        "recommended": {
            "reasoning": "gpt-5.2",
            "coding": "gpt-5.2-codex",
        },
        "notes": notes,
    }


def _resolve_model(
    requested_model: Optional[str],
    task_type: Optional[str],
    available_models: List[str],
) -> Tuple[str, Optional[str]]:
    """
    Resolve the model to use based on request and task type.

    Returns: (model_to_use, warning_message_or_none)
    """
    effective_task = task_type if task_type in TASK_TYPES else DEFAULT_TASK_TYPE
    default_model = TASK_MODEL_DEFAULTS[effective_task]

    if not requested_model:
        return default_model, None

    if requested_model in available_models:
        return requested_model, None

    warning = f"Model '{requested_model}' not available. Using '{default_model}' instead."
    return default_model, warning


def _normalize_upstream_tool_response(resp: dict) -> Tuple[str, bool]:
    if not isinstance(resp, dict):
        return _json_dumps(resp), True

    if "error" in resp:
        err = resp.get("error")
        if isinstance(err, dict):
            msg = err.get("message") if isinstance(err.get("message"), str) else _json_dumps(err)
            return msg, True
        if isinstance(err, str):
            return err, True
        return _json_dumps(err), True

    result = resp.get("result")
    if isinstance(result, dict):
        is_error = bool(result.get("isError") is True)
        if isinstance(result.get("error"), str):
            is_error = True
        return _extract_text(result), is_error

    return _json_dumps(resp), True


def _bridge_tools() -> list:
    # Static fallback schema; prefer dynamic passthrough from upstream in tools/list.
    return [
        {
            "name": "codex",
            "description": (
                "Run a Codex session and return JSON {conversationId, output, session}.\n\n"
                "**Automatic Model Selection:**\n"
                "- taskType='coding' (default) -> gpt-5.2-codex\n"
                "- taskType='discussion' or 'research' -> gpt-5.2\n"
                "- Invalid models fall back to task-appropriate default\n"
                "- reasoningEffort defaults to 'xhigh'"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The *initial user prompt* to start the Codex conversation."},
                    "taskType": {
                        "type": "string",
                        "enum": ["coding", "discussion", "research"],
                        "description": "Task type for automatic model selection. Defaults to 'coding'.",
                    },
                    "model": {"type": "string", "description": "Optional override for the model name (e.g. \"gpt-5.2\", \"o3\"). Validated against available models."},
                    "profile": {"type": "string", "description": "Optional Codex config profile name."},
                    "cwd": {"type": "string", "description": "Optional working directory."},
                    "sandbox": {"type": "string", "description": "Sandbox mode."},
                    "approval-policy": {"type": "string", "description": "Approval policy."},
                    "config": {
                        "type": "object",
                        "description": "Config overrides (mapped to Codex CLI -c values).",
                        "additionalProperties": True,
                    },
                    "base-instructions": {"type": "string", "description": "Optional base instructions for Codex."},
                    "developer-instructions": {
                        "type": "string",
                        "description": "Optional developer instructions for Codex.",
                    },
                    "compact-prompt": {"type": "string", "description": "Prompt used when Codex compacts the conversation."},
                    "reasoningEffort": {
                        "type": "string",
                        "description": "Optional convenience override mapped to config.model_reasoning_effort.",
                    },
                    "reasoningSummary": {
                        "type": "string",
                        "description": "Optional convenience override mapped to config.model_reasoning_summary.",
                    },
                    "timeoutMs": {"type": "integer", "description": "Overall tool timeout in milliseconds."},
                    "startupTimeoutMs": {
                        "type": "integer",
                        "description": "How long to wait for conversationId/session metadata after tool completion.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional name/topic for this session (e.g., 'auth-security-review'). Makes it easier to find and reference later.",
                    },
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "codex-reply",
            "description": "Continue a Codex conversation. Returns JSON {conversationId, output, session?}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "Conversation/session id returned by codex."},
                    "prompt": {"type": "string", "description": "Next user prompt."},
                    "timeoutMs": {"type": "integer", "description": "Overall tool timeout in milliseconds."},
                },
                "required": ["conversationId", "prompt"],
            },
        },
    ]


def _bridge_extra_tools() -> list:
    return [
        {
            "name": "codex-bridge-info",
            "description": "Get Codex Bridge info (versions, paths, state). Returns JSON.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "codex-bridge-options",
            "description": "List common options (models, reasoning enums, sandbox/approval). Returns JSON.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "codex-bridge-sessions",
            "description": "List known Codex conversations captured by the bridge. Returns JSON {data,nextCursor}. Use 'query' to search by session name.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max items to return (default 50)."},
                    "cursor": {"type": "string", "description": "Pagination cursor from a previous call."},
                    "query": {"type": "string", "description": "Search sessions by name (case-insensitive substring match)."},
                },
            },
        },
        {
            "name": "codex-bridge-session",
            "description": "Get metadata for a single conversationId. Returns JSON or null.",
            "inputSchema": {
                "type": "object",
                "properties": {"conversationId": {"type": "string"}},
                "required": ["conversationId"],
            },
        },
        {
            "name": "codex-bridge-name-session",
            "description": "Set or update the name/topic of a Codex session for easier reference. Returns the updated session info.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "The conversation ID to name."},
                    "name": {"type": "string", "description": "The name/topic to assign to this session (e.g., 'auth-security-review')."},
                },
                "required": ["conversationId", "name"],
            },
        },
        {
            "name": "codex-bridge-delete-session",
            "description": "Delete a session from the bridge's session index. Optionally delete the underlying Codex rollout file. Useful for cleaning up failed/test sessions.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "The conversation ID to delete."},
                    "deleteRollout": {"type": "boolean", "description": "If true, also delete the underlying Codex rollout file. Default: false."},
                },
                "required": ["conversationId"],
            },
        },
        {
            "name": "codex-bridge-export-session",
            "description": "Export a session's conversation as formatted markdown. Useful for documentation and sharing.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "The conversation ID to export."},
                    "format": {"type": "string", "enum": ["markdown", "json"], "description": "Export format. Default: markdown."},
                },
                "required": ["conversationId"],
            },
        },
        {
            "name": "codex-bridge-read-rollout",
            "description": "Read the last N lines from a session's Codex rollout log file. Useful for debugging session history.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "The conversation ID to read rollout for."},
                    "lines": {"type": "integer", "description": "Number of lines to read from the end (default 50, max 500)."},
                },
                "required": ["conversationId"],
            },
        },
    ]


@dataclass
class InflightRequest:
    cancel_event: threading.Event
    upstream_request_id: Optional[int] = None


class CodexBridgeServer:
    def __init__(self) -> None:
        self._client: Optional[CodexMcpClient] = None
        self._codex_binary: Optional[str] = None
        self._codex_binary_error: Optional[str] = None
        try:
            self._codex_binary = _find_codex_binary()
        except Exception as e:
            self._codex_binary_error = str(e)

        self._state_dir = _get_state_dir()
        self._sessions = SessionStore(self._state_dir)
        self._should_exit = threading.Event()
        self._session_queue: queue.Queue = queue.Queue(maxsize=2048)
        self._session_writer_thread = threading.Thread(target=self._session_writer, daemon=True)
        self._session_writer_thread.start()

        self._write_lock = threading.Lock()
        self._inflight_lock = threading.Lock()
        self._inflight: Dict[Any, InflightRequest] = {}

        self._tools_cache: Optional[list] = None
        self._tools_cache_lock = threading.Lock()

    def _get_client(self) -> CodexMcpClient:
        if self._client is None or not self._client.is_alive():
            if self._client is not None:
                self._client.close()
            if not self._codex_binary:
                raise RuntimeError(self._codex_binary_error or "Codex binary not configured")
            self._client = CodexMcpClient(self._codex_binary, on_session_configured=self._enqueue_session)
        return self._client

    def _enqueue_session(self, info: SessionInfo) -> None:
        try:
            self._session_queue.put_nowait(info)
        except queue.Full:
            pass

    def _session_writer(self) -> None:
        while not self._should_exit.is_set():
            try:
                info = self._session_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if isinstance(info, SessionInfo):
                    self._sessions.add(info)
            except Exception:
                pass

    def _send(self, msg: dict) -> None:
        payload = _json_dumps(msg) + "\n"
        with self._write_lock:
            sys.stdout.write(payload)
            sys.stdout.flush()

    def _tools_list(self) -> list:
        with self._tools_cache_lock:
            if self._tools_cache is not None:
                return self._tools_cache

        base_tools: list = []
        try:
            client = self._get_client()
            base_tools = client.list_tools(timeout_s=3.0)
        except Exception:
            base_tools = _bridge_tools()

        # Patch tool descriptions (input schemas come from upstream when possible).
        patched: list = []
        for tool in base_tools:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if name == "codex":
                tool = dict(tool)
                tool["description"] = "Run a Codex session and return JSON {conversationId, output, session}."
                schema = tool.get("inputSchema")
                if isinstance(schema, dict):
                    schema = dict(schema)
                    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
                    props = dict(props)
                    props.setdefault(
                        "reasoningEffort",
                        {
                            "type": "string",
                            "description": "Optional convenience override mapped to config.model_reasoning_effort.",
                        },
                    )
                    props.setdefault(
                        "reasoningSummary",
                        {
                            "type": "string",
                            "description": "Optional convenience override mapped to config.model_reasoning_summary.",
                        },
                    )
                    props.setdefault(
                        "timeoutMs", {"type": "integer", "description": "Overall tool timeout in milliseconds."}
                    )
                    props.setdefault(
                        "startupTimeoutMs",
                        {
                            "type": "integer",
                            "description": "How long to wait for conversationId/session metadata after tool completion.",
                        },
                    )
                    props.setdefault(
                        "name",
                        {
                            "type": "string",
                            "description": "Optional name/topic for this session (e.g., 'auth-security-review'). Makes it easier to find and reference later.",
                        },
                    )
                    schema["properties"] = props
                    tool["inputSchema"] = schema
            elif name == "codex-reply":
                tool = dict(tool)
                tool["description"] = "Continue a Codex conversation. Returns JSON {conversationId, output, session?}."
                schema = tool.get("inputSchema")
                if isinstance(schema, dict):
                    schema = dict(schema)
                    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
                    props = dict(props)
                    props.setdefault(
                        "timeoutMs", {"type": "integer", "description": "Overall tool timeout in milliseconds."}
                    )
                    schema["properties"] = props
                    tool["inputSchema"] = schema
            patched.append(tool)

        patched.extend(_bridge_extra_tools())
        with self._tools_cache_lock:
            self._tools_cache = patched
        return patched

    def _handle_codex_tool(
        self,
        msg_id: Any,
        args: dict,
        inflight: InflightRequest,
    ) -> dict:
        timeout_ms = args.pop("timeoutMs", None)
        startup_timeout_ms = args.pop("startupTimeoutMs", None)
        reasoning_effort = args.pop("reasoningEffort", None)
        reasoning_summary = args.pop("reasoningSummary", None)
        session_name = args.pop("name", None)  # Bridge-specific: name for the session
        task_type = args.pop("taskType", None)  # Bridge-specific: for automatic model selection

        # Resolve model based on task type and availability
        models_info = _discover_gpt52_models(self._codex_binary or "", self._sessions)
        available = models_info.get("available", API_AUTH_MODELS)
        requested_model = args.get("model")
        resolved_model, model_warning = _resolve_model(requested_model, task_type, available)
        args["model"] = resolved_model

        # Default reasoning effort to xhigh if not specified
        if not reasoning_effort:
            reasoning_effort = DEFAULT_REASONING_EFFORT

        timeout_s = 600.0
        if isinstance(timeout_ms, int) and timeout_ms > 0:
            timeout_s = max(1.0, min(60.0 * 60.0, timeout_ms / 1000.0))
        startup_timeout_s = 5.0
        if isinstance(startup_timeout_ms, int) and startup_timeout_ms > 0:
            startup_timeout_s = max(0.1, min(60.0, startup_timeout_ms / 1000.0))

        if isinstance(reasoning_effort, str) and reasoning_effort:
            cfg = args.get("config")
            if not isinstance(cfg, dict):
                cfg = {}
            cfg = dict(cfg)
            cfg["model_reasoning_effort"] = reasoning_effort
            args["config"] = cfg
        if isinstance(reasoning_summary, str) and reasoning_summary:
            cfg = args.get("config")
            if not isinstance(cfg, dict):
                cfg = {}
            cfg = dict(cfg)
            cfg["model_reasoning_summary"] = reasoning_summary
            args["config"] = cfg

        # Default sandbox to danger-full-access if not specified
        if not args.get("sandbox"):
            args["sandbox"] = DEFAULT_SANDBOX

        client = self._get_client()
        upstream_id, resp = client.call_tool(
            "codex", args, timeout_s=timeout_s, cancel_event=inflight.cancel_event
        )
        inflight.upstream_request_id = upstream_id

        session = client.get_session_for_request(
            upstream_id, timeout_s=startup_timeout_s, cancel_event=inflight.cancel_event
        )

        output_text, is_error = _normalize_upstream_tool_response(resp)
        payload: Dict[str, Any] = {"output": output_text}
        if session is not None:
            # If a name was provided, update the session with it
            if isinstance(session_name, str) and session_name:
                session = session.with_name(session_name)
                # Update the stored session with the name
                self._sessions.update(session.conversation_id, name=session_name)
            payload["conversationId"] = session.conversation_id
            payload["session"] = _session_info_payload(session)
        else:
            # Missing session means we couldn't capture the conversationId - this is an error
            # because the caller won't be able to continue the conversation
            is_error = True
            payload["conversationId"] = None
            payload["error"] = "Failed to capture session info (conversationId unavailable). The conversation cannot be continued."
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=is_error))

    def _handle_codex_reply_tool(
        self,
        msg_id: Any,
        args: dict,
        inflight: InflightRequest,
    ) -> dict:
        conversation_id = args.get("conversationId")
        prompt = args.get("prompt")
        if not isinstance(conversation_id, str) or not isinstance(prompt, str):
            return _jsonrpc_response(
                msg_id,
                _tool_text_result("codex-reply requires {conversationId: string, prompt: string}", is_error=True),
            )

        timeout_ms = args.get("timeoutMs")
        timeout_s = 600.0
        if isinstance(timeout_ms, int) and timeout_ms > 0:
            timeout_s = max(1.0, min(60.0 * 60.0, timeout_ms / 1000.0))

        client = self._get_client()
        upstream_id, resp = client.call_tool(
            "codex-reply",
            {"conversationId": conversation_id, "prompt": prompt},
            timeout_s=timeout_s,
            cancel_event=inflight.cancel_event,
        )
        inflight.upstream_request_id = upstream_id

        output_text, is_error = _normalize_upstream_tool_response(resp)
        payload: Dict[str, Any] = {"conversationId": conversation_id, "output": output_text}

        # Increment history count on successful reply
        if not is_error:
            session = self._sessions.increment_history(conversation_id)
            # Session recovery: if session was deleted from index but reply succeeded,
            # try to recover session info from the session_configured event
            if session is None:
                recovered_session = client.get_session_for_request(
                    upstream_id, timeout_s=2.0, cancel_event=inflight.cancel_event
                )
                if recovered_session is not None:
                    # Re-add the recovered session to the index
                    self._sessions.add(recovered_session)
                    session = recovered_session
                    payload["recovered"] = True
        else:
            session = self._sessions.get(conversation_id)

        if session is not None:
            payload["session"] = _session_info_payload(session)
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=is_error))

    def _handle_delete_session_tool(self, msg_id: Any, args: dict) -> dict:
        cid = args.get("conversationId")
        if not isinstance(cid, str) or not cid:
            return _jsonrpc_response(msg_id, _tool_text_result("conversationId is required", is_error=True))

        delete_rollout = args.get("deleteRollout", False)
        rollout_deleted = False
        rollout_error = None

        # Get session info before deleting (to get rollout path)
        session = self._sessions.get(cid)
        rollout_path = session.rollout_path if session else None

        deleted = self._sessions.delete(cid)
        if not deleted:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Session not found: {cid}", is_error=True))

        # Optionally delete the rollout file
        if delete_rollout and rollout_path:
            try:
                path = Path(rollout_path)
                if path.exists():
                    path.unlink()
                    rollout_deleted = True
            except Exception as e:
                rollout_error = str(e)

        result = {"deleted": True, "conversationId": cid}
        if delete_rollout:
            result["rolloutDeleted"] = rollout_deleted
            if rollout_error:
                result["rolloutError"] = rollout_error

        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(result), is_error=False))

    def _handle_read_rollout_tool(self, msg_id: Any, args: dict) -> dict:
        cid = args.get("conversationId")
        if not isinstance(cid, str) or not cid:
            return _jsonrpc_response(msg_id, _tool_text_result("conversationId is required", is_error=True))

        lines_count = args.get("lines", 50)
        if not isinstance(lines_count, int):
            lines_count = 50
        lines_count = max(1, min(500, lines_count))

        session = self._sessions.get(cid)
        if session is None:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Session not found: {cid}", is_error=True))

        rollout_path = session.rollout_path
        if not rollout_path:
            return _jsonrpc_response(msg_id, _tool_text_result("Session has no rollout path", is_error=True))

        try:
            path = Path(rollout_path)
            if not path.exists():
                return _jsonrpc_response(msg_id, _tool_text_result(f"Rollout file not found: {rollout_path}", is_error=True))

            # Read last N lines efficiently
            with path.open("r", encoding="utf-8") as f:
                all_lines = f.readlines()
            last_lines = all_lines[-lines_count:]

            payload = {
                "conversationId": cid,
                "rolloutPath": rollout_path,
                "linesRequested": lines_count,
                "linesReturned": len(last_lines),
                "totalLines": len(all_lines),
                "content": "".join(last_lines),
            }
            return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))
        except Exception as e:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Error reading rollout: {e}", is_error=True))

    def _handle_export_session_tool(self, msg_id: Any, args: dict) -> dict:
        cid = args.get("conversationId")
        if not isinstance(cid, str) or not cid:
            return _jsonrpc_response(msg_id, _tool_text_result("conversationId is required", is_error=True))

        export_format = args.get("format", "markdown")
        if export_format not in ("markdown", "json"):
            export_format = "markdown"

        session = self._sessions.get(cid)
        if session is None:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Session not found: {cid}", is_error=True))

        rollout_path = session.rollout_path
        if not rollout_path:
            return _jsonrpc_response(msg_id, _tool_text_result("Session has no rollout path", is_error=True))

        try:
            path = Path(rollout_path)
            if not path.exists():
                return _jsonrpc_response(msg_id, _tool_text_result(f"Rollout file not found: {rollout_path}", is_error=True))

            # Parse the rollout JSONL file
            messages: List[dict] = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    event_type = entry.get("type")
                    payload = entry.get("payload", {})

                    # Extract user messages
                    if event_type == "event_msg" and payload.get("type") == "user_message":
                        messages.append({
                            "role": "user",
                            "content": payload.get("message", ""),
                            "timestamp": entry.get("timestamp"),
                        })

                    # Extract assistant messages
                    if event_type == "event_msg" and payload.get("type") == "agent_message":
                        messages.append({
                            "role": "assistant",
                            "content": payload.get("message", ""),
                            "timestamp": entry.get("timestamp"),
                        })

                    # Also capture response_item messages for completeness
                    if event_type == "response_item" and payload.get("type") == "message":
                        role = payload.get("role")
                        content_items = payload.get("content", [])
                        text_parts = []
                        for item in content_items:
                            if isinstance(item, dict) and item.get("type") in ("input_text", "output_text"):
                                text = item.get("text", "")
                                if text:
                                    text_parts.append(text)
                        if text_parts and role in ("user", "assistant"):
                            # Skip if this is a duplicate of an event_msg we already captured
                            combined_text = "\n".join(text_parts)
                            if not messages or messages[-1].get("content") != combined_text:
                                messages.append({
                                    "role": role,
                                    "content": combined_text,
                                    "timestamp": entry.get("timestamp"),
                                })

            if export_format == "json":
                payload = {
                    "conversationId": cid,
                    "name": session.name,
                    "model": session.model,
                    "messages": messages,
                }
                return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

            # Format as markdown
            md_lines = [
                f"# Codex Session: {session.name or cid}",
                "",
                "## Metadata",
                f"- **Conversation ID**: `{cid}`",
                f"- **Model**: {session.model or 'unknown'}",
                f"- **Sandbox**: {session.sandbox_policy.get('type', 'unknown') if session.sandbox_policy else 'unknown'}",
                f"- **Reasoning Effort**: {session.reasoning_effort or 'unknown'}",
                "",
                "## Conversation",
                "",
            ]

            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")

                if role == "user":
                    md_lines.append(f"### User {f'({timestamp})' if timestamp else ''}")
                else:
                    md_lines.append(f"### Assistant {f'({timestamp})' if timestamp else ''}")

                md_lines.append("")
                md_lines.append(content)
                md_lines.append("")

            markdown = "\n".join(md_lines)
            payload = {
                "conversationId": cid,
                "format": "markdown",
                "content": markdown,
            }
            return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

        except Exception as e:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Error exporting session: {e}", is_error=True))

    def _handle_bridge_info_tool(self, msg_id: Any) -> dict:
        codex_version = _get_codex_version(self._codex_binary) if self._codex_binary else None
        upstream_info = self._client.server_info() if self._client is not None else None
        payload = {
            "bridgeVersion": BRIDGE_VERSION,
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "codexBinary": self._codex_binary,
            "codexBinaryError": self._codex_binary_error,
            "codexCliVersion": codex_version,
            "upstreamServerInfo": upstream_info,
            "stateDir": str(self._state_dir),
            "sessionsFile": str(self._sessions.path),
            "sessionCount": self._sessions.count(),
        }
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

    def _handle_bridge_options_tool(self, msg_id: Any) -> dict:
        enums: dict = {}
        if self._codex_binary:
            schema_path = _ensure_schema_cache(self._codex_binary, self._state_dir)
            if schema_path is not None:
                enums = _extract_enums_from_schema(schema_path)
        if not enums.get("reasoningEffort"):
            enums["reasoningEffort"] = ["none", "minimal", "low", "medium", "high", "xhigh"]
        if not enums.get("reasoningSummary"):
            enums["reasoningSummary"] = ["auto", "concise", "detailed", "none"]

        models = _discover_gpt52_models(self._codex_binary or "", self._sessions) if self._codex_binary else None
        payload = {
            "sandboxModes": ["read-only", "workspace-write", "danger-full-access"],
            "approvalPolicies": ["untrusted", "on-failure", "on-request", "never"],
            "reasoningEffortValues": enums.get("reasoningEffort"),
            "reasoningSummaryValues": enums.get("reasoningSummary"),
            "networkAccessValues": enums.get("networkAccess") or ["restricted", "enabled"],
            "models": models,
            "configKeys": {
                "reasoningEffort": "model_reasoning_effort",
                "reasoningSummary": "model_reasoning_summary",
            },
            "defaults": {
                "reasoningEffort": DEFAULT_REASONING_EFFORT,
                "sandbox": DEFAULT_SANDBOX,
                "taskTypes": TASK_TYPES,
                "taskModelDefaults": TASK_MODEL_DEFAULTS,
                "defaultTaskType": DEFAULT_TASK_TYPE,
            },
        }
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

    def _handle_sessions_list_tool(self, msg_id: Any, args: dict) -> dict:
        limit = args.get("limit")
        cursor = args.get("cursor")
        query = args.get("query")
        if limit is None:
            limit_int = 50
        elif isinstance(limit, int):
            limit_int = max(1, min(200, limit))
        else:
            return _jsonrpc_response(msg_id, _tool_text_result("limit must be an integer", is_error=True))
        if cursor is not None and not isinstance(cursor, str):
            return _jsonrpc_response(msg_id, _tool_text_result("cursor must be a string", is_error=True))
        if query is not None and not isinstance(query, str):
            return _jsonrpc_response(msg_id, _tool_text_result("query must be a string", is_error=True))

        # If query is provided, search by name instead of listing
        if query:
            results = self._sessions.search(query=query, limit=limit_int)
            payload = {"data": [_session_info_payload(info) for info in results], "nextCursor": None}
        else:
            payload = self._sessions.list(limit=limit_int, cursor=cursor)
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

    def _handle_name_session_tool(self, msg_id: Any, args: dict) -> dict:
        cid = args.get("conversationId")
        name = args.get("name")
        if not isinstance(cid, str) or not cid:
            return _jsonrpc_response(msg_id, _tool_text_result("conversationId is required", is_error=True))
        if not isinstance(name, str) or not name:
            return _jsonrpc_response(msg_id, _tool_text_result("name is required", is_error=True))
        updated = self._sessions.update(conversation_id=cid, name=name)
        if updated is None:
            return _jsonrpc_response(msg_id, _tool_text_result(f"Session not found: {cid}", is_error=True))
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(_session_info_payload(updated)), is_error=False))

    def _handle_session_get_tool(self, msg_id: Any, args: dict) -> dict:
        cid = args.get("conversationId")
        if not isinstance(cid, str) or not cid:
            return _jsonrpc_response(msg_id, _tool_text_result("conversationId must be a string", is_error=True))
        info = self._sessions.get(cid)
        payload = _session_info_payload(info) if info is not None else None
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

    def _tool_call_worker(self, msg_id: Any, tool_name: str, args: dict) -> None:
        try:
            with self._inflight_lock:
                inflight = self._inflight.get(msg_id)
            if inflight is None:
                return

            if tool_name == "codex":
                resp = self._handle_codex_tool(msg_id, args, inflight)
                self._send(resp)
                return
            if tool_name == "codex-reply":
                resp = self._handle_codex_reply_tool(msg_id, args, inflight)
                self._send(resp)
                return
            if tool_name == "codex-bridge-info":
                self._send(self._handle_bridge_info_tool(msg_id))
                return
            if tool_name == "codex-bridge-options":
                self._send(self._handle_bridge_options_tool(msg_id))
                return
            if tool_name == "codex-bridge-sessions":
                self._send(self._handle_sessions_list_tool(msg_id, args))
                return
            if tool_name == "codex-bridge-session":
                self._send(self._handle_session_get_tool(msg_id, args))
                return
            if tool_name == "codex-bridge-name-session":
                self._send(self._handle_name_session_tool(msg_id, args))
                return
            if tool_name == "codex-bridge-delete-session":
                self._send(self._handle_delete_session_tool(msg_id, args))
                return
            if tool_name == "codex-bridge-read-rollout":
                self._send(self._handle_read_rollout_tool(msg_id, args))
                return
            if tool_name == "codex-bridge-export-session":
                self._send(self._handle_export_session_tool(msg_id, args))
                return

            self._send(
                _jsonrpc_response(
                    msg_id,
                    _tool_text_result(f"Unknown tool: {tool_name}", is_error=True),
                )
            )
        except CancelledError as e:
            self._send(_jsonrpc_response(msg_id, _tool_text_result(str(e), is_error=True)))
        except TimeoutError as e:
            self._send(_jsonrpc_response(msg_id, _tool_text_result(str(e), is_error=True)))
        except Exception as e:
            self._send(_jsonrpc_response(msg_id, _tool_text_result(f"Bridge error: {e}", is_error=True)))
        finally:
            with self._inflight_lock:
                self._inflight.pop(msg_id, None)

    def handle(self, msg: dict) -> Any:
        method = msg.get("method")
        msg_id = msg.get("id")

        # JSON-RPC 2.0: id must be String, Number, or Null when present
        # Note: bool is subclass of int in Python, so explicitly reject it
        if "id" in msg and (isinstance(msg_id, bool) or not isinstance(msg_id, (str, int, float, type(None)))):
            return _jsonrpc_error(None, JSONRPC_INVALID_REQUEST, "Invalid Request: id must be string, number, or null")

        if method == "initialize" and msg_id is not None:
            params = msg.get("params") or {}
            requested_version = None
            if isinstance(params, dict):
                pv = params.get("protocolVersion")
                if isinstance(pv, str) and pv:
                    requested_version = pv
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": requested_version or MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {"name": "codex-bridge", "title": "Codex Bridge", "version": BRIDGE_VERSION},
                },
            }

        if method == "shutdown" and msg_id is not None:
            return _jsonrpc_response(msg_id, None)

        if method == "exit":
            self._should_exit.set()
            return None

        if method == "$/cancelRequest":
            params = msg.get("params") or {}
            cancel_id = params.get("id")
            with self._inflight_lock:
                inflight = self._inflight.get(cancel_id)
            if inflight is not None:
                inflight.cancel_event.set()
                if inflight.upstream_request_id is not None:
                    try:
                        self._get_client().cancel_request(inflight.upstream_request_id)
                    except Exception:
                        pass
            return None

        if method == "tools/list" and msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": self._tools_list()}}

        if method == "prompts/list" and msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}

        if method == "resources/list" and msg_id is not None:
            resources = [
                {
                    "uri": "codex-bridge://info",
                    "name": "Codex Bridge Info",
                    "mimeType": "application/json",
                    "description": "Bridge versions and state.",
                },
                {
                    "uri": "codex-bridge://options",
                    "name": "Codex Bridge Options",
                    "mimeType": "application/json",
                    "description": "Common models/enums/options.",
                },
                {
                    "uri": "codex-bridge://sessions",
                    "name": "Codex Bridge Sessions",
                    "mimeType": "application/json",
                    "description": "Known conversations captured by the bridge.",
                },
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": resources}}

        if method == "resources/read" and msg_id is not None:
            params = msg.get("params") or {}
            uri = params.get("uri")
            if not isinstance(uri, str):
                return _jsonrpc_error(msg_id, JSONRPC_INVALID_PARAMS, "resources/read requires {uri: string}")
            if uri == "codex-bridge://info":
                info = json.loads(self._handle_bridge_info_tool(0)["result"]["content"][0]["text"])
                return _jsonrpc_response(
                    msg_id, {"contents": [{"uri": uri, "mimeType": "application/json", "text": _json_dumps(info)}]}
                )
            if uri == "codex-bridge://options":
                info = json.loads(self._handle_bridge_options_tool(0)["result"]["content"][0]["text"])
                return _jsonrpc_response(
                    msg_id, {"contents": [{"uri": uri, "mimeType": "application/json", "text": _json_dumps(info)}]}
                )
            if uri == "codex-bridge://sessions":
                info = json.loads(self._handle_sessions_list_tool(0, {})["result"]["content"][0]["text"])
                return _jsonrpc_response(
                    msg_id, {"contents": [{"uri": uri, "mimeType": "application/json", "text": _json_dumps(info)}]}
                )
            if uri.startswith("codex-bridge://session/"):
                cid = uri.split("/", 3)[-1]
                info_obj = json.loads(self._handle_session_get_tool(0, {"conversationId": cid})["result"]["content"][0]["text"])
                return _jsonrpc_response(
                    msg_id,
                    {"contents": [{"uri": uri, "mimeType": "application/json", "text": _json_dumps(info_obj)}]},
                )
            return _jsonrpc_error(msg_id, JSONRPC_INVALID_PARAMS, f"Unknown resource URI: {uri}")

        if method == "resources/templates/list" and msg_id is not None:
            templates = [
                {
                    "uriTemplate": "codex-bridge://session/{conversationId}",
                    "name": "Session by conversationId",
                    "description": "Session metadata captured by the bridge.",
                }
            ]
            return _jsonrpc_response(msg_id, {"resourceTemplates": templates})

        if method == "tools/call" and msg_id is not None:
            params = msg.get("params") or {}
            tool_name = params.get("name")
            args = params.get("arguments") or {}
            if not isinstance(tool_name, str):
                return _jsonrpc_response(
                    msg_id, _tool_text_result("tools/call requires params.name: string", is_error=True)
                )
            if not isinstance(args, dict):
                return _jsonrpc_response(
                    msg_id, _tool_text_result("tools/call requires params.arguments: object", is_error=True)
                )
            with self._inflight_lock:
                if msg_id in self._inflight:
                    return _jsonrpc_response(
                        msg_id, _tool_text_result("Duplicate request id (already in-flight)", is_error=True)
                    )
                inflight = InflightRequest(cancel_event=threading.Event())
                self._inflight[msg_id] = inflight
            t = threading.Thread(target=self._tool_call_worker, args=(msg_id, tool_name, dict(args)), daemon=True)
            t.start()
            return _ASYNC

        if msg_id is not None:
            return _jsonrpc_error(msg_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}")
        return None

    def should_exit(self) -> bool:
        return self._should_exit.is_set()


def main() -> None:
    server = CodexBridgeServer()
    for line in sys.stdin:
        msg, err_code, err_msg = _try_parse_json(line)
        if err_code is not None:
            # Parse errors do not include an id.
            server._send(_jsonrpc_error(None, err_code, err_msg or "Error"))
            continue
        if not msg:
            continue
        resp = server.handle(msg)
        if resp is not None and resp is not _ASYNC:
            server._send(resp)
        if server.should_exit():
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
