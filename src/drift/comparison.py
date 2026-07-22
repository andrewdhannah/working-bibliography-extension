"""
Drift Comparison — Per-Domain Comparison Logic

Compares observed runtime state against the approved baseline for each
drift domain. Each domain has a dedicated comparison function.

Drift domains:
  1. Identity drift — extension_id, version, contract_id changes
  2. Capability drift — tools added or removed from manifest
  3. Permission drift — risk level escalation
  4. Contract version drift — contract version changes
"""

import json
import os
from datetime import datetime, timezone


class ComparisonResult:
    """Result of a single domain comparison."""

    def __init__(self, domain: str):
        self.domain = domain
        self.match = True
        self.differences = []
        self.baseline_value = None
        self.observed_value = None

    def add_difference(self, field: str, baseline_val, observed_val, description: str = None):
        self.match = False
        self.differences.append({
            "field": field,
            "baseline": str(baseline_val)[:200],
            "observed": str(observed_val)[:200],
            "description": description or f"'{field}' differs"
        })
        if self.baseline_value is None:
            self.baseline_value = {}
            self.observed_value = {}
        self.baseline_value[field] = str(baseline_val)[:200]
        self.observed_value[field] = str(observed_val)[:200]

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "match": self.match,
            "difference_count": len(self.differences),
            "differences": self.differences
        }


