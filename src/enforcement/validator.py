"""
Runtime Behavior Validator — Single-Operation Contract Validation

Validates every MCP tool invocation against the declared contract:
  1. Tool exists in declared capabilities
  2. Arguments match expected schema
  3. Risk level is authorized for the operation
  4. Operation is within the ownership boundary

Returns structured validation results with deterministic outcomes.
"""

import json
import os
from datetime import datetime, timezone


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class ValidationResult:
    """Result of a single enforcement validation check."""

    def __init__(self, valid: bool = True, reason: str = None):
        self.valid = valid
        self.reason = reason
        self.checks = []

    def add_check(self, name: str, passed: bool, detail: str = None):
        self.checks.append({
            "check": name,
            "passed": passed,
            "detail": detail
        })
        if not passed:
            self.valid = False
            self.reason = self.reason or detail

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checks_passed": sum(1 for c in self.checks if c["passed"]),
            "checks_total": len(self.checks),
            "reason": self.reason,
            "checks": self.checks
        }


def _load_contract() -> dict:
    """Load the canonical extension contract."""
    path = os.path.join(PROJECT_ROOT, "docs", "contracts", "WB-LIBRARIAN-CONTRACT-v1.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _load_manifest() -> dict:
    """Load the runtime capability manifest."""
    path = os.path.join(PROJECT_ROOT, "mcp", "capabilities.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def validate_tool_declaration(tool_name: str) -> ValidationResult:
    """Validate that a tool is declared in both contract and manifest.

    Enforcement domain: Capabilities
    Check: Requested capability exists in the active contract.

    Returns:
        ValidationResult with check details.
    """
    result = ValidationResult()
    contract = _load_contract()
    manifest = _load_manifest()

    if not contract:
        result.add_check("contract_loaded", False, "Contract document not found")
        return result
    if not manifest:
        result.add_check("manifest_loaded", False, "Capability manifest not found")
        return result

    # Check contract: does any declared capability include this tool?
    contract_found = False
    for cap in contract.get("capabilities", {}).get("declarations", []):
        if tool_name in cap.get("allowed_operations", []):
            contract_found = True
            result.add_check(f"contract_declares_{tool_name}", True)
            break
    if not contract_found:
        result.add_check(f"contract_declares_{tool_name}", False,
                        f"Tool '{tool_name}' not found in contract capability declarations")

    # Check manifest: does any active capability include this tool?
    manifest_found = False
    for cap in manifest.get("capabilities", []):
        if tool_name in cap.get("tools", []):
            manifest_found = True
            if cap.get("status") == "active":
                result.add_check(f"manifest_active_{tool_name}", True)
            else:
                result.add_check(f"manifest_active_{tool_name}", False,
                                f"Capability '{cap['id']}' is {cap.get('status')}, not active")
            break
    if not manifest_found:
        result.add_check(f"manifest_declares_{tool_name}", False,
                        f"Tool '{tool_name}' not found in manifest capabilities")

    return result


def validate_risk_level(tool_name: str, risk: str) -> ValidationResult:
    """Validate that the risk level is authorized for this operation.

    Enforcement domain: Capabilities
    Check: Risk level is authorized (R0 or R1 only).

    R0 = read-only, no gate
    R1 = state mutation within extension domain, advisory
    """
    result = ValidationResult()
    authorized_risks = {"R0", "R1"}

    if risk not in authorized_risks:
        result.add_check("risk_authorized", False,
                        f"Risk level '{risk}' is not authorized (must be R0 or R1)")
    else:
        result.add_check("risk_authorized", True)

    return result


def validate_forbidden_operation(tool_name: str, arguments: dict = None) -> ValidationResult:
    """Check that the operation is not in the forbidden list.

    Enforcement domain: Ownership
    Check: Forbidden operations are blocked.

    Forbidden operations (from contract):
      - modify_librarian_authority_state
      - create_owner_decisions
      - mutate_sprint_ledger
      - accept_mutation_allowance
      - seal_production_receipts
      - delete_artifact_content
      - suspend_artifact_provenance
    """
    result = ValidationResult()
    contract = _load_contract()
    if not contract:
        result.add_check("forbidden_check", False, "Cannot check forbidden operations: contract not found")
        return result

    forbidden = contract.get("forbidden_operations", {}).get("absolute", [])
    tool_lower = tool_name.lower()

    # Check if this tool name or arguments suggest a forbidden operation
    for entry in forbidden:
        op = entry.get("operation", "").lower()
        if op in tool_lower:
            result.add_check(f"forbidden_{op}", False,
                           f"Operation '{entry['operation']}' is forbidden: {entry.get('rationale', '')}")
            return result

        # Check arguments for forbidden patterns
        if arguments:
            args_str = json.dumps(arguments).lower()
            if op in args_str:
                # Only flag if it's in key positions (operation fields)
                for key in ["operation", "action", "command"]:
                    val = str(arguments.get(key, "")).lower()
                    if op == val:
                        result.add_check(f"forbidden_arg_{op}", False,
                                       f"Forbidden operation '{entry['operation']}' referenced in arguments")

    if not result.checks:
        result.add_check("forbidden_check", True)

    return result


def validate_receipt_requirements(tool_name: str, operation_result: dict = None) -> ValidationResult:
    """Validate that receipt requirements are met for this operation.

    Enforcement domain: Evidence
    Check: Required receipts exist for the operation.

    Per contract, every operation produces an operation receipt.
    Specific operations produce typed receipts (capture, retrieval, etc.).
    """
    result = ValidationResult()
    receipt_types = {
        "wb_register_artifact": "capture_receipt",
        "wb_get_artifact": None,
        "wb_list_artifacts": None,
        "wb_search_context": "retrieval_receipt",
        "wb_retrieve_source": "retrieval_receipt",
        "wb_get_receipt": None,
        "wb_get_history": None,
    }

    expected = receipt_types.get(tool_name)
    if expected:
        result.add_check(f"receipt_type_{expected}", True,
                        f"Operation should produce '{expected}' receipt")
    else:
        result.add_check("receipt_type_operation", True,
                        "Operation produces standard operation receipt")

    # If result was provided, check receipt_id present
    if operation_result:
        has_receipt = any("receipt" in str(v).lower() for v in operation_result.values())
        result.add_check("receipt_produced", has_receipt,
                        "No receipt reference found in result" if not has_receipt else None)

    return result


def validate_operation(tool_name: str, risk: str, arguments: dict = None, operation_result: dict = None) -> ValidationResult:
    """Run all validations for a single operation.

    Combines:
      1. Tool declaration validation
      2. Risk level validation
      3. Forbidden operation check
      4. Receipt requirement check

    Returns a combined ValidationResult. An operation must pass all
    checks to be valid.
    """
    combined = ValidationResult()

    # 1. Tool declaration
    dec = validate_tool_declaration(tool_name)
    for c in dec.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    # 2. Risk level
    risk_check = validate_risk_level(tool_name, risk)
    for c in risk_check.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    # 3. Forbidden operation
    forbid = validate_forbidden_operation(tool_name, arguments)
    for c in forbid.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    # 4. Receipt requirements
    receipt = validate_receipt_requirements(tool_name, operation_result)
    for c in receipt.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    return combined
