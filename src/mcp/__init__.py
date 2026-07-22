"""
Working Bibliography Extension — MCP Interface

Implements the contract-defined MCP surface for the Working Bibliography
Extension. Follows JSON-RPC 2.0 over HTTP, same pattern as Librarian's
MCPController.swift.

Only capabilities marked "active" in mcp/capabilities.json are exposed
through tools/list. Pending capabilities are contract-defined but unavailable.
"""
