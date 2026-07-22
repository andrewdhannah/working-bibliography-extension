# Agent Capability Model — Extension Awareness Architecture

**Sprint:** WB-AGENT-CAPABILITY-DISCOVERY-1
**Status:** Draft — requires Owner authorization
**Date:** 2026-07-21

---

## 1. Problem

The extension model has proven that an extension can govern itself — declare identity, pass handshake, enforce contracts, detect drift, handle revocation. But the model is incomplete without the agent side.

Without capability awareness, an agent will either:

| Failure Mode | Example | Cause |
|---|---|---|
| Assume access | "Let me search the research library" when WB is SUSPENDED | Agent doesn't know capability state |
| Invent tools | "Calling wb_search_context" when WB is REVOKED | Agent doesn't know tool is unavailable |
| Silent fallback | Using stale context without explaining source | Agent doesn't know context is stale |
| False absence | Not using WB when it's ACTIVE | Agent doesn't know capability exists |

Milestone 4 solves this by giving the agent a governed capability projection at session start, keeping it fresh through lifecycle events, and verifying before execution.

---

## 2. Architecture

```
                 Agent
                   │
                   │ 1. capability_projection() at startup
                   │ 2. verify() before R1+ execution
                   │ 3. lifecycle_invalidation events
                   ▼
            Librarian Core
                   │
          Capability Projection Service
                   │
        ┌──────────┼──────────┐
        │          │          │
       WB       Runtime    Future
    Extension   Node     Extensions
```

### Key Invariant

> The agent never trusts the extension directly. The extension never controls the agent. The Librarian remains the custody and authorization boundary.

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
Agent receives projection at startup
    ↓
Agent reasons from projection
    ↓
Agent verifies before execution (R1+)
    ↓
Librarian enforces at runtime
```

---

## 3. Capability Freshness Model — Three-Layer Architecture

### Layer 1: Session/Startup Refresh

At agent startup, the agent requests the full capability projection:

```
Agent
  │
  │ capability_projection()
  ▼
Librarian
  │
  │ Returns:
  │   - available extensions
  │   - lifecycle state per extension
  │   - approved capabilities per extension
  │   - projection_id (for staleness detection)
  │   - generated_at timestamp
  ▼
Agent builds capability context
```

The agent begins every session with a known, current state.

### Layer 2: Lifecycle Invalidation

Extensions do not push capability changes directly to the agent. The authority chain is:

```
Extension
    │
    │ lifecycle change (drift detected, suspended, revoked)
    ▼
Librarian
    │
    │ capability projection marked stale
    ▼
Agent (on next check)
    │
    │ projection_id no longer current
    │
    ▼
Agent refreshes projection
```

The extension cannot say "I am active, trust me." It says "My state changed. Please reevaluate me."

### Layer 3: Pre-Execution Verification

For R1+ actions (mutations, searches), the agent verifies before execution:

```
Agent wants: wb_search_context()
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
Execute
```

For R0 actions (reads from cache), the cached projection is sufficient.

### Freshness Invariant

| Layer | When | R0 Actions | R1+ Actions |
|---|---|---|---|
| 1 | Session start | Full projection cached | Full projection cached |
| 2 | Lifecycle event | Projection invalidated | Projection invalidated |
| 3 | Before execution | Not checked (cache OK) | Verified against source |

> The agent may reason from cached capability state, but execution authority is always resolved by the governance layer.

---

## 4. Capability Projection Data Model

```json
{
  "projection_id": "cap-proj-20260721-001",
  "generated_at": "2026-07-21T18:00:00Z",
  "source": "librarian-core",
  "extensions": [
    {
      "extension_id": "working-bibliography-extension",
      "display_name": "Working Bibliography Extension",
      "lifecycle_state": "ACTIVE",
      "contract_id": "wb-librarian-contract-v1",
      "contract_version": "1.0.0",
      "registration_receipt": "rcp-wb-registration-...",
      "capabilities": [
        {
          "id": "artifact.read",
          "tools": ["wb_get_artifact", "wb_list_artifacts"],
          "risk": "R0",
          "status": "active"
        },
        {
          "id": "artifact.register",
          "tools": ["wb_register_artifact"],
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
| PR-001 | Only extensions in ACTIVE state appear in executable capabilities |
| PR-002 | Extension in REGISTERED/CONTRACT_VERIFIED/OWNER_APPROVED appears as "not yet active" |
| PR-003 | Extension in SUSPENDED appears with state "suspended" and no executable capabilities |
| PR-004 | Extension in REVOKED appears with state "revoked" and historical reference only |
| PR-005 | Extension not registered does not appear in any projection |
| PR-006 | Each projection has a unique projection_id for staleness detection |
| PR-007 | Projection always includes generated_at timestamp |

---

## 5. Agent Capability Context

The agent builds and maintains a capability context from the projection:

```python
class CapabilityContext:
    """The agent's understanding of available governed capabilities."""

    def __init__(self):
        self.projection_id = None
        self.generated_at = None
        self.extensions = {}  # extension_id -> ExtensionState
        self.capability_index = {}  # tool_name -> ExtensionCapability

    def has_capability(self, tool_name: str) -> bool:
        """Check if a tool is available in the current context."""
        return tool_name in self.capability_index

    def get_extension_state(self, extension_id: str) -> str:
        """Get the lifecycle state of an extension."""
        ext = self.extensions.get(extension_id)
        return ext.lifecycle_state if ext else "unknown"

    def is_executable(self, tool_name: str) -> bool:
        """Check if a tool can be executed (extension is ACTIVE)."""
        cap = self.capability_index.get(tool_name)
        if not cap:
            return False
        ext = self.extensions.get(cap.extension_id)
        return ext and ext.lifecycle_state == "ACTIVE"
```

### Agent Reasoning Rules

| Rule | Description |
|---|---|
| AR-001 | Agent may only use capabilities present in its current capability projection |
| AR-002 | Agent must not invent tools not in the projection |
| AR-003 | Agent must not claim access to a suspended or revoked extension |
| AR-004 | Agent must refresh projection when projection_id no longer matches |
| AR-005 | Agent must verify R1+ capabilities before execution |
| AR-006 | Historical capability access does not imply current authorization |

---

## 6. State-to-Agent Behavior Matrix

| Extension State | In Projection? | Executable? | Agent Behavior |
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
| Agent session start | Full projection fetch | `capability_projection()` |
| Projection ID mismatch | Refresh projection | Compare cached vs current ID |
| R1+ capability execution | Verify capability | Check against live projection |
| Lifecycle invalidation event | Mark projection stale | Librarian-side event (future) |
| Periodic refresh | Check projection age | Configurable interval (default: 30min) |

---

## 8. Integration with Existing Startup

The capability projection becomes part of the agent startup sequence:

```
Current startup:           With capability projection:

A — Entrypoint             A — Entrypoint
B — Contract               B — Contract
C — MCP Context            C — MCP Context
E — Verification              +-- capability_projection()
H — Optional Tools         E — Verification
                           H — Optional Tools
                               +-- capability context built
```

The projection is fetched during step C (MCP Context), after project identity is established but before verification begins.

---

## 9. Non-Goals

| Non-Goal | Why |
|---|---|
| Agent polls every extension directly | Extension self-assertion breaks the governance model |
| Real-time push to agent | Requires push infrastructure beyond current MCP |
| Agent caches capabilities across sessions | Each session must re-establish capability context |
| Agent discovers capabilities without Librarian | Librarian is the single authority |
| Extension controls its projection entry | Librarian controls the projection based on lifecycle state |
