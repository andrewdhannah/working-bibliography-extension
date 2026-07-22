"""
Permission enforcement for Working Bibliography MCP tools.

Validates every tool call against:
1. The capability manifest (is this tool declared?)
2. The permissions config (is this operation allowed?)
3. The lifecycle state (is the extension active?)
4. The forbidden operations list (is this a forbidden action?)
"""

import json
import os
from datetime import datetime, timezone


MCP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "mcp")


# Runtime lifecycle state (simulated — real implementation would use
# the Librarian extension port layer)
_lifecycle_state = "ACTIVE"
_lifecycle_initialized_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(filename: str) -> dict:
    """Load a JSON configuration file from the mcp/ directory."""
    path = os.path.join(MCP_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def get_capabilities() -> dict:
    """Load the capability manifest."""
    return _load_json("capabilities.json")


def get_permissions() -> dict:
    """Load the permissions configuration."""
    return _load_json("permissions.json")


def get_lifecycle_state() -> str:
    """Get the current extension lifecycle state."""
    return _lifecycle_state


def set_lifecycle_state(state: str) -> str:
    """Set the lifecycle state (for testing and handshake simulation)."""
    global _lifecycle_state, _lifecycle_initialized_at
    allowed_states = ["REGISTERED", "CONTRACT_VERIFIED", "OWNER_APPROVED", "ACTIVE", "SUSPENDED", "REVOKED"]
    if state not in allowed_states:
        raise ValueError(f"Invalid lifecycle state: {state}. Must be one of {allowed_states}")
    _lifecycle_state = state
    return _lifecycle_state


def check_tool_permission(tool_name: str) -> dict:
    """Check whether a tool call is permitted.

    Returns:
        dict with:
            allowed: bool
            reason: str (if denied)
            capability_id: str (if found)
            risk: str (R0/R1)
            produces_receipt: bool
    """
    capabilities = get_capabilities()
    permissions = get_permissions()
    state = get_lifecycle_state()

    # 1. Check lifecycle state — only ACTIVE allows execution
    if state != "ACTIVE":
        return {
            "allowed": False,
            "reason": f"Extension is in {state} state. Capabilities require ACTIVE state.",
            "capability_id": None,
            "risk": None,
            "produces_receipt": False
        }

    # 2. Find which capability declares this tool
    capability_id = None
    for cap in capabilities.get("capabilities", []):
        if tool_name in cap.get("tools", []):
            capability_id = cap.get("id")
            # Check if this capability is active
            if cap.get("status") != "active":
                return {
                    "allowed": False,
                    "reason": f"Capability '{capability_id}' is not active (status: {cap.get('status')}). Not yet implemented.",
                    "capability_id": capability_id,
                    "risk": cap.get("risk"),
                    "produces_receipt": True
                }
            break

    if not capability_id:
        return {
            "allowed": False,
            "reason": f"Tool '{tool_name}' is not declared in the capability manifest.",
            "capability_id": None,
            "risk": None,
            "produces_receipt": False
        }

    # 3. Check permissions config for allowed operations
    for perm_scope, perm_config in permissions.get("allowed_operations", {}).items():
        if tool_name in perm_config.get("tools", []):
            # Check if this permission is pending
            if perm_config.get("status") == "pending":
                return {
                    "allowed": False,
                    "reason": f"Permission scope '{perm_scope}' for tool '{tool_name}' is pending. Not yet implemented.",
                    "capability_id": capability_id,
                    "risk": perm_config.get("risk"),
                    "produces_receipt": perm_config.get("produces_receipt", True)
                }
            return {
                "allowed": True,
                "reason": None,
                "capability_id": capability_id,
                "risk": perm_config.get("risk"),
                "produces_receipt": perm_config.get("produces_receipt", True)
            }

    # 4. Tool found in capabilities but not in permissions — configuration error
    return {
        "allowed": False,
        "reason": f"Tool '{tool_name}' is declared in capabilities but not configured in permissions.",
        "capability_id": capability_id,
        "risk": None,
        "produces_receipt": False
    }


def check_forbidden_operation(operation: str) -> dict:
    """Check whether an operation is in the forbidden list.

    Returns:
        dict with:
            is_forbidden: bool
            outcome: str (SUSPENDED or REVOKE, if forbidden)
            rationale: str (if forbidden)
    """
    permissions = get_permissions()
    for forbidden in permissions.get("forbidden_operations", []):
        if forbidden == operation or operation.startswith(forbidden):
            enforcement = permissions.get("enforcement", {})
            outcomes = enforcement.get("violation_outcomes", {})
            outcome = outcomes.get("contract_breach", "REVOKED")
            return {
                "is_forbidden": True,
                "outcome": outcome,
                "rationale": f"Operation '{operation}' is forbidden by contract (WB-LIBRARIAN-CONTRACT-v1)."
            }

    return {
        "is_forbidden": False,
        "outcome": None,
        "rationale": None
    }
