# ADR-WB-004 — No Owner Decisions from Extension

**Status:** Accepted
**Date:** 2026-07-21
**Context:** WB-ARCHITECTURE-VISION-1

---

## Decision

The Working Bibliography extension never originates Librarian Owner decisions. Owner decisions are a core governance mechanism and remain exclusively under core authority.

## Rationale

Owner decisions are the highest authority surface in the Librarian governance model. Allowing an extension to originate them would violate the extension boundary: the extension would be creating governance state in the core. The ADDON-BOUNDARY-CONTRACT.md explicitly forbids this.

The extension's role is to produce evidence (receipts) that the Owner can use to make decisions — not to make decisions on the Owner's behalf.

## Consequences

- WB receipts are evidence, not decisions
- All trust transitions (approve, suspend, revoke) require Owner action through core
- Owner reviews WB drift evidence through core tools
- No decision authority leaks into extension space

## Affected Components

- Receipt model (evidence only, not decisions)
- Drift governance (detection produces evidence; Owner decides action)
- Handshake lifecycle (OWNER_APPROVED gate requires core action)