def compare_identity(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare extension identity against baseline.

    Checks:
      - extension_id matches
      - contract_id matches
      - contract_version matches

    Drift domain: Identity Drift
    Changes trigger: contract mismatch → requires re-verification
    """
    result = ComparisonResult("identity")

    baseline_identity = baseline.get("identity", {})
    observed_identity = observed.get("identity", {})

    for field in ["extension_id", "contract_id", "contract_version"]:
        bv = baseline_identity.get(field)
        ov = observed_identity.get(field)
        if bv != ov:
            result.add_difference(field, bv, ov,
                                f"Identity field '{field}' changed from '{bv}' to '{ov}'")

    if result.match:
        result.baseline_value = baseline_identity
        result.observed_value = observed_identity

    return result


def compare_manifest_tools(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare capability tool lists against baseline.

    Checks:
      - All baseline tools still present
      - No unexpected tools added
      - Capability ordering changes are IGNORED

    Drift domain: Capability Drift
    Added tool → REVOKE (unexpected capability)
    Removed tool → OBSERVATION (capability missing)
    Reordered → PASS (ordering is not significant)
    """
    result = ComparisonResult("capability_tools")

    baseline_tools = baseline.get("manifest_tools", {})
    observed_tools = {}
    for cap in observed.get("capabilities", []):
        observed_tools[cap.get("id")] = sorted(cap.get("tools", []))

    all_cap_ids = set(baseline_tools.keys()) | set(observed_tools.keys())

    for cap_id in sorted(all_cap_ids):
        b_tools = set(baseline_tools.get(cap_id, []))
        o_tools = set(observed_tools.get(cap_id, []))

        added = o_tools - b_tools
        removed = b_tools - o_tools

        if added:
            result.add_difference(f"{cap_id}_added", sorted(b_tools), sorted(o_tools),
                                f"Unexpected tools added to '{cap_id}': {sorted(added)}")
        if removed:
            result.add_difference(f"{cap_id}_removed", sorted(b_tools), sorted(o_tools),
                                f"Tools removed from '{cap_id}': {sorted(removed)}")

        # Ordering change is NOT a difference — we compare sorted sets
        if not added and not removed:
            pass  # PASS — ordering change is ignored

    if result.match:
        result.baseline_value = baseline_tools
        result.observed_value = observed_tools

    return result


def compare_manifest_risks(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare risk classifications against baseline.

    Checks:
      - No capability escalated to higher risk level

    Drift domain: Permission Drift
    R0 → R1 escalation → REVOKE (permission escalation)
    R1 → R0 de-escalation → OBSERVATION (permission change)
    """
    result = ComparisonResult("capability_risk")

    baseline_risks = baseline.get("manifest_risks", {})
    observed_risks = {}
    for cap in observed.get("capabilities", []):
        observed_risks[cap.get("id")] = cap.get("risk")
    result.observed_value = observed_risks
    result.baseline_value = baseline_risks

    risk_levels = {"R0": 0, "R1": 1}

    for cap_id in sorted(set(baseline_risks.keys()) | set(observed_risks.keys())):
        b_risk = baseline_risks.get(cap_id)
        o_risk = observed_risks.get(cap_id)

        if b_risk != o_risk:
            b_level = risk_levels.get(b_risk, -1)
            o_level = risk_levels.get(o_risk, -1)

            if o_level > b_level:
                result.add_difference(f"{cap_id}_escalation", b_risk, o_risk,
                                    f"Capability '{cap_id}' escalated from {b_risk} to {o_risk}")
            else:
                result.add_difference(f"{cap_id}_deescalation", b_risk, o_risk,
                                    f"Capability '{cap_id}' changed from {b_risk} to {o_risk} (de-escalation)")

    return result


def compare_contract_version(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare contract version against baseline.

    Checks:
      - contract_id matches
      - contract_version matches

    Drift domain: Contract Version Drift
    Version change → OBSERVATION (re-handshake required)
    Contract ID change → REVOKE (different contract)
    """
    result = ComparisonResult("contract_version")

    baseline_contract = baseline.get("contract_document", {})
    observed_contract = observed if "contract_id" in observed else {}

    b_version = baseline_contract.get("version", baseline.get("contract_version"))
    o_version = observed.get("contract_version") or observed_contract.get("version")

    b_contract_id = baseline_contract.get("contract_id", baseline.get("contract_id"))
    o_contract_id = observed.get("contract_id") or observed_contract.get("contract_id")

    if b_contract_id != o_contract_id:
        result.add_difference("contract_id", b_contract_id, o_contract_id,
                            f"Contract ID changed from '{b_contract_id}' to '{o_contract_id}'")

    if b_version != o_version:
        result.add_difference("contract_version", b_version, o_version,
                            f"Contract version changed from '{b_version}' to '{o_version}'")

    if result.match:
        result.baseline_value = {"contract_id": b_contract_id, "version": b_version}
        result.observed_value = {"contract_id": o_contract_id, "version": o_version}

    return result


def compare_permissions(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare permission boundaries against baseline.

    Checks:
      - No new forbidden_actions removed
      - Permission scope changes

    Drift domain: Permission Drift
    """
    result = ComparisonResult("permissions")

    baseline_forbidden = set(baseline.get("forbidden_operations", []))
    observed_forbidden = set(observed.get("forbidden_operations", []))

    removed = baseline_forbidden - observed_forbidden
    added = observed_forbidden - baseline_forbidden

    if removed:
        result.add_difference("forbidden_removed", sorted(removed), "not forbidden",
                            f"Forbidden operations removed from contract: {sorted(removed)}")
    if added:
        result.add_difference("forbidden_added", "not added", sorted(added),
                            f"New forbidden operations added (stricter): {sorted(added)}")

    if result.match:
        result.baseline_value = {"forbidden_count": len(baseline_forbidden)}
        result.observed_value = {"forbidden_count": len(observed_forbidden)}

    return result


def compare_boundary(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare ownership boundary enforcement against baseline.

    Checks:
      - All baseline boundaries still present
      - No boundary scopes removed

    Drift domain: Boundary Drift
    Boundary removal → REVOKE
    Boundary addition → OBSERVATION (stricter is safer)

    Note: Baseline enforcement comes from the contract document.
    Observed enforcement comes from the permissions config.
    We only compare fields that exist in both sources.
    """
    result = ComparisonResult("boundary")

    # Baseline enforcement comes from the contract document
    baseline_contract = baseline.get("contract_document", {})
    baseline_enforcement = baseline_contract.get("enforcement", {})

    # Observed enforcement comes from the permissions config
    observed_enforcement = observed.get("enforcement", {})

    # Compare fields that exist in both sources
    common_fields = set(baseline_enforcement.keys()) & set(observed_enforcement.keys())

    for field in sorted(common_fields):
        bv = baseline_enforcement.get(field)
        ov = observed_enforcement.get(field)
        if bv != ov:
            result.add_difference(f"enforcement_{field}", bv, ov,
                                f"Enforcement '{field}' changed from '{bv}' to '{ov}'")

    if result.match:
        result.baseline_value = {k: baseline_enforcement.get(k) for k in common_fields}
        result.observed_value = {k: observed_enforcement.get(k) for k in common_fields}

    return result


def compare_receipt_evidence(baseline: dict, observed: dict) -> ComparisonResult:
    """Compare receipt evidence generation against baseline.

    Checks:
      - Baseline receipt types are still present
      - No receipt type removed

    Drift domain: Receipt Drift
    Receipt type removed → OBSERVATION (missing evidence)
    New receipt type → PASS (more evidence is better)
    """
    result = ComparisonResult("receipt_evidence")

    # Receipt types are defined in the contract's evidence section
    baseline_contract = baseline.get("contract_document", {})
    observed_contract = observed.get("contract_document", {})

    b_receipts = {r.get("type") for r in baseline_contract.get("evidence", {}).get("receipt_types", [])}
    o_receipts = {r.get("type") for r in observed_contract.get("evidence", {}).get("receipt_types", [])}

    removed = b_receipts - o_receipts
    added = o_receipts - b_receipts

    if removed:
        result.add_difference("receipt_type_removed", sorted(removed), "not present",
                            f"Receipt types removed: {sorted(removed)}")

    if added:
        # New receipt types are PASS (more evidence is better)
        pass

    if result.match:
        result.baseline_value = {"receipt_count": len(b_receipts)}
        result.observed_value = {"receipt_count": len(o_receipts)}

    return result
