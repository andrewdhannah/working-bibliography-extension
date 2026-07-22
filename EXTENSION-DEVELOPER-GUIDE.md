# Librarian Extension Developer Guide

**Build a governed capability that connects to the Librarian governance kernel.**

This guide explains how to create an extension for the Librarian ecosystem. It is based on the Working Bibliography Extension — the first reference implementation of the Librarian extension model.

---

## 1. What Is a Librarian Extension?

A Librarian extension is an independently governed capability that connects to the Librarian core through a declared contract, identity verification, and lifecycle management. Unlike a plugin (which requests access), an extension establishes trust through a verifiable process.

### Core Principle

> Extensions are not granted access. They establish a contract, declare capabilities, pass validation, and operate within defined ownership boundaries.

### Two Extension Types

| Type | Example | Owns | Contract |
|---|---|---|---|
| **Knowledge Custody Provider** | Working Bibliography, Document Archive | Artifacts, provenance, indexes, lifecycle | connector_custody |
| **Capability Provider** | Embedding service, Model runtime | Model execution, service state | service_capability |

### Architecture

```
Librarian Core (governance kernel)
    │
MCP Extension Port (JSON-RPC 2.0)
    │
Your Extension
    │
    ├── Owned domain (your data, your lifecycle)
    ├── Declared capabilities (your MCP tools)
    └── Extension contract (your promises)
```

---

## 2. What Your Extension Owns vs What Librarian Owns

### Your Extension Owns

- **Domain data** — artifacts, records, files your extension manages
- **Provenance** — source metadata, timestamps, authorship
- **Domain lifecycle** — state transitions within your domain
- **Derived indexes** — embeddings, search vectors, caches
- **Domain receipts** — evidence of your operations
- **Extension identity** — manifest, capabilities, contract

### Librarian Core Owns

- **Governance authority** — who can do what
- **Owner decisions** — approval, rejection, escalation
- **Project lifecycle** — sprint state, phase transitions
- **Sprint ledger** — canonical work history
- **Core custody records** — checkouts, mutation allowances
- **Extension approval** — registration, verification, activation
- **Trust evaluation** — drift monitoring, suspension, revocation

### Absolute Prohibitions

| Never Do This | Why | Consequence |
|---|---|---|
| Write Librarian authority state | Authority is core-only | REVOKED |
| Create or resolve Owner decisions | Decisions require Owner | REVOKED |
| Mutate sprint ledger | Core-controlled record | REVOKED |
| Accept core mutation allowance | EXTERNAL_REFERENCE only | REVOKED |
| Seal production receipts | Sealing is authority act | REVOKED |
| Delete artifact content | Content persists for audit | SUSPENDED |
| Modify provenance after creation | Immutable by design | SUSPENDED |

---

## 3. Extension Lifecycle

Your extension progresses through six governed states:

```
                     REGISTERED
                         │
                    Identity verified
                         ▼
                  CONTRACT_VERIFIED
                         │
                 Capabilities validated
                         │
                ┌── Owner approves ──►
                         │
                         ▼
                   OWNER_APPROVED
                         │
                   Activation signal
                         ▼
                      ACTIVE
                         │
                 ┌───────┴───────┐
                 │               │
           Drift detected   Contract violated
                 │               │
                 ▼               ▼
            SUSPENDED         REVOKED
                 │               │
        ┌────────┴────────┐      │
        │                 │      │
     Cleared         Terminated  │
        │                 │      │
        ▼                 ▼      ▼
     ACTIVE           REVOKED ───┘
                      (terminal)
```

| State | Meaning | Capabilities |
|---|---|---|
| REGISTERED | Discovered, identity known | None |
| CONTRACT_VERIFIED | Manifest validated | None |
| OWNER_APPROVED | Owner authorized activation | Unlocked |
| ACTIVE | Full capability access | All declared |
| SUSPENDED | Drift detected, review | Blocked |
| REVOKED | Contract violation | Permanently blocked |

### Key Rules

- **H-001:** Identity must be declared before any capability
- **H-002:** Contract must be verified before Owner can approve
- **H-003:** Owner approval is required before capabilities activate
- **H-004:** Extension cannot self-approve or self-elevate capabilities
- **H-006:** REVOKED is terminal — a new registration is required
- **H-008:** No implicit trust — every attachment requires verification

---

## 4. Files You Need to Create

### Required

| File | Purpose | Reference |
|---|---|---|
| `docs/identity/PROJECT-IDENTITY.md` | Extension purpose, hypothesis, non-goals | [PROJECT-IDENTITY.md](docs/identity/PROJECT-IDENTITY.md) |
| `docs/contracts/YOUR-CONTRACT-v1.json` | Formal contract with Librarian | [WB-LIBRARIAN-CONTRACT-v1.json](docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json) |
| `mcp/capabilities.json` | Capability manifest | [capabilities.json](mcp/capabilities.json) |
| `mcp/permissions.json` | Permission boundaries | [permissions.json](mcp/permissions.json) |
| `src/handshake/` | Identity + lifecycle implementation | [src/handshake/](src/handshake/) |
| `src/enforcement/` | Runtime contract enforcement | [src/enforcement/](src/enforcement/) |

