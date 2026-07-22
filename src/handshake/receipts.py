"""
Handshake-Specific Receipts — Registration, Verification, Approval, Lifecycle

Per WB-LIBRARIAN-CONTRACT-v1 evidence.receipt_types, the handshake produces:
  - Registration receipt (when identity is established)
  - Contract verification receipt (when contract/capabilities validated)
  - Approval state receipt (when Owner approves)
  - Lifecycle transition receipt (on every state change)
"""

import json
import os
import hashlib
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "handshake")


def _ensure_dir():
    """Ensure receipts directory exists."""
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def _generate_id(receipt_type: str) -> str:
    """Generate a unique receipt ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    h = hashlib.sha256(f"{receipt_type}:{ts}:{os.urandom(8).hex()}".encode()).hexdigest()[:12]
    return f"rcp-wb-{receipt_type}-{ts}-{h}"


def _write(receipt: dict):
    """Write a receipt to persistent storage."""
    _ensure_dir()
    path = os.path.join(RECEIPTS_DIR, f"{receipt['receipt_id']}.json")
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2)


def generate_registration_receipt(identity: dict) -> dict:
    """Generate a receipt when extension identity is established.

    Per EXTENSION-HANDSHAKE-CONTRACT.md §2 Step 1.
    Corresponds to: REGISTERED state entry.
    """
    receipt = {
        "receipt_id": _generate_id("registration"),
        "receipt_type": "registration_receipt",
        "extension_id": identity.get("extension_id"),
        "version": identity.get("version"),
        "contract_id": identity.get("contract_id"),
        "contract_version": identity.get("contract_version"),
        "state": "REGISTERED",
        "registered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_contract_verification_receipt(validation_result: dict) -> dict:
    """Generate a receipt when contract and capabilities are validated.

    Per EXTENSION-HANDSHAKE-CONTRACT.md §2 Step 3.
    Corresponds to: CONTRACT_VERIFIED state entry.
    """
    receipt = {
        "receipt_id": _generate_id("contract_verification"),
        "receipt_type": "contract_verification_receipt",
        "contract_id": "wb-librarian-contract-v1",
        "contract_version": "1.0.0",
        "valid": validation_result.get("valid", False),
        "checks_passed": validation_result.get("checks_passed", 0),
        "checks_total": validation_result.get("checks_total", 0),
        "errors": validation_result.get("errors", []),
        "warnings": validation_result.get("warnings", []),
        "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_approval_receipt(extension_id: str, approved_by: str = "owner") -> dict:
    """Generate a receipt when the Owner approves the extension.

    Per EXTENSION-HANDSHAKE-CONTRACT.md §2 Step 5.
    Corresponds to: OWNER_APPROVED state.
    """
    receipt = {
        "receipt_id": _generate_id("approval"),
        "receipt_type": "approval_receipt",
        "extension_id": extension_id,
        "approved_by": approved_by,
        "state": "OWNER_APPROVED",
        "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_lifecycle_receipt(extension_id: str, from_state: str, to_state: str,
                               reason: str, authority: str) -> dict:
    """Generate a receipt for any lifecycle state transition.

    Per EXTENSION-HANDSHAKE-CONTRACT.md lifecycle diagram.
    Produced on every transition in the 6-state machine.
    """
    receipt = {
        "receipt_id": _generate_id("lifecycle"),
        "receipt_type": "lifecycle_transition_receipt",
        "extension_id": extension_id,
        "from_state": from_state,
        "to_state": to_state,
        "reason": reason,
        "authority": authority,
        "transitioned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_activation_receipt(extension_id: str) -> dict:
    """Generate a receipt when the extension becomes ACTIVE.

    Corresponds to: ACTIVE state entry — capabilities unlocked.
    """
    receipt = {
        "receipt_id": _generate_id("activation"),
        "receipt_type": "activation_receipt",
        "extension_id": extension_id,
        "state": "ACTIVE",
        "activated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt
