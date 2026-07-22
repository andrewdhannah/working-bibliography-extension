# Consumer Capability Model — Extension Awareness Architecture

**Sprint:** WB-CONSUMER-CAPABILITY-DISCOVERY-1
**Status:** Draft — requires Owner authorization
**Date:** 2026-07-21

---

## 1. Problem

The extension model has proven that an extension can govern itself — declare identity, pass handshake, enforce contracts, detect drift, handle revocation. But the model is incomplete without the consumer side.

"Consumer" means any actor that requests governed capabilities:
- An AI agent (OpenWork, Claude, DeepSeek, GPT)
- A CLI tool
- A desktop application
- A workflow engine
- A human operator interface
- Another service

Without capability awareness, any consumer will either:

| Failure Mode | Example | Cause |
|---|---|---|
| Assume access | "Let me search the research library" when WB is SUSPENDED | Consumer doesn't know capability state |
| Invent tools | "Calling wb_search_context" when WB is REVOKED | Consumer doesn't know tool is unavailable |
| Silent fallback | Using stale context without explaining source | Consumer doesn't know context is stale |
| False absence | Not using WB when it's ACTIVE | Consumer doesn't know capability exists |

Milestone 4 solves this by giving any consumer a governed capability projection — a governance artifact that describes available extensions, their lifecycle state, and their declared capabilities.

---

## 2. Architecture

```
                  Any Consumer
                         |
        ┌────────────────┼────────────────┐
        │                │                │
     AI Agent         CLI Tool         Human UI
   (OpenWork)           (any)          (Future)
        │                │                │
        └────────────────┼────────────────┘
                         |
                    MCP Protocol
                         |
                         ▼
              Librarian Governance Kernel
                         |
        ┌────────────────┼────────────────┐
        │                │                │
 Capability Registry  Contracts       Receipts
        │                │                │
        └────────────────┼────────────────┘
                         |
                         ▼
              Extension Ecosystem
        ┌────────────┬────────────┬───────────┐
        │            │            │           │
       WB        Runtime Node   QA Pilot   Future
```

### Key Invariant (ADR-WB-008)

> The consumer is not part of the trust chain. It is a requesting actor. Librarian does not need to know what the consumer is, only that it is authorized to request a capability projection.

### Trust Chain

```
Extension declares identity
    ↓
Librarian validates and registers
    ↓
Extension reaches ACTIVE state
    ↓
Librarian includes in capability projection
    ↓
Consumer requests projection
    ↓
Consumer reasons from projection
    ↓
Consumer executes via MCP
    ↓
Librarian enforces at runtime
```

---

## 3. Capability Freshness Model — Three-Layer Architecture

### Layer 1: Consumer Startup

When a consumer starts or connects, it requests the full capability projection:

```
Consumer (any)
  │
  │ capability_projection()
  ▼
Librarian
  │
  │ Returns:
  │   - projection_id
  │   - available extensions
  │   - lifecycle state per extension
  │   - approved capabilities per extension
  │   - generated_at timestamp
  ▼
Consumer builds capability context
```

Every session begins with a known, current state — regardless of consumer type.

### Layer 2: Lifecycle Invalidation

Extensions do not push capability changes directly to the consumer. The authority chain is:

```
Extension
    │
    │ lifecycle change (drift detected, suspended, revoked)
    ▼
Librarian
    │
    │ capability projection marked stale (projection_id changes)
    ▼
Consumer (on next check)
    │
    │ projection_id no longer current
    │
    ▼
Consumer refreshes projection
```

The extension cannot say "I am active, trust me." It says "My state changed. Please reevaluate me."

### Layer 3: Pre-Execution Verification

For R1+ actions (mutations, searches), the consumer verifies before execution:

```
Consumer wants: wb_search_context()
    │
    ▼
Capability check:
    Is WB registered?       ✅
    Is contract verified?   ✅
    Is owner approved?      ✅
    Is ACTIVE?              ✅
    Is capability allowed?  ✅
    │
    ▼
Execute via MCP
```

For R0 actions (reads), the cached projection is sufficient.

### Freshness Invariant

| Layer | When | R0 Actions | R1+ Actions |
|---|---|---|---|
| 1 | Consumer startup | Full projection cached | Full projection cached |
| 2 | Lifecycle event | Projection invalidated | Projection invalidated |
| 3 | Before execution | Not checked (cache OK) | Verified against source |

> The consumer may reason from cached capability state, but execution authority is always resolved by the governance layer.

---

## 4. Capability Projection Data Model