### Recommended

| File | Purpose |
|---|---|
| `docs/architecture/ARCHITECTURE.md` | System design and data flow |
| `docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md` | Handshake protocol specification |
| `docs/contracts/CAPABILITY-MANIFEST.md` | Capability declaration format |
| `docs/contracts/CONTRACT-BOUNDARIES.md` | Ownership and prohibited domains |
| `docs/schemas/*.schema.json` | Domain-specific JSON schemas |
| `tests/fixtures/` | Valid, invalid, boundary test fixtures |

---

## 5. Contract Structure

Your contract is a JSON document that declares identity, capabilities, ownership, forbidden operations, lifecycle, and evidence requirements.

### Minimal Contract

```json
{
  "contract_id": "your-extension-contract-v1",
  "contract_type": "connector_custody",
  "version": "1.0.0",
  "stability": "MAJOR",
  "parties": [
    { "role": "extension", "id": "your-extension-id", "domain": "your_domain" },
    { "role": "core", "id": "librarian", "domain": "governance_kernel" }
  ],
  "identity": {
    "extension_id": "your-extension-id",
    "contract_id": "your-extension-contract-v1",
    "contract_version": "1.0.0"
  },
  "capabilities": {
    "declarations": [
      {
        "capability_id": "your.read",
        "allowed_operations": ["your_get_item", "your_list_items"],
        "risk_classification": "R0"
      }
    ]
  },
  "ownership": {
    "extension_owns": { "domains": ["your_domain_items"] },
    "core_owns": { "domains": ["governance_authority", "owner_decisions"] }
  },
  "forbidden_operations": {
    "absolute": [
      { "operation": "modify_librarian_authority_state", "violation_outcome": "REVOKE" }
    ]
  },
  "lifecycle": {
    "state_machine": [
      { "state": "REGISTERED", "capabilities_active": false },
      { "state": "CONTRACT_VERIFIED", "capabilities_active": false },
      { "state": "OWNER_APPROVED", "capabilities_active": false },
      { "state": "ACTIVE", "capabilities_active": true },
      { "state": "SUSPENDED", "capabilities_active": false },
      { "state": "REVOKED", "capabilities_active": false }
    ]
  },
  "evidence": {
    "receipt_types": [
      { "type": "operation_receipt", "required_fields": ["operation", "timestamp"] }
    ]
  }
}
```

See [WB-LIBRARIAN-CONTRACT-v1.json](docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json) for a complete example.

---

## 6. Capability Declaration

Capabilities are declared in `mcp/capabilities.json` and validated against the contract during the handshake.

### Capability Fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique identifier (e.g., `your.read`) |
| `tools` | Yes | MCP tool names implementing this capability |
| `risk` | Yes | R0 (read-only) or R1 (state mutation in domain) |
| `permissions` | Yes | Scopes like `read:items`, `write:items` |
| `status` | Yes | `active` or `pending` |

### Risk Classification

| Risk | Meaning | Gate |
|---|---|---|
| R0 | Read-only, no state mutation | None |
| R1 | State mutation within your domain | Advisory — evidence logged |

### Example

```json
{
  "id": "your.read",
  "tools": ["your_get_item", "your_list_items"],
  "risk": "R0",
  "description": "Read items from your domain",
  "permissions": ["read:items"],
  "status": "active"
}
```

### Declared ≠ Available

Capabilities can be declared but marked `"status": "pending"`. This means they are contract-defined but not yet implemented. The MCP server automatically excludes pending capabilities from `tools/list`.

---

## 7. Handshake Protocol

When your extension starts, it must complete the handshake before any capabilities are available.

### Implementation Steps

```python
# 1. Announce identity
announcement = {
    "extension_id": "your-extension-id",
    "version": "0.1.0",
    "contract_id": "your-contract-v1",
    "contract_version": "1.0.0",
    "declared_at": "2026-07-21T18:00:00Z"
}

# 2. Run full handshake
result = orchestrator.execute_full_handshake(announcement)
# → REGISTERED → CONTRACT_VERIFIED

# 3. Wait for Owner approval
# (Requires external Owner action through Librarian core)

# 4. Activate after approval
approval = orchestrator.approve_and_activate(extension_id, approved_by="owner")
# → OWNER_APPROVED → ACTIVE
```

The reference implementation is in [src/handshake/](src/handshake/).

### Validation Checks

On handshake, the Librarian-side port layer validates:

| Check | What It Verifies |
|---|---|
| Identity format | extension_id, version, contract_id match expected patterns |
| Extension ID | Matches contract party |
| Contract version | Known and supported |
| Capability coverage | Every declared tool exists in your MCP `tools/list` |
| Forbidden actions | All contract forbidden operations are acknowledged |
| Risk classification | R0 or R1 only |

