"""
Drift Detector — Orchestrated Scan, Compare, Classify

Orchestrates the full drift detection pipeline:
  1. Load approved baseline
  2. Capture current runtime state
  3. Compare each domain against baseline
  4. Classify findings (PASS / OBSERVATION / REVOKE)
  5. Generate drift scan receipt

This is the main entry point for drift scanning. Call run_scan() to
perform a complete drift check.
"""

import json
import os
from datetime import datetime, timezone

from . import baseline as drift_baseline
from . import comparison as drift_comparison
from . import classifier as drift_classifier
from . import receipts as drift_receipts
from . import observer as drift_observer


class DriftScanResult:
    """Complete result of a drift scan."""

    def __init__(self):
        self.scan_id = None
        self.scanned_at = None
        self.baseline = None
        self.classification = None
        self.receipt_id = None
        self.state_after_scan = None

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "scanned_at": self.scanned_at,
            "classification": self.classification.to_dict() if self.classification else None,
            "receipt_id": self.receipt_id,
            "state_after_scan": self.state_after_scan
        }


def _get_lifecycle_state() -> str:
    """Get the current lifecycle state from the handshake module."""
    try:
        import sys
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if root not in sys.path:
            sys.path.insert(0, root)
        from src.handshake import lifecycle
        state = lifecycle.get_current_state("working-bibliography-extension")
        return state["state"] if state else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def run_scan(extension_id: str = "working-bibliography-extension",
             force_recapture: bool = False) -> DriftScanResult:
    """Run a complete drift scan.

    Args:
        extension_id: The extension to scan
        force_recapture: If True, capture a new baseline before scanning

    Returns:
        DriftScanResult with classification and receipt
    """
    result = DriftScanResult()
    result.scan_id = f"ds-{extension_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    result.scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: Load baseline
    if force_recapture or not drift_baseline.baseline_exists(extension_id):
        bl = drift_baseline.capture_baseline(extension_id)
        drift_baseline.store_baseline(bl)
        result.baseline = "freshly_captured"
        baseline_data = bl.to_dict()
    else:
        baseline_data = drift_baseline.load_baseline(extension_id)
        result.baseline = "loaded"

    if not baseline_data:
        raise RuntimeError(f"No baseline found for extension '{extension_id}'")

    # Step 2: Capture current state using observer
    observed = drift_observer.observe()
    current_manifest = observed.manifest
    current_permissions = observed.permissions
    current_identity = observed.identity
    current_contract = observed.contract

    # Step 3: Compare each domain (6 domains)
    identity_result = drift_comparison.compare_identity(baseline_data, {
        "identity": current_identity
    })

    manifest_tools_result = drift_comparison.compare_manifest_tools(
        baseline_data, current_manifest
    )

    manifest_risks_result = drift_comparison.compare_manifest_risks(
        baseline_data, current_manifest
    )

    contract_result = drift_comparison.compare_contract_version(
        baseline_data, current_contract
    )

    permissions_result = drift_comparison.compare_permissions(
        baseline_data, current_permissions
    )

    boundary_result = drift_comparison.compare_boundary(
        baseline_data, current_permissions
    )

    receipt_result = drift_comparison.compare_receipt_evidence(
        baseline_data, current_contract
    )

    domain_count = 7  # identity, capability_tools, capability_risk, contract, permissions, boundary, receipt

    # Step 4: Classify
    classification = drift_classifier.classify_drift(
        identity_result, manifest_tools_result, manifest_risks_result,
        contract_result, permissions_result, boundary_result, receipt_result
    )

    result.classification = classification

    # Step 5: Check lifecycle state for drift-after-suspension rule
    lifecycle_state = observed.lifecycle_state
    result.state_after_scan = lifecycle_state

    # Drift while suspended → remain suspended
    if lifecycle_state == "SUSPENDED" and classification.classification != "PASS":
        result.state_after_scan = "SUSPENDED (drift detected — remaining suspended)"

    # Step 6: Generate receipt
    receipt = drift_receipts.generate_drift_scan_receipt(
        extension_id=extension_id,
        baseline_hash=baseline_data.get("baseline_hash", "unknown"),
        classification=classification.classification,
        domain_count=domain_count,
        finding_count=len(classification.findings),
        lifecycle_state=lifecycle_state
    )
    result.receipt_id = receipt["receipt_id"]

    return result
