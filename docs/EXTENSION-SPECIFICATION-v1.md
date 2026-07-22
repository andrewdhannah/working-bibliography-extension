# Librarian Extension Specification v1

**Compliance requirements for governed extensions. Independent of implementation.**

---

## 1. Extension Definition

A Librarian extension is an independently governed capability that connects to the Librarian governance kernel through a declared contract, identity verification, lifecycle management, and continuous compliance monitoring.

An extension is **not** a plugin. It does not request access — it establishes trust through a verifiable process.

### Core Principle

> Extensions are not granted access. They establish a contract, declare capabilities, pass validation, and operate within defined ownership boundaries.

---

## 2. Required Artifacts

Every Librarian extension must provide:

| Artifact | Required | Format | Purpose |
|---|---|---|---|
| Identity declaration | Yes | JSON | extension_id, version, contract reference |
| Contract document | Yes | JSON | Formal agreement between extension and core |
| Capability manifest | Yes | JSON | Declared tools, risk levels, permissions |
| Permission configuration | Yes | JSON | Allowed operations, forbidden actions, enforcement |
| Handshake implementation | Yes | Code | Lifecycle state machine supporting 6 states |
| MCP server | Yes | Code | JSON-RPC 2.0 surface for declared capabilities |
| Receipt generation | Yes | Code | Evidence for every governed operation |
| Drift detection | Yes | Code | Continuous comparison against approved baseline |
| Enforcement logic | Yes | Code | Contract validation, boundary checks |
| Revocation handling | Yes | Code | SUSPENDED/REVOKED state enforcement |

---

## 3. Identity Requirements

### 3.1 Identity Fields

| Field | Required | Format | Example |
|---|---|---|---|
| `extension_id` | Yes | `^[a-z][a-z0-9_-]+$` | `working-bibliography-extension` |
| `version` | Yes | semver `^\d+\.\d+\.\d+$` | `0.1.0` |
| `contract_id` | Yes | `^[a-z][a-z0-9_-]+-v\d+$` | `wb-librarian-contract-v1` |
| `contract_version` | Yes | semver `^\d+\.\d+\.\d+$` | `1.0.0` |
| `owner_domain` | Yes | string | `knowledge_custody` |
| `declared_at` | Yes | ISO 8601 | `2026-07-21T18:00:00Z` |

### 3.2 Identity Rules

| Rule | Description |
|---|---|
| ID-001 | extension_id is immutable after registration |
| ID-002 | A re-handshake is required if identity changes |
| ID-003 | extension_id must match the contract's party declaration |
| ID-004 | Impersonation of another registered ID → REVOKED |

---

## 4. Contract Requirements

### 4.1 Contract Structure

```json
{
  "contract_id": "your-extension-contract-v1",
  "contract_type": "connector_custody",
  "version": "1.0.0",
  "stability": "MAJOR",
  "parties": [
    { "role": "extension", "id": "your-extension-id" },
    { "role": "core", "id": "librarian" }
  ],
  "identity": { ... },
  "capabilities": { "declarations": [...] },
  "ownership": {
    "extension_owns": { "domains": [...] },
    "core_owns": { "domains": [...] }
  },
  "forbidden_operations": { "absolute": [...] },
  "lifecycle": { "state_machine": [...], "transitions": [...] },
  "evidence": { "receipt_types": [...] },
  "enforcement": { ... },
  "drift_classification": { "PASS": ..., "OBSERVATION": ..., "REVOKE": ... },
  "non_goals": [...]
}
```

### 4.2 Required Contract Sections

| Section | Required | Purpose |
|---|---|---|
| contract_id | Yes | Unique contract identifier |
| contract_type | Yes | Must be `connector_custody` or `service_capability` |
| version | Yes | Contract document version |
| parties | Yes | Extension + Core (minimum 2) |
| identity | Yes | Extension identity reference |
| capabilities.declarations | Yes | Declared capabilities (≥1) |
| ownership.extension_owns | Yes | What the extension owns |
| ownership.core_owns | Yes | What Librarian owns |
| forbidden_operations.absolute | Yes | Never-allowed operations (≥1) |
| lifecycle.state_machine | Yes | Lifecycle states (≥3: REGISTERED, ACTIVE, REVOKED) |
| evidence.receipt_types | Yes | Evidence types (≥1) |
| enforcement | Yes | Drift monitoring and violation outcomes |

