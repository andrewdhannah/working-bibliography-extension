# Working Bibliography Extension — Architecture Document

**Sprint:** WB-ARCHITECTURE-VISION-1
**Status:** Draft — ratified by Owner authorization
**Date:** 2026-07-21

---

## 1. System Overview

The Working Bibliography Extension is a standalone knowledge custody provider that connects to the Librarian core through the MCP extension port. It operates entirely within addon-owned space and does not depend on, modify, or extend the Librarian core.

### Canonical Statement

```
Librarian Core: governance kernel, authority state, Owner decisions, custody model
    │
MCP Extension Port: JSON-RPC 2.0, tools/list, tools/call, capability registration
    │
Working Bibliography Extension: knowledge custody, provenance, retrieval
```

### Dependency Direction

```
Librarian Core ──── no dependency ──── Working Bibliography
     │                                       │
     │  (MCP port)                 (MCP server)
     │                                       │
     └────────────── optional ───────────────┘
```

The extension requires Librarian to be present for governance integration, but the core does not require the extension.

---

## 2. Layers

```
┌─────────────────────────────────────────────────────┐
│                  Extension Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │  Identity   │  │   Contract   │  │ Lifecycle  │   │
│  │  Manifest   │  │  Enforcement │  │  State     │   │
│  └─────────────┘  └──────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────┤
│                   Knowledge Layer                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │  Capture    │  │  Normalize   │  │   Index    │   │
│  │  Pipeline   │  │  & Extract   │  │ Embeddings │   │
│  └─────────────┘  └──────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────┤
│                   Artifact Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │  Identity   │  │  Provenance  │  │ Lifecycle  │   │
│  │  (WB-ID)    │  │  (Source)    │  │ (active→)  │   │
│  └─────────────┘  └──────────────┘  └────────────┘   │
├─────────────────────────────────────────────────────┤
│                Storage Layer (Independent)            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │  Artifact   │  │  Content     │  │  Vector    │   │
│  │  Registry   │  │  Store       │  │  Index     │   │
│  │  (SQLite)   │  │  (Text)      │  │  (Derived) │   │
│  └─────────────┘  └──────────────┘  └────────────┘   │
│         │                │                │            │
│         └────────────────┼────────────────┘            │
│                     (all WB-owned)                     │
└───────────────────────────────────────────────────────┘
         │
         │ MCP (Librarian has NO direct DB access)
         │
         v
    Librarian Core
    (accesses WB artifacts only through MCP tools)
```

### Layer Responsibilities

| Layer | Responsibilities | Depends On |
|---|---|---|
| **Extension** | Identity, contract enforcement, lifecycle state, MCP surface | Artifact Layer |
| **Knowledge** | Ingestion, normalization, extraction, embedding, retrieval | Artifact Layer |
| **Artifact** | Identity, provenance, content representation, relationships | Storage Layer |
| **Storage** | Artifact registry, content storage, vector index | Local filesystem |

---

## 3. Data Flow

### Capture Path (Write)

```
Input (URL / HTML / PDF / Text / Chat Export)
    │
    v
Capture ───────────────────► Capture Receipt
    │
    v
Normalize (encoding, structure)
    │
    v
Extract (readable text, metadata)
    │
    v
Create Artifact (WB-ID, hash, source, representation)
    │
    ├──► Content Store (canonical text + representation)
    │
    └──► Artifact Registry (identity, provenance, lifecycle)
            │
            v
        Embedding (derived index — NOT canonical)
            │
            v
        Vector Store (searchable, replaceable)
```

### Retrieval Path (Read)

```
Query
    │
    v
Search (vector similarity + metadata filter)
    │
    v
Result (matching text + artifact ID + source + timestamp + hash)
    │
    ├──► Retrieval Receipt
    │
    └──► Return to caller
```

The key architectural invariant: **the retrieval path always resolves back to the canonical artifact.** The embedding is an index, not an artifact. A search result without artifact identity and provenance is an incomplete result.

---

## 4. Component Boundaries

### Working Bibliography Components

| Component | Location | Purpose |
|---|---|---|
| Artifact model | `src/model/` | Identity, provenance, content, lifecycle |
| Capture pipeline | `src/capture/` | Input normalization and artifact creation |
| Index layer | `src/index/` | Embedding and vector storage |
| Retrieval | `src/retrieval/` | Search and provenance-aware results |
| MCP server | `src/mcp/` | Extension MCP surface |
| Receipts | `src/receipts/` | Evidence generation |

### Configuration Files

| File | Purpose |
|---|---|
| `mcp/capabilities.json` | Declared capabilities for handshake |
| `mcp/permissions.json` | Read/write boundaries and access control |
| `schemas/wb-artifact.schema.json` | Artifact validation |
| `schemas/wb-contract.schema.json` | Contract validation |
| `schemas/wb-capability.schema.json` | Capability declaration validation |

---

## 5. MCP Surface

The extension exposes its capabilities through a standard MCP JSON-RPC 2.0 interface, following the same pattern established by Librarian's `MCPController.swift`.

### Capability Declaration

```json
{
  "extension_id": "working-bibliography-extension",
  "version": "0.1.0",
  "capabilities": {
    "artifact": {
      "read": ["wb_get_artifact", "wb_list_artifacts"],
      "write": ["wb_register_artifact"]
    },
    "knowledge": {
      "search": ["wb_search_context"],
      "read": ["wb_retrieve_source"]
    },
    "provenance": {
      "read": ["wb_get_receipt", "wb_get_history"]
    }
  }
}
```

