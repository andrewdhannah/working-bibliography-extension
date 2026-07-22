"""
Validation Receipts — Evidence of Compliance Testing

Produces validation_receipt for every validation run.
"""

import json
import os
import hashlib
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "validation")


def _ensure_dir():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def _generate_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    h = hashlib.sha256(f"validation:{ts}:{os.urandom(8).hex()}".encode()).hexdigest()[:12]
    return f"rcp-wb-validation-{ts}-{h}"


def _write(receipt: dict):
    _ensure_dir()
    path = os.path.join(RECEIPTS_DIR, f"{receipt['receipt_id']}.json")
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2)


def generate_validation_receipt(fixture_name: str, category: str,
                                 passed: bool, domains_passed: int,
                                 domains_total: int) -> dict:
    """Generate a receipt for a validation fixture run."""
    receipt = {
        "receipt_id": _generate_id(),
        "receipt_type": "validation_receipt",
        "fixture_name": fixture_name,
        "category": category,
        "result": "PASS" if passed else "FAIL",
        "domains_passed": domains_passed,
        "domains_total": domains_total,
        "validated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt


def generate_compliance_receipt(extension_id: str, verdict: str,
                                 fixtures_passed: int, fixtures_total: int) -> dict:
    """Generate a receipt for a full compliance evaluation."""
    receipt = {
        "receipt_id": _generate_id(),
        "receipt_type": "compliance_receipt",
        "extension_id": extension_id,
        "verdict": verdict,
        "fixtures_passed": fixtures_passed,
        "fixtures_total": fixtures_total,
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt
