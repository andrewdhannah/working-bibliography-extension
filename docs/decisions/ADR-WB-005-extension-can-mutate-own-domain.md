# ADR-WB-005 — Extension Can Mutate Its Own Domain

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

The Working Bibliography extension can modify its own data within its own domain. This includes artifact lifecycle transitions (active → archived → revoked), metadata updates, and index regeneration. No mutation crosses into Librarian space.

## Rationale

The extension manages external knowledge artifacts. Those artifacts have their own lifecycle independent of Librarian state. Allowing the extension to manage its own domain:

1. Prevents Librarian from becoming a bottleneck for artifact management
2. Keeps the extension boundary clean (no write-back to core)
3. Allows the extension to implement domain-specific lifecycle rules
4. Maintains the invariant that core state is never modified by the extension

## Consequences

- Artifact lifecycle is managed by WB, not Librarian
- Core has read-only visibility into WB artifacts
- Artifact deletion (archived/revoked) is a WB decision, not a core decision
- The extension is responsible for its own data integrity

## Affected Components

- Artifact model (lifecycle field managed by WB)
- Capture pipeline (creates and transitions artifacts)
- MCP tools (read/write split for own domain)
