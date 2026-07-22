"""
Revocation Policy — Suspension vs Revocation Decision Logic

Maps drift classifications and violation types to lifecycle actions:

  PASS       → No action (remain ACTIVE)
  OBSERVATION → No automatic action (remain ACTIVE, owner notification)
  REVOKE     → SUSPEND or REVOKE depending on severity

Determines whether a drift finding should trigger suspension (investigation
possible) or immediate revocation (contract breach).
"""

# Drift classifications that require action
SUSPEND_TRIGGERS = [
    "capability_removed",
    "contract_version_mismatch",
    "risk_deescalation",
    "receipt_type_removed",
    "boundary_enforcement_change",
]

REVOKE_TRIGGERS = [
    "capability_added",
    "risk_escalation",
    "forbidden_removed",
    "identity_mismatch",
    "contract_id_changed",
    "boundary_violation",
    "librarian_domain_crossing",
]


class PolicyDecision:
    """Result of a policy evaluation."""

    def __init__(self):
        self.action = None  # "none", "notify", "suspend", "revoke"
        self.reason = None
        self.drift_reference = None
        self.authority_required = None
        self.owner_action_required = False

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "drift_reference": self.drift_reference,
            "authority_required": self.authority_required,
            "owner_action_required": self.owner_action_required
        }


def evaluate_drift_classification(classification: str, findings: list,
                                   lifecycle_state: str = "ACTIVE") -> PolicyDecision:
    """Evaluate what action to take based on drift classification.

    Args:
        classification: PASS, OBSERVATION, or REVOKE
        findings: List of drift findings with field and description
        lifecycle_state: Current lifecycle state

    Returns:
        PolicyDecision with recommended action
    """
    decision = PolicyDecision()

    if lifecycle_state == "SUSPENDED":
        # Already suspended — recommend remain suspended
        decision.action = "none"
        decision.reason = "Extension is already SUSPENDED. Owner review required for next action."
        decision.owner_action_required = True
        return decision

    if lifecycle_state == "REVOKED":
        decision.action = "none"
        decision.reason = "Extension is REVOKED. No further action possible."
        return decision

    if classification == "PASS":
        decision.action = "none"
        decision.reason = "No drift detected. Extension remains ACTIVE."
        return decision

    if classification == "OBSERVATION":
        decision.action = "notify"
        decision.reason = "Non-breaking deviation detected. Owner notified, extension continues."
        decision.owner_action_required = False
        return decision

    if classification == "REVOKE":
        # Check what kind of finding triggered the REVOKE
        for finding in findings:
            field = finding.get("field", "")
            domain = finding.get("domain", "")

            # Immediate revocation triggers
            for trigger in REVOKE_TRIGGERS:
                if trigger in field.lower() or trigger in domain.lower():
                    decision.action = "revoke"
                    decision.reason = f"Critical contract violation: {finding.get('description', field)}"
                    decision.authority_required = "owner"
                    decision.owner_action_required = True
                    decision.drift_reference = finding.get("description", "")
                    return decision

            # Suspension triggers (may escalate to revocation)
            for trigger in SUSPEND_TRIGGERS:
                if trigger in field.lower() or trigger in domain.lower():
                    decision.action = "suspend"
                    decision.reason = f"Contract deviation detected: {finding.get('description', field)}"
                    decision.authority_required = "automated_notify_owner"
                    decision.owner_action_required = True
                    decision.drift_reference = finding.get("description", "")
                    return decision

        # Default for unclassified REVOKE findings — suspend for review
        decision.action = "suspend"
        decision.reason = "Contract deviation detected requiring investigation."
        decision.owner_action_required = True
        decision.drift_reference = findings[0].get("description", "Unknown drift") if findings else "Unknown"
        return decision

    return decision
