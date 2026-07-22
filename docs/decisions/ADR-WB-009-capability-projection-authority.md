# ADR-WB-009 — Capability Projection Authority

**Status:** Accepted
**Date:** 2026-07-21
**Context:** EPIC-CONSUMER-EXTENSION-AWARENESS-1, pre-sprint WB-CONSUMER-CAPABILITY-DISCOVERY-1
**Supersedes:** None
**Cross-ref:** ADR-WB-008, EXTENSION-SPECIFICATION-v1.md §3, CAPABILITY-PROJECTION-CONTRACT.md

---

## Decision

Librarian is the sole authority for capability projection. Extensions declare capabilities. Consumers request projections. **Neither extensions nor consumers may define availability state independently.**

## Rationale

### Prevents Extension Self-Attestation

Without this ADR, a consumer could ask an extension directly:

```
Consumer asks Extension:
  "Are you available?"
Extension:
  "Yes, trust me."
```

This bypasses the governance layer entirely. The extension could claim ACTIVE state when it is actually SUSPENDED or REVOKED.

### Prevents Consumer Assumption

Without this ADR, a consumer could assume:

```
"I could call this capability yesterday, so I can call it today."
```

This bypasses lifecycle enforcement. A SUSPENDED extension should not be callable even if it was ACTIVE moments before.

### Correct Flow

```
Consumer asks Librarian:
  "What capabilities are currently approved?"

Librarian responds:
  Extension X:
    registered:        ✅
    contract verified: ✅
    owner approved:    ✅
    active:            ❌ (suspended due to drift)

Consumer reasons from projection.
Consumer does not query extension directly.
```

### Three-Rule Authority Chain

| Rule | Description |
|---|---|
| **Extensions declare** | Extensions declare capabilities in their manifest and contract. This is a promise, not proof of availability. |
| **Librarian projects** | Librarian determines actual availability based on lifecycle state, contract verification, and enforcement status. |
| **Consumers consume** | Consumers receive the projection and reason from it. They may not bypass Librarian to query extensions directly for availability. |

## Consequences

- `librarian_capability_projection()` is the sole MCP tool for capability discovery. Extensions do not expose their own `is_available()` or `status()` tools for consumer-side capability checks.
- Extensions may expose health/status endpoints for operational purposes (monitoring, debugging), but consumers must not use these for capability authorization.
- The projection is a governance artifact. It carries `authority: "librarian-core"` and a `projection_id` for staleness detection.
- Consumers that bypass the projection (querying extensions directly for availability) are non-compliant with the consumer contract.
- This ADR completes the ecosystem boundary: extension contract (provider side) + consumer contract (requester side) + projection authority (governance side).

## Affected Components

- `librarian_capability_projection()` MCP tool (authority source)
- Consumer capability context (reads projection, never queries extensions directly)
- Extension MCP surface (no `is_available` or `capability_status` tools for consumers)
- Capability projection contract (CP-001 through CP-009)

## Unaffected

- Extension health/status endpoints for operational monitoring
- Extension self-governance (handshake, enforcement, drift, revocation)
- ADR-WB-001 through ADR-WB-008
- Working Bibliography artifact model and storage
