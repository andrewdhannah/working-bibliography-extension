"""
Projection MCP Adapter — Wraps Projection Service as an MCP Tool

This adapter is designed to be wired into Librarian's MCPController.swift.
It implements the JSON-RPC 2.0 handler pattern that Librarian's MCP server uses:
  - tools/list: declares the librarian_capability_projection tool
  - tools/call: executes the projection and returns results

When wired into Librarian core, the adapter reads from the actual extension
registry and handshake lifecycle state. In standalone mode, it uses fixtures.
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.projection.service import ProjectionService


# MCP tool definition for Librarian integration
PROJECTION_TOOL_DEFINITION = {
    "name": "librarian_capability_projection",
    "description": "Returns the current set of governed extensions with their lifecycle state and declared capabilities. "
                   "This is the single entry point for any consumer to discover available governed capabilities. "
                   "Consumer-agnostic — works with AI agents, CLIs, applications, and services.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "projection_id": {
                "type": "string",
                "description": "Optional — if provided and still current, returns 'unchanged' with no extension data"
            }
        }
    }
}


def handle_projection_call(arguments: dict) -> dict:
    """Handle a tools/call for librarian_capability_projection.
    
    This function can be called directly from Librarian's MCPController.swift
    handleCallTool() switch statement.
    
    Args:
        arguments: dict with optional 'projection_id' key
    
    Returns:
        MCP-compatible result dict with 'content' list
    """
    service = ProjectionStateHolder.get_service()
    known_id = arguments.get("projection_id") if isinstance(arguments, dict) else None
    
    projection = service.build_projection(known_projection_id=known_id)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(projection.to_dict(), indent=2)
            }
        ]
    }


class ProjectionStateHolder:
    """Holds the projection service instance.
    
    In Librarian core mode, this would be initialized at startup with
    access to the extension registry and lifecycle storage.
    """
    _service = None

    @classmethod
    def initialize(cls, state_source: dict = None):
        """Initialize the projection service.
        
        Args:
            state_source: Optional fixture data for testing.
                          If None, reads from live file system.
        """
        cls._service = ProjectionService(state_source=state_source)

    @classmethod
    def get_service(cls) -> ProjectionService:
        if cls._service is None:
            cls._service = ProjectionService()
        return cls._service


# ─── Standalone Server for Testing ───────────────────────────────────

MCP_SERVER_PORT = 8766


class ProjectionMCPHandler(BaseHTTPRequestHandler):
    """MCP-compatible handler for testing the projection endpoint."""

    def do_POST(self):
        if self.path != "/mcp":
            self._send_error(404, "Use POST /mcp")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": [PROJECTION_TOOL_DEFINITION]}
            }
        elif method == "tools/call":
            tool_name = params.get("name") if isinstance(params, dict) else None
            arguments = params.get("arguments", {}) if isinstance(params, dict) else {}

            if tool_name == "librarian_capability_projection":
                result = handle_projection_call(arguments)
                # Ensure result has the MCP standard format
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {tool_name}"}
                }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

        self._send_json(response)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({
                "jsonrpc": "2.0",
                "result": {
                    "service": "capability-projection",
                    "status": "available",
                    "authority": "librarian-core"
                },
                "id": None
            })
        else:
            self._send_error(404, "Not found")

    def _send_json(self, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code, message):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


def start_projection_server(port: int = MCP_SERVER_PORT, state_source: dict = None):
    """Start the standalone projection server for testing."""
    ProjectionStateHolder.initialize(state_source)
    server = HTTPServer(("127.0.0.1", port), ProjectionMCPHandler)

    print(f"Capability Projection Server")
    print(f"  Authority:  librarian-core")
    print(f"  Endpoint:   http://127.0.0.1:{port}/mcp")
    print(f"  Tool:       librarian_capability_projection")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    start_projection_server()
