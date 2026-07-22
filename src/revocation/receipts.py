"""
Revocation Receipts — Suspension, Revocation, and Restoration Evidence

Produces:
  suspension_receipt:  When capabilities are suspended
  revocation_receipt:  When access is permanently revoked
  restoration_receipt: When suspended extension is restored to ACTIVE
"""

import json
import os
import hashlib
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "access")


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


def generate_suspension_receipt(extension_id: str, previous_state: str,
                                 new_state: str, trigger: str,
                                 drift_reference: str = None) -> dict:
    """Generate a receipt when extension capabilities are suspended.

    Required fields:
      extension_id, previous_state, new_state, trigger, drift_reference, timestamp
    """
    receipt = {
        "receipt_id": _generate_id("suspension"),
        "receipt_type": "suspension_receipt",
        "extension_id": extension_id,
        "previous_state": previous_state,
        "new_state": new_state,
        "trigger": trigger,
        "drift_reference": drift_reference,
        "suspended_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_revocation_receipt(extension_id: str, contract_version: str,
                                 reason: str, authority: str,
                                 affected_capabilities: list,
                                 drift_reference: str = None) -> dict:
    """Generate a receipt when extension access is permanently revoked.

    Required fields:
      extension_id, contract_version, reason, authority,
      affected_capabilities, timestamp
    """
    receipt = {
        "receipt_id": _generate_id("revocation"),
        "receipt_type": "revocation_receipt",
        "extension_id": extension_id,
        "contract_version": contract_version,
        "reason": reason,
        "authority": authority,
        "affected_capabilities": affected_capabilities,
        "drift_reference": drift_reference,
        "revoked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_restoration_receipt(extension_id: str, previous_state: str,
                                  approval_reference: str,
                                  restored_capabilities: list) -> dict:
    """Generate a receipt when a suspended extension is restored to ACTIVE.

    Required fields:
      extension_id, previous_state, approval_reference,
      restored_capabilities, timestamp
    """
    receipt = {
        "receipt_id": _generate_id("restoration"),
        "receipt_type": "restoration_receipt",
        "extension_id": extension_id,
        "previous_state": previous_state,
        "approval_reference": approval_reference,
        "restored_capabilities": restored_capabilities,
        "restored_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt
