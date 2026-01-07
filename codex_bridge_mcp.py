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


MCP_PROTOCOL_VERSION = "2024-11-05"
BRIDGE_VERSION = "0.3.0"

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

    @staticmethod
    def from_session_configured_event(event: dict) -> Optional["SessionInfo"]:
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
                        )
                    except Exception:
                        continue
                    if conversation_id not in self._by_id:
                        self._order.append(conversation_id)
                    self._by_id[conversation_id] = info
        except OSError:
            return

    def add(self, info: SessionInfo) -> None:
        with self._lock:
            if info.conversation_id in self._by_id:
                return
            self._by_id[info.conversation_id] = info
            self._order.append(info.conversation_id)
            record = {
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
            }
            try:
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(_json_dumps(record) + "\n")
            except OSError:
                pass

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


def _discover_gpt52_models(codex_binary: str, sessions: SessionStore) -> dict:
    known = ["gpt-5.2", "gpt-5.2-codex", "gpt-5.2-mini", "gpt-5.2-nano"]
    seen = set(known)
    discovered = list(known)

    # Also include anything we have actually seen in session_configured events.
    try:
        with sessions._lock:
            for info in sessions._by_id.values():
                if info.model and info.model.startswith("gpt-5.2") and info.model not in seen:
                    seen.add(info.model)
                    discovered.append(info.model)
    except Exception:
        pass
    return {
        "known": known,
        "discovered": discovered,
        "notes": [
            "Model availability depends on your Codex auth mode and account entitlements.",
            "If a model hangs, cancel the request or lower timeoutMs.",
        ],
    }


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
            "description": "Run a Codex session and return JSON {conversationId, output, session}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Initial user prompt."},
                    "model": {"type": "string", "description": "Optional override for the model name."},
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
            "description": "List known Codex conversations captured by the bridge. Returns JSON {data,nextCursor}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max items to return (default 50)."},
                    "cursor": {"type": "string", "description": "Pagination cursor from a previous call."},
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

        client = self._get_client()
        upstream_id, resp = client.call_tool(
            "codex", args, timeout_s=timeout_s, cancel_event=inflight.cancel_event
        )
        inflight.upstream_request_id = upstream_id

        session = client.get_session_for_request(
            upstream_id, timeout_s=startup_timeout_s, cancel_event=inflight.cancel_event
        )

        output_text, is_error = _normalize_upstream_tool_response(resp)
        payload: Dict[str, Any] = {"conversationId": session.conversation_id if session else None, "output": output_text}
        if session is not None:
            payload["session"] = _session_info_payload(session)
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
        session = self._sessions.get(conversation_id)
        if session is not None:
            payload["session"] = _session_info_payload(session)
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=is_error))

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
            "gpt52Models": models,
            "configKeys": {
                "reasoningEffort": "model_reasoning_effort",
                "reasoningSummary": "model_reasoning_summary",
            },
        }
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

    def _handle_sessions_list_tool(self, msg_id: Any, args: dict) -> dict:
        limit = args.get("limit")
        cursor = args.get("cursor")
        if limit is None:
            limit_int = 50
        elif isinstance(limit, int):
            limit_int = max(1, min(200, limit))
        else:
            return _jsonrpc_response(msg_id, _tool_text_result("limit must be an integer", is_error=True))
        if cursor is not None and not isinstance(cursor, str):
            return _jsonrpc_response(msg_id, _tool_text_result("cursor must be a string", is_error=True))
        payload = self._sessions.list(limit=limit_int, cursor=cursor)
        return _jsonrpc_response(msg_id, _tool_text_result(_json_dumps(payload), is_error=False))

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

        if method == "initialize" and msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
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
