"""
Drift Scan Receipts — Evidence of Drift Detection

Produces drift_scan_receipt for every completed drift scan.

Required fields (per spec):
  extension_id
  baseline_hash
  observed_hash
  drift_domain
  classification
  timestamp
"""

import json
import os
import hashlib
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "drift_scans")


def _ensure_dir():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def _generate_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    h = hashlib.sha256(f"drift_scan:{ts}:{os.urandom(8).hex()}".encode()).hexdigest()[:12]
    return f"rcp-wb-drift_scan-{ts}-{h}"


def _write(receipt: dict):
    _ensure_dir()
    path = os.path.join(RECEIPTS_DIR, f"{receipt['receipt_id']}.json")
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2)


def generate_drift_scan_receipt(extension_id: str, baseline_hash: str,
                                classification: str, domain_count: int,
                                finding_count: int, lifecycle_state: str) -> dict:
    """Generate a drift scan receipt.

    Required fields (per spec):
      extension_id     — which extension was scanned
      baseline_hash    — hash of the approved baseline
      classification   — PASS, OBSERVATION, or REVOKE
      drift_domain     — which domain(s) had findings
      timestamp        — when the scan occurred
    """
    receipt = {
        "receipt_id": _generate_id(),
        "receipt_type": "drift_scan_receipt",
        "extension_id": extension_id,
        "baseline_hash": baseline_hash,
        "classification": classification,
        "domain_count": domain_count,
        "finding_count": finding_count,
        "lifecycle_state": lifecycle_state,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write(receipt)
    return receipt
