# Contract Boundaries — Ownership and Prohibited Domains

**Sprint:** WB-EXTENSION-CONTRACT-1
**Status:** Ratified
**Contract:** `WB-LIBRARIAN-CONTRACT-v1`
**Date:** 2026-07-21

---

## 1. Purpose

This document defines the explicit ownership boundaries between Working Bibliography and Librarian core. A clear boundary is the most important prerequisite for trust in an extension relationship.

---

## 2. Working Bibliography Ownership

Working Bibliography owns everything within its storage domain:

| Domain | What It Includes | Invariant |
|---|---|---|
| **Knowledge Artifact Identity** | Artifact IDs (`WB-XXXXX`), content hashes, spec versions | Immutable after creation |
| **Knowledge Artifact Provenance** | Source metadata (url, title, author, publisher, retrieved_at) | Immutable after creation |
| **Knowledge Artifact Content** | Canonical text, source representation, chunks | Content preserved; lifecycle governs access |
| **Knowledge Artifact Lifecycle** | Lifecycle state, transitions, transition reasons | Managed within WB; never crosses to core |
| **Derived Retrieval Indexes** | Embeddings, chunks, search vectors | Extension-owned; disposable |
| **Evidence Receipts** | Capture, retrieval, lifecycle, drift, embedding receipts | Evidence only; no authority |
| **Extension Identity** | Manifest, declared capabilities, contract reference | Self-declared; verified by core |
| **Storage Infrastructure** | SQLite DB, text store, vector index | Independent from core storage |

### What WB Can Do Without External Authorization

- Create artifacts from captured sources
- Transition artifact lifecycle within own domain (active → archived → revoked)
- Generate and regenerate derived indexes from canonical content
- Create evidence receipts for every operation
- Declare its own capabilities and forbidden actions
- Operate independently of Librarian core (no core dependency)

---

## 3. Librarian Core Ownership

Librarian core owns everything in the governance domain:

| Domain | What It Includes | Invariant |
|---|---|---|
| **Governance Authority** | Authority state, delegation matrix, enforcement rules | Never delegated to extension |
| **Owner Decisions** | Decision records, approval receipts, verification receipts | No extension originates decisions |
| **Project Lifecycle** | Lifecycle cursor, phase transitions, branch states | Managed by core only |
| **Sprint Ledger** | Sprint records, work items, work packet state | Core-controlled record |
| **Core MCP Tools** | project_get_cursor, project_get_profile, work_result_intake, etc. | Not modified by extension |
| **Core Custody Records** | Custody events, mutation allowances, conflict states | Extension uses EXTERNAL_REFERENCE only |
| **Extension Approval** | Registration decisions, contract verification, activation approval | Owner authority only |

---

## 4. Extension Relationship Types

### Knowledge Custody Provider (Working Bibliography)

```
Role: Owns artifacts, provenance, and retrieval indexes
Contract: Connector custody
Example: Working Bibliography, Document Archive
```

### Capability Provider (Future)

```
Role: Provides computational service
Contract: Service capability
Example: Embedding Provider, Model Runtime, Summarizer
```

### Shared Infrastructure

```
Role: Available to any extension
Contract: None (capability consumed through provider)
Example: Embedding model inference
```

---

## 5. Prohibited Domain Crossings

### Absolute Prohibitions (Violation → REVOKED)

| Crossing | Why | Detection |
|---|---|---|
| Extension writes to Librarian authority state | Authority is core-only domain | Write access blocked at storage layer |
| Extension creates or resolves Owner decisions | Decisions require Owner authority | No decision MCP tools exposed |
| Extension mutates sprint ledger | Ledger is core-controlled record | Write access blocked at storage layer |
| Extension accepts core mutation allowance | Extension uses EXTERNAL_REFERENCE only | Custody mode mismatch detected |
| Extension seals production receipts | Sealing is authority act | No seal capability declared |
| Extension impersonates another registered identity | Identity integrity violation | Identity verification at handshake |

### Suspension-Level Prohibitions (Violation → SUSPENDED)

