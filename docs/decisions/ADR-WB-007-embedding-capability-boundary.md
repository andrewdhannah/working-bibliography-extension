# ADR-WB-007 — Embedding Capability Boundary

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARTIFACT-MODEL-1 (pre-ratification clarification)
**Supersedes:** None
**Cross-ref:** ADR-WB-001 (embedding is not the artifact)

---

## Decision

Embedding generation is a shared capability that can be consumed by extensions. Generated embeddings are **derived artifacts owned by the extension that owns the source artifact**. The embedding provider does not own knowledge custody.

This means:

1. The embedding *model* can be shared infrastructure (a `Capability Provider`).
2. The embedding *store* is owned by the extension that owns the source artifact (a `Knowledge Custody Provider`).
3. Librarian core does not host, query, or store embeddings for any extension domain.
4. A future Embedding Provider Extension can offer `generate_embedding(text, model_id)` as a shared service.
5. Each Knowledge Custody Provider maintains its own vector index from the embeddings it generates.

## Rationale

### Why not share Librarian's core database?

The existing Librarian database represents **governance state**: projects, sprints, receipts, lifecycle, authority, validation. The Working Bibliography represents **knowledge custody state**: captured articles, documents, source metadata, extracted text, embeddings, research relationships.

| Librarian DB (Governance) | WB DB (Knowledge Custody) |
|---|---|
| projects | artifacts |
| sprints | sources |
| receipts (governance) | receipts (capture, retrieval) |
| lifecycle state | artifact lifecycle |
| authority, validation | provenance, embeddings |

These are different domains. Combining them creates coupling: a WB schema change would require a Librarian migration, increasing core risk. That violates the extension principle.

### Why not share the vector store?

The same boundary applies. If every extension shared a single vector store:

| Problem | Consequence |
|---|---|
| Cross-extension namespace collisions | Artifacts from different domains mix in search results |
| Single point of failure | Vector store outage affects all capabilities |
| Coupled migration | Embedding model change requires coordinated re-index across domains |
| Custody ambiguity | Who owns a vector when multiple extensions contribute? |

Each extension owns its retrieval layer because retrieval is a domain-specific function, not cross-cutting infrastructure.

### What can be shared?

The embedding model — the neural network that converts text to vectors — can be a shared infrastructure capability. It is a computational service, not a storage service. A future Embedding Provider Extension could offer:

```
embedding.generate(text, model_id) → vector[]
```

Multiple extensions call the same service, but each stores the results in its own index.

## Consequences

- Working Bibliography maintains an **independent storage domain**: its own SQLite database (artifact metadata, provenance, lifecycle), text store (canonical artifacts), and vector index (embeddings).
- Librarian accesses WB artifacts **only through governed extension contracts and MCP interfaces**. No direct database access.
- A future Embedding Provider Extension can be added as a `Capability Provider` without changing core storage.
- No vector store lives in Librarian core. Vector stores are extension-owned.
- Migration from one embedding model to another is extension-local — regenerate the extension's vector index, not a shared index.
- The embedding store is disposable. The canonical artifact (text + provenance + hash) survives index loss (per ADR-WB-001).

## Extension Relationship Types

This ADR establishes two distinct extension relationship patterns:

### 1. Capability Provider

Provides a computational service. Does not own knowledge custody.

| Attribute | Value |
|---|---|
| Example | Embedding Provider, Model Runtime |
| Owns | Model weights, inference pipeline, service state |
| Does not own | Artifacts, vectors, custody records |
| Contract | "I provide `generate_embedding(text)` → vector" |
| Trust model | Output correctness, availability, model versioning |

### 2. Knowledge Custody Provider

Owns artifacts and their derived data.

| Attribute | Value |
|---|---|
| Example | Working Bibliography, Document Archive, Chat Memory |
| Owns | Artifacts, sources, provenance, embeddings, lifecycle |
| Does not own | Shared infrastructure (models, runtimes) |
| Contract | "I provide `retrieve_context(query)` → artifact + provenance" |
| Trust model | Identity, integrity, lifecycle governance, drift detection |

### Capability Provider + Knowledge Custody Provider (Composed)

```
User asks: "Find documents about governance and summarize them"
    │
    v
Working Bibliography (Knowledge Custody Provider)
    │
    ├── generate_embedding("governance", "model-v2")  ← uses Embedding Provider
    │
    ├── search own vector index                         ← own storage
    │
    ├── retrieve matched artifacts                      ← own DB
    │
    └── return artifact_id + provenance + text
```

The Knowledge Custody Provider orchestrates the Capability Provider, but the data never leaves extension-owned storage.

## Affected Components

- Storage architecture (WB owns independent SQLite + text store + vector index)
- Extension contract types (two distinct patterns documented)
- MCP capability registry (capabilities classified by type)
- Architecture diagram (shared embedding model, per-extension vector stores)

## Unaffected

- Artifact schema (unchanged — embeddings were already derived per ADR-WB-001)
- Librarian core database (unchanged — no new tables)
- Librarian MCP controller (unchanged — new tools live in extension)
- Receipt model (unchanged — receipts are per-extension evidence)
