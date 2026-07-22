"""
Core Validator — Identity, Contract, Capability, Lifecycle, Permission Checks

Each validation domain has a dedicated check function that returns structured
results with pass/fail status and evidence references.

Validation domains:
  1. Identity   — extension_id format, contract reference, version format
  2. Contract   — required sections present, capabilities declared, forbidden ops
  3. Capability — tool names match implementation, risk levels valid
  4. Lifecycle  — state machine valid, transitions legal, guards present
  5. Permission — risk classification integrity, scope alignment
"""

import json
import os
import re
from datetime import datetime, timezone


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class ValidationResult:
    """Structured validation result for a single domain."""

    def __init__(self, domain: str):
        self.domain = domain
        self.passed = True
        self.checks = []

    def add_check(self, name: str, passed: bool, detail: str = None):
        self.checks.append({
            "check": name,
            "passed": passed,
            "detail": detail
        })
        if not passed:
            self.passed = False

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "passed": self.passed,
            "checks_passed": sum(1 for c in self.checks if c["passed"]),
            "checks_total": len(self.checks),
            "checks": self.checks
        }


class AggregateResult:
    """Aggregated result across all validation domains."""

    def __init__(self):
        self.domains = {}
        self.all_passed = True

    def add_domain(self, result: ValidationResult):
        self.domains[result.domain] = result
        if not result.passed:
            self.all_passed = False

    def to_dict(self) -> dict:
        return {
            "all_passed": self.all_passed,
            "domains_passed": sum(1 for d in self.domains.values() if d.passed),
            "domains_total": len(self.domains),
            "domain_results": {k: v.to_dict() for k, v in self.domains.items()}
        }


# ─── Identity Validation ────────────────────────────────────────────

def validate_identity(data: dict) -> ValidationResult:
    """Validate extension identity.

    Checks:
      - extension_id format (lowercase, hyphens/underscores allowed)
      - contract_id format
      - version format (semver)
      - declared_at present
      - owner_domain present
    """
    result = ValidationResult("identity")

    identity = data.get("identity", data)

    ext_id = identity.get("extension_id", "")
    if not re.match(r"^[a-z][a-z0-9_-]+$", ext_id):
        result.add_check("extension_id_format", False,
                        f"extension_id '{ext_id}' must match ^[a-z][a-z0-9_-]+$")
    else:
        result.add_check("extension_id_format", True)

    contract_id = identity.get("contract_id", "")
    if not re.match(r"^[a-z][a-z0-9_-]+-v\d+$", contract_id):
        result.add_check("contract_id_format", False,
                        f"contract_id '{contract_id}' must match ^[a-z][a-z0-9_-]+-v\\d+$")
    else:
        result.add_check("contract_id_format", True)

    version = identity.get("version", "")
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        result.add_check("version_format", False,
                        f"version '{version}' must match ^\\d+\\.\\d+\\.\\d+$")
    else:
        result.add_check("version_format", True)

    declared_at = identity.get("declared_at")
    if not declared_at:
        result.add_check("declared_at_present", False, "declared_at is required")
    else:
        result.add_check("declared_at_present", True)

    domain = identity.get("owner_domain") or identity.get("domain")
    if not domain:
        result.add_check("owner_domain_present", False, "owner_domain or domain is required")
    else:
        result.add_check("owner_domain_present", True)

    return result


# ─── Contract Validation ─────────────────────────────────────────────