### 4.3 Contract Rules

| Rule | Description |
|---|---|
| CT-001 | Contract must declare both extension_owns and core_owns domains |
| CT-002 | Forbidden operations must include authority state mutation prohibition |
| CT-003 | Lifecycle must include REGISTERED, ACTIVE, and REVOKED states |
| CT-004 | Evidence must define at least one receipt type |
| CT-005 | Contract version changes require re-handshake |

---

## 5. Capability Requirements

### 5.1 Capability Structure

```json
{
  "id": "your.read",
  "display_name": "Read Items",
  "tools": ["your_get_item", "your_list_items"],
  "risk": "R0",
  "description": "Read items from your domain",
  "permissions": ["read:items"],
  "status": "active"
}
```

### 5.2 Risk Classification

| Level | Meaning | Gate |
|---|---|---|
| R0 | Read-only, no state mutation | None |
| R1 | State mutation within extension domain | Advisory — evidence logged |
| R2 | Reserved for future use | Requires core expansion |

### 5.3 Permission Scopes

| Scope | Pattern | Example |
|---|---|---|
| Read | `read:<domain>` | `read:artifacts`, `read:items` |
| Write | `write:<domain>` | `write:artifacts`, `write:items` |

### 5.4 Capability Rules

| Rule | Description |
|---|---|
| CP-001 | Each capability must have a unique ID |
| CP-002 | Each capability must have ≥1 tool |
| CP-003 | Risk must be R0 or R1 |
| CP-004 | Status must be `active` or `pending` |
| CP-005 | `pending` capabilities are contract-defined but not exposed in tools/list |
| CP-006 | Permission scopes must start with `read:` or `write:` |

---

## 6. MCP Requirements

### 6.1 Protocol

- Transport: JSON-RPC 2.0 over HTTP
- Endpoint: `POST /mcp`
- Methods: `tools/list`, `tools/call`
- Health: `GET /health`

### 6.2 Tool Naming

| Rule | Description |
|---|---|
| MCP-001 | All extension tools must use a unique prefix (e.g., `wb_`) |
| MCP-002 | Tools must not use Librarian-owned prefixes: `project_`, `librarian_`, `runtime_`, `mcp_` |
| MCP-003 | Every tool must have a declared input schema |
| MCP-004 | tools/list must return only `active` capabilities |
| MCP-005 | tools/call must validate lifecycle state before execution |

### 6.3 Permission Enforcement

Every tool call must pass through four gates:

```
1. Lifecycle check: Is extension ACTIVE?
2. Capability check: Is tool declared in manifest?
3. Permission check: Does capability have required scope?
4. Enforcement: Does operation match contract? Within boundaries?
```

---

## 7. Lifecycle Requirements

### 7.1 Required States

| State | Required | Capabilities |
|---|---|---|
| REGISTERED | Yes | None |
| CONTRACT_VERIFIED | Recommended | None |
| OWNER_APPROVED | Recommended | None |
| ACTIVE | Yes | All declared |
| SUSPENDED | Recommended | Blocked (read-only exceptions) |
| REVOKED | Yes | None (historical access only) |

### 7.2 Required Transitions

| From | To | Authority |
|---|---|---|
| REGISTERED | CONTRACT_VERIFIED | automated |
| CONTRACT_VERIFIED | OWNER_APPROVED | owner |
| OWNER_APPROVED | ACTIVE | automated |
| ACTIVE | SUSPENDED | automated or owner |
| ACTIVE | REVOKED | owner |
| SUSPENDED | ACTIVE | owner |
| SUSPENDED | REVOKED | owner |

### 7.3 Lifecycle Rules

| Rule | Description |
|---|---|
| LC-001 | REVOKED is terminal — no transitions out |
| LC-002 | Capabilities require ACTIVE state |
| LC-003 | Owner approval is required before activation |
| LC-004 | Extension cannot self-approve or self-elevate |
| LC-005 | Every transition must produce a receipt |

---

## 8. Evidence Requirements

### 8.1 Required Receipt Types

