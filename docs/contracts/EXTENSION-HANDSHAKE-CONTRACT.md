# Extension Handshake Contract

**Sprint:** WB-EXTENSION-CONTRACT-1
**Status:** Ratified
**Contract:** `WB-LIBRARIAN-CONTRACT-v1`
**Date:** 2026-07-21

---

## 1. Purpose

The handshake is the protocol by which an external extension establishes identity, presents its contract, validates its capabilities, and gains Owner-approved access to the Librarian governance environment.

The handshake is not a one-time event. It is the entry point to a governed lifecycle.

---

## 2. Handshake Sequence

```
Extension                               Librarian Core

     │                                       │
     │  1. Announce identity                  │
     │  ─────────────────────────────────►    │ REGISTERED
     │                                       │
     │  2. Present contract                   │
     │  ─────────────────────────────────►    │
     │                                       │
     │  3. Validate capabilities              │
     │  ◄─────────────────────────────────    │
     │                                       │ CONTRACT_VERIFIED
     │                                       │
     │  4. Request activation                 │
     │  ─────────────────────────────────►    │
     │                                       │ (Owner review)
     │                                       │
     │  5. Owner approves                     │
     │  ◄─────────────────────────────────    │ OWNER_APPROVED
     │                                       │
     │  6. Capabilities active                │
     │  ─────────────────────────────────►    │ ACTIVE
```

### Step 1: Announce Identity

The extension announces itself through its MCP presence. The announcement must include:

| Field | Required | Description |
|---|---|---|
| `extension_id` | Yes | Unique identifier matching contract |
| `version` | Yes | Extension software version |
| `contract_id` | Yes | Contract version this extension implements |
| `declared_at` | Yes | ISO 8601 timestamp of announcement |

### Step 2: Present Contract

The extension presents its contract for verification. The contract presentation includes:

1. The contract document itself (a governed artifact in the extension repo)
2. The contract version identifier
3. The declared capability list
4. The forbidden operations list

The Librarian core reads the contract from the extension's declared source. The contract is not stored in the core — it is referenced through the handshake.

### Step 3: Validate Capabilities

The Librarian-side port layer validates:

| Check | What Is Verified |
|---|---|
| Identity match | Extension ID matches contract party |
| Capability coverage | Every declared tool in the manifest exists in the extension's `tools/list` |
| Forbidden action enumeration | All contract-forbidden operations are acknowledged |
| Contract version | Contract version is known and supported |
| Capability scope | No tool exists outside declared capabilities |

If all checks pass, the handshake advances to CONTRACT_VERIFIED.

### Step 4: Request Activation

The extension signals readiness for activation. This does not grant capabilities — it places the extension in the approval queue.

### Step 5: Owner Approves

The Owner explicitly authorizes activation through the Librarian Owner decision mechanism. The approval is bound to:

- The specific extension identity
- The specific contract version
- The approved capability set
- A timestamp

Approval is not blanket authorization. It is an explicit, recorded, reviewable decision.

### Step 6: Capabilities Active

The extension's capabilities are unlocked. The extension enters ACTIVE state.

---

## 3. Re-Handshake

A re-handshake is required when:

| Trigger | What Changes |
|---|---|
| Contract version changes | New contract must be verified and re-approved |
| Extension version changes | New capability list must be validated |
| After SUSPENDED cleared | Drift resolved, re-verification needed |
| After REVOKED (not possible — terminal) | New registration required |

---

## 4. Handshake Data Structures

### Identity Announcement

```json
{
  "extension_id": "working-bibliography-extension",
  "display_name": "Working Bibliography Extension",
  "version": "0.1.0",
  "contract_id": "wb-librarian-contract-v1",
  "contract_version": "1.0.0",
  "owner_domain": "knowledge_custody",
  "declared_at": "2026-07-21T18:00:00Z"
}
```

### Capability Declaration

```json
{
  "capabilities": [
    {
      "id": "artifact.read",
      "tools": ["wb_get_artifact", "wb_list_artifacts"],
      "risk": "R0"
    },
    {
      "id": "artifact.register",
      "tools": ["wb_register_artifact"],
      "risk": "R1"
    },
    {
      "id": "knowledge.search",
      "tools": ["wb_search_context"],
      "risk": "R0"
    },
    {
      "id": "knowledge.retrieve",
      "tools": ["wb_retrieve_source"],
      "risk": "R0"
    },
    {
      "id": "provenance.read",
      "tools": ["wb_get_receipt", "wb_get_history"],
      "risk": "R0"
    }
  ]
}
```

### Contract Presentation

```json
{
  "contract_id": "wb-librarian-contract-v1",
  "contract_type": "connector_custody",
  "version": "1.0.0",
  "stability": "MAJOR",
  "declared_forbidden_actions": [
    "modify_librarian_authority_state",
    "create_owner_decisions",
    "mutate_sprint_ledger",
    "accept_mutation_allowance",
    "seal_production_receipts",
    "delete_artifact_content",
    "modify_artifact_provenance"
  ],
  "receipt_types": [
    "capture_receipt",
    "retrieval_receipt",
    "lifecycle_receipt",
    "drift_receipt",
    "embedding_receipt"
  ]
}
```

---

## 5. Handshake Lifecycle Diagram

```
Extension MCP boots
        │
        v
Announce identity ──────────────► REGISTERED
        │                               │
        │  Identity valid?              │
        │  Contract present?            │
        │  Capabilities declared?       │
        │                               │
        ▼                               ▼
Present contract ───────────────► CONTRACT_VERIFIED
        │                               │
        │  Tools match manifest?        │
        │  Forbidden actions listed?    │
        │  Contract version known?      │
        │                               │
        ▼                               ▼
Await activation ◄────────────── OWNER_APPROVED
        │                    (Owner reviews)
        │
        │  Owner approves?
        │
        ▼
ACTIVE ───────────────────────── Capabilities unlocked
        │
        ├── Drift detected ────► SUSPENDED ──► Owner review
        │                                         │
        │                             ┌───────────┴───────────┐
        │                             │                       │
        │                             ▼                       ▼
        │                         ACTIVE (cleared)       REVOKED
        │
        └── Violation ──────────► REVOKED (terminal)
```

---

## 6. Handshake Contract Invariants

| ID | Invariant |
|---|---|
| H-001 | Identity must be declared before any capability is exercised |
| H-002 | Contract must be verified before Owner can approve |
| H-003 | Owner approval is required before capabilities activate |
| H-004 | Extension cannot self-approve or self-elevate capabilities |
| H-005 | A re-handshake is required after any contract or version change |
| H-006 | REVOKED is terminal — a new registration is required to re-attach |
| H-007 | The handshake produces a registration receipt as evidence |
| H-008 | No implicit trust — every attachment requires explicit verification |
