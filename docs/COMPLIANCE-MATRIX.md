# Compliance Matrix — Librarian Extension Requirements

**Maps each requirement to its artifact, validator, and compliance level.**

---

## Identity

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| extension_id present and formatted | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| version in semver format | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| contract_id present | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| contract_version present | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| owner_domain declared | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| declared_at timestamp | `identity.json` or manifest | `validate_identity()` | L1 | §3.1 |
| extension_id matches contract party | Identity + Contract | `validate_identity()` | L1 | ID-003 |

## Contract

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| contract_id | `contract.json` | `validate_contract()` | L1 | §4.2 |
| contract_type (connector_custody) | `contract.json` | `validate_contract()` | L1 | §4.2 |
| version | `contract.json` | `validate_contract()` | L1 | §4.2 |
| parties (≥2) | `contract.json` | `validate_contract()` | L1 | §4.2 |
| capabilities.declarations (≥1) | `contract.json` | `validate_contract()` | L1 | CT-001 |
| ownership (extension + core) | `contract.json` | `validate_contract()` | L1 | CT-001 |
| forbidden_operations.absolute (≥1) | `contract.json` | `validate_contract()` | L1 | CT-002 |
| lifecycle.state_machine (≥3 states) | `contract.json` | `validate_contract()` | L1 | CT-003 |
| evidence.receipt_types (≥1) | `contract.json` | `validate_contract()` | L1 | CT-004 |

## Capability

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| Unique capability IDs | `capabilities.json` | `validate_capabilities()` | L1 | CP-001 |
| ≥1 tool per capability | `capabilities.json` | `validate_capabilities()` | L1 | CP-002 |
| Risk is R0 or R1 | `capabilities.json` | `validate_capabilities()` | L1 | CP-003 |
| Status is active or pending | `capabilities.json` | `validate_capabilities()` | L1 | CP-004 |
| Permission scopes valid | `capabilities.json` | `validate_capabilities()` | L1 | CP-006 |

## MCP

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| JSON-RPC 2.0 over HTTP | MCP server | Runtime | L2 | §6.1 |
| tools/list returns active tools | MCP server | Runtime | L2 | MCP-004 |
| tools/call validates lifecycle | MCP server | Runtime | L2 | MCP-005 |
| wb_ prefix on tools | MCP server | Runtime | L2 | MCP-001 |
| No Librarian-owned prefixes | MCP server | `check_tool_boundary()` | L2 | MCP-002 |
| Permission enforcement per call | MCP server | `check_tool_permission()` | L2 | §6.3 |

## Lifecycle

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| REGISTERED state | Handshake | `validate_lifecycle()` | L2 | LC-001 |
| ACTIVE state | Handshake | `validate_lifecycle()` | L2 | LC-002 |
| REVOKED state | Handshake | `validate_lifecycle()` | L2 | LC-003 |
| State transitions valid | Handshake | `validate_transition()` | L2 | §7.2 |
| REVOKED is terminal | Handshake | `validate_transition()` | L2 | LC-001 |
| Owner approval for activation | Handshake | `check_authority()` | L2 | LC-003 |

## Evidence

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| Registration receipt | Receipts | `validate_receipt_evidence()` | L3 | EV-001 |
| Operation receipt per call | Receipts | `validate_receipt_evidence()` | L3 | EV-001 |
| Lifecycle transition receipt | Receipts | `validate_receipt_evidence()` | L3 | EV-001 |
| Drift receipt on findings | Receipts | `validate_receipt_evidence()` | L3 | EV-001 |

## Drift

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| Baseline captured at handshake | `baseline.py` | `capture_baseline()` | L3 | DR-001 |
| Identity drift detection | `drift/` | `compare_identity()` | L3 | §9.1 |
| Capability drift detection | `drift/` | `compare_manifest_tools()` | L3 | §9.1 |
| Permission drift detection | `drift/` | `compare_permissions()` | L3 | §9.1 |
| Drift scan receipt per check | `receipts/drift_scans/` | `generate_drift_scan_receipt()` | L3 | DR-004 |

## Revocation

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| SUSPENDED blocks capabilities | Revocation | `is_operation_allowed()` | L3 | RV-001 |
| REVOKED is terminal | Revocation | `validate_transition()` | L3 | RV-002 |
| Recovery requires owner | Revocation | `check_authority()` | L3 | RV-003 |
| Suspension receipt | Revocation | Receipts | L3 | RV-004 |
| Revocation receipt | Revocation | Receipts | L3 | RV-004 |
| Restoration receipt | Revocation | Receipts | L3 | RV-004 |

## Validation

| Requirement | Artifact | Validator | Level | Reference |
|---|---|---|---|---|
| Valid extension fixture passes | `tests/fixtures/valid/` | `run_full_validation()` | L4 | §11 |
| Invalid extension fixture fails | `tests/fixtures/invalid/` | `run_full_validation()` | L4 | §11 |
| Boundary condition tested | `tests/fixtures/boundary/` | `run_full_validation()` | L4 | §11 |
| Compliance report generated | `validation/report.py` | `ValidationReport` | L4 | §11 |

---

## Compliance Level Summary

| Level | Total Checks | Gate |
|---|---|---|
| L1 — Contract | ~20 | Registration possible |
| L2 — Runtime | ~35 | Activation possible |
| L3 — Governed | ~55 | Full lifecycle governance |
| L4 — Certified | ~60 + fixture suite | Verifiable compliance |

## Quick Reference

```
Require an extension?
  → Check L1 artifacts (identity, contract, capabilities)

Activate an extension?
  → Verify L2 (MCP, handshake, enforcement)

Govern an extension?
  → Confirm L3 (drift, revocation, receipts)

Publish an extension?
  → Pass L4 (validation fixtures, compliance report)
```
