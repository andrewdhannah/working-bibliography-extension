"""
Revocation Authorization — Authority Checks for State Transitions

Enforces who can authorize lifecycle state transitions:

  Transition               Required Authority
  ACTIVE → SUSPENDED       automated (drift detected) or owner
  ACTIVE → REVOKED         owner
  SUSPENDED → ACTIVE       owner (clears drift)
  SUSPENDED → REVOKED      owner (terminates)
  REVOKED → anything       NOT ALLOWED (terminal)
"""

from datetime import datetime, timezone


# Authority levels for lifecycle transitions
AUTHORITY_LEVELS = {
    "automated": 0,        # System can initiate suspension on drift
    "automated_notify_owner": 1,  # System + owner notification
    "owner": 2,            # Owner must explicitly authorize
}


def check_authority(from_state: str, to_state: str, authority: str) -> dict:
    """Check if the given authority is sufficient for a state transition.

    Args:
        from_state: Current lifecycle state
        to_state: Desired lifecycle state
        authority: The authority attempting the transition

    Returns:
        dict with 'authorized' (bool) and 'reason' (str)
    """
    result = {
        "authorized": False,
        "reason": None,
        "required_authority": None,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    # REVOKED is terminal
    if from_state == "REVOKED":
        result["reason"] = "REVOKED is terminal. No transitions allowed."
        result["required_authority"] = "none (terminal state)"
        return result

    # Define transition authority requirements
    requirements = {
        ("ACTIVE", "SUSPENDED"): "automated",
        ("ACTIVE", "REVOKED"): "owner",
        ("SUSPENDED", "ACTIVE"): "owner",
        ("SUSPENDED", "REVOKED"): "owner",
    }

    required = requirements.get((from_state, to_state))
    if not required:
        result["reason"] = f"No transition rule for {from_state} → {to_state}"
        return result

    result["required_authority"] = required

    # Check authority level
    auth_level = AUTHORITY_LEVELS.get(authority, -1)
    required_level = AUTHORITY_LEVELS.get(required, -1)

    if auth_level < 0:
        result["reason"] = f"Unknown authority: '{authority}'"
        return result

    if auth_level < required_level:
        result["reason"] = (f"Insufficient authority: '{authority}' (level {auth_level}) "
                           f"cannot authorize {from_state} → {to_state}. "
                           f"Requires '{required}' (level {required_level}).")
        return result

    result["authorized"] = True
    result["reason"] = f"Authorized by '{authority}'"
    return result
