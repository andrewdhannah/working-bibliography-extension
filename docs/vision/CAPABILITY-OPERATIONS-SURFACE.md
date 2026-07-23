# Capability Operations Surface — Dashboard and Core Model

**Status:** Planning capture — distilled from architecture discussion (2026-07-22)
**Prerequisite:** Extension ecosystem (sealed #542–#545), Distributed platform planning
**Related:** `docs/vision/EXTENSION-ECOSYSTEM-ROADMAP.md`, `docs/vision/DISTRIBUTED-CAPABILITY-PLATFORM.md`

---

## Overview — The Next Layer

The extension ecosystem (Layer 1) is proven. The distributed platform (Layer 2) is
planned. Between them sits an architectural refinement: a canonical capability model
that unifies extensions and nodes under the same abstraction, and an operations
surface (dashboard) that visualizes the governance state without becoming a special
case.

```
                 Consumers
        (Agents, OpenWork, CLI, workflows)
                       │
                       │
              Capability Invocation
                       │
                       ▼
          ┌────────────────────────┐
          │   Librarian Core        │
          │  Governance Kernel      │
          ├────────────────────────┤
          │ Registry   Projection   │
          │ Lifecycle  Receipts     │
          │ Policy     Scheduler    │
          └────────────────────────┘
              │                │
              ▼                ▼

       Extensions             Nodes
   (knowledge providers)   (execution providers)

   WB                       GPU machine
   QA Pilot                Model runtime
   Crawler                 Embedding service
   Search                  Validation worker
```

---

## 1. CORE-CAPABILITY-MODEL-v1

A canonical definition of what a capability is, who provides it, and how it is
governed. The scheduler should not care whether a provider is an extension or a
node — it should only see governed providers that can satisfy a capability request.

### Extension Capability

```json
{
  "capability": "knowledge.search",
  "namespace": "knowledge",
  "provider": {
    "type": "extension",
    "id": "working-bibliography",
    "version": "0.1.0"
  },
  "state": "ACTIVE",
  "risk": "R0",
  "permissions": ["read:artifacts"],
  "receipts": ["approval", "validation", "health"]
}
```

### Node Capability

```json
{
  "capability": "model.inference",
  "namespace": "model",
  "provider": {
    "type": "node",
    "id": "andrew-gpu-node-01",
    "hardware": { "gpu": "RX 570" }
  },
  "state": "ACTIVE",
  "risk": "R1",
  "permissions": ["execute:model"],
  "receipts": ["approval", "validation", "health"]
}
```

### Model Fields

| Field | Description |
|-------|-------------|
| `capability` | Capability identifier (namespaced) |
| `namespace` | Capability namespace for collision resolution |
| `provider.type` | `extension` or `node` |
| `provider.id` | Unique provider identifier |
| `provider.version` | Provider version |
| `provider.hardware` | Node-specific hardware metadata (optional) |
| `state` | Current lifecycle state |
| `risk` | Risk classification (R0, R1, R2) |
| `permissions` | Granted permissions |
| `receipts` | Evidence receipts (approval, validation, health) |

### Key Invariant

The scheduler does not care that one provider is an extension and another is a node.
It only sees: "Which governed provider can satisfy this capability request?"

---

## 2. Dashboard as Governance Consumer

The dashboard does not own add-ons. It visualizes the Librarian governance state.
It is another consumer of the projection system, not another authority.

```
                 Dashboard
                     |
              MCP / Core API
                     |
        Librarian Governance Kernel
                     |
      ┌──────────────┼──────────────┐
      │              │              │
 Capability      Lifecycle      Receipts
 Projection      State          Evidence
      │
      ▼
 Extension Ecosystem
```

### Proposed Dashboard Section

```
Dashboard
├── Overview
├── Projects
├── Operations
├── Governance
├── Nodes
└── Extensions
      ├── Installed Extensions
      ├── Available Capabilities
      ├── Lifecycle State
      ├── Permissions
      ├── Receipts
      ├── Drift Status
      ├── Health
      └── Actions
```

### Example: Extension Detail View

```
Working Bibliography

Status: ACTIVE

Trust:
  Contract: VERIFIED
  Owner Approval: YES
  Last Drift Check: PASS

Capabilities:
  ✓ wb_search_context
  ✓ wb_get_artifact
  ✓ wb_register_artifact

Permissions:
  read:artifacts
  write:artifacts

Receipts:
  Last activation: 2026-07-22
  Last validation: 2026-07-22
  Last projection: 2026-07-22

Actions:
  Suspend
  Review Drift
  View Contract
```

The UI shows evidence. It does not grant itself permission.

### Future Multi-Node View

When nodes exist, the dashboard can show:

```
Capability: semantic_search

Providers:
  1. WB Node
     Confidence: 0.91
     Latency: 40ms
     State: ACTIVE

  2. Research Node
     Confidence: 0.87
     Latency: 120ms
     State: ACTIVE

Scheduler chooses.
Dashboard observes.
```

---

## 3. Add-on SDK for Dashboard — What Not To Do

### Wrong approach

```
Extension
   └── injects UI into dashboard
```

This recreates the browser-extension problem: every add-on becomes a privileged
code path that can modify the UI surface. It violates the same separation of
concerns that the capability projection enforces.

### Correct approach

The extension declares metadata. The dashboard renders generically.

```json
{
  "extension_id": "working-bibliography",
  "dashboard_surface": {
    "summary": "Knowledge custody provider",
    "metrics": [
      "artifact_count",
      "source_count",
      "drift_status"
    ]
  }
}
```

The dashboard says "I know how to display extension state." It does not say
"I know how Working Bibliography works."

This is the same principle proven by the MCP stable protocol: the core provides
primitives; participants provide data; the consumer renders according to its
own capabilities.

---

## 4. OS Architecture Analogy — Extended

| OS Concept | Librarian Equivalent |
|------------|---------------------|
| Kernel | Governance Kernel |
| Driver | Extension |
| Syscall | Capability Invocation |
| Process | Agent Session |
| Scheduler | Capability Router |
| Device Manager | Node Registry |
| Task Monitor | Dashboard |

The dashboard is closer to Activity Monitor / Task Manager than to a plugin
marketplace. It answers:

- What exists?
- What is available?
- Who owns it?
- Is it healthy?
- Why is it unavailable?

It does not answer: "How does this extension implement itself?"

---

## 5. Maturity Position

| Stage | Status |
|-------|--------|
| **Stage 1 — Extension Governance** | ✅ Proven (sealed #542–#545) |
| **Stage 2 — Consumer Awareness** | ✅ Proven (live proof phases 1–5) |
| **Stage 3 — Generic Invocation** | 🔲 Planned (`librarian_capability_execute`) |
| **Stage 4 — Node Registry** | 🔲 Planned (CORE-CAPABILITY-MODEL-v1) |
| **Stage 5 — Scheduler** | 🔲 Planned (multi-provider routing) |
| **Stage 6 — Distributed Identity** | 🔲 Planned (cryptographic node auth) |
| **Stage 7 — Operations Surface** | 🔲 Planned (dashboard visualization) |

---

## 6. Suggested Platform Epic

### EPIC-CAPABILITY-OPERATIONS-SURFACE-1

| Sprint | Scope |
|--------|-------|
| **CORE-CAPABILITY-MODEL-1** | Canonical capability identity model (extension + node unified) |
| **CAPABILITY-DASHBOARD-MODEL-1** | Projection schema consumed by dashboard UI |
| **EXTENSION-DASHBOARD-CONTRACT-1** | Optional extension metadata for dashboard rendering |
| **DASHBOARD-EXTENSION-VIEW-1** | Generic extension lifecycle display (state, caps, permissions, receipts) |
| **DASHBOARD-CAPABILITY-MAP-1** | Provider/capability relationship visualization |
| **DASHBOARD-NODE-TOPOLOGY-1** | Future distributed node topology visualization |

### Architectural Rule

New extensions should never require dashboard changes. A new extension appears
because it registers and projects state, not because someone edits SwiftUI views.

This is the same principle proven by the MCP stable protocol:
**Stable protocol, dynamic participants.**

---

## Relationship to Other Planning Documents

| Document | Focus |
|----------|-------|
| `EXTENSION-ECOSYSTEM-ROADMAP.md` | Extension-layer capabilities (knowledge archive, source trust, namespace) |
| `DISTRIBUTED-CAPABILITY-PLATFORM.md` | Distributed execution (node registry, scheduler, network trust) |
| `CONVERSATION-HISTORY-INGESTION.md` | Knowledge provenance (chat import, cross-provider continuity) |
| `CAPABILITY-OPERATIONS-SURFACE.md` | Core capability model + dashboard visualization (this document) |
