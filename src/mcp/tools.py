"""
Tool implementations for the Working Bibliography MCP interface.

Each tool follows the contract-defined capability surface from
WB-LIBRARIAN-CONTRACT-v1. Tools validate input, enforce permissions,
execute within the ownership boundary, and produce receipts.

Initial tools (active):
  - wb_get_artifact       (R0 — artifact.read)
  - wb_list_artifacts     (R0 — artifact.read)
  - wb_register_artifact  (R1 — artifact.register)
"""

from . import storage, receipts, permissions


def get_tool_definitions() -> list:
    """Return the MCP tool definitions for tools/list.

    Only returns tools for capabilities marked 'active' in the manifest.
    """
    caps = permissions.get_capabilities()
    tools = []

    for cap in caps.get("capabilities", []):
        if cap.get("status") != "active":
            continue
        for tool_name in cap.get("tools", []):
            tool_def = _get_tool_definition(tool_name)
            if tool_def:
                tools.append(tool_def)

    return tools


def _get_tool_definition(tool_name: str) -> dict:
    """Get the MCP tool definition for a single tool."""
    definitions = {
        "wb_get_artifact": {
            "name": "wb_get_artifact",
            "description": "Retrieve a governed knowledge artifact by its artifact ID. Returns artifact metadata, content, provenance, and lifecycle state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "pattern": "^WB-[0-9]{5}$",
                        "description": "The artifact ID to retrieve (format: WB-XXXXX)"
                    }
                },
                "required": ["artifact_id"]
            }
        },
        "wb_list_artifacts": {
            "name": "wb_list_artifacts",
            "description": "List governed knowledge artifacts with optional text filter and pagination. Returns artifact metadata (identity, source title, lifecycle state, captured_at).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "Optional text filter applied to artifact content and metadata"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of artifacts to return (default 100, max 500)",
                        "default": 100
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of artifacts to skip (default 0)",
                        "default": 0
                    }
                }
            }
        },
        "wb_register_artifact": {
            "name": "wb_register_artifact",
            "description": "Create a new governed artifact from captured source material. Validates input, generates artifact identity and content hash, stores the artifact in the extension's storage domain, and produces a capture receipt. Returns the complete artifact record with generated fields.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "object",
                        "description": "Provenance metadata about the original source",
                        "properties": {
                            "url": {"type": "string", "description": "Original source URL"},
                            "title": {"type": "string", "description": "Source title"},
                            "author": {"type": "string", "description": "Source author"},
                            "publisher": {"type": "string", "description": "Source publisher"},
                            "retrieved_at": {"type": "string", "format": "date-time", "description": "When the source was retrieved"}
                        },
                        "required": ["retrieved_at"]
                    },
                    "content": {
                        "type": "object",
                        "description": "Canonical content representation",
                        "properties": {
                            "canonical_text": {"type": "string", "description": "Extracted readable text"},
                            "raw_format": {
                                "type": "string",
                                "enum": ["html", "pdf", "text", "chat_export", "markdown", "json", "unknown"],
                                "description": "Original format"
                            }
                        },
                        "required": ["canonical_text", "raw_format"]
                    },
                    "relationships": {
                        "type": "object",
                        "description": "Optional relationships to other artifacts",
                        "properties": {
                            "derived_from": {"type": "array", "items": {"type": "string"}},
                            "supersedes": {"type": "array", "items": {"type": "string"}},
                            "related_to": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "lifecycle": {
                        "type": "string",
                        "enum": ["active", "archived", "revoked"],
                        "description": "Initial lifecycle state (default: active)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Custom key-value annotations"
                    }
                },
                "required": ["source", "content"]
            }
        }
    }
    return definitions.get(tool_name)


def call_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool call and return the result.

    Args:
        tool_name: The MCP tool name
        arguments: Tool-specific arguments

    Returns:
        dict with 'content' (list of results) or 'isError' (bool)
    """
    # Permission check
    perm = permissions.check_tool_permission(tool_name)
    if not perm.get("allowed"):
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Permission denied: {perm.get('reason', 'Unknown reason')}"}]
        }

    # Forbidden operation check
    forbidden = permissions.check_forbidden_operation(tool_name)
    if forbidden.get("is_forbidden"):
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Forbidden operation: {forbidden.get('rationale', '')}"}]
        }

    # Route to tool implementation
    tool_map = {
        "wb_get_artifact": _tool_get_artifact,
        "wb_list_artifacts": _tool_list_artifacts,
        "wb_register_artifact": _tool_register_artifact,
    }

    handler = tool_map.get(tool_name)
    if not handler:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
        }

    return handler(arguments, perm)


def _tool_get_artifact(arguments: dict, perm: dict) -> dict:
    """Handler for wb_get_artifact."""
    artifact_id = arguments.get("artifact_id")
    if not artifact_id:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Missing required parameter: artifact_id"}]
        }

    artifact = storage.get_artifact(artifact_id)
    if not artifact:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Artifact not found: {artifact_id}"}]
        }

    return {
        "content": [{"type": "text", "text": json.dumps(artifact, indent=2)}]
    }


def _tool_list_artifacts(arguments: dict, perm: dict) -> dict:
    """Handler for wb_list_artifacts."""
    filter_text = arguments.get("filter")
    limit = min(arguments.get("limit", 100), 500)
    offset = arguments.get("offset", 0)

    result = storage.list_artifacts(filter_text=filter_text, limit=limit, offset=offset)

    return {
        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
    }


def _tool_register_artifact(arguments: dict, perm: dict) -> dict:
    """Handler for wb_register_artifact."""
    source = arguments.get("source", {})
    content = arguments.get("content", {})

    # Validate required fields
    if not source.get("retrieved_at"):
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Missing required field: source.retrieved_at"}]
        }
    if not content.get("canonical_text"):
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Missing required field: content.canonical_text"}]
        }
    if content.get("raw_format") not in ("html", "pdf", "text", "chat_export", "markdown", "json", "unknown"):
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Invalid raw_format: {content.get('raw_format')}. Must be one of: html, pdf, text, chat_export, markdown, json, unknown"}]
        }

    # Build artifact data
    artifact_data = {
        "source": source,
        "content": {
            "canonical_text": content["canonical_text"],
            "raw_format": content["raw_format"]
        },
        "relationships": arguments.get("relationships", {}),
        "lifecycle": arguments.get("lifecycle", "active"),
        "metadata": arguments.get("metadata", {})
    }

    # Store artifact
    artifact = storage.store_artifact(artifact_data)

    # Generate capture receipt
    receipt = receipts.generate_capture_receipt(
        artifact_id=artifact["artifact_id"],
        content_hash=artifact["content_hash"],
        source=artifact["source"]
    )

    return {
        "content": [
            {"type": "text", "text": json.dumps(artifact, indent=2)},
            {"type": "text", "text": f"\nCapture receipt: {receipt['receipt_id']}"}
        ]
    }


# Import json for tool handlers
import json
