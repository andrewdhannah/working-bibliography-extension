# Working Bibliography Extension — Vision Document

**Sprint:** WB-ARCHITECTURE-VISION-1
**Status:** Draft — ratified by Owner authorization
**Date:** 2026-07-21

---

## 1. Why This Extension Exists

AI systems increasingly reason over external information — articles, documentation, conversation transcripts, research papers, chat exports — that lacks provenance, identity, or lifecycle management. Every planning session, design discussion, or research query produces context that is valuable beyond its immediate use, but it disappears when the session ends.

The Librarian solves this for internally generated artifacts: code changes, sprint decisions, governance receipts. It provides identity, custody, version history, and traceable usage for the outputs of AI-assisted work.

The Working Bibliography extends the same governance primitive to *what AI reads and remembers* — the inputs, not just the outputs.

### The Problem

| Today | With Working Bibliography |
|---|---|
| External context has no identity | Every captured source has a stable artifact ID |
| Provenance is lost on retrieval | Source, timestamp, and hash are preserved |
| Embeddings become the source of truth | The canonical artifact is the source; embeddings are derived indexes |
| Context disappears after session | Governed knowledge persists with lifecycle control |
| Trust is implicit | Each artifact has verifiable integrity |

### Core Insight

The hard problem is not storing information. The hard problem is maintaining a trustworthy relationship between information, decisions, and actions. The same custody model that governs AI work outputs can govern AI knowledge inputs.

---

## 2. What Working Bibliography Owns

| Domain | Ownership | Rationale |
|---|---|---|
| Captured sources | Full | Artifact creation, normalization, storage |
| Content representation | Full | Text extraction, chunking, metadata |
| Derived indexes | Full | Embeddings, search vectors, retrieval |
| Artifact lifecycle | Full | active → archived → revoked transitions |
| Search and retrieval | Full | Knowledge port implementation |
| Provenance records | Full | Capture receipts, retrieval receipts |
| Extension identity | Full | Manifest, capability declaration, handshake |
| Contract enforcement | Full | Drift detection, access control |
| Receipt generation | Full | Evidence artifacts for governance |

### What Working Bibliography Does *Not* Own

| Surface | Owner | Reason |
|---|---|---|
| Authority state | Librarian core | Cannot mutate governance records |
| Owner decisions | Librarian core | Cannot create or resolve decisions |
| Sprint ledgers | Librarian core | Cannot write sprint state |
| Custody of Librarian artifacts | Librarian core | Cannot accept mutation allowance |
| Core MCP tools | Librarian core | Cannot modify existing tool surface |
| Extension approval | Librarian core (Owner) | Trust is granted by Owner, not self-declared |

---

## 3. What Librarian Core Owns (Unchanged)

| Domain | Role |
|---|---|
| Governance authority | Ultimate source of trust |
| Lifecycle management | Project cursor, phase transitions |
| Owner decision records | Decision receipts, verification |
| Core MCP tool surface | `project_get_cursor`, `project_get_profile`, `work_result_intake`, etc. |
| Custody model | OWNER_HELD, LOCAL_CANONICAL, DELEGATED_*, EXTERNAL_REFERENCE |
| Sprint ledger | Canonical work history |
| Drift governance | Escalation protocol, resolution |
| Extension approval | REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE |

Librarian core is not modified by the existence of the extension. The core does not depend on the extension.

---

## 4. How Attachment Works

```
Extension                           Librarian Core

Announce identity ─────────────►   REGISTERED
        │                              │
        │◄──── Verify contract         │
        │                              │ CONTRACT_VERIFIED
        │                              │
        │◄──── Owner approval           │
        │                              │ OWNER_APPROVED
        │                              │
Capabilities active ──────────►   ACTIVE
```

1. **REGISTERED** — Extension announces: name, version, capabilities, contract reference. Discovery does not grant access.
2. **CONTRACT_VERIFIED** — Declared capabilities are validated against available tools. Forbidden actions are enumerated.
3. **OWNER_APPROVED** — Owner explicitly authorizes activation. Trust is granted, not assumed.
4. **ACTIVE** — Capabilities are accessible through MCP. Normal operations proceed.
5. **SUSPENDED** — Drift detected. Access temporarily removed while investigation proceeds.
6. **REVOKED** — Contract violated. Access permanently terminated. Core unaffected.

---

## 5. How Trust Is Established

Trust is not inherent. It is built through verifiable evidence at each stage:

