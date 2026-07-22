"""
MCP Server for Working Bibliography Extension.

Implements JSON-RPC 2.0 over HTTP, following the same pattern as
Librarian's MCPController.swift.

Endpoints:
  POST /mcp  — JSON-RPC 2.0 handler (supports tools/list and tools/call)

The server validates every request against the capability manifest,
permissions config, and lifecycle state before executing any tool.

Per the extension contract (WB-LIBRARIAN-CONTRACT-v1):
  - Only declared active capabilities are available through tools/list
  - Every tool call is permission-checked and produces a receipt
  - Undeclared operations are rejected
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.mcp import tools, permissions, receipts


MCP_VERSION = "1.0.0"
EXTENSION_ID = "working-bibliography-extension"
DEFAULT_PORT = 8765


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP JSON-RPC 2.0."""

    def do_POST(self):
        """Handle POST requests to /mcp."""
        if self.path != "/mcp":
            self._send_error(404, "Not found. Use POST /mcp")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_jsonrpc_error(None, -32700, "Parse error: invalid JSON")
            return

        # Validate JSON-RPC 2.0 structure
        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        req_id = request.get("id")

        if jsonrpc != "2.0":
            self._send_jsonrpc_error(req_id, -32600, f"Invalid Request: jsonrpc must be '2.0', got '{jsonrpc}'")
            return

        if not method:
            self._send_jsonrpc_error(req_id, -32600, "Invalid Request: method is required")
            return

        params = request.get("params", {})

        # Route method
        if method == "tools/list":
            response = self._handle_tools_list(req_id)
        elif method == "tools/call":
            response = self._handle_tools_call(req_id, params)
        else:
            response = self._make_response(req_id, None, {
                "code": -32601,
                "message": f"Method not found: {method}"
            })

        self._send_json(response)

    def do_GET(self):
        """Handle GET for health check."""
        if self.path == "/health":
            health = {
                "status": "ok",
                "extension_id": EXTENSION_ID,
                "version": "0.1.0",
                "mcp_version": MCP_VERSION,
                "lifecycle_state": permissions.get_lifecycle_state(),
                "uptime": (datetime.now(timezone.utc) - self.server.start_time).total_seconds() if hasattr(self.server, 'start_time') else 0
            }
            self._send_json({"jsonrpc": "2.0", "result": health, "id": None})
        else:
            self._send_error(404, "Not found")

    def _handle_tools_list(self, req_id):
        """Handle tools/list — return declared capabilities."""
        tool_defs = tools.get_tool_definitions()
        return self._make_response(req_id, {"tools": tool_defs})

    def _handle_tools_call(self, req_id, params):
        """Handle tools/call — execute a tool with permission enforcement."""
        tool_name = params.get("name") if isinstance(params, dict) else None
        arguments = params.get("arguments", {}) if isinstance(params, dict) else {}

        if not tool_name:
            return self._make_response(req_id, None, {
                "code": -32602,
                "message": "Invalid params: 'name' is required"
            })

        # Check lifecycle state first
        state = permissions.get_lifecycle_state()
        if state != "ACTIVE":
            return self._make_response(req_id, None, {
                "code": -32000,
                "message": f"Extension is in {state} state. Capabilities require ACTIVE state.",
                "data": {"lifecycle_state": state, "required_state": "ACTIVE"}
            })

        result = tools.call_tool(tool_name, arguments)
        if result.get("isError"):
            error_text = result.get("content", [{}])[0].get("text", "Unknown error")
            return self._make_response(req_id, None, {
                "code": -32000,
                "message": error_text
            })
        return self._make_response(req_id, result.get("content"), None)

    def _make_response(self, req_id, result, error=None):
        """Build a JSON-RPC 2.0 response."""
        resp = {"jsonrpc": "2.0"}
        if req_id is not None:
            resp["id"] = req_id
        if error:
            resp["error"] = error if isinstance(error, dict) else {"code": -32000, "message": str(error)}
        else:
            resp["result"] = result
        return resp

    def _send_jsonrpc_error(self, req_id, code, message):
        """Send a JSON-RPC error response."""
        error = {"code": code, "message": message}
        response = self._make_response(req_id, None, error)
        self._send_json(response)

    def _send_json(self, data):
        """Send a JSON response."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, message):
        """Send an HTTP error response."""
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default HTTP logging for cleaner output."""
        if os.environ.get("WB_MCP_VERBOSE"):
            super().log_message(format, *args)


def start_server(port: int = DEFAULT_PORT):
    """Start the MCP server."""
    server = HTTPServer(("127.0.0.1", port), MCPRequestHandler)
    server.start_time = datetime.now(timezone.utc)

    print(f"Working Bibliography Extension MCP Server")
    print(f"  Extension:  {EXTENSION_ID}")
    print(f"  Version:    0.1.0")
    print(f"  MCP:        {MCP_VERSION}")
    print(f"  Endpoint:   http://127.0.0.1:{port}/mcp")
    print(f"  Health:     http://127.0.0.1:{port}/health")
    print(f"  Lifecycle:  {permissions.get_lifecycle_state()}")
    print(f"  Tools:      {len(tools.get_tool_definitions())} active")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down MCP server...")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    start_server(port)