| Receipt Type | Required | Produced When |
|---|---|---|
| registration_receipt | Yes | Handshake identity established |
| contract_verification_receipt | Yes | Contract validated |
| approval_receipt | Yes | Owner approves |
| activation_receipt | Yes | Extension becomes ACTIVE |
| operation_receipt | Yes | Every tool call |
| lifecycle_receipt | Yes | Every state transition |
| drift_receipt | Yes | Drift detected |

### 8.2 Evidence Rules

| Rule | Description |
|---|---|
| EV-001 | Every operation must produce a receipt |
| EV-002 | Receipts are evidence, not authority records |
| EV-003 | Receipts never cross into Librarian's decision chain |
| EV-004 | Receipts must include a unique ID |
| EV-005 | Receipt storage is extension-local |

---

## 9. Drift Requirements

### 9.1 Drift Domains

| Domain | What Is Compared | Classification |
|---|---|---|
| Identity | extension_id, contract_id, version | REVOKE on change |
| Capability (tools) | Declared vs observed tool lists | REVOKE on add, OBSERVATION on remove |
| Capability (risk) | Risk level per capability | REVOKE on escalation |
| Contract version | Version string | OBSERVATION |
| Permissions | Forbidden operations list | REVOKE on removal |
| Boundary | Enforcement configuration | REVOKE on critical change |
| Receipt evidence | Required receipt types | OBSERVATION on removal |

### 9.2 Classification Rules

| Classification | Meaning | Action |
|---|---|---|
| PASS | Expected matches observed | None |
| OBSERVATION | Non-breaking deviation | Owner notified, extension continues |
| REVOKE | Contract violation confirmed | SUSPENDED or REVOKED |

### 9.3 Drift Rules

| Rule | Description |
|---|---|
| DR-001 | Baseline must be captured at handshake time |
| DR-002 | Drift detection does not automatically remediate |
| DR-003 | Drift while SUSPENDED → remain SUSPENDED |
| DR-004 | Every drift scan produces a receipt |

---

## 10. Revocation Requirements

### 10.1 Access Control by State

| Operation | ACTIVE | SUSPENDED | REVOKED |
|---|---|---|---|
| Capability execution | ✅ | ❌ | ❌ |
| Health checks | ✅ | ✅ | ❌ |
| Identity queries | ✅ | ✅ | ✅ |
| Receipt retrieval | ✅ | ✅ | ✅ |
| Drift reports | ✅ | ✅ | ✅ (history) |
| Audit queries | ✅ | ❌ | ✅ |

### 10.2 Revocation Rules

| Rule | Description |
|---|---|
| RV-001 | Revocation is not deletion. Identity, receipts, history preserved |
| RV-002 | REVOKED is terminal |
| RV-003 | Recovery from SUSPENDED requires owner authority |
| RV-004 | Every suspension/revocation/restoration produces a receipt |

---

## 11. Compliance Levels

| Level | Requirements | Status |
|---|---|---|
| **L1 — Contract** | Identity + Contract + Capability manifest | Minimum for registration |
| **L2 — Runtime** | L1 + MCP server + Handshake + Enforcement | Minimum for activation |
| **L3 — Governed** | L2 + Drift detection + Revocation + Receipts | Full governed extension |
| **L4 — Certified** | L3 + Validation fixtures + Compliance report | Passes automated validation |

### L1 — Contract Compliance

Required:
- Identity declaration
- Contract document with all required sections
- Capability manifest

Result: Extension can be REGISTERED and CONTRACT_VERIFIED

### L2 — Runtime Compliance

Required:
- L1 compliance
- Working MCP server implementing declared capabilities
- Handshake lifecycle (6 states)
- Permission enforcement on every tool call

Result: Extension can reach ACTIVE state

### L3 — Governed Compliance

Required:
- L2 compliance
- Baseline capture at handshake
- Drift detection across all 7 domains
- Revocation handling (SUSPENDED + REVOKED states)
- Receipts for every operation and transition

Result: Full governance control loop

### L4 — Certified Compliance

Required:
- L3 compliance
- Passing validation test suite (14 fixture scenarios)
- Published compliance report
- Developer documentation

Result: Certified Librarian extension