| Stage | Evidence |
|---|---|
| Identity | Extension manifest (name, version, capability list) |
| Contract | Signed capability declaration matching tool surface |
| Integrity | Content hashing on every artifact |
| Drift | Expected vs observed behavior comparison (PASS / OBSERVATION / REVOKE) |
| Lifecycle | State transitions recorded in receipts |

### Trust Boundaries

- **Before activation:** No capabilities are accessible. The extension is registered but untrusted.
- **After activation:** Capabilities are accessible but monitored. Drift detection runs continuously.
- **After suspension:** Capabilities are blocked. Evidence is preserved for Owner review.
- **After revocation:** Identity is preserved but capabilities are permanently disabled. Core health is confirmed.

---

## 6. What Happens When Trust Fails

### Drift Scenarios

| Drift Type | Detection | Action |
|---|---|---|
| Capability mismatch | Expected tool differs from observed tool | SUSPENDED → Owner review |
| Contract violation | Forbidden action attempted | SUSPENDED → Owner review |
| Hash mismatch | Artifact content does not match stored hash | OBSERVATION → Owner notified |
| Identity change | Extension identity differs from manifest | REVOKED |
| Beacon failure | Extension stops responding | SUSPENDED → automatic retry → REVOKED |

### Failure Recovery

1. **SUSPENDED** — Capabilities blocked. Evidence logged. Owner notified.
2. **Owner reviews** evidence and decides: restore access (return to ACTIVE) or terminate (move to REVOKED).
3. **If restored:** Extension must re-handshake before capabilities are re-enabled.
4. **If revoked:** Identity remains registered but capabilities are permanently disabled. Core health is verified.

### Core Independence Invariant

Under no failure scenario does the Librarian core degrade. The extension is a capability provider, not a core dependency. This invariant is tested explicitly through intentional disconnection.

---

## 7. Evidence Model

Every operation in the extension produces a receipt:

| Operation | Receipt Type | Content |
|---|---|---|
| Artifact capture | `capture_receipt` | artifact_id, content_hash, source, timestamp |
| Knowledge retrieval | `retrieval_receipt` | query, results, artifact references, timestamp |
| Extension handshake | `registration_receipt` | identity, contract, capabilities, state |
| Drift detection | `drift_receipt` | expected behavior, observed behavior, classification |
| State transition | `lifecycle_receipt` | from_state, to_state, reason, timestamp |

Receipts are the evidence trail connecting the extension's operations to the Librarian governance model. They are not Librarian decision records — they are extension-level evidence that can be presented to the Owner for review.

---

## 8. Non-Goals (Explicit)

| Non-Goal | Rationale |
|---|---|
| Replace Librarian custody | Extends it to external knowledge, does not replace internal model |
| Create parallel governance | Uses existing Librarian governance through extension port |
| Autonomous Owner decisions | All trust transitions require Owner action |
| Memory without consent | Every artifact capture is an explicit decision |
| Multi-user collaboration | Deferred — existing multi-user docs provide model when needed |
| Cloud/edge sync | Deferred — CLOUD-EDGE-CUSTODY-ARCHITECTURE.md defines pattern |
| Real-time collaboration | Out of scope for reference implementation |
| PDF native rendering | Beyond capture scope |
| Automatic ingestion | Capture requires explicit trigger — preserves custody boundary |
| Modify Librarian core | The experiment tests whether the core can support an ecosystem unchanged |

---

## 9. Relationship to Larger Ecosystem

The Working Bibliography is the first tenant of the extension ecosystem, not the ecosystem itself.

```
                    Librarian Core
                         |
                  Governance Kernel
                         |
              MCP Extension Port Model
                         |
        +----------------+----------------+
        |                |                |
 Working Bibliography  Future Add-on    Future Add-on
 (reference impl)      Capability       Capability
```

Each tenant operates in addon-owned space, connects through contracts, and proves the core can support an ecosystem without expansion. The Working Bibliography proves the specific case of external knowledge custody. Future add-ons will prove other capability boundaries.

---

## 10. Measuring Success

The experiment succeeds when:

1. A user captures an external article through the extension.
2. The artifact has stable identity, provenance, and verifiable integrity.
3. An AI query retrieves the artifact through governed search.
4. The extension can be disconnected without affecting Librarian core.
5. The extension can be reconnected without data loss.
6. Drift is detected and classified.
7. The Owner can approve, suspend, and revoke access.

The larger experiment succeeds when:

> A capability external to Librarian can participate in Librarian governance through explicit identity, contract, capability declaration, and lifecycle control.
