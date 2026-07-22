# ADR-WB-003 — Contract Lives in Extension Repository

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

The Working Bibliography extension contract (`WB-LIBRARIAN-CONTRACT-v1`) lives in the Working Bibliography repository as a governed artifact. The Librarian core gets a read-only capability reference to it, not a copy.

## Rationale

The contract is the extension's promise. It is authored and maintained by the extension owner as part of the extension's governance. Placing it in the extension repository:

1. Keeps the contract co-located with the implementation it governs
2. Prevents the core from becoming a registry of external contracts
3. Gives the extension owner authority over contract versioning
4. Allows the core to verify the contract without owning it

The Librarian core references the contract through the handshake protocol, where it is read and validated at registration time.

## Consequences

- The contract must be independently accessible at handshake time
- The core reads the contract; it does not store it
- Contract versioning is managed by the extension
- A contract change requires re-verification and re-approval

## Affected Components

- Handshake protocol (reads contract from extension)
- Contract enforcement (validates against live reference)