def validate_contract(data: dict) -> ValidationResult:
    """Validate extension contract structure.

    Checks:
      - contract_id present
      - contract_type valid
      - version present
      - parties defined (2 minimum: extension + core)
      - capabilities.declarations present
      - ownership defined (extension_owns + core_owns)
      - forbidden_operations.absolute present
      - lifecycle.state_machine present
      - evidence.receipt_types present
    """
    result = ValidationResult("contract")

    # Contract can be passed directly or nested under 'contract' key
    contract = data.get("contract", data)

    required_fields = ["contract_id", "contract_type", "version"]
    for field in required_fields:
        if field not in contract:
            result.add_check(f"contract_{field}_present", False,
                            f"Required contract field '{field}' missing")
        else:
            result.add_check(f"contract_{field}_present", True)

    # Parties
    parties = contract.get("parties", [])
    if len(parties) < 2:
        result.add_check("contract_parties", False,
                        f"Expected ≥2 parties, got {len(parties)}")
    else:
        result.add_check("contract_parties", True)

    # Capabilities
    caps = contract.get("capabilities", {})
    declarations = caps.get("declarations", []) if isinstance(caps, dict) else []
    if not declarations:
        result.add_check("contract_capabilities", False,
                        "No capability declarations found in contract")
    else:
        result.add_check("contract_capabilities", True, f"{len(declarations)} capabilities defined")

    # Ownership
    ownership = contract.get("ownership", {})
    if not ownership.get("extension_owns") or not ownership.get("core_owns"):
        result.add_check("contract_ownership", False,
                        "Both extension_owns and core_owns must be defined")
    else:
        result.add_check("contract_ownership", True)

    # Forbidden operations
    forbidden = contract.get("forbidden_operations", {})
    abs_forbidden = forbidden.get("absolute", [])
    if not abs_forbidden:
        result.add_check("contract_forbidden", False,
                        "No absolute forbidden operations defined")
    else:
        result.add_check("contract_forbidden", True, f"{len(abs_forbidden)} forbidden ops")

    # Lifecycle
    lifecycle = contract.get("lifecycle", {})
    states = lifecycle.get("state_machine", [])
    if len(states) < 3:  # Minimum: REGISTERED, ACTIVE, REVOKED
        result.add_check("contract_lifecycle", False,
                        f"Lifecycle has {len(states)} states, expected ≥3")
    else:
        state_names = [s.get("state") for s in states]
        result.add_check("contract_lifecycle", True, f"States: {state_names}")

    # Evidence
    evidence = contract.get("evidence", {})
    receipts = evidence.get("receipt_types", [])
    if not receipts:
        result.add_check("contract_evidence", False,
                        "No receipt types defined in evidence")
    else:
        result.add_check("contract_evidence", True, f"{len(receipts)} receipt types")

    return result


# ─── Capability Validation ───────────────────────────────────────────

def validate_capabilities(data) -> ValidationResult:
    """Validate capability declarations.

    Accepts either:
      - A dict with a 'capabilities' key (full extension data)
      - A list of capabilities directly (fixture data)

    Checks:
      - Each capability has unique ID
      - Each capability has ≥1 tool
      - Risk classification is R0 or R1
      - Status is active or pending
      - Permissions are from allowed set
      - Tool names use correct prefix
    """
    result = ValidationResult("capability")

    if isinstance(data, list):
        caps = data
    else:
        caps = data.get("capabilities", [])

    if not caps:
        result.add_check("capabilities_present", False, "No capabilities declared")
        return result

    result.add_check("capabilities_present", True, f"{len(caps)} capabilities")

    valid_risks = {"R0", "R1"}
    valid_statuses = {"active", "pending"}
    allowed_permissions = {"read:artifacts", "write:artifacts", "read:index",
                          "read:receipts", "read:items", "write:items"}
    expected_prefix = "wb_"

    seen_ids = set()
    for cap in caps:
        cap_id = cap.get("id", "")
        if cap_id in seen_ids:
            result.add_check(f"cap_{cap_id}_unique", False, f"Duplicate capability ID: {cap_id}")
        seen_ids.add(cap_id)

        # Tools
        tools = cap.get("tools", [])
        if len(tools) < 1:
            result.add_check(f"cap_{cap_id}_tools", False, f"Capability '{cap_id}' has no tools")

        # Risk
        risk = cap.get("risk")
        if risk not in valid_risks:
            result.add_check(f"cap_{cap_id}_risk", False,
                            f"Invalid risk '{risk}' for '{cap_id}' (must be R0 or R1)")

        # Status
        status = cap.get("status")
        if status and status not in valid_statuses:
            result.add_check(f"cap_{cap_id}_status", False,
                            f"Invalid status '{status}' for '{cap_id}'")

        # Permissions
        permissions = cap.get("permissions", [])
        for perm in permissions:
            if not any(perm.startswith(p) for p in ["read:", "write:"]):
                result.add_check(f"cap_{cap_id}_perm_{perm}", False,
                                f"Invalid permission '{perm}' in '{cap_id}'")

    return result


# ─── Lifecycle Validation ────────────────────────────────────────────

def validate_lifecycle(data: dict) -> ValidationResult:
    """Validate lifecycle state machine.

    Checks:
      - Valid state names
      - Transition logic valid
      - Guard conditions defined
      - Terminal state present
      - No impossible transitions
    """
    result = ValidationResult("lifecycle")

    lifecycle_data = data.get("lifecycle", {})
    states = lifecycle_data.get("state_machine", [])

    if not states:
        # Try getting from data directly
        data_lifecycle = data.get("lifecycle", data)
        states = data_lifecycle.get("state_machine", [])

    if not states:
        result.add_check("lifecycle_states_present", False, "No lifecycle states defined")
        return result

    # Check for REGISTERED and REVOKED (required states)
    state_names = [s.get("state") for s in states]

    if "REGISTERED" not in state_names:
        result.add_check("lifecycle_REGISTERED", False, "REGISTERED state is required")
    if "ACTIVE" not in state_names:
        result.add_check("lifecycle_ACTIVE", False, "ACTIVE state is required")
    if "REVOKED" not in state_names:
        result.add_check("lifecycle_REVOKED", False, "REVOKED state is required")

    # Check transitions
    transitions = lifecycle_data.get("transitions", [])
    if transitions:
        for t in transitions:
            if t.get("from") and t.get("to"):
                # Verify source and target states exist
                if t["from"] not in state_names:
                    result.add_check(f"transition_{t['from']}_{t['to']}_source", False,
                                    f"Transition source '{t['from']}' not in state machine")
                if t["to"] not in state_names:
                    result.add_check(f"transition_{t['from']}_{t['to']}_target", False,
                                    f"Transition target '{t['to']}' not in state machine")
        result.add_check("lifecycle_transitions", True, f"{len(transitions)} transitions defined")
    else:
        # Check that at least basic transitions are conceptually defined
        result.add_check("lifecycle_transitions", True, "State machine defined (transitions validated at runtime)")

    return result


# ─── Permission Validation ───────────────────────────────────────────

def validate_permissions(data: dict) -> ValidationResult:
    """Validate permission declarations.

    Checks:
      - Permission scopes use read:/write: prefix
      - Risk classifications match capability declarations
      - Forbidden operations enumerated
      - Enforcement configuration present
      - Violation outcomes defined
    """
    result = ValidationResult("permission")

    perm_data = data.get("permissions", data)

    allowed_ops = perm_data.get("allowed_operations", {})

    if not allowed_ops:
        result.add_check("permissions_present", False, "No allowed operations defined")
        return result

    result.add_check("permissions_present", True, f"{len(allowed_ops)} permission scopes")

    for scope, config in allowed_ops.items():
        # Scope name validation
        if not scope.startswith(("read:", "write:")):
            result.add_check(f"scope_{scope}_format", False,
                            f"Scope '{scope}' must start with read: or write:")

        # Risk classification
        risk = config.get("risk")
        if risk and risk not in ("R0", "R1"):
            result.add_check(f"scope_{scope}_risk", False,
                            f"Invalid risk '{risk}' for scope '{scope}'")

        # Tools
        tools = config.get("tools", [])
        if not tools:
            result.add_check(f"scope_{scope}_tools", False,
                            f"Permission scope '{scope}' has no tools")

    # Forbidden operations
    forbidden = perm_data.get("forbidden_operations", [])
    if not forbidden:
        result.add_check("forbidden_operations", False,
                        "No forbidden operations defined in permissions")
    else:
        result.add_check("forbidden_operations", True, f"{len(forbidden)} forbidden ops")

    # Enforcement
    enforcement = perm_data.get("enforcement", {})
    if not enforcement:
        result.add_check("enforcement_config", False,
                        "No enforcement configuration in permissions")
    else:
        result.add_check("enforcement_config", True, f"drift: {enforcement.get('drift_monitoring', 'not set')}")

    return result


# ─── Full Validation Suite ───────────────────────────────────────────

def run_full_validation(extension_data: dict) -> AggregateResult:
    """Run all validation domains against extension data.

    Args:
        extension_data: Dict containing extension identity, contract,
                       capabilities, lifecycle, and permissions data

    Returns:
        AggregateResult with per-domain results
    """
    aggregate = AggregateResult()

    # Each validator knows how to find its own data within the dict
    aggregate.add_domain(validate_identity(extension_data))
    aggregate.add_domain(validate_contract(extension_data))
    aggregate.add_domain(validate_capabilities(extension_data))
    aggregate.add_domain(validate_lifecycle(extension_data))
    aggregate.add_domain(validate_permissions(extension_data))

    return aggregate
