"""
Policy Engine — Orchestrated Enforcement Decision-Making

Evaluates every operation against all enforcement domains and produces
a deterministic decision:

  1. Validator: Is this operation contract-valid?
  2. Boundary Checker: Is this operation within ownership boundaries?
  3. Drift Detector: Does this operation indicate drift?

The policy engine combines these checks into an enforcement result
that includes the decision (ALLOW, REJECT, SUSPEND) and the evidence.
"""

import os
import sys
from datetime import datetime, timezone
from enum import Enum

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.enforcement import validator, boundary_checker, drift_detector
from src.enforcement import receipts as enforcement_receipts

# Import handshake lifecycle for state transitions
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
from src.handshake import lifecycle as lifecycle_module


class EnforcementDecision(Enum):
    """Deterministic enforcement outcomes."""
    ALLOW = "ALLOW"
    REJECT = "REJECT"
    SUSPEND = "SUSPEND"


class EnforcementResult:
    """Result of a full policy evaluation."""

    def __init__(self):
        self.decision = EnforcementDecision.ALLOW
        self.validator_result = None
        self.boundary_result = None
        self.drift_result = None
        self.receipt_id = None
        self.reason = None

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "receipt_id": self.receipt_id,
            "validator": self.validator_result.to_dict() if self.validator_result else None,
            "boundary": self.boundary_result.to_dict() if self.boundary_result else None,
            "drift": self.drift_result.to_dict() if self.drift_result else None,
        }


class PolicyEngine:
    """Policy evaluation engine for extension contract enforcement.

    Evaluates operations through a three-stage pipeline:
      validator → boundary checker → drift detector
    """

    def __init__(self):
        self._drift = drift_detector.DriftDetector()
        self._violation_count = 0

    def evaluate(self, tool_name: str, risk: str, arguments: dict = None,
                 operation_result: dict = None) -> EnforcementResult:
        """Evaluate an operation against all enforcement domains.

        Returns:
            EnforcementResult with decision (ALLOW, REJECT, SUSPEND) and evidence.
        """
        result = EnforcementResult()

        # Stage 1: Contract validation
        val = validator.validate_operation(tool_name, risk, arguments, operation_result)
        result.validator_result = val
        if not val.valid:
            result.decision = EnforcementDecision.REJECT
            result.reason = val.reason or "Contract validation failed"
            result.receipt_id = enforcement_receipts.generate_enforcement_receipt(
                tool_name, "REJECT", val.reason, val.to_dict()
            )["receipt_id"]
            self._violation_count += 1
            return result

        # Stage 2: Boundary check
        boundary = boundary_checker.check_ownership_boundary(tool_name, arguments)
        result.boundary_result = boundary
        if boundary.violation:
            result.decision = EnforcementDecision.REJECT
            result.reason = boundary.violation_detail or "Ownership boundary violation"
            result.receipt_id = enforcement_receipts.generate_boundary_receipt(
                tool_name, boundary.violation_type, boundary.violation_detail
            )["receipt_id"]
            self._violation_count += 1
            return result

        # Stage 3: Drift detection
        drift = self._drift.detect_all(tool_name, arguments)
        result.drift_result = drift

        if drift.classification == drift_detector.DriftClassification.REVOKE:
            result.decision = EnforcementDecision.SUSPEND
            result.reason = "Contract violation detected — extension should transition to SUSPENDED"
            # Notify lifecycle
            self._transition_lifecycle("SUSPENDED", f"REVOKE drift: {drift.classification}")
            result.receipt_id = enforcement_receipts.generate_drift_receipt(
                tool_name, drift.classification, drift.to_dict()
            )["receipt_id"]
            self._violation_count += 1
            return result
        elif drift.classification == drift_detector.DriftClassification.OBSERVATION:
            result.reason = "Non-blocking deviation observed — logged"
            result.receipt_id = enforcement_receipts.generate_drift_receipt(
                tool_name, drift.classification, drift.to_dict()
            )["receipt_id"]
            # OBSERVATION still allows the operation
            result.decision = EnforcementDecision.ALLOW
            return result

        # All checks passed
        result.decision = EnforcementDecision.ALLOW
        result.reason = "All enforcement checks passed"
        result.receipt_id = enforcement_receipts.generate_enforcement_receipt(
            tool_name, "ALLOW", "Contract compliant", val.to_dict()
        )["receipt_id"]

        return result

    def _transition_lifecycle(self, target_state: str, reason: str):
        """Transition the extension lifecycle state (for violations)."""
        try:
            lifecycle_module.transition_to(
                "working-bibliography-extension",
                target_state,
                reason=reason,
                authority="automated_notify_owner"
            )
        except Exception:
            pass  # Lifecycle transition may fail if already in same state

    def get_violation_count(self) -> int:
        """Get the total number of enforcement violations."""
        return self._violation_count

    def get_drift_history(self) -> list:
        """Get the drift detection history."""
        return self._drift._observations