| Crossing | Why | Detection |
|---|---|---|
| Extension deletes artifact content | Content must persist for audit | Lifecycle enforcement |
| Extension modifies artifact provenance after creation | Provenance is immutable | Hash verification |
| Extension expands capabilities without re-handshake | Static declaration required | Capability list drift detection |

---

## 6. Boundary Diagram

```
┌─────────────────────────────────────────────────────────┐
│                 WORKING BIBLIOGRAPHY                      │
│                                                           │
│  ┌─────────────────┐  ┌──────────────────────────────┐   │
│  │  Owned Domain   │  │  External References          │   │
│  │                  │  │                               │   │
│  │  • Artifacts    │  │  • Embedding capability       │   │
│  │  • Provenance   │  │    (optional, via Capability  │   │
│  │  • Content      │  │     Provider)                  │   │
│  │  • Lifecycle    │  │                               │   │
│  │  • Indexes      │  │  • Librarian governance       │   │
│  │  • Receipts     │  │    (via MCP extension port)    │   │
│  │  • Identity     │  │                               │   │
│  └─────────────────┘  └──────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Forbidden Zone                                    │    │
│  │  ⛔ Authority state  ⛔ Owner decisions            │    │
│  │  ⛔ Sprint ledger    ⛔ Core custody               │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            │
                            │ MCP Contract Boundary
                            │
┌─────────────────────────────────────────────────────────┐
│                   LIBRARIAN CORE                          │
│                                                           │
│  ┌─────────────────┐  ┌──────────────────────────────┐   │
│  │  Owned Domain   │  │  Extension References         │   │
│  │                  │  │                               │   │
│  │  • Authority    │  │  • Registered extensions      │   │
│  │  • Decisions    │  │  • Extension capabilities     │   │
│  │  • Lifecycle    │  │    (read-only reference)      │   │
│  │  • Sprint       │  │                               │   │
│  │  • Custody      │  │  • Extension contract         │   │
│  │  • Tools        │  │    (read-only reference)      │   │
│  └─────────────────┘  └──────────────────────────────┘   │
│                                                           │
│  ⚠️ Core never depends on extension                       │
│  ⚠️ Core never stores extension data                      │
│  ⚠️ Core never delegates authority to extension           │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Evidence and Audit Boundaries

| Evidence Type | Owned By | Governed By |
|---|---|---|
| Capture receipts | Working Bibliography | WB contract |
| Retrieval receipts | Working Bibliography | WB contract |
| Lifecycle receipts | Working Bibliography | WB contract |
| Drift receipts | Working Bibliography | WB contract |
| Embedding receipts | Working Bibliography | WB contract |
| Registration receipt | Working Bibliography + Librarian | Joint — handshake record |
| Owner approval receipt | Librarian core | Core — decision record |
| Verification receipt | Librarian core | Core — verification record |

---

## 8. Cross-Domain Reference Rules

| Rule | Description |
|---|---|
| CR-001 | A WB artifact cannot reference a Librarian artifact by artifact_id |
| CR-002 | A Librarian decision cannot reference a WB artifact as authority evidence |
| CR-003 | WB receipts are evidence, not decisions — never placed in core decision chain |
| CR-004 | Core Owner decisions about extension state reference extension_id, not internal WB data |
| CR-005 | WB artifacts used in Librarian context use EXTERNAL_REFERENCE custody mode |
| CR-006 | No cross-domain foreign key constraints — each domain manages its own identifiers |

---

## 9. Incident Response Boundaries

| Incident | WB Action | Core Action |
|---|---|---|
| Extension crash | Self-recovery, state preserved | No action — core unaffected |
| Core crash | Wait for re-handshake | Recovery then re-verify extensions |
| Drift detected | Produce drift receipt, self-suspend | Owner notified, decision expected |
| Contract violation | Cease capability execution | REVOKE state, evidence preserved |
| Embedding model change | Regenerate index, update receipts | No action — extension-owned index |
| Data integrity failure | Produce evidence, request recovery | No action — extension-owned data |
