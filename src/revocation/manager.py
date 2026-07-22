"""
Revocation Manager — Orchestrates Suspension, Revocation, and Restoration

Integrates drift detection, policy evaluation, lifecycle transitions, and
receipt production into a single workflow.

Entry points:
  process_drift_result(drift_result)  — evaluate drift and take action
  suspend(trigger, authority)         — suspend extension capabilities
  revoke(reason, authority)           — permanently revoke access
  restore(approval_reference)         — restore from suspension
  get_access_state()                  — current access state with allowed ops
"""

import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.handshake import lifecycle as h_lifecycle
from src.revocation import lifecycle as r_lifecycle
from src.revocation import policy as r_policy
from src.revocation import authorization as r_authorization
from src.revocation import receipts as r_receipts


class RevocationManager:
    """Manages the suspension/revocation lifecycle for the extension."""

    def __init__(self):
        self._violation_count = 0

    def process_drift_result(self, drift_result) -> dict:
        """Evaluate a drift scan result and take appropriate action.

        Integrates:
          1. Drift classification (from drift detector)
          2. Policy evaluation (suspend vs revoke vs notify)
          3. Lifecycle transition (if action required)
          4. Receipt generation

        Args:
            drift_result: DriftScanResult from drift.detector.run_scan()

        Returns:
            dict with action, result, and receipt
        """
        classification = drift_result.classification.classification if drift_result.classification else "PASS"
        findings = drift_result.classification.findings if drift_result.classification else []
        current_state = drift_result.state_after_scan or self._get_state()

        # Step 1: Evaluate policy
        policy_decision = r_policy.evaluate_drift_classification(
            classification, findings, current_state
        )

        result = {
            "classification": classification,
            "policy_decision": policy_decision.to_dict(),
            "lifecycle_action": None,
            "receipt_id": None,
            "success": True
        }

        # Step 2: Execute action if needed
        if policy_decision.action == "suspend":
            outcome = self.suspend(
                trigger=policy_decision.reason,
                authority=policy_decision.authority_required or "automated_notify_owner",
                drift_reference=policy_decision.drift_reference
            )
            result["lifecycle_action"] = "SUSPENDED"
            result["receipt_id"] = outcome.get("receipt_id")
            result["success"] = outcome.get("success", True)

        elif policy_decision.action == "revoke":
            outcome = self.revoke(
                reason=policy_decision.reason,
                authority=policy_decision.authority_required or "owner",
                drift_reference=policy_decision.drift_reference
            )
            result["lifecycle_action"] = "REVOKED"
            result["receipt_id"] = outcome.get("receipt_id")
            result["success"] = outcome.get("success", True)

        elif policy_decision.action == "notify":
            # OBSERVATION — owner notified, no state change
            result["lifecycle_action"] = None
            result["receipt_id"] = None

        else:  # "none"
            result["lifecycle_action"] = None
            result["receipt_id"] = None

        return result

    def suspend(self, trigger: str, authority: str = "automated_notify_owner",
                drift_reference: str = None) -> dict:
        """Suspend extension capabilities.

        SUSPENDED state: health checks, identity, receipts, drift allowed.
        All other capabilities blocked.
        """
        result = {"success": False, "action": "suspend"}

        current_state = self._get_state()
        if current_state == "SUSPENDED":
            result["success"] = True
            result["message"] = "Already SUSPENDED"
            return result
        if current_state == "REVOKED":
            result["message"] = "Cannot suspend — extension is REVOKED"
            return result

        # Check authority
        auth = r_authorization.check_authority(current_state, "SUSPENDED", authority)
        if not auth["authorized"]:
            result["message"] = auth["reason"]
            return result

        # Execute transition
        try:
            h_lifecycle.transition_to(
                "working-bibliography-extension",
                "SUSPENDED",
                reason=trigger,
                authority=authority
            )
        except Exception as e:
            result["message"] = str(e)
            return result

        # Generate receipt
        receipt = r_receipts.generate_suspension_receipt(
            "working-bibliography-extension",
            current_state,
            "SUSPENDED",
            trigger,
            drift_reference
        )

        self._violation_count += 1
        result["success"] = True
        result["receipt_id"] = receipt["receipt_id"]
        result["state"] = "SUSPENDED"
        return result

    def revoke(self, reason: str, authority: str = "owner",
               drift_reference: str = None) -> dict:
        """Permanently revoke extension capabilities.

        REVOKED state: historical receipts, audit queries, identity lookup only.
        Terminal state — no transition out.
        """
        result = {"success": False, "action": "revoke"}

        current_state = self._get_state()
        if current_state == "REVOKED":
            result["message"] = "Already REVOKED"
            return result

        # Check authority
        auth = r_authorization.check_authority(current_state, "REVOKED", authority)
        if not auth["authorized"]:
            result["message"] = auth["reason"]
            return result

        # If currently ACTIVE, go through SUSPENDED first or direct to REVOKED
        target_state = "REVOKED"
        try:
            if current_state == "ACTIVE":
                # Can go directly to REVOKED with owner authority
                h_lifecycle.transition_to(
                    "working-bibliography-extension",
                    target_state,
                    reason=reason,
                    authority=authority
                )
            else:
                h_lifecycle.transition_to(
                    "working-bibliography-extension",
                    target_state,
                    reason=reason,
                    authority=authority
                )
        except Exception as e:
            result["message"] = str(e)
            return result

        # Get current capabilities for the receipt
        capabilities = self._get_capabilities()

        receipt = r_receipts.generate_revocation_receipt(
            "working-bibliography-extension",
            "1.0.0",
            reason,
            authority,
            capabilities,
            drift_reference
        )

        self._violation_count += 1
        result["success"] = True
        result["receipt_id"] = receipt["receipt_id"]
        result["state"] = "REVOKED"
        result["affected_capabilities"] = capabilities
        return result

    def restore(self, approval_reference: str, authority: str = "owner") -> dict:
        """Restore a suspended extension to ACTIVE.

        Requires owner authority.
        """
        result = {"success": False, "action": "restore"}

        current_state = self._get_state()
        if current_state != "SUSPENDED":
            result["message"] = f"Cannot restore from {current_state}. Only SUSPENDED can be restored."
            return result

        # Check authority
        auth = r_authorization.check_authority("SUSPENDED", "ACTIVE", authority)
        if not auth["authorized"]:
            result["message"] = auth["reason"]
            return result

        # Execute transition
        try:
            h_lifecycle.transition_to(
                "working-bibliography-extension",
                "ACTIVE",
                reason=f"Owner cleared drift: {approval_reference}",
                authority=authority
            )
        except Exception as e:
            result["message"] = str(e)
            return result

        # Generate receipt
        capabilities = self._get_capabilities()
        receipt = r_receipts.generate_restoration_receipt(
            "working-bibliography-extension",
            "SUSPENDED",
            approval_reference,
            capabilities
        )

        result["success"] = True
        result["receipt_id"] = receipt["receipt_id"]
        result["state"] = "ACTIVE"
        result["restored_capabilities"] = capabilities
        return result

    def get_access_state(self) -> dict:
        """Get the current access state with allowed operations."""
        state = self._get_state()
        tool_tester = lambda t: r_lifecycle.is_operation_allowed(t, state)

        return {
            "lifecycle_state": state,
            "capabilities_blocked": state != "ACTIVE",
            "historical_access": state in ("SUSPENDED", "REVOKED"),
            "audit_access": state == "REVOKED",
            "violation_count": self._violation_count
        }

    def _get_state(self) -> str:
        """Get current lifecycle state."""
        try:
            state = h_lifecycle.get_current_state("working-bibliography-extension")
            return state["state"] if state else "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def _get_capabilities(self) -> list:
        """Get current declared capability list."""
        try:
            mcp_dir = os.path.join(PROJECT_ROOT, "mcp", "capabilities.json")
            with open(mcp_dir) as f:
                manifest = json.load(f)
            return [c.get("id") for c in manifest.get("capabilities", []) if c.get("status") == "active"]
        except Exception:
            return []
