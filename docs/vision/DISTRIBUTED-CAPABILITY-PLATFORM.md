# Distributed Capability Platform — Architectural Planning

**Status:** Planning capture — distilled from architecture discussion (2026-07-22)
**Prerequisite:** EPIC-LIBRARIAN-CAPABILITY-PROJECTION-INTEGRATION-1 (sealed #542–#545)
**Serves:** Both `working-bibliography-extension` and `librarian` core
**See also:** `docs/vision/EXTENSION-ECOSYSTEM-ROADMAP.md` (extension-layer roadmap)

---

## Overview — Three-Layer Architecture

The conversation revealed that the governance model proven for extensions extends naturally
to distributed execution. The resulting architecture has three distinct layers:

```
                 Consumers (agents, CLIs, OpenWork, workflows)
                            │
                            │ librarian_capability_projection()
                            │ librarian_capability_execute()
                            ▼
                  Governance Kernel
          (authoritative state, contracts, lifecycle, 
           receipts, projections, scheduling policy)
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    Capability Providers    │       Capability Providers
      (Extensions)          │         (Runtime Nodes)
            │               │               │
 Working Bibliography    GPU Workstation   Cloud VM
 QA Pilot               Laptop            Remote Model
 Web Crawler            Office Server     Raspberry Pi
```

**Key insight:** Extensions and runtime nodes are peers from the kernel's perspective.
Both are governed capability providers with different implementations behind the same
execution contract. The same governance model — identity, lifecycle, contracts,
capability projection, drift detection, suspension — applies to both.

---

## 1. The Distributed Governance Model

### Extensions vs Nodes

| | Extension | Runtime Node |
|---|---|---|
| **Provides** | Business capabilities | Execution resources |
| **Examples** | Bibliography, QA Pilot, Crawler | GPU workstation, laptop, cloud VM |
| **Capabilities** | `knowledge.search`, `document.extract` | `model.inference`, `embedding.generate` |
| **Lifecycle** | Same 6-state machine | Same 6-state machine |
| **Governance** | Contract + handshake + projection | Contract + handshake + projection |

### OS Architecture Analogy

| Operating System | Librarian |
|-----------------|-----------|
| Kernel | Governance Kernel |
| Driver | Extension / Node |
| Device registration | Capability registration |
| Scheduler | Capability scheduler |
| Syscall | `librarian_capability_execute` |
| Process | Consumer (agent, CLI, workflow) |
| Hardware | Runtime nodes (GPUs, local compute, remote) |

### Why This Scales

Everything looks like:

```
identity
lifecycle
capabilities
health
projection
```

Whether it is a bibliography, a GPU node, a crawler, a QA system, or a model runtime,
the governance kernel interacts with the same concepts. The implementation behind the
endpoint is different, but the governance model is the same.

---

## 2. The Stable Invocation Architecture

### Current State

Capability projection is implemented. Extensions expose their own MCP servers.
Consumers discover capabilities through Librarian. But consumers currently call
extension endpoints directly after discovery.

### Future Direction — Generic Invocation Bridge

Introduce `librarian_capability_execute` as a core primitive:

```json
{
  "capability": "knowledge.search",
  "provider": "working-bibliography",    // optional — scheduler can choose
  "arguments": {
    "query": "SQLite WAL architecture"
  },
  "execution_policy": {
    "prefer": "local",
    "timeout_ms": 30000
  }
}
```

Responsibilities:

1. Resolve capability to provider(s) via capability registry
2. Verify lifecycle state is ACTIVE
3. Verify permissions and contract compliance
4. Schedule execution (select provider if multiple eligible)
5. Route request to selected provider
6. Record execution receipt
7. Return result to consumer

### Invariant

Extensions add capabilities. They do not add Core MCP methods.

The Core owns:
- registration
- projection
- lifecycle
- authorization
- execution routing

The extension/node owns:
- capability implementation

### Protocol Flow

```
Consumer                    Governance Kernel                Capability Provider
    │                              │                              │
    │  librarian_capability_execute│                              │
    │ ──────────────────────────►  │                              │
    │                              │  resolve provider            │
    │                              │  verify lifecycle            │
    │                              │  verify permissions          │
    │                              │  schedule (select node)      │
    │                              │                              │
    │                              │  JSON-RPC call               │
    │                              │ ──────────────────────────►  │
    │                              │                              │
    │                              │  ◄────────────────────────── │
    │                              │  result + receipt            │
    │                              │                              │
    │  ◄────────────────────────── │                              │
    │  result + receipt            │                              │
```

---

## 3. Node Registry

Nodes become governed entities with the same lifecycle extensions use.

### Node Metadata

```json
{
  "node_id": "node-andrew-office-gpu",
  "owner": "andrew",
  "display_name": "Office GPU Workstation",
  "endpoint": "https://office.example.com:8765/mcp",
  "public_key": "ssh-ed25519 AAA...",
  "capabilities": [
    "embedding.generate",
    "model.inference",
    "vision.caption"
  ],
  "lifecycle": "ACTIVE",
  "registered_at": "2026-07-22T08:00:00Z",
  "health": {
    "status": "healthy",
    "last_seen": "2026-07-22T08:05:00Z",
    "latency_ms": 18
  }
}
```

### Node Lifecycle States

```
REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE
                                                  → DEGRADED → OFFLINE
                                                  → SUSPENDED → REVOKED
```

| State | Meaning |
|-------|---------|
| REGISTERED | Identity established, not yet validated |
| CONTRACT_VERIFIED | Contract and capabilities validated |
| OWNER_APPROVED | Owner explicitly authorized |
| ACTIVE | Full capability access |
| DEGRADED | Health concerns detected, capabilities limited |
| OFFLINE | Not reachable, state preserved |
| SUSPENDED | Drift or policy violation |
| REVOKED | Terminal — identity preserved, capabilities disabled |

### Health Monitoring as Evidence

Health checks produce receipts, not just status pings:

```json
{
  "receipt_type": "node_health_receipt",
  "node_id": "node-andrew-office-gpu",
  "status": "healthy",
  "latency_ms": 18,
  "observed_at": "2026-07-22T08:05:00Z",
  "capabilities_verified": ["embedding.generate", "model.inference"]
}
```

---

## 4. Scheduler Service

The scheduler selects which provider executes a capability request.

### Selection Policy

```
Capability Request: embedding.generate

Available Providers:
  Node A (office GPU)     latency: 18ms   confidence: high    local
  Node B (cloud VM)       latency: 42ms   confidence: high    remote
  Node C (laptop)         suspended       confidence: medium  local

Scheduler selects: Node A
```

### Policy Dimensions

| Policy | Behavior |
|--------|----------|
| **Latency-first** | Lowest measured latency wins |
| **Confidence-first** | Highest provider confidence wins |
| **Owner-preferred** | Explicit owner affinity |
| **Cost-aware** | Prefer local/owned resources over paid |
| **Local-first** | Prefer same-network providers |
| **Quorum** | Execute on multiple, compare results |

### Multi-Provider Resolution

When two providers implement the same shared capability:

```
research.search
  Provider A (WB)       confidence: 0.94
  Provider B (Academic) confidence: 0.88
```

The scheduler may:
- Select highest confidence
- Route to both and compare
- Fail over if primary unavailable

---

## 5. Network Trust Model

### Three Layers

```
1. Governance Protocol ─── largely solved
   Identity, registration, contracts, handshake, lifecycle,
   projection, receipts, authority, suspension/revocation.
   Location-independent — same concepts apply locally or remotely.

2. Transport ─── mostly solved
   MCP (JSON-RPC over HTTP/HTTPS). A node is just another network
   endpoint. The messages are the same, handshake is the same,
   capability projection is the same.

3. Trust and Discovery ─── needs design
   How does the core discover nodes?
   Which nodes are allowed?
   How are identities verified? (cryptographic key pairs)
   How are keys rotated?
   How do nodes reconnect after failure?
   How is network partition handled?
   How are duplicate registrations prevented?
   What happens when an endpoint changes?
```

### Endpoint Migration as Lifecycle Event

If a node's endpoint changes:

```
office.example.com → office2.example.com
```

This is a lifecycle event, not just a URL edit. The node must:
1. Prove identity (sign request with private key)
2. Provide evidence of previous registration
3. Request endpoint update
4. Receive updated registration receipt

### Multi-User Ownership

```
Andrew
 ├── Office Node
 ├── Laptop Node
 └── GPU Server

Sarah
 ├── Workstation
 └── QA Node

Team
 └── Shared Validation Cluster
```

Every node registers identically. Ownership determines:
- Visibility (who can see which nodes)
- Permissions (who can schedule work on which nodes)
- Scheduling eligibility (owner-affinity policies)
- Policy application

---

## 6. Knowledge Archive Evolution

### Source Trust Timeline

A source becomes a governed entity with history:

```json
{
  "source_id": "arxiv.org",
  "trust_status": "approved",
  "first_captured": "2026-01-15",
  "total_captures": 1200,
  "change_history": "stable",
  "owner_policy": "allowed",
  "last_verified": "2026-07-22"
}
```

Versus:

```json
{
  "source_id": "unknown-blog.com",
  "trust_status": "conditional",
  "first_captured": "2026-07-22",
  "total_captures": 1,
  "change_history": "new",
  "owner_policy": "review_required"
}
```

### Snapshot Timeline (Lightweight Wayback)

Instead of duplicate full archives:

```
example.com/doc.html
    2026-01-01   SHA256: abc123   (current at time)
    2026-03-14   SHA256: def456   (changed)
    2026-05-22   SHA256: abc123   (unchanged, reference-only)
```

### Evidence-Backed Validation

| Tier | Meaning | Consensus Required |
|------|---------|-------------------|
| **A** | Single trusted source | One authoritative provider |
| **B** | Agreement between two sources | Two independent captures match |
| **C** | Majority across multiple sources | 3+ independent sources agree |

Disagreement between sources produces a drift observation rather than silent acceptance.

---

## 7. Suggested Platform Epics

### Core Infrastructure

| Epic | Description |
|------|-------------|
| **EPIC-CAPABILITY-EXECUTION-BRIDGE-1** | `librarian_capability_execute` primitive — generic invocation, provider resolution, lifecycle verification, receipt generation |
| **EPIC-CAPABILITY-SCHEDULER-1** | Multi-provider scheduling — selection policies, latency awareness, confidence routing, failover |
| **EPIC-NODE-REGISTRY-1** | Node as governed entity — identity, metadata, lifecycle, health monitoring |
| **EPIC-DISTRIBUTED-NODE-GOVERNANCE-1** | Node lifecycle (DEGRADED, OFFLINE), health-as-evidence, reconnection protocol |
| **EPIC-MULTI-PROVIDER-ROUTING-1** | Capability namespace resolution, collision policy, shared capability scheduling |
| **EPIC-DISTRIBUTED-TRUST-INFRASTRUCTURE-1** | Node authentication (cryptographic), secure transport (TLS/mTLS), key rotation, network partition handling |
| **EPIC-MULTI-USER-OWNERSHIP-1** | Per-user node ownership, visibility scoping, affinity scheduling, cross-user resource sharing |

### Extension SDK / Node SDK

| Epic | Description |
|------|-------------|
| **EPIC-EXTENSION-SDK-EVOLUTION-1** | Additional templates: crawler, scheduler, health, test harness |
| **EPIC-NODE-SDK-1** | Separate SDK for runtime nodes: identity registration, heartbeat, capability advertisement, execution adapter, receipt generation |

### Knowledge Archive

| Epic | Description |
|------|-------------|
| **EPIC-KNOWLEDGE-ARCHIVE-1** | Snapshot history, change-aware crawling, deduplication, delta storage, retention policies, storage quotas |
| **EPIC-SOURCE-TRUST-1** | Source identity records, trust history, A/B/C validation tiers, source policy engine (approved/conditional/blocked) |
| **EPIC-CRAWL-GOVERNANCE-1** | Crawler policies, rate limits, scheduling, robots compliance, evidence receipts |

---

## 8. Key Architectural Invariants

| Invariant | Rationale |
|-----------|-----------|
| The MCP surface stops growing horizontally | New extensions never require MCPController.swift changes |
| Capabilities are discovered through projection, not hardcoded | Extensions register; the kernel projects; consumers discover |
| Providers and consumers never negotiate trust directly | ADR-WB-009: the consumer is not part of the trust chain |
| Nodes follow the same governance model as extensions | Identity, lifecycle, contracts, projection, drift — same model |
| Transport is an implementation detail | The kernel does not care whether a node is local or remote as long as identity is provable |
| An unavailable provider is removed from consumer context | Capability Absence Invariant: agent does not call what is not projected |
| Storage limits are Owner decisions | Extensions cannot silently become infinite archives |
| Every operation produces a receipt | Evidence chain for audit, drift detection, and trust history |

---

## 9. OS Architecture Summary

```
Applications
    │
Consumers (agents, OpenWork, CLI, workflows)
    │
Capability Execute (librarian_capability_execute)
    │
Scheduler (policy-based provider selection)
    │
Capability Registry (projection + lifecycle + contracts)
    │
Extensions + Nodes (governed capability providers)
```

Equivalent to:

```
Application
System Call
Kernel
Scheduler
Drivers
Hardware
```

This analogy should appear in platform architecture documentation because it succinctly
explains the separation of concerns. The kernel does not know how every device works
internally. A driver registers what it can do. The scheduler decides which resource
runs work. Applications request services through stable interfaces.

---

## 10. Relationship to Existing Roadmap

This document extends `EXTENSION-ECOSYSTEM-ROADMAP.md` (sections 1–6) with the distributed
execution layer. The combined model:

```
Layer 1: Extension Ecosystem (sealed #542–#545, roadmap sections 1–6)
  - Knowledge archive, source trust, MCP stable protocol,
    multi-node scheduling, repeatable extension flow,
    capability namespace

Layer 2: Distributed Platform (this document)
  - Node registry, invocation bridge, scheduler service,
    network trust model, multi-user ownership,
    node SDK, evidence-backed validation
```

The first layer is proven and operational. The second layer is the next architectural
frontier — turning the governance kernel from a single-machine extension host into a
distributed capability operating system.