### Tool Classification

Following the Librarian R0/R1 pattern:

| Tool | Risk | Gate |
|---|---|---|
| `wb_get_artifact` | R0 | None — read-only artifact access |
| `wb_list_artifacts` | R0 | None — read-only listing |
| `wb_search_context` | R0 | None — read-only search |
| `wb_retrieve_source` | R0 | None — read-only source access |
| `wb_get_receipt` | R0 | None — read-only receipt access |
| `wb_get_history` | R0 | None — read-only history |
| `wb_register_artifact` | R1 | Advisory — creates new artifact |

The read-heavy surface is intentional: the extension's primary function is knowledge preservation and retrieval. Mutation is limited to artifact registration (which produces evidence receipts).

---

## 6. Attach/Detach Architecture

### Attachment Sequence

```
1. Extension starts                 → MCP server boots
2. Extension announces identity     → tools/list includes extension tools
3. Librarian discovers extension    → REGISTERED
4. Contract verified                → CONTRACT_VERIFIED
5. Owner approves                   → OWNER_APPROVED
6. Extension capabilities active    → ACTIVE
```

### Detachment Sequence

```
1. Drift detected / Owner revokes   → SUSPENDED / REVOKED
2. Capabilities blocked             → tools/list no longer includes extension tools
3. Core health verified             → Librarian READ operation succeeds
4. Evidence preserved               → Drift/revocation receipts logged
```

### State Persistence Across Detachment

| Data | On Detach | On Reattach |
|---|---|---|
| Artifacts | Persist in WB storage | Available immediately |
| Embeddings | Persist in WB vector store | Available immediately |
| Receipts | Persist in WB receipts/ | Available immediately |
| Contract | Persist in WB docs/contracts/ | Re-verified on handshake |
| Capabilities | Persist in WB mcp/capabilities.json | Re-declared on handshake |
| Librarian state | Unaffected | Unchanged |

---

## 7. Storage Architecture

Per ADR-WB-007, Working Bibliography maintains an independent storage domain. No data is stored in Librarian core databases or vector stores.

```
working-bibliography-extension/storage/
├── working_bibliography.sqlite      ← Artifact metadata, provenance, lifecycle
├── artifacts/                        ← Canonical text content
│   ├── wb-00001/
│   │   ├── canonical.txt
│   │   └── source.html
│   └── wb-00042/
│       ├── canonical.txt
│       └── source.md
└── index/                            ← Derived vector index (replaceable)
    ├── embeddings.bin
    └── chunks.json
```

### Two Extension Relationship Types

The extension model distinguishes two patterns (per ADR-WB-007):

### 1. Capability Provider

Provides a computational service. Does not own knowledge custody.

| Attribute | Value |
|---|---|
| Example | Embedding Provider, Model Runtime |
| Owns | Model weights, inference pipeline, service state |
| Does not own | Artifacts, vectors, custody records |
| Contract | "I provide `generate_embedding(text)` → vector" |

### 2. Knowledge Custody Provider

Owns artifacts and their derived data.

| Attribute | Value |
|---|---|
| Example | Working Bibliography, Document Archive |
| Owns | Artifacts, sources, provenance, embeddings, lifecycle |
| Does not own | Shared infrastructure (models, runtimes) |
| Contract | "I provide `retrieve_context(query)` → artifact + provenance" |

### Composed Example

```
User query → WB searches own vector index
    → WB calls Embedding Provider for new content
    → WB stores vectors in own index
    → WB returns artifact_id + provenance + text
    → Librarian receives governed context
```

## 9. Relationship to Add-On Contract

The extension operates under the existing `ADDON-BOUNDARY-CONTRACT.md` from Librarian:

| Add-On Rule | Working Bibliography Compliance |
|---|---|
| Cannot modify originals | ✅ Artifacts are new, not modifications of Librarian originals |
| Cannot bypass human approval | ✅ All trust transitions require Owner action |
| Cannot mutate authority state | ✅ No ownership, decision, or sprint ledger writes |
| Cannot hide network behavior | ✅ Capabilities declared in manifest |
| Cannot delete custody records | ✅ Receipts are additive, never destructive |
| Fails closed when permissions missing | ✅ SUSPENDED/REVOKED block all capabilities |

---

## 10. Key Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| A-001 | The canonical artifact is text + provenance. Embeddings are derived. | Architecture rule — enforced at schema level |
| A-002 | Every artifact has verifiable identity and content hash. | Schema validation + hash verification |
| A-003 | No Librarian state mutation originates from this extension. | ADDON-BOUNDARY-CONTRACT — forbidden actions list |
| A-004 | Extension survival does not affect Librarian core. | Detachment test — core health check |
| A-005 | Trust is granted by Owner, not self-declared. | Lifecycle state machine — OWNER_APPROVED gate |
| A-006 | Every operation produces a receipt. | Receipt generation at every pipeline stage |
| A-007 | Unknown does not equal untrusted. | REGISTERED state without execution rights |
| A-008 | Extension maintains independent storage domain. Librarian accesses data only through MCP contracts. | ADR-WB-007 — no direct DB access |
