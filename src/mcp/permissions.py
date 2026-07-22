"""
Permission enforcement for Working Bibliography MCP tools.

Validates every tool call against:
1. The capability manifest (is this tool declared?)
2. The permissions config (is this operation allowed?)
3. The lifecycle state (is the extension active?) — uses handshake module
4. The forbidden operations list (is this a forbidden action?)

The lifecycle state is managed by the handshake module (src/handshake/lifecycle.py).
Before the handshake completes, the extension is in REGISTERED or CONTRACT_VERIFIED
state and capabilities are unavailable.
"""

import json
import os
import sys

# Ensure project root is on path for handshake import
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

MCP_DIR = os.path.join(PROJECT_ROOT, "mcp")

# Import handshake lifecycle if available
try:
    from src.handshake import lifecycle as handshake_lifecycle
    _handshake_available = True
except ImportError:
    _handshake_available = False


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
    """Get the current extension lifecycle state from the handshake module."""
    if _handshake_available:
        state = handshake_lifecycle.get_current_state("working-bibliography-extension")
        if state:
            return state["state"]
    return "REGISTERED"


def can_execute() -> bool:
    """Check if the extension can execute capabilities.

    Delegates to the handshake lifecycle module for persistent state.
    """
    if _handshake_available:
        return handshake_lifecycle.can_execute("working-bibliography-extension")
    return False


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
    if not can_execute():
        return {
            "allowed": False,
            "reason": f"Extension is in {state} state. Capabilities require ACTIVE state (handshake must complete first).",
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
