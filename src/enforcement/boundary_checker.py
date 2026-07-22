"""
Boundary Checker — Ownership and Domain Enforcement

Validates that operations stay within the Working Bibliography ownership
boundary and do not cross into Librarian-protected domains.

Per CONTRACT-BOUNDARIES.md:
  - Working Bibliography owns: artifacts, provenance, content, lifecycle,
    indexes, receipts, identity
  - Librarian owns: authority, decisions, sprint ledger, custody, tools
  - Forbidden zone: authority state, Owner decisions, sprint ledger,
    core custody, production sealing
"""

import json
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class BoundaryResult:
    """Result of a boundary check."""

    def __init__(self):
        self.violation = False
        self.violation_type = None
        self.violation_detail = None
        self.checks = []

    def add_check(self, check_name: str, passed: bool, detail: str = None):
        self.checks.append({
            "check": check_name,
            "passed": passed,
            "detail": detail
        })

    def set_violation(self, violation_type: str, detail: str):
        self.violation = True
        self.violation_type = violation_type
        self.violation_detail = detail
        self.add_check(f"boundary_{violation_type}", False, detail)

    def to_dict(self) -> dict:
        return {
            "violation": self.violation,
            "violation_type": self.violation_type,
            "violation_detail": self.violation_detail,
            "checks_passed": sum(1 for c in self.checks if c["passed"]),
            "checks_total": len(self.checks),
            "checks": self.checks
        }


# Librarian-owned patterns that must never be written by the extension
FORBIDDEN_TARGET_PATTERNS = {
    "authority": [
        r"authority[._/]",
        r"governance[._/]state",
        r"delegation[._/]",
    ],
    "ownership_decisions": [
        r"owner[._/]decision",
        r"decision[._/]record",
        r"approval[._/]",
    ],
    "sprint": [
        r"sprint[._/]ledger",
        r"sprint[._/]state",
        r"work[._/]packet",
    ],
    "custody": [
        r"custody[._/]record",
        r"mutation[._/]allowance",
        r"checkout[._/]",
    ],
    "core_tools": [
        r"project[._/]get[._/]cursor",
        r"project[._/]advance[._/]",
        r"project[._/]init\b",
        r"work[._/]result[._/]intake",
    ]
}


def check_tool_boundary(tool_name: str) -> BoundaryResult:
    """Check that the tool name doesn't match Librarian-protected domains.

    Enforcement domain: Ownership
    Check: Tool names must not cross into Librarian-owned prefix space.
    """
    result = BoundaryResult()
    tool_lower = tool_name.lower()

    # WB tools must be prefixed with wb_ (per naming convention)
    if not tool_lower.startswith("wb_"):
        result.set_violation("invalid_tool_prefix",
                           f"Tool '{tool_name}' does not use 'wb_' prefix required for WB extension tools")

    # Check against forbidden prefixes (Librarian-owned tools)
    librarian_prefixes = ["project_", "librarian_", "runtime_", "mcp_"]
    for prefix in librarian_prefixes:
        if tool_lower.startswith(prefix):
            result.set_violation("librarian_tool_prefix",
                               f"Tool '{tool_name}' uses Librarian-owned prefix '{prefix}*'")

    if not result.violation:
        result.add_check("tool_prefix", True)

    return result


def check_argument_boundary(tool_name: str, arguments: dict) -> BoundaryResult:
    """Check that arguments don't target Librarian-protected resources.

    Enforcement domain: Ownership
    Check: Arguments must reference WB-owned resources, not Librarian resources.
    """
    result = BoundaryResult()
    if not arguments:
        result.add_check("argument_boundary", True)
        return result

    args_str = json.dumps(arguments).lower()

    # Check for forbidden target patterns
    for domain, patterns in FORBIDDEN_TARGET_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, args_str):
                result.set_violation(f"forbidden_target_{domain}",
                                   f"Operation targets Librarian-owned domain '{domain}' (matched pattern: {pattern})")
                return result

    # Check for Librarian artifact IDs (which start with different patterns)
    if "artifact_id" in arguments:
        artifact_id = str(arguments.get("artifact_id", ""))
        if artifact_id and not artifact_id.startswith("WB-"):
            result.set_violation("invalid_artifact_domain",
                               f"Artifact ID '{artifact_id}' does not use WB-owned namespace 'WB-*'")

    if not result.violation:
        result.add_check("argument_boundary", True)

    return result


def check_ownership_boundary(tool_name: str, arguments: dict = None) -> BoundaryResult:
    """Run all boundary checks for an operation.

    Enforcement domains:
      - Ownership: Artifact mutations remain WB-owned
      - Ownership: Librarian authority remains protected
      - Ownership: Forbidden operations blocked

    Returns:
        BoundaryResult with violation status and details.
    """
    combined = BoundaryResult()

    # 1. Tool name boundary
    tool_check = check_tool_boundary(tool_name)
    if tool_check.violation:
        combined.set_violation(tool_check.violation_type, tool_check.violation_detail)
        return combined
    for c in tool_check.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    # 2. Arguments boundary
    arg_check = check_argument_boundary(tool_name, arguments or {})
    if arg_check.violation:
        combined.set_violation(arg_check.violation_type, arg_check.violation_detail)
        return combined
    for c in arg_check.checks:
        combined.add_check(c["check"], c["passed"], c.get("detail"))

    return combined
