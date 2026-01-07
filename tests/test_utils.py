"""Tests for utility functions in codex_bridge_mcp."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from io import StringIO

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import codex_bridge_mcp as cbm


class TestJsonDumps:
    """Tests for _json_dumps function."""

    def test_simple_object(self):
        result = cbm._json_dumps({"key": "value"})
        assert result == '{"key":"value"}'

    def test_nested_object(self):
        result = cbm._json_dumps({"outer": {"inner": 123}})
        assert result == '{"outer":{"inner":123}}'

    def test_unicode_preserved(self):
        result = cbm._json_dumps({"emoji": "Hello"})
        assert "Hello" in result
        # ensure_ascii=False should preserve unicode
        assert "\\u" not in result or "Hello" in result

    def test_list(self):
        result = cbm._json_dumps([1, 2, 3])
        assert result == "[1,2,3]"

    def test_compact_separators(self):
        # No spaces after : or ,
        result = cbm._json_dumps({"a": 1, "b": 2})
        assert " " not in result


class TestTryParseJson:
    """Tests for _try_parse_json function."""

    def test_valid_json_object(self):
        msg, err_code, err_msg = cbm._try_parse_json('{"jsonrpc": "2.0", "id": 1}')
        assert msg == {"jsonrpc": "2.0", "id": 1}
        assert err_code is None
        assert err_msg is None

    def test_empty_string(self):
        msg, err_code, err_msg = cbm._try_parse_json("")
        assert msg is None
        assert err_code is None
        assert err_msg is None

    def test_whitespace_only(self):
        msg, err_code, err_msg = cbm._try_parse_json("   \n\t  ")
        assert msg is None
        assert err_code is None
        assert err_msg is None

    def test_invalid_json(self):
        msg, err_code, err_msg = cbm._try_parse_json("{invalid json}")
        assert msg is None
        assert err_code == cbm.JSONRPC_PARSE_ERROR
        assert err_msg == "Parse error"

    def test_json_array_invalid_request(self):
        # JSON-RPC messages must be objects, not arrays
        msg, err_code, err_msg = cbm._try_parse_json("[1, 2, 3]")
        assert msg is None
        assert err_code == cbm.JSONRPC_INVALID_REQUEST
        assert err_msg == "Invalid Request"

    def test_json_primitive_invalid_request(self):
        msg, err_code, err_msg = cbm._try_parse_json('"just a string"')
        assert msg is None
        assert err_code == cbm.JSONRPC_INVALID_REQUEST
        assert err_msg == "Invalid Request"

    def test_strips_whitespace(self):
        msg, err_code, err_msg = cbm._try_parse_json('  {"id": 1}  \n')
        assert msg == {"id": 1}
        assert err_code is None


class TestJsonrpcResponse:
    """Tests for _jsonrpc_response function."""

    def test_basic_response(self):
        result = cbm._jsonrpc_response(1, {"status": "ok"})
        assert result == {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"},
        }

    def test_null_id(self):
        result = cbm._jsonrpc_response(None, "result")
        assert result["id"] is None

    def test_string_id(self):
        result = cbm._jsonrpc_response("req-123", [1, 2, 3])
        assert result["id"] == "req-123"
        assert result["result"] == [1, 2, 3]


class TestJsonrpcError:
    """Tests for _jsonrpc_error function."""

    def test_basic_error(self):
        result = cbm._jsonrpc_error(1, -32600, "Invalid Request")
        assert result == {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request",
            },
        }

    def test_error_with_data(self):
        result = cbm._jsonrpc_error(2, -32603, "Internal error", {"detail": "stack trace"})
        assert result["error"]["data"] == {"detail": "stack trace"}

    def test_error_without_data(self):
        result = cbm._jsonrpc_error(3, -32601, "Method not found")
        assert "data" not in result["error"]

    def test_null_id_for_parse_error(self):
        result = cbm._jsonrpc_error(None, cbm.JSONRPC_PARSE_ERROR, "Parse error")
        assert result["id"] is None


class TestToolTextResult:
    """Tests for _tool_text_result function."""

    def test_success_result(self):
        result = cbm._tool_text_result("Operation completed", False)
        assert result == {
            "content": [{"type": "text", "text": "Operation completed"}],
            "isError": False,
        }

    def test_error_result(self):
        result = cbm._tool_text_result("Something went wrong", True)
        assert result["isError"] is True

    def test_is_error_coerced_to_bool(self):
        # Passing truthy/falsy values should be coerced to bool
        result = cbm._tool_text_result("test", 1)
        assert result["isError"] is True

        result = cbm._tool_text_result("test", 0)
        assert result["isError"] is False


class TestConstants:
    """Tests for module constants."""

    def test_jsonrpc_error_codes(self):
        assert cbm.JSONRPC_PARSE_ERROR == -32700
        assert cbm.JSONRPC_INVALID_REQUEST == -32600
        assert cbm.JSONRPC_METHOD_NOT_FOUND == -32601
        assert cbm.JSONRPC_INVALID_PARAMS == -32602
        assert cbm.JSONRPC_INTERNAL_ERROR == -32603

    def test_bridge_version_format(self):
        # Version should be semver-ish
        parts = cbm.BRIDGE_VERSION.split(".")
        assert len(parts) >= 2
        assert all(p.isdigit() for p in parts)

    def test_mcp_protocol_version(self):
        # Should be a date-like format
        assert "-" in cbm.MCP_PROTOCOL_VERSION
        assert len(cbm.MCP_PROTOCOL_VERSION) == 10  # YYYY-MM-DD


class TestCancelledError:
    """Tests for CancelledError exception."""

    def test_is_runtime_error(self):
        assert issubclass(cbm.CancelledError, RuntimeError)

    def test_can_raise_and_catch(self):
        with pytest.raises(cbm.CancelledError):
            raise cbm.CancelledError("Task cancelled")
