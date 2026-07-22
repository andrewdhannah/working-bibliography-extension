# ADR-WB-001 — The Embedding Is Not the Artifact

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

The canonical artifact is captured text with provenance. The embedding is a *derived index* — disposable and replaceable. The artifact is evidence.

## Rationale

A common RAG mistake is treating the vector database as the source of truth. This creates an untraceable dependency: if the embedding is lost, the knowledge is lost; if the embedding contains errors, there is no canonical reference to verify against.

By separating the canonical artifact (text + provenance + hash) from the derived index (embeddings + vectors), we ensure:

1. Artifact identity survives index rebuilds
2. Content integrity can be verified independently
3. The embedding layer can be replaced without custody loss
4. Search results always resolve back to a verifiable source

## Consequences

- The artifact is the source of truth. Everything else is derived.
- Embedding loss does not destroy custody records.
- Search results must include artifact identity and provenance.
- Storage requirements increase (store text + embeddings, not embeddings alone).

## Affected Components

- Artifact model (text + provenance is required; embeddings are optional)
- Capture pipeline (must store canonical representation before embedding)
- Retrieval interface (must return artifact identity with every result)
