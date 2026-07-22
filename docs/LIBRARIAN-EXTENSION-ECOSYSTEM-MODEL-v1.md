# Librarian Extension Ecosystem Model v1

**Derived from:** Working Bibliography Extension — first reference implementation
**Date:** 2026-07-21
**Status:** Model validated through implementation

---

## 1. Roles

The ecosystem has exactly three roles:

```
Provider (Extension)
    │ declares capabilities, accepts contract terms
    ▼
Governance Kernel (Librarian)
    │ verifies contracts, projects availability, enforces boundaries
    ▼
Consumer (Agent, CLI, App, Service)
    │ discovers capabilities, reasons from projection, executes within trust
```

### Role Invariants

| Role | Owns | Does Not Own |
|---|---|---|
| **Provider** | Domain logic, artifacts, lifecycle within domain | Authority, decisions, projection |
| **Governance Kernel** | Registry, contracts, receipts, projection, enforcement | Domain logic, consumer behavior |
| **Consumer** | Its own reasoning, execution decisions | Capability availability, extension trust |

---

## 2. Trust Boundaries

### Boundary 1: Provider → Governance Kernel

```
Provider declares identity        → Kernel registers
Provider presents contract         → Kernel verifies
Provider completes handshake       → Kernel tracks lifecycle
Provider operates                  → Kernel enforces + detects drift
Provider violates contract         → Kernel suspends or revokes
```

**Rule:** The provider never asserts its own availability to consumers. All availability comes through the kernel's projection.

### Boundary 2: Governance Kernel → Consumer

```
Consumer requests projection       → Kernel returns governed state
Consumer builds context            → Consumer derives from projection
Consumer executes via MCP          → Kernel enforces at runtime
```

**Rule:** The consumer never queries providers directly for capability state. The projection is the sole source of availability truth.

### Boundary 3: Provider ↔ Consumer (No Direct Trust)

```
Provider never says "I am available" to consumer.
Consumer never asks "Are you available?" to provider.
```

Both communicate through the governance kernel.

---

## 3. Lifecycle Authority

| State | Who Can Enter | Who Can Exit | Consumer Sees |
|---|---|---|---|
| NOT_REGISTERED | — | — | Not in projection |
| REGISTERED | Automated (identity valid) | Automated (contract verified) | Extension exists, no capabilities |
| CONTRACT_VERIFIED | Automated (validation passes) | Owner (approve) | Pending approval |
| OWNER_APPROVED | Owner | Automated (activate) | Approved, not yet active |
| ACTIVE | Automated (activation) | Automated (drift) or Owner (revoke) | Capabilities available |
| SUSPENDED | Automated (drift detected) or Owner | Owner (restore or revoke) | Extensions exists, no capabilities |
| REVOKED | Owner | None (terminal) | Historical record only |

### Authority Transfer

| Event | Authority |
|---|---|
| Registration | Automated (based on valid identity) |
| Contract verification | Automated (based on validation) |
| Activation approval | **Owner only** |
| Suspension | Automated (drift detected) or Owner |
| Restoration | **Owner only** |
| Revocation | **Owner only** |

---

## 4. Capability Projection Rules

### Inclusion

| Extension State | In Projection? | Capabilities Listed? | Availability |
|---|---|---|---|
| ACTIVE | Yes | Yes (active only) | `available` |
| SUSPENDED | Yes | No | `suspended` |
| REVOKED | Yes (historical) | No | `revoked` |
| REGISTERED | Yes (info) | No | `not_approved` |
| CONTRACT_VERIFIED | Yes (info) | No | `not_approved` |
| OWNER_APPROVED | Yes (info) | No | `unavailable` |

### Staleness Detection

- Each projection has a unique `projection_id`
- `projection_id` changes when any extension transitions lifecycle state
- Consumer provides known `projection_id` to check staleness
- Server returns `status: "unchanged"` if still current

---

## 5. Receipt Chain

Every governed operation produces a receipt:

```
Operation → Receipt → Evidence
```

| Receipt Type | Produced By | Consumed By |
|---|---|---|
| registration_receipt | Provider (via handshake) | Kernel, Consumer |
| contract_verification_receipt | Provider (via handshake) | Kernel, Consumer |
| approval_receipt | Kernel (via Owner decision) | Consumer |
| activation_receipt | Provider (via lifecycle) | Kernel, Consumer |
| operation_receipt | Provider (per tool call) | Kernel, Consumer |
| lifecycle_receipt | Provider (per transition) | Kernel, Consumer |
| drift_receipt | Provider (on drift detection) | Kernel, Consumer |
| suspension_receipt | Provider (on suspension) | Kernel, Consumer |
| revocation_receipt | Provider (on revocation) | Kernel, Consumer |
| projection_receipt | Kernel (per projection request) | Consumer |

---

## 6. Dependency Direction

```
Consumer ──────> Kernel ──────> Provider
    │                │
    │ projection     │ registry, contracts, receipts
    │                │
    └── No direct ───┘
    consumer-provider trust
```

### Non-Dependencies

- Kernel does not depend on any provider
- Consumer does not depend on any specific provider
- Provider does not depend on any specific consumer
- Provider does not depend on other providers

### Optional Dependencies

- Provider may depend on Capability Providers (e.g., embedding model)
- These are declared in the manifest as optional dependencies
- The provider operates in degraded mode if a dependency is unavailable
- The dependency provider is itself a governed extension

---

## 7. Extension SDK Contract

A generated extension must:

1. Start in REGISTERED state — never skip to ACTIVE
2. Include standard forbidden operations (authority mutation, owner decisions, ledger writes)
3. Declare capabilities as `pending` — activation requires owner approval
4. Include validation fixtures for all compliance domains
5. Generate unique extension_id and contract_id
6. Enforce capability namespace isolation (tool prefixes per extension)

---

## 8. Ecosystem Proof Points

| Claim | Evidence |
|---|---|
| An extension can be independently developed and governed | Working Bibliography: 9 ADRs, full lifecycle |
| The contract is the integration point, not the code | Contract defined before implementation |
| Extensions are not trusted because they connect | 6-state lifecycle with explicit approval gate |
| Unavailable is a valid state, not a failure | Suspended/revoked: no capabilities, evidence preserved |
| Consumers can safely discover capabilities | Consumer harness: 46 tests, no invention |
| Multiple extensions compose without leaking | Composition: 50 tests, namespace isolation |
| New extensions can be created without platform knowledge | SDK generates contract-compliant scaffold |
| The governance kernel survives extension removal | Revocation test: core unaffected, receipts preserved |