```json
{
  "projection_id": "CP-20260721-0001",
  "generated_at": "2026-07-21T18:00:00Z",
  "authority": "librarian-core",
  "extensions": [
    {
      "extension_id": "working-bibliography-extension",
      "display_name": "Working Bibliography Extension",
      "lifecycle": "ACTIVE",
      "contract_id": "wb-librarian-contract-v1",
      "contract_version": "1.0.0",
      "registration_receipt": "rcp-wb-registration-...",
      "capabilities": [
        {
          "name": "artifact.read",
          "tools": ["wb_get_artifact", "wb_list_artifacts"],
          "risk": "R0",
          "status": "active"
        },
        {
          "name": "artifact.register",
          "tools": ["wb_register_artifact"],
          "risk": "R1",
          "status": "active"
        }
      ]
    },
    {
      "extension_id": "runtime-node",
      "display_name": "Librarian Runtime Node",
      "lifecycle": "ACTIVE",
      "capabilities": [
        {
          "name": "model.execute",
          "tools": ["model_execute", "model_status"],
          "risk": "R1",
          "status": "active"
        }
      ]
    }
  ]
}
```

### Projection Rules

| Rule | Description |
|---|---|
| PR-001 | Only extensions in ACTIVE state appear with executable capabilities |
| PR-002 | Extension in REGISTERED/CONTRACT_VERIFIED/OWNER_APPROVED appears as "not yet active" |
| PR-003 | Extension in SUSPENDED appears with lifecycle "SUSPENDED" and no executable capabilities |
| PR-004 | Extension in REVOKED appears with lifecycle "REVOKED" and historical reference only |
| PR-005 | Extension not registered does not appear in any projection |
| PR-006 | Each projection has a unique projection_id for staleness detection |
| PR-007 | Projection always includes generated_at and authority fields |

---

## 5. Consumer Capability Context

A consumer builds and maintains a capability context from the projection. The context structure is consumer-independent — any consumer can build the same model:

```python
class CapabilityContext:
    """Consumer's understanding of available governed capabilities.
    
    This class is consumer-agnostic. Any AI agent, CLI tool, or
    application can use it to reason about available extensions.
    """

    def __init__(self):
        self.projection_id = None
        self.generated_at = None
        self.extensions = {}  # extension_id -> ExtensionState
        self.capability_index = {}  # tool_name -> CapabilityRef

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self.capability_index

    def get_extension_state(self, extension_id: str) -> str:
        """Get the lifecycle state of an extension."""
        ext = self.extensions.get(extension_id)
        return ext.lifecycle_state if ext else "unknown"

    def is_executable(self, tool_name: str) -> bool:
        """Check if a tool can be executed."""
        cap = self.capability_index.get(tool_name)
        if not cap:
            return False
        ext = self.extensions.get(cap.extension_id)
        return ext and ext.lifecycle_state == "ACTIVE"
```

### Consumer Reasoning Rules

| Rule | Description |
|---|---|
| CR-001 | Consumer may only use capabilities present in its current projection |
| CR-002 | Consumer must not invent tools not in the projection |
| CR-003 | Consumer must not claim access to a suspended or revoked extension |
| CR-004 | Consumer must refresh projection when projection_id no longer matches |
| CR-005 | Consumer must verify R1+ capabilities before execution |
| CR-006 | Historical capability access does not imply current authorization |
| CR-007 | Consumer is responsible for its own behavior given the projection — Librarian does not enforce consumer-side behavior |

---

## 6. State-to-Consumer Behavior Matrix

| Extension State | In Projection? | Executable? | Consumer Behavior Example |
|---|---|---|---|
| Not registered | No | No | Does not mention extension |
| REGISTERED | Yes (info only) | No | "Extension discovered, not yet active" |
| CONTRACT_VERIFIED | Yes (info only) | No | "Contract verified, awaiting approval" |
| OWNER_APPROVED | Yes (info only) | No | "Approved, not yet activated" |
| ACTIVE | Yes | Yes | Full capability access |
| SUSPENDED | Yes (blocked) | No | "Extension suspended — not available" |
| REVOKED | Yes (history) | No | "Extension revoked — historical records only" |

---

## 7. Refresh Triggers

| Trigger | Action | Mechanism |
|---|---|---|
| Consumer startup | Full projection fetch | `capability_projection()` |
| Projection ID mismatch | Refresh projection | Compare cached vs current ID |
| R1+ capability execution | Verify capability | Check against live projection |
| Lifecycle invalidation event | Mark projection stale | Librarian-side (projection_id changes) |
| Periodic refresh | Check projection age | Configurable per consumer |

---

## 8. Integration with Librarian MCP Surface

The capability projection is exposed as a standard Librarian MCP tool:

```
Tool: librarian_capability_projection
Risk: R0 (read-only)
Input: optional projection_id
Output: full projection or "unchanged" status
```

This tool is the single entry point for any consumer to discover available governed capabilities. It is not agent-specific, not OpenWork-specific — any MCP client can call it.

---

## 9. Non-Goals

| Non-Goal | Why |
|---|---|
| Consumer polls every extension directly | Extension self-assertion breaks the governance model |
| Real-time push to consumer | Requires push infrastructure beyond current MCP |
| Consumer caches capabilities across sessions | Each session must re-establish capability context |
| Consumer discovers capabilities without Librarian | Librarian is the single authority |
| Extension controls its projection entry | Librarian controls the projection based on lifecycle state |
| Librarian enforces consumer-side behavior | Consumer is responsible for its own reasoning |
