# ADR-WB-002 — No Custom Custody Model

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

The Working Bibliography does not define its own custody model. It inherits `EXTERNAL_REFERENCE` and `ADVISORY_CONTEXT_ONLY` custody modes from the existing Librarian multinode custody model defined in `MULTINODE-MCP-DOCUMENT-CUSTODY.md`.

## Rationale

Custody is a core governance primitive. Creating a parallel custody model would violate the architectural principle that the extension operates within existing governance boundaries. The multinode model already defines:

- 10 custody modes (including EXTERNAL_REFERENCE for off-core artifacts)
- 8 mutation allowances
- 9 conflict states
- Cross-context validation rules

Working Bibliography artifacts are external to Librarian core — the `EXTERNAL_REFERENCE` mode is the correct fit. When accessed from a Librarian context, `ADVISORY_CONTEXT_ONLY` ensures the core is not affected by extension state.

## Consequences

- No new custody schema or implementation required
- Extension artifacts are governed by WB, referenced by Librarian
- No mutation allowances cross the extension boundary

## Affected Components

- Custody documentation (references existing Librarian model)
- Handshake contract (declares custody mode)