---

## 8. MCP Interface

Your extension exposes capabilities through a JSON-RPC 2.0 MCP server (same pattern as Librarian's MCPController.swift).

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `POST /mcp` | `tools/list` | Returns declared active tools |
| `POST /mcp` | `tools/call` | Executes a tool with permission+enforcement checks |
| `GET /health` | — | Lifecycle state and health status |

### Permission Enforcement

Every tool call passes through a four-stage gate:

```
1. Lifecycle check  → Is extension ACTIVE?
2. Capability check → Is tool declared in manifest?
3. Permission check → Does capability have required scope?
4. Enforcement     → Does operation match contract? Within boundaries? Drift-free?
```

### Tool Naming Convention

- All extension tools must use a unique prefix (e.g., `wb_` for Working Bibliography)
- Tools must not use Librarian-owned prefixes: `project_`, `librarian_`, `runtime_`, `mcp_`

The reference implementation is in [src/mcp/](src/mcp/).

---

## 9. Receipt Requirements

Every governed operation in your extension should produce a receipt. Receipts are evidence artifacts that document what happened, when, and with what identity.

### Required Receipt Types

| Receipt Type | When Produced | Key Fields |
|---|---|---|
| `registration_receipt` | Handshake step 1 | extension_id, contract_id |
| `contract_verification_receipt` | Handshake step 3 | checks passed, errors, warnings |
| `approval_receipt` | Owner approves | extension_id, approved_by |
| `activation_receipt` | Extension becomes ACTIVE | extension_id |
| `operation_receipt` | Every tool call | operation, result, timestamp |
| `drift_receipt` | Drift detected | expected, observed, classification |
| `lifecycle_receipt` | Every state transition | from_state, to_state, reason |

### Receipt Storage

Receipts are stored in the extension's local receipt store (`receipts/`). They are evidence, not authority records. They never cross into Librarian's decision chain.

---

## 10. Drift Monitoring

After activation, your extension is continuously monitored for drift. Drift is the difference between what your contract promises and what your runtime does.

### Classifications

| Classification | Meaning | Action |
|---|---|---|
| PASS | Expected matches observed | No action |
| OBSERVATION | Minor deviation, not violation | Logged, Owner notified |
| REVOKE | Contract violation confirmed | SUSPENDED or REVOKED |

### What Is Monitored

| Surface | Expected | Drift If |
|---|---|---|
| Capability list | `tools/list` matches declared capabilities | Missing or extra tools |
| Tool behavior | Response matches declared schema | Schema mismatch |
| Forbidden actions | No forbidden action attempted | Forbidden action detected |
| Artifact integrity | Content hash matches stored hash | Hash mismatch |
| Beacon | Extension responds to health check | No response |

---

## 11. Testing Requirements

Your extension must pass these tests to be considered compliant:

| Test | What It Proves |
|---|---|
| Valid capability execution → PASS | Core functionality works |
| Unknown capability request → REJECT | Boundary enforcement works |
| Forbidden operation → REVOKE | Contract enforcement works |
| Missing approval → no activation | Lifecycle enforcement works |
| Extension disconnect → Librarian healthy | Isolation works |
| Reconnect → state restored | Persistence works |

See [tests/fixtures/](tests/fixtures/) for example test fixtures.

---

## 12. Reference Implementation

The complete reference implementation is this repository — the Working Bibliography Extension.

Use it as:
- **Template:** Copy the structure for your own extension
- **Example:** See how each layer is implemented
- **Validator:** Test your extension against the same patterns
- **Contract reference:** Compare your contract against a known-compliant one

### Key Files to Study

| File | What It Teaches |
|---|---|
| `docs/identity/PROJECT-IDENTITY.md` | Identity definition |
| `docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json` | Contract structure |
| `mcp/capabilities.json` | Capability declaration |
| `src/handshake/orchestrator.py` | Handshake implementation |
| `src/mcp/server.py` | MCP server pattern |
| `src/enforcement/policy_engine.py` | Enforcement pipeline |
| `src/handshake/lifecycle.py` | 6-state lifecycle machine |

---

## 13. Summary: What to Implement

```
Required:
✓ Extension identity (PROJECT-IDENTITY.md)
✓ Contract declaration (CONTRACT-v1.json)
✓ Capability manifest (capabilities.json)
✓ Permission declaration (permissions.json)
✓ Handshake support (identity + validation + lifecycle)
✓ MCP interface (tools/list + tools/call)
✓ Receipt generation (every operation)
✓ Lifecycle handling (6-state machine)
✓ Drift response (PASS / OBSERVATION / REVOKE)
✓ Detach safety (core unaffected)

Prohibited:
✗ Librarian authority mutations
✗ Owner decision creation
✗ Sprint ledger writes
✗ Core custody records
✗ Production sealing
✗ Provenance modification
✗ Content deletion

Extensions are not granted access.
They establish a contract, declare capabilities, pass validation,
and operate within defined ownership boundaries.
```
