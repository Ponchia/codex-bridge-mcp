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
from typing import Dict, Optional


MCP_PROTOCOL_VERSION = "2024-11-05"


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr, flush=True)


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _read_json_line(line: str) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        _eprint("[codex-bridge] Failed to parse JSON line:", line[:500])
        return None
    if isinstance(msg, dict):
        return msg
    return None


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
class ToolResult:
    output_text: str
    is_error: bool
    conversation_id: Optional[str] = None


class CodexMcpClient:
    def __init__(self, codex_binary: str) -> None:
        self._codex_binary = codex_binary
        self._proc = subprocess.Popen(
            [codex_binary, "mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 1
        self._pending: Dict[int, queue.Queue] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._session_id_by_request_id: Dict[int, str] = {}

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

    def _read_stderr(self) -> None:
        assert self._proc.stderr is not None
        for line in self._proc.stderr:
            _eprint("[codex] " + line.rstrip("\n"))

    def _read_stdout(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            msg = _read_json_line(line)
            if not msg:
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
                    self._session_id_by_request_id[request_id] = event["session_id"]
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
        rid = self._next_id
        self._next_id += 1
        return rid

    def _send(self, msg: dict) -> None:
        if not self._proc.stdin:
            raise RuntimeError("Codex MCP stdin is closed")
        payload = _json_dumps(msg) + "\n"
        with self._write_lock:
            self._proc.stdin.write(payload)
            self._proc.stdin.flush()

    def _request(self, method: str, params: Optional[dict] = None, timeout_s: float = 120.0) -> dict:
        rid = self._new_id()
        q: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[rid] = q

        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        try:
            return q.get(timeout=timeout_s)
        except queue.Empty as e:
            raise TimeoutError(f"Timed out waiting for Codex MCP response to {method}") from e

    def _initialize(self) -> None:
        self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "codex-bridge", "version": "0.1.0"},
            },
            timeout_s=15.0,
        )
        # Codex MCP server (currently) doesn't implement notifications/initialized; skip it.

    def run_codex(self, arguments: dict) -> ToolResult:
        rid = self._new_id()
        q: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[rid] = q

        self._send(
            {
                "jsonrpc": "2.0",
                "id": rid,
                "method": "tools/call",
                "params": {"name": "codex", "arguments": arguments},
            }
        )

        try:
            resp = q.get(timeout=600.0)
        except queue.Empty as e:
            raise TimeoutError("Timed out waiting for Codex tool response") from e

        conversation_id = None
        for _ in range(200):
            conversation_id = self._session_id_by_request_id.get(rid)
            if conversation_id:
                break
            time.sleep(0.01)

        result = resp.get("result") or {}
        if isinstance(result, dict) and result.get("isError") is True:
            return ToolResult(output_text=_extract_text(result), is_error=True, conversation_id=conversation_id)

        if isinstance(result, dict) and isinstance(result.get("error"), str):
            return ToolResult(output_text=result["error"], is_error=True, conversation_id=conversation_id)

        return ToolResult(output_text=_extract_text(result), is_error=False, conversation_id=conversation_id)

    def run_codex_reply(self, conversation_id: str, prompt: str) -> ToolResult:
        resp = self._request(
            "tools/call",
            {"name": "codex-reply", "arguments": {"conversationId": conversation_id, "prompt": prompt}},
            timeout_s=600.0,
        )
        result = resp.get("result") or {}
        if isinstance(result, dict) and result.get("isError") is True:
            return ToolResult(output_text=_extract_text(result), is_error=True, conversation_id=conversation_id)
        if isinstance(result, dict) and isinstance(result.get("error"), str):
            return ToolResult(output_text=result["error"], is_error=True, conversation_id=conversation_id)
        return ToolResult(output_text=_extract_text(result), is_error=False, conversation_id=conversation_id)


def _extract_text(result: dict) -> str:
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
    if isinstance(result.get("content"), str):
        return result["content"]
    return _json_dumps(result)


def _bridge_tools() -> list:
    return [
        {
            "name": "codex",
            "description": "Run a Codex session and return JSON {conversationId, output}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "User prompt to start the Codex session."},
                    "model": {"type": "string", "description": "Optional model override (e.g. \"o3\", \"gpt-5.2-codex\")."},
                    "profile": {"type": "string", "description": "Optional Codex config profile name."},
                    "cwd": {"type": "string", "description": "Optional working directory."},
                    "sandbox": {
                        "type": "string",
                        "description": "Sandbox mode: read-only, workspace-write, or danger-full-access.",
                    },
                    "approval-policy": {
                        "type": "string",
                        "description": "Approval policy: untrusted, on-failure, on-request, never.",
                    },
                    "config": {
                        "type": "object",
                        "description": "Config overrides (mapped to Codex CLI -c values).",
                        "additionalProperties": True,
                    },
                    "base-instructions": {"type": "string", "description": "Optional base instructions for Codex."},
                    "developer-instructions": {"type": "string", "description": "Optional developer instructions for Codex."},
                    "compact-prompt": {"type": "string", "description": "Prompt used when Codex compacts the conversation."},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "codex-reply",
            "description": "Continue a Codex conversation. Returns JSON {conversationId, output}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string", "description": "Conversation/session id returned by codex."},
                    "prompt": {"type": "string", "description": "User prompt to continue the conversation."},
                },
                "required": ["conversationId", "prompt"],
            },
        },
    ]


class CodexBridgeServer:
    def __init__(self) -> None:
        self._client: Optional[CodexMcpClient] = None
        self._codex_binary = _find_codex_binary()

    def _get_client(self) -> CodexMcpClient:
        if self._client is None or not self._client.is_alive():
            if self._client is not None:
                self._client.close()
            self._client = CodexMcpClient(self._codex_binary)
        return self._client

    def handle(self, msg: dict) -> Optional[dict]:
        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize" and msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "codex-bridge", "title": "Codex Bridge", "version": "0.1.0"},
                },
            }

        if method == "tools/list" and msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": _bridge_tools()}}

        if method == "prompts/list" and msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}

        if method == "resources/list" and msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}

        if method == "tools/call" and msg_id is not None:
            params = msg.get("params") or {}
            tool_name = params.get("name")
            args = params.get("arguments") or {}

            if tool_name == "codex":
                client = self._get_client()
                res = client.run_codex(dict(args))
                payload = {"conversationId": res.conversation_id, "output": res.output_text}
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": _json_dumps(payload)}],
                        "isError": bool(res.is_error),
                    },
                }

            if tool_name == "codex-reply":
                conversation_id = args.get("conversationId")
                prompt = args.get("prompt")
                if not isinstance(conversation_id, str) or not isinstance(prompt, str):
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "codex-reply requires {conversationId: string, prompt: string}",
                                }
                            ],
                            "isError": True,
                        },
                    }
                client = self._get_client()
                res = client.run_codex_reply(conversation_id, prompt)
                payload = {"conversationId": res.conversation_id, "output": res.output_text}
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": _json_dumps(payload)}],
                        "isError": bool(res.is_error),
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True,
                },
            }

        return None


def main() -> None:
    server = CodexBridgeServer()
    for line in sys.stdin:
        msg = _read_json_line(line)
        if not msg:
            continue
        resp = server.handle(msg)
        if resp is not None:
            sys.stdout.write(_json_dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

