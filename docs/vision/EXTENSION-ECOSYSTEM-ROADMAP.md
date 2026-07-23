# Extension Ecosystem Roadmap — Beyond the Reference Implementation

**Status:** Planning capture — distilled from operational proof sessions (2026-07-22)
**Sealed sprints:** #542–#545 (EPIC-LIBRARIAN-CAPABILITY-PROJECTION-INTEGRATION-1)
**Serves:** Both `working-bibliography-extension` and `librarian` core

---

## What the Reference Implementation Proved

The WB extension demonstrated a complete governed capability loop:

```
External Sources
    ↓
Governed Ingestion
    ↓
Canonical Artifact + Provenance (SHA-256, source URL, capture timestamp)
    ↓
Capability Projection       ← Librarian governance kernel decides availability
    ↓
Consumer Context            ← agent sees only available capabilities
    ↓
Agent Reasoning             ← answers grounded in governed sources, not model memory
    ↓
Evidence-backed Output
    ↓
Lifecycle Governance        ← drift detection, suspension, Owner recovery
```

Evidence: 20/20 operational proof checks (Phase 1–5), 22/22 live consumer proof checks.
Key invariant: the agent only knows a capability is available because the Librarian projection says so.

---

## What Comes Next: Turning the Extension Into a Platform

The reference implementation proved the architecture works. The next set of capabilities turns the
bibliography add-on from a single-purpose tool into a governed knowledge archive system. None of
these require changing the Librarian MCP core — they are new extensions or new capabilities on
existing extensions, discovered through the capability projection.

---

## 1. Knowledge Archive System (WB-ARCHIVE-GOVERNANCE-1)

### Content-Addressed Snapshots

The basic artifact model already supports identity via content hash, source URL, timestamp, and
provenance receipt. Extend it into a versioned snapshot system:

```
Source:
    sqlite.org/wal.html

Snapshots:
    2026-07-22   SHA256: abc123   Version: current
    2026-05-10   SHA256: def456   Version: previous
    2025-12-01   SHA256: ghi789   Version: archived
```

Deduplication rule:

```
If URL = same AND SHA256 = same:
    reference existing artifact
    update observation timestamp
    do NOT store another copy
```

### Retention Policies

Each extension declares an archive policy in its capability manifest:

```json
{
  "archive_policy": {
    "max_storage_mb": 5000,
    "snapshot_policy": "adaptive",
    "retain_versions": 10
  }
}
```

Policy modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Minimal** | Current snapshot + receipt history only | Documentation |
| **Research** | Current + all changed snapshots + monthly checkpoints | Scientific / technical research |
| **Audit** | Immutable — every captured state forever | Standards, compliance, legal evidence |

### Change-Aware Crawling

Do not crawl everything at the same frequency:

| Source Classification | Crawl Frequency |
|----------------------|-----------------|
| NIST standards | Weekly |
| SQLite docs | Monthly |
| Technical blog | Quarterly |
| Forum post | Capture once |

Guard: before storing, ask "Has this source changed enough to justify another snapshot?"

### Snapshot Compression Model

```
Artifact
 ├── Canonical current content (full)
 ├── Snapshot index
 └── Historical deltas
```

Example:

```
sqlite.html: 100 KB current
    Jan:     +2 KB change
    Feb:     +4 KB change
    Mar:     unchanged (reference only)
```

### Storage Limits as Governance Rules

When an archive limit is reached, the system should not silently delete. It should create an
Owner decision:

```
Archive limit reached: 5 GB maximum
Action required: Choose retention policy
  1. Remove unchanged snapshots
  2. Compress historical versions
  3. Archive externally
  4. Increase quota
```

### New Capabilities for WB-ARCHIVE-GOVERNANCE-1

```
wb_capture_snapshot
wb_compare_snapshot
wb_list_source_history
wb_apply_retention_policy
wb_verify_source_integrity
```

---

## 2. Source Trust Timeline

A source becomes more than URL → document. It becomes:

```
Source Identity
 ├── Snapshot timeline
 ├── Trust history
 └── Usage history
```

Example:

```
Source: example.com/security-paper
2025-01    Trust: Approved
2025-06    Domain changed ownership
2025-07    Librarian drift detected
2025-07    Source suspended
```

The agent can then know: "This source was trusted when captured, but its current state has changed."

### A/B/C Source Validation

For research contexts, sources can be classified:

| Tier | Meaning | Examples |
|------|---------|---------|
| **A** | Approved evidence | NVIDIA technical papers, llama.cpp docs, academic papers |
| **B** | Useful, requires comparison | Engineering blogs, benchmarks |
| **C** | Discovery only | Forum discussions, social posts |

The agent reasons differently per tier:

```
Claim: "Model X runs at Y tokens/sec"
Evidence:
  A: No supporting evidence
  B: Two benchmarks
  C: One forum claim
Status: Unverified
```

### Source Governance Policy

A policy layer, not an MCP change:

```json
{
  "approved": ["arxiv.org", "ieee.org", "sqlite.org"],
  "conditional": ["wikipedia.org", "medium.com"],
  "blocked": ["unknown-domains"]
}
```

The crawler extension declares:

```
permission: network.read
policy: requires approved-source-list
```

The Librarian policy engine evaluates: can this extension access this source?

---

## 3. The MCP as a Stable Protocol, Not a Tool Catalog

### What Must Remain Stable

These are platform primitives — equivalent to OS syscalls:

