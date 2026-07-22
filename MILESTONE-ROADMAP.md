# Working Bibliography Extension — Milestone Roadmap

**Repository:** `andrewdhannah/working-bibliography-extension`
**Status:** Milestone 1 complete, Milestone 2 in progress

---

## Milestone 1 — Extension Contract Reference ✅

**Goal:** A complete, documented extension that can be inspected and understood as a reference implementation.

### Completed

| Layer | Deliverable | Sprint |
|---|---|---|
| Identity | PROJECT-IDENTITY.md, registered in Librarian | WB-REPOSITORY-CREATION-1 |
| Architecture | ARCHITECTURE.md, EXTENSION-PORT-MODEL.md, 7 ADRs | WB-ARCHITECTURE-VISION-1 |
| Artifact Model | wb-artifact.schema.json, 18 fixtures, model invariants | WB-ARTIFACT-MODEL-1 |
| Contract | WB-LIBRARIAN-CONTRACT-v1.json, handshake, boundaries | WB-EXTENSION-CONTRACT-1 |

### Key Decisions (ADRs)

| ADR | Decision |
|---|---|
| ADR-WB-001 | The embedding is not the artifact. Canonical = text + provenance. |
| ADR-WB-002 | No custom custody model. Inherits EXTERNAL_REFERENCE from Librarian. |
| ADR-WB-003 | Contract lives in extension repo. Core gets read-only reference. |
| ADR-WB-004 | No Owner decisions from extension. Evidence only, never authority. |
| ADR-WB-005 | Extension can mutate own domain. Lifecycle managed within WB. |
| ADR-WB-006 | EXTERNAL_REFERENCE custody mode for WB artifacts in Librarian context. |
| ADR-WB-007 | Embedding capability boundary. Model is shared; store is extension-owned. |

---

## Milestone 2 — Governed Extension Runtime 🔄

**Goal:** A working MCP server with full lifecycle governance that demonstrates attach, operate, drift-detect, and detach.

### In Progress

| Sprint | Status | What It Proves |
|---|---|---|
| WB-MCP-INTERFACE-1 | ✅ | Contract becomes executable MCP surface |
| WB-EXTENSION-HANDSHAKE-1 | ✅ | Identity + lifecycle state machine |
| WB-CONTRACT-ENFORCEMENT-1 | ✅ | Runtime behavior validated against contract |
| WB-DRIFT-DETECTION-1 | ⏳ | Continuous PASS/OBSERVATION/REVOKE classification |
| WB-ACCESS-REVOCATION-1 | 🔒 | Extension isolation and controlled removal |
| WB-VALIDATION-FIXTURES-1 | 🔒 | Repeatable validation suite |

### Architecture Verified

```
Contract (WB-LIBRARIAN-CONTRACT-v1)
    ↓
Capability Declaration (mcp/capabilities.json)
    ↓
Permission Validation (mcp/permissions.json + permissions.py)
    ↓
Lifecycle Check (handshake/lifecycle.py — 6-state machine)
    ↓
Enforcement (validator + boundary + drift)
    ↓
Tool Execution (MCP tools)
    ↓
Receipt Generation (receipts/)
```

---

## Milestone 3 — Public Extension Example 🔒

**Goal:** A reusable developer guide that enables other developers to build Librarian-compatible extensions.

### Planned

| Deliverable | Purpose |
|---|---|
| EXTENSION-DEVELOPER-GUIDE.md | Step-by-step extension authoring guide |
| EXTENSION-SPECIFICATION-v1.md | Formal extension contract specification |
| minimal-extension example | Minimal working extension scaffold |
| Contract validation examples | How to verify an extension against the spec |

### Target Audience Questions

A developer should be able to read the documentation and answer:

- What is a Librarian extension?
- What does my extension own vs what does Librarian own?
- What files do I need to create?
- How do I declare capabilities?
- How does the handshake work?
- How does my extension get approved?
- How is drift detected?
- What happens if my extension fails?

---

## Relationship to Librarian Core

```
Librarian Core                    Extension Repositories
(andrewdhannah/librarian)         (andrewdhannah/working-bibliography-extension)
         │                                    │
         │ Governance kernel                   │ Reference implementation
         │ Custody model                       │ Extension model example
         │ Owner decisions                     │ Developer guide
         │ Extension validation                │ Reusable contracts
         │ Capability registry                 │ Test fixtures
         │                                    │
         └────────── Extension Contract ───────┘
```

The core validates extensions against the contract. Extensions implement the contract. This repository is the first proof that the contract is implementable.
