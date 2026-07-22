# Extension Port Model — Architecture

**Sprint:** WB-ARCHITECTURE-VISION-1
**Status:** Draft — ratified by Owner authorization
**Date:** 2026-07-21

---

## 1. What Is the Extension Port?

The extension port is not a physical port. It is the architectural boundary where external capabilities attach to the Librarian governance kernel through MCP contracts. The port is defined by:

1. **Identity** — An extension announces itself with a manifest
2. **Contract** — The extension declares capabilities and accepts constraints
3. **Lifecycle** — The extension transitions through governed states
4. **Enforcement** — The extension is monitored for drift
5. **Recovery** — The extension can be suspended or revoked without core impact

The port model turns the Librarian MCP layer from a tool invocation surface into an **extension capability system**.

---

## 2. Port Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Librarian Core                     │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │          Governance Kernel (unchanged)         │   │
│  │  - Authority state                             │   │
│  │  - Owner decisions                             │   │
│  │  - Lifecycle management                        │   │
│  │  - Custody model                               │   │
│  └──────────────────┬────────────────────────────┘   │
│                     │ MCP                             │
│  ┌──────────────────▼────────────────────────────┐   │
│  │         Project Harness MCP Surface            │   │
│  │  get_cursor / get_profile / advance_cursor    │   │
│  │  work_result_intake / project_assemble_context │   │
│  └──────────────────┬────────────────────────────┘   │
│                     │                                 │
└─────────────────────┼─────────────────────────────────┘
                      │
                      │ MCP JSON-RPC 2.0 (port 3456)
                      │
              ┌───────┴───────────────────────┐
              │      Extension Port Layer      │
              │                               │
              │  ┌─────────────────────────┐   │
              │  │  Handshake Protocol      │   │
              │  │  Identity → Contract →   │   │
              │  │  Capabilities → Approval │   │
              │  └─────────────────────────┘   │
              │  ┌─────────────────────────┐   │
              │  │  Lifecycle State Machine │   │
              │  │  REGISTERED → ACTIVE →   │   │
              │  │  → SUSPENDED → REVOKED   │   │
              │  └─────────────────────────┘   │
              │  ┌─────────────────────────┐   │
              │  │  Drift Monitor           │   │
              │  │  PASS / OBSERVATION /    │   │
              │  │  REVOKE                  │   │
              │  └─────────────────────────┘   │
              │                               │
              └───────┬───────────────────────┘
                      │
              ┌───────┴───────────────────────┐
              │      Extension Instance        │
              │  (e.g. Working Bibliography)   │
              │                               │
              │  ┌─────────────────────────┐   │
              │  │  Capability Tools        │   │
              │  │  wb_get_artifact         │   │
              │  │  wb_search_context       │   │
              │  │  wb_register_artifact    │   │
              │  └─────────────────────────┘   │
              │  ┌─────────────────────────┐   │
              │  │  Contract Enforcer       │   │
              │  │  Capabilities match      │   │
              │  │  Forbidden actions       │   │
              │  └─────────────────────────┘   │
              └───────────────────────────────┘
```

---

## 3. Extension Lifecycle State Machine

```
                   REGISTERED
                       │
                       │ Contract manifest received
                       │ Identity verified
                       ▼
                CONTRACT VERIFIED
                       │
                       │ Declared capabilities validated
                       │ Forbidden actions enumerated
                       │
                       │ ── Owner approves ──►
                       │
                       ▼
                 OWNER APPROVED
                       │
                       │ Trust granted
                       │ Capabilities unlocked
                       ▼
                     ACTIVE
                       │
              ┌────────┴────────┐
              │                 │
        Drift detected    Contract violated
              │                 │
              ▼                 ▼
         SUSPENDED          REVOKED
              │                 │
     ┌────────┴────────┐        │
     │                 │        │
  Owner clears     Owner        │
  drift            revokes      │
     │                 │        │
     ▼                 ▼        │
   ACTIVE           REVOKED ◄───┘
                       │
                  Terminal state
                  Identity preserved
                  Capabilities disabled