```
librarian_capability_projection
librarian_extension_register
librarian_extension_transition
librarian_extension_list
librarian_documentation_generate
librarian_documentation_drift_check
```

They answer: What extensions exist? Are they trusted? What capabilities are available?
What evidence supports that? What lifecycle state are they in?

### What Must NOT Happen

```
New crawler add-on → modify MCPController.swift → rebuild Librarian
New PDF analyzer   → modify MCPController.swift → rebuild Librarian
New DB connector   → modify MCPController.swift → rebuild Librarian
```

The core becomes a giant integration point.

### What Should Happen: Generic Capability Invocation

A future `librarian_capability_execute` bridge:

```json
Request:
{
  "capability": "wb_search_sources",
  "arguments": { "topic": "local AI inference" }
}
```

Librarian checks:

```
Capability Registry:
  wb_search_sources
    Provider:   working-bibliography-extension
    State:      ACTIVE
    Permission: research:web
    Risk:       R1
    Allowed:    yes

→ Route to WB Extension MCP endpoint
→ wb_search_sources(topic)
```

The core does not know what a crawler is. The MCP is like a network layer — TCP/IP does not
change every time a new website appears.

### OS Analogy

| OS Concept | Librarian Equivalent |
|------------|---------------------|
| Process | Extension |
| Syscall | MCP primitive |
| Device driver | Capability provider |
| Scheduler | Capability routing |
| Permissions | Extension contract |
| Process state | Lifecycle state |
| Memory protection | Capability isolation |

---

## 4. Multi-Node Scheduling and Collision Detection

(This was planned in earlier sprints. Captured here for continuity.)

When multiple nodes can satisfy the same capability request, a scheduler selects among them:

```
Capability Request: research.search

Available Providers:
  WB Extension       latency: 200ms   confidence: high    local
  External Node      latency: 3s      confidence: medium   remote

Scheduler chooses: WB Extension
```

This becomes relevant when:
- A Runtime Node and WB both provide overlapping capabilities
- QA Pilot runs validation in parallel
- Multiple consumers request the same capability simultaneously

Existing collision detection infrastructure (from composition sprints) handles namespace
isolation. The remaining work is routing policy.

---

## 5. New Extension Flow (Repeatable)

Every future add-on follows the same pattern, proven by WB:

```
1. SDK scaffold → extension package
2. Declare identity, capabilities, permissions, tools, risk levels
3. Register with Librarian → REGISTERED
4. Contract validation → CONTRACT_VERIFIED
5. Owner approval → OWNER_APPROVED
6. Activation → ACTIVE
7. Capability projection exposes to consumers
8. Drift monitoring
9. Suspension / recovery
```

No MCPController.swift changes. No Librarian rebuild. The consumer does not need to know:
where the data lives, which database is used, whether the provider is Python, Swift, Rust,
remote, or local, or how many nodes exist.

---

## 6. Capability Namespace Specification

Once multiple nodes, providers, and scheduling are in play, the namespace becomes the
equivalent of a kernel ABI. Capability names must be collision-free and ownership must
be deterministic.

### Ownership Rules

```
namespace:
    knowledge.*

reserved:
    librarian.*

extension-owned:
    wb.*          (Working Bibliography)
    runtime.*     (Runtime Node)
    qa.*          (QA Pilot)

shared:
    research.*    (any approved provider can implement)
    archive.*     (any approved provider can implement)
```

### Resolution Order

When a consumer requests a capability, the scheduler resolves by:

1. **Exact match** — `wb.search` → Working Bibliography only
2. **Namespace match** — `research.search` → any approved provider with `research.*`
3. **Shared capability** — `archive.snapshot` → scheduler selects from eligible providers

### Collision Policy

Existing collision detection infrastructure (from composition sprints) handles namespace
isolation. Rules:

| Scenario | Resolution |
|----------|-----------|
| Two providers, same capability, fixed namespace | First-registered wins (with override) |
| Two providers, same capability, shared namespace | Scheduler selects by policy |
| Provider claims `librarian.*` | Rejected at contract validation |
| Provider publishes undeclared capability | REVOKE classification (beyond drift) |

The namespace spec becomes part of the contract that every extension validates against
at registration time, preventing namespace conflicts before they reach the scheduler.

---

## Summary of Planned Capability Sets

| Milestone | Capabilities | Description |
|-----------|-------------|-------------|
| **WB-ARCHIVE-GOVERNANCE-1** | `wb_capture_snapshot`, `wb_compare_snapshot`, `wb_list_source_history`, `wb_apply_retention_policy`, `wb_verify_source_integrity` | Versioned snapshots, retention, drift-aware source timelines |
| **WB-RESEARCH-CRAWL-1** | `research.source.discover`, `research.source.capture`, `research.archive.query` | Change-aware crawling with A/B/C source classification |
| **WB-SOURCE-POLICY-1** | Source approval lists, trust history, domain-based gating | Policy engine for which sources are ingestible |
| **CORE-INVOCATION-BRIDGE-1** | `librarian_capability_execute` | Generic capability invocation without MCP core changes |
| **CORE-SCHEDULER-1** | Multi-provider routing, latency-based selection, collision resolution | Capability scheduling across extension nodes |

---

## Architectural Boundary

The Librarian should not become "a giant MCP server containing every possible tool."
It should become "a governance kernel that schedules and authorizes capability providers."

That is why the extension SDK and projection work mattered. It moved the system from
plugin architecture toward capability operating system architecture.
