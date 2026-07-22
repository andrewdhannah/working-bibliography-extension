# ADR-WB-006 — EXTERNAL_REFERENCE Custody Mode for WB Artifacts

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

When Working Bibliography artifacts are accessed from a Librarian context, they use the `EXTERNAL_REFERENCE` custody mode from the multinode custody model. When accessed outside a Librarian context, they use `ADVISORY_CONTEXT_ONLY`.

## Rationale

The multinode custody model defines dedicated modes for cross-context artifact access:

- **EXTERNAL_REFERENCE:** The artifact is governed by an external authority (WB), referenced by Librarian through the extension contract. Librarian does not hold custody — WB does.
- **ADVISORY_CONTEXT_ONLY:** The artifact provides advisory context to the reasoning process but does not carry Librarian custody guarantees.

This distinction prevents confusion about who holds custody in which context. Within WB, WB holds custody. Within Librarian, the artifact is a reference — not a custody object.

## Consequences

- WB artifacts in Librarian context are always references, never custody objects
- No Librarian mutation allowance for WB artifacts
- WB artifacts do not appear in Librarian custody records
- The extension contract defines the reference path

## Affected Components

- Handshake contract (declares custody mode)
- Artifact retrieval (Librarian-side reference)
- Custody documentation (references existing model)