```

### State Definitions

| State | Meaning | Capabilities |
|---|---|---|
| **REGISTERED** | Extension discovered, identity known | None |
| **CONTRACT_VERIFIED** | Manifest validated against declared tools | None |
| **OWNER_APPROVED** | Owner explicitly authorized activation | Unlocked |
| **ACTIVE** | Full capability access | All declared |
| **SUSPENDED** | Drift detected, investigation underway | Blocked |
| **REVOKED** | Contract violation, permanent termination | Permanently blocked |

### State Transitions

| From | To | Trigger | Authority |
|---|---|---|---|
| REGISTERED | CONTRACT_VERIFIED | Contract validation passes | Automated |
| CONTRACT_VERIFIED | OWNER_APPROVED | Owner authorization | Owner |
| OWNER_APPROVED | ACTIVE | Activation signal | Automated |
| ACTIVE | SUSPENDED | Drift detected | Automated + Owner notified |
| ACTIVE | REVOKED | Contract violation | Owner |
| SUSPENDED | ACTIVE | Owner clears drift | Owner |
| SUSPENDED | REVOKED | Owner terminates | Owner |

---

## 4. Handshake Protocol

### Extension Announcement

The extension announces itself through its MCP `tools/list` response:

```json
{
  "extension": {
    "id": "working-bibliography-extension",
    "version": "0.1.0",
    "contract": "wb-librarian-contract-v1"
  },
  "capabilities": {
    "artifact": { "read": ["wb_get_artifact"], "write": ["wb_register_artifact"] },
    "knowledge": { "search": ["wb_search_context"] },
    "provenance": { "read": ["wb_get_receipt"] }
  },
  "forbidden_actions": [
    "modify_authority_state",
    "create_owner_decisions",
    "mutate_sprint_ledger"
  ]
}
```

### Contract Verification

The Librarian-side port layer validates:

1. Declared capabilities correspond to actual MCP tools on the extension
2. Forbidden actions match the ADDON-BOUNDARY-CONTRACT prohibitions
3. Extension identity is unique and not impersonating another registered extension
4. Contract version is known and supported

### Owner Approval

Owner explicitly approves the extension through the existing Owner decision mechanism. The approval binds:

- Extension identity
- Declared capabilities
- Active contract version
- Approval timestamp

### Activation

After approval, the extension's tools become available in the Librarian's MCP composite tool list. The extension is now ACTIVE.

---

## 5. Contract Structure

Extension contracts follow the existing CROSS-REPO-CONTRACT-MODEL.md conventions:

```json
{
  "contract_id": "wb-librarian-contract-v1",
  "contract_type": "connector_custody",
  "version": "1.0.0",
  "stability": "MAJOR",
  "parties": [
    { "role": "extension", "id": "working-bibliography-extension" },
    { "role": "core", "id": "librarian" }
  ],
  "promises": {
    "artifact_identity": "Every artifact has a stable, verifiable ID",
    "provenance_preservation": "Source, timestamp, and hash are always retained",
    "no_state_mutation": "Extension never writes Librarian authority state",
    "declared_capabilities_only": "Only tools in the capability list are exposed"
  },
  "forbidden_actions": [
    "modify_librarian_authority_state",
    "create_owner_decisions",
    "mutate_sprint_ledger",
    "accept_mutation_allowance",
    "seal_production_receipts"
  ],
  "enforcement": {
    "drift_monitoring": "active",
    "review_frequency": "per_operation",
    "escalation_path": "drift_detected → SUSPENDED → Owner review"
  }
}
```

---

## 6. Drift Monitoring

Drift is the difference between what an extension promises and what it does.

### Classification

| Classification | Meaning | Action |
|---|---|---|
| **PASS** | Expected behavior matches observed behavior | No action |
| **OBSERVATION** | Minor deviation detected, not yet a violation | Logged, Owner notified |
| **REVOKE** | Contract violation confirmed | SUSPENDED or REVOKED |

### Monitored Surfaces

| Surface | Expected | Monitored By |
|---|---|---|
| Capability list | `tools/list` matches declared capabilities | Port layer |
| Tool behavior | Tool response matches declared schema | Port layer |
| Forbidden actions | No forbidden action attempted | Port layer gates |
| Artifact integrity | Content hash matches stored hash | Extension self-check |
| Beacon | Extension responds to health check | Port layer |

---

## 7. Port Layer Responsibilities (Not Yet Implemented)

The extension port layer is currently an architectural concept. It will be implemented by `WB-EXTENSION-HANDSHAKE-1` and `WB-CONTRACT-ENFORCEMENT-1`. The port layer's future responsibilities:

| Responsibility | Sprint |
|---|---|
| Extension identity registry | WB-EXTENSION-HANDSHAKE-1 |
| Contract validation | WB-CONTRACT-ENFORCEMENT-1 |
| Lifecycle state machine | WB-EXTENSION-HANDSHAKE-1 |
| Drift monitoring | WB-DRIFT-DETECTION-1 |
| Access revocation | WB-ACCESS-REVOCATION-1 |
| Receipt generation | WB-CONTRACT-ENFORCEMENT-1 |

---

## 8. Integration Points with Existing Librarian Infrastructure

| Existing Artifact | Integration Point |
|---|---|
| `ADDON-BOUNDARY-CONTRACT.md` | Forbidden actions list, core-owned vs addon-owned |
| `MULTINODE-MCP-DOCUMENT-CUSTODY.md` | EXTERNAL_REFERENCE custody mode, mutation allowances |
| `DRIFT-ESCALATION-PROTOCOL.md` | 5-state escalation, PASS/OBSERVATION/REVOKE classification |
| `EPIC-AUTHORIZATION-LANE.md` | category_bounded authorization, owner_must_confirm_each |
| `LOOP-KERNEL-ADDONS.md` | Add-on lifecycle, manifest format |
| `CROSS-REPO-CONTRACT-MODEL.md` | Contract types, stability levels |
| `capability-registry.schema.json` | Capability ID naming, lifecycle |
| `GO-TO-MARKET-LIBRARIAN.png` | Existing MCP composition model |

---

## 9. Architectural Non-Goals for the Port Model

| Non-Goal | Why |
|---|---|
| Dynamic port discovery | The port is declared, not discovered |
| Autonomous extension registration | Requires identity verification |
| Capability escalation | Extensions cannot expand their own permissions |
| Hot-plug without handshake | Every attachment requires contract verification |
| Multi-tenant port sharing | Each extension gets its own lifecycle instance |
| Port load balancing | Out of scope for reference implementation |
