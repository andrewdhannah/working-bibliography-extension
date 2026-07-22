"""
Extension Lifecycle State Machine — Handshake Steps 4-6

Implements the 6-state lifecycle defined in WB-LIBRARIAN-CONTRACT-v1:

  REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE
                                                     → SUSPENDED → REVOKED

Each transition has guard conditions that must be satisfied before the
state change is permitted. Invalid transitions are rejected with a clear
reason.

Per EXTENSION-HANDSHAKE-CONTRACT.md:
  H-001: Identity must be declared before any capability
  H-002: Contract must be verified before Owner can approve
  H-003: Owner approval required before capabilities activate
  H-004: Extension cannot self-approve or self-elevate
  H-005: Re-handshake required after contract/version change
  H-006: REVOKED is terminal
  H-008: No implicit trust
"""

import json
import os
from datetime import datetime, timezone


LIFECYCLE_STORAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "handshake")


# Valid state machine transitions with guard condition descriptions
TRANSITIONS = {
    "REGISTERED": {
        "to": ["CONTRACT_VERIFIED"],
        "guard": "Contract and capability manifest validated"
    },
    "CONTRACT_VERIFIED": {
        "to": ["OWNER_APPROVED"],
        "guard": "Owner explicitly authorizes activation"
    },
    "OWNER_APPROVED": {
        "to": ["ACTIVE"],
        "guard": "Activation signal sent after approval"
    },
    "ACTIVE": {
        "to": ["SUSPENDED", "REVOKED"],
        "guard": "Drift detected (SUSPENDED) or contract violation (REVOKED)"
    },
    "SUSPENDED": {
        "to": ["ACTIVE", "REVOKED"],
        "guard": "Owner clears drift (ACTIVE) or Owner terminates (REVOKED)"
    },
    "REVOKED": {
        "to": [],
        "guard": "Terminal state — no transitions out"
    }
}

VALID_STATES = list(TRANSITIONS.keys())
TERMINAL_STATES = ["REVOKED"]


class LifecycleError(Exception):
    """Raised when a lifecycle transition is invalid."""
    pass


def _state_path(extension_id: str) -> str:
    """Get the filesystem path for a lifecycle state file."""
    return os.path.join(LIFECYCLE_STORAGE, f"{extension_id}_lifecycle.json")


def _ensure_storage():
    """Ensure lifecycle storage directory exists."""
    os.makedirs(LIFECYCLE_STORAGE, exist_ok=True)


def get_current_state(extension_id: str) -> dict:
    """Get the current lifecycle state for an extension.

    Returns:
        dict with state, entered_at, etc., or None if not found.
    """
    path = _state_path(extension_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def initialize_state(extension_id: str, reason: str = "Identity announcement validated") -> dict:
    """Initialize the lifecycle at REGISTERED state.

    Per lifecyle state machine: REGISTERED is the entry state.
    """
    _ensure_storage()
    state = {
        "extension_id": extension_id,
        "state": "REGISTERED",
        "entered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "previous_state": None,
        "transition_reason": reason,
        "transition_count": 0,
        "history": []
    }
    with open(_state_path(extension_id), "w") as f:
        json.dump(state, f, indent=2)
    return state


def transition_to(extension_id: str, target_state: str, reason: str, authority: str = "automated") -> dict:
    """Transition the lifecycle to a new state.

    Args:
        extension_id: The extension's identity
        target_state: The desired state
        reason: Why the transition is occurring
        authority: Who/what authorized the transition (automated, owner, system)

    Returns:
        Updated state dict

    Raises:
        LifecycleError if the transition is invalid

    Per lifecycle contract:
      - REVOKED is terminal (H-006)
      - Owner approval required for OWNER_APPROPED (H-003)
      - Contract verification must precede Owner approval (H-002)
    """
    current = get_current_state(extension_id)
    if not current:
        raise LifecycleError(f"No lifecycle state found for extension '{extension_id}'. Must initialize first.")

    from_state = current["state"]

    # Check terminal
    if from_state in TERMINAL_STATES:
        raise LifecycleError(f"Cannot transition from terminal state '{from_state}' (H-006). REVOKED is terminal.")

    # Check valid transition
    allowed_targets = TRANSITIONS.get(from_state, {}).get("to", [])
    if target_state not in allowed_targets:
        raise LifecycleError(
            f"Invalid transition: '{from_state}' → '{target_state}'. "
            f"Allowed targets from '{from_state}': {allowed_targets}. "
            f"Guard: {TRANSITIONS[from_state]['guard']}"
        )

    # Authority checks
    if target_state == "OWNER_APPROVED" and authority != "owner":
        raise LifecycleError(f"Transition to OWNER_APPROVED requires owner authority (H-003). Got '{authority}'.")

    if target_state in ("SUSPENDED", "REVOKED") and from_state == "ACTIVE":
        if target_state == "SUSPENDED" and authority not in ("automated_notify_owner", "automated"):
            raise LifecycleError("Transition ACTIVE → SUSPENDED requires automated detection or owner action.")
        if target_state == "REVOKED" and authority != "owner":
            raise LifecycleError("Transition to REVOKED requires owner authority.")

    # Execute transition
    current["previous_state"] = from_state
    current["state"] = target_state
    current["entered_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current["transition_reason"] = reason
    current["transition_count"] += 1

    if "history" not in current:
        current["history"] = []
    current["history"].append({
        "from_state": from_state,
        "to_state": target_state,
        "timestamp": current["entered_at"],
        "reason": reason,
        "authority": authority
    })

    with open(_state_path(extension_id), "w") as f:
        json.dump(current, f, indent=2)

    return current


def is_active(extension_id: str) -> bool:
    """Check if the extension is in ACTIVE state."""
    state = get_current_state(extension_id)
    return state is not None and state["state"] == "ACTIVE"


def can_execute(extension_id: str) -> bool:
    """Check if the extension can execute capabilities.

    Per contract: capabilities are only available in ACTIVE state.
    """
    return is_active(extension_id)


def get_lifecycle_history(extension_id: str) -> list:
    """Get the full lifecycle transition history."""
    state = get_current_state(extension_id)
    if not state:
        return []
    return state.get("history", [])


def reset_state(extension_id: str) -> dict:
    """Reset the lifecycle state to REGISTERED (for testing/re-handshake)."""
    return initialize_state(extension_id, reason="Lifecycle reset for re-handshake")
