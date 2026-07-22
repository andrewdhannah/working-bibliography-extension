"""
Enforcement-Specific Receipts — Enforcement, Drift, Boundary Violation

Produces evidence receipts for every enforcement decision:
  - Enforcement receipt: Generic enforcement check result
  - Drift receipt: Drift detection classification
  - Boundary violation receipt: Ownership boundary violation
  - Policy evaluation receipt: Full policy evaluation result
"""

import json
import os
import hashlib
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "enforcement")


def _ensure_dir():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def _generate_id(receipt_type: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    h = hashlib.sha256(f"{receipt_type}:{ts}:{os.urandom(8).hex()}".encode()).hexdigest()[:12]
    return f"rcp-wb-{receipt_type}-{ts}-{h}"


def _write(receipt: dict):
    _ensure_dir()
    path = os.path.join(RECEIPTS_DIR, f"{receipt['receipt_id']}.json")
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2)


def generate_enforcement_receipt(tool_name: str, decision: str, reason: str, validation_detail: dict = None) -> dict:
    """Generate a receipt for a contract enforcement check.

    Produced on every enforcement evaluation (ALLOW, REJECT, SUSPEND).
    """
    receipt = {
        "receipt_id": _generate_id("enforcement"),
        "receipt_type": "enforcement_receipt",
        "tool_name": tool_name,
        "decision": decision,
        "reason": reason,
        "check_count": validation_detail.get("checks_total", 0) if validation_detail else 0,
        "checks_passed": validation_detail.get("checks_passed", 0) if validation_detail else 0,
        "enforced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_drift_receipt(tool_name: str, classification: str, drift_detail: dict = None) -> dict:
    """Generate a receipt for drift detection.

    Produced when drift is detected (PASS, OBSERVATION, or REVOKE).
    """
    receipt = {
        "receipt_id": _generate_id("drift"),
        "receipt_type": "enforcement_drift_receipt",
        "tool_name": tool_name,
        "classification": classification,
        "checks_passed": drift_detail.get("checks_passed", 0) if drift_detail else 0,
        "checks_total": drift_detail.get("checks_total", 0) if drift_detail else 0,
        "findings_count": len(drift_detail.get("details", [])) if drift_detail else 0,
        "detected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_boundary_receipt(tool_name: str, violation_type: str, detail: str) -> dict:
    """Generate a receipt for an ownership boundary violation.

    Produced when an operation crosses into a Librarian-protected domain.
    """
    receipt = {
        "receipt_id": _generate_id("boundary"),
        "receipt_type": "boundary_violation_receipt",
        "tool_name": tool_name,
        "violation_type": violation_type,
        "detail": detail,
        "violated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_policy_receipt(result: dict) -> dict:
    """Generate a receipt for a full policy evaluation result."""
    receipt = {
        "receipt_id": _generate_id("policy"),
        "receipt_type": "policy_evaluation_receipt",
        "decision": result.get("decision"),
        "reason": result.get("reason"),
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt
