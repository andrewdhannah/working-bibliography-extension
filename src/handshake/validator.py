"""
Contract and Capability Validator — Handshake Steps 2-3

Implements:
  Step 2: Librarian retrieves and validates contract declaration
  Step 3: Capability manifest is validated against contract

Per EXTENSION-HANDSHAKE-CONTRACT.md:
  - Contract version must be known and supported
  - Every declared tool must exist in the extension's tools/list
  - No tool may appear outside declared capabilities
  - Forbidden actions must be acknowledged
  - Capability scope must not exceed contract definitions
"""

import json
import os
from datetime import datetime, timezone


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _load_json(path: str) -> dict:
    """Load a JSON file."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _load_contract() -> dict:
    """Load the canonical extension contract."""
    path = os.path.join(PROJECT_ROOT, "docs", "contracts", "WB-LIBRARIAN-CONTRACT-v1.json")
    return _load_json(path)


def _load_capability_manifest() -> dict:
    """Load the runtime capability manifest."""
    path = os.path.join(PROJECT_ROOT, "mcp", "capabilities.json")
    return _load_json(path)


def get_available_tools() -> list:
    """Get the list of tools currently available from the MCP server.

    In a live system this would call tools.list on the MCP endpoint.
    For the handshake implementation, we read from the capability manifest
    which is the declared tool surface.
    """
    manifest = _load_capability_manifest()
    tools = []
    for cap in manifest.get("capabilities", []):
        tools.extend(cap.get("tools", []))
    return sorted(set(tools))


class ValidationError(Exception):
    """Raised when contract or capability validation fails."""
    pass


class ValidationResult:
    """Container for validation results with structured output."""

    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []
        self.valid = True

    def add_check(self, name: str, passed: bool, detail: str = None):
        self.checks.append({
            "check": name,
            "passed": passed,
            "detail": detail
        })
        if not passed:
            self.valid = False
            self.errors.append(f"{name}: {detail}")

    def add_warning(self, name: str, detail: str):
        self.warnings.append({"check": name, "detail": detail})
        self.checks.append({
            "check": name,
            "passed": True,
            "detail": f"WARNING: {detail}"
        })

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checks_passed": sum(1 for c in self.checks if c["passed"]),
            "checks_total": len(self.checks),
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks
        }


def validate_contract_version(contract_version: str) -> bool:
    """Check if the declared contract version is known and supported.

    Per WB-LIBRARIAN-CONTRACT-v1: stability MAJOR, version 1.0.0
    """
    contract = _load_contract()
    if not contract:
        return False
    known_version = contract.get("version")
    return contract_version == known_version


def validate_capability_manifest(manifest: dict) -> ValidationResult:
    """Validate the capability manifest against the contract.

    Checks (per CAPABILITY-MANIFEST.md §6):
      M-001: All required identity fields present
      M-002: extension_id matches contract party
      M-003: Every declared tool exists in tools/list
      M-004: No tool appears without a declared capability
      M-005: Forbidden actions match the contract
      M-006: Risk classification is valid
      M-008: Receipt types match the contract
    """
    result = ValidationResult()
    contract = _load_contract()

    if not contract:
        result.add_check("contract_load", False, "Contract document not found")
        return result

    # M-001: Required identity fields
    req_fields = ["extension_id", "version", "contract_id", "contract_version", "declared_at"]
    identity = manifest.get("identity", {})
    for field in req_fields:
        if field not in identity:
            result.add_check(f"M-001_identity_{field}", False, f"Missing identity field: {field}")

    # M-002: extension_id matches contract
    declared_id = identity.get("extension_id")
    contract_id = contract.get("identity", {}).get("extension_id")
    if declared_id and contract_id:
        result.add_check("M-002_id_match", declared_id == contract_id,
                        f"extension_id '{declared_id}' vs contract '{contract_id}'")
    else:
        result.add_check("M-002_id_match", False, "Cannot compare identity: missing fields")

    # M-003: Every declared tool exists in available tools
    available = get_available_tools()
    for cap in manifest.get("capabilities", []):
        for tool in cap.get("tools", []):
            exists = tool in available
            result.add_check(f"M-003_tool_exists_{tool}", exists,
                           f"Tool '{tool}' declared in manifest but not in tools/list" if not exists else None)

    # M-004: No tool without a declared capability (inverse of M-003)
    declared_tools = set()
    for cap in manifest.get("capabilities", []):
        declared_tools.update(cap.get("tools", []))
    for tool in available:
        if tool not in declared_tools:
            result.add_check(f"M-004_tool_undeclared_{tool}", False,
                           f"Tool '{tool}' exists in tools/list but is not declared in any capability")

    # M-005: Forbidden actions match contract
    manifest_forbidden = {f.get("action") for f in manifest.get("forbidden_actions", [])}
    contract_forbidden = {f.get("operation") for f in contract.get("forbidden_operations", {}).get("absolute", [])}
    missing_forbidden = contract_forbidden - manifest_forbidden
    for action in missing_forbidden:
        result.add_check(f"M-005_forbidden_missing_{action}", False,
                        f"Forbidden action '{action}' is in the contract but not in the manifest")

    # M-006: Risk classification valid
    valid_risks = {"R0", "R1"}
    for cap in manifest.get("capabilities", []):
        risk = cap.get("risk")
        if risk not in valid_risks:
            result.add_check(f"M-006_risk_{cap['id']}", False,
                           f"Invalid risk classification '{risk}' for capability '{cap['id']}'")

    # M-008: Receipt types match contract
    manifest_receipts = {r.get("type") for r in manifest.get("receipt_types", [])}
    contract_receipts = {r.get("type") for r in contract.get("evidence", {}).get("receipt_types", [])}
    missing_receipts = contract_receipts - manifest_receipts
    for rtype in missing_receipts:
        result.add_warning(f"M-008_receipt_missing_{rtype}",
                          f"Receipt type '{rtype}' is in the contract but not in the manifest")

    return result


def validate_contract_compatibility(declared_version: str) -> ValidationResult:
    """Validate that the declared contract version is compatible.

    Checks:
      - Contract version exists
      - Version matches known contract
      - Contract stability allows this connection
    """
    result = ValidationResult()
    contract = _load_contract()

    if not contract:
        result.add_check("contract_load", False, "Contract document not found")
        return result

    version_ok = validate_contract_version(declared_version)
    result.add_check("version_match", version_ok,
                    f"Contract version '{declared_version}' vs known '{contract.get('version')}'" if not version_ok else None)

    stability = contract.get("stability", "unknown")
    result.add_check("contract_stability", stability == "MAJOR",
                    f"Expected MAJOR stability, got '{stability}'" if stability != "MAJOR" else None)

    contract_type = contract.get("contract_type")
    expected_type = "connector_custody"
    result.add_check("contract_type", contract_type == expected_type,
                    f"Expected '{expected_type}', got '{contract_type}'" if contract_type != expected_type else None)

    return result


def validate_activation_readiness(registration: dict, manifest_validation: ValidationResult,
                                  contract_validation: ValidationResult) -> ValidationResult:
    """Check whether the extension is ready for OWNER_APPROVED → ACTIVE transition.

    Requirements:
      - Identity registered
      - Manifest validated (no errors)
      - Contract compatible (no errors)
    """
    result = ValidationResult()

    state = registration.get("state", "UNKNOWN")
    result.add_check("state_is_registered_or_verified",
                    state in ("REGISTERED", "CONTRACT_VERIFIED"),
                    f"Current state is '{state}', expected REGISTERED or CONTRACT_VERIFIED")

    result.add_check("manifest_valid", manifest_validation.valid,
                    "Capability manifest has validation errors" if not manifest_validation.valid else None)

    result.add_check("contract_compatible", contract_validation.valid,
                    "Contract compatibility has errors" if not contract_validation.valid else None)

    return result
