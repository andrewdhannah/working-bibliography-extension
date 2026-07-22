"""
Revocation Lifecycle — SUSPENDED / REVOKED State Rules

Defines the allowed and blocked access patterns for each lifecycle state,
and the rules for transitioning between states.

Access rules:
  ACTIVE:     All capabilities available
  SUSPENDED:  Health, identity, receipts, drift reports (read-only)
              No capability execution, no artifact mutation
  REVOKED:    Historical receipts, audit queries, identity lookup only
              No capability execution, no handshake bypass, no auto-reactivation

Transition rules:
  ACTIVE → SUSPENDED     Yes (drift detected, owner review)
  SUSPENDED → ACTIVE     Yes (owner clears drift, requires 'owner' authority)
  SUSPENDED → REVOKED    Yes (owner decision or critical violation)
  REVOKED → ACTIVE       No (terminal state)
  REVOKED → any other    No (terminal state)
"""


# Allowed operations per lifecycle state
# Each entry maps: state -> (tool prefix, reason)
ALLOWED_WHEN_SUSPENDED = [
    # Health
    ("health", "Health checks allowed during suspension"),
    # Identity queries
    ("identity", "Identity queries allowed during suspension"),
    # Receipt retrieval
    ("get_receipt", "Historical receipt access allowed during suspension"),
    ("get_history", "Historical receipt access allowed during suspension"),
    # Drift reports
    ("drift_scan", "Drift reports allowed during suspension"),
    ("drift_status", "Drift reports allowed during suspension"),
]

ALLOWED_WHEN_REVOKED = [
    # Identity lookup
    ("identity", "Identity lookup allowed after revocation"),
    # Historical receipt access
    ("get_receipt", "Historical receipt access allowed after revocation"),
    ("get_history", "Historical receipt access allowed after revocation"),
    # Audit queries
    ("audit", "Audit queries allowed after revocation"),
    ("drift_scan", "Drift history allowed after revocation"),
]


def is_operation_allowed(tool_name: str, lifecycle_state: str) -> tuple:
    """Check if an operation is allowed in the given lifecycle state.

    Args:
        tool_name: The MCP tool name being called
        lifecycle_state: Current lifecycle state (ACTIVE, SUSPENDED, REVOKED)

    Returns:
        tuple of (allowed: bool, reason: str)
    """
    tool_lower = tool_name.lower()

    if lifecycle_state == "ACTIVE":
        # All capabilities available (permission check happens elsewhere)
        return True, None

    if lifecycle_state == "SUSPENDED":
        for prefix, reason in ALLOWED_WHEN_SUSPENDED:
            if tool_lower.startswith(prefix) or prefix in tool_lower:
                return True, None
        return False, f"Capability execution is blocked while SUSPENDED. Allowed: health, identity queries, receipts, drift reports."

    if lifecycle_state == "REVOKED":
        for prefix, reason in ALLOWED_WHEN_REVOKED:
            if tool_lower.startswith(prefix) or prefix in tool_lower:
                return True, None
        return False, f"Extension access is REVOKED. Only historical receipt access and audit queries allowed."

    return False, f"Unknown lifecycle state: {lifecycle_state}"


def validate_transition(from_state: str, to_state: str, authority: str) -> tuple:
    """Validate a lifecycle state transition.

    Args:
        from_state: Current state
        to_state: Desired state
        authority: Who/what authorized the transition

    Returns:
        tuple of (valid: bool, reason: str)
    """
    # Terminal state check
    if from_state == "REVOKED":
        return False, f"REVOKED is terminal. Cannot transition from {from_state} to {to_state}."

    # Allowed transitions
    allowed = {
        "ACTIVE": ["SUSPENDED", "REVOKED"],
        "SUSPENDED": ["ACTIVE", "REVOKED"],
    }

    targets = allowed.get(from_state, [])
    if to_state not in targets:
        return False, f"Invalid transition: {from_state} → {to_state}. Allowed: {targets}."

    # Authority checks
    if to_state == "ACTIVE" and authority != "owner":
        return False, f"Transition to ACTIVE requires 'owner' authority. Got: {authority}."

    if to_state in ("SUSPENDED", "REVOKED") and from_state == "ACTIVE":
        if to_state == "REVOKED" and authority != "owner":
            return False, f"Transition to REVOKED requires 'owner' authority. Got: {authority}."

    return True, None
