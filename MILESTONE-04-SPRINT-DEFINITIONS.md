# Milestone 4 — Consumer Extension Awareness: Sprint Definitions

**Project:** `working-bibliography-extension`
**Status:** Draft — each requires Owner authorization
**Sequence:** Define projection → Expose on Librarian → Build consumer harness → Compose → Package

**Per ADR-WB-008:** Consumers (AI agents, CLIs, applications, services) are not governance participants. They consume capability projections but do not define capability authority.

---

## Overview

```
Milestone 4 proves the missing half of the extension model:

Milestones 1-3: "Can an extension behave safely?"             ✅
Milestone 4:    "Can any consumer safely reason about          ⏳
                available extensions?"
```

### Final Architecture

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

---

## Sprint: WB-CONSUMER-CAPABILITY-DISCOVERY-1 (Definition)

**Authorization prompt:**
> Authorize sprint WB-CONSUMER-CAPABILITY-DISCOVERY-1 for project working-bibliography-extension.

**Objective:** Define the capability projection model, freshness rules, invalidation rules, and consumer context model. No runtime implementation — contract-first.

**Scope:**
- Capability projection data model (consumer-agnostic)
- Three-layer freshness model (startup refresh, lifecycle invalidation, pre-execution verify)
- Consumer capability context structure
- State-to-consumer-behavior matrix (7 states)
- Projection staleness detection via projection_id
- Integration with Librarian MCP surface

**Required outputs:**
- `docs/consumer/CONSUMER-CAPABILITY-MODEL.md`
- `docs/consumer/CAPABILITY-PROJECTION-CONTRACT.md`

**Key decisions:**
- Librarian is the single authority for capability projection
- Extensions do not self-assert capability state to consumers
- The projection is a governance artifact, not an agent-specific protocol
- Any MCP client can request the projection (consumer-agnostic)
- Hybrid freshness: cache on startup, invalidate on lifecycle events, verify on R1+ execution
- Projection_id enables staleness detection without full data transfer

**Constraints:**
- No MCP implementation
- No Librarian core changes
- No consumer harness code
- No extension modification

**Acceptance criteria:**
- Projection data model is defined and consumer-agnostic
- Freshness rules cover all three layers
- State-to-consumer-behavior matrix covers all 7 lifecycle states
- Staleness detection mechanism is defined
- Integration point with Librarian MCP is identified

---

## Sprint: WB-LIBRARIAN-CAPABILITY-PROJECTION-1 (Librarian Core)

**Authorization prompt:**
> Authorize sprint WB-LIBRARIAN-CAPABILITY-PROJECTION-1 for project working-bibliography-extension.

**Objective:** Expose governed capability state through a new Librarian MCP tool. This is the smallest possible core change — a single MCP tool that reads from the existing node registry and extension lifecycle state.

**Scope:**
- Implement `librarian_capability_projection()` MCP tool
- Wire into `buildToolList()` and `handleCallTool()` in `MCPController.swift`
- Projection reads from: extension lifecycle state + capability manifest
- Projection_id generation and staleness tracking
- Conditional return ("unchanged" if projection_id matches)

**Required outputs:**
- Librarian MCP: `librarian_capability_projection` tool (wired and callable)
- Projection logic: reads registered extensions, checks lifecycle state, returns capabilities

**Required behavior:**
- ACTIVE extension → included with capabilities
- SUSPENDED extension → included without capabilities
- REVOKED extension → included as historical marker
- REGISTERED/CONTRACT_VERIFIED/OWNER_APPROVED → included as info-only
- Unregistered extension → not in projection
- Any MCP client can call the tool (consumer-agnostic)

**Wire details:**
- Add `case "librarian_capability_projection":` to `handleCallTool` switch
- Add tool definition to `buildToolList()`
- Projection handler aggregates state from handshake lifecycle + capability manifest
- Existing `CapabilityMCPHandlers.swift` defines `librarian_capability_find` and `librarian_capability_search` — these become internal query primitives used by the projection

**Constraints:**
- No capability registry schema changes
- No new database tables
- No modification of extension lifecycle code
- Must work with existing handshake lifecycle state
- Tool is R0 (read-only, no gate)

**Acceptance criteria:**
- `librarian_capability_projection()` returns projection when called with no args
- `librarian_capability_projection({"projection_id": "..."})` returns "unchanged" or new projection
- ACTIVE extension appears with capabilities
- SUSPENDED extension appears without capabilities
- REVOKED extension appears as historical
- Unregistered extension does not appear

---

## Sprint: WB-CONSUMER-CONTEXT-HARNESS-1 (Conformance Test)

**Authorization prompt:**
> Authorize sprint WB-CONSUMER-CONTEXT-HARNESS-1 for project working-bibliography-extension.

**Objective:** Build a deterministic conformance harness that simulates any consumer reasoning about available governed extensions. This proves the capability awareness model works for any consumer type.

**Scope:**
- Consumer capability context simulator (consumer-agnostic)
- Five-state matrix test scenarios
- Projection consumer that builds capability index
- Pre-execution verification logic
- Absence/limitation explanation rules

**Required outputs:**
```
src/consumer/
├── capability_context.py     # Consumer capability context model
├── capability_index.py       # Flat tool lookup from projection
├── discovery.py              # Query Librarian for projection
├── executor.py               # Execute with pre-verification (R1+)
├── absence_handler.py        # Graceful limitation explanation
└── scenarios/
    ├── extension_available.json
    ├── extension_missing.json
    ├── extension_suspended.json
    ├── extension_revoked.json
    └── extension_reconnected.json

tests/test_consumer_harness.py
```

**Five-state acceptance matrix:**

| State | Projected? | Executable? | Consumer Behavior |
|---|---|---|---|
| ACTIVE | Yes | Yes | Uses extension |
| SUSPENDED | Yes (blocked) | No | Refuses capability, explains suspension |
| REVOKED | Yes (history) | No | Refuses capability, explains revocation |
| Not registered | No | No | Does not mention extension |
| Reconnected (ACTIVE) | Yes (refreshed) | Yes | Refreshes and uses |

**Constraints:**
- Consumer harness is a deterministic Python class, not an LLM
- No OpenWork integration (consumer-agnostic)
- All tests produce pass/fail evidence receipts
- Harness models any consumer, not a specific agent

**Acceptance criteria:**
- Consumer correctly uses capability when ACTIVE
- Consumer correctly refuses capability when SUSPENDED
- Consumer correctly refuses when REVOKED
- Consumer correctly continues without unregistered extension
- Consumer correctly refreshes on reconnection
- All 5 scenarios produce deterministic pass/fail results
- Receipts generated for each test scenario

---

## Sprint: WB-CONTEXT-COMPOSITION-1 (Multi-Extension)

**Authorization prompt:**
> Authorize sprint WB-CONTEXT-COMPOSITION-1 for project working-bibliography-extension.

**Objective:** Prove any consumer can reason across multiple simultaneous extensions with different capability domains without collapsing them together.

**Scope:**
- Multi-extension projection fixture
- Consumer reasoning across domains
- Capability isolation (no cross-extension confusion)
- Domain-aware consumer responses

**Projection fixture:**
```json
{
  "extensions": [
    {
      "extension_id": "working-bibliography-extension",
      "lifecycle": "ACTIVE",
      "capabilities": ["wb_search_context", "wb_get_artifact"]
    },
    {
      "extension_id": "runtime-node",
      "lifecycle": "ACTIVE",
      "capabilities": ["model_execute", "model_status"]
    },
    {
      "extension_id": "qa-pilot",
      "lifecycle": "REGISTERED",
      "capabilities": []
    }
  ]
}
```

**Required outputs:**
- Multi-extension projection fixtures
- Consumer reasoning across domains
- Capability isolation tests
- Domain collision detection

**Test scenarios:**

| Scenario | Expected |
|---|---|
| Multiple ACTIVE extensions | Consumer uses each for its domain |
| One SUSPENDED, one ACTIVE | Consumer uses ACTIVE, explains SUSPENDED |
| Capability name collision | Consumer identifies by extension_id, not tool name alone |
| Extension with similar domain | Consumer distinguishes by extension identity |
| All extensions unavailable | Consumer explains all limitations, continues |

**Constraints:**
- Extensions are simulated via fixtures (no real Runtime Node or QA Pilot MCP needed)
- Consumer must identify capabilities by extension_id + capability_id pair
- No capability leakage between extensions
- Consumer-agnostic — any consumer type can use the same projection

**Acceptance criteria:**
- Consumer correctly composes multiple extensions
- Consumer correctly handles mixed lifecycle states
- Consumer correctly isolates capabilities per extension
- Consumer correctly explains partial availability
- Receipts generated for each composition scenario

---

## Sprint: WB-EXTENSION-SDK-1 (SDK Generation)

**Authorization prompt:**
> Authorize sprint WB-EXTENSION-SDK-1 for project working-bibliography-extension.

**Objective:** Package the extension protocol as a reusable SDK template that generates validation artifacts, contract templates, MCP skeletons, and receipt definitions.

**Scope:**
- SDK directory structure
- Template generator (`src/sdk/generator.py`)
- Validation artifact generator
- Contract template with required sections
- MCP skeleton with tools/list and tools/call
- Lifecycle state machine template
- Receipt definition template

**Required outputs:**
```
src/sdk/
├── generator.py              # Main generator entry point
├── templates/
│   ├── contract.json          # Contract template
│   ├── capabilities.json      # Capability manifest template
│   ├── permissions.json       # Permissions template
│   ├── identity.json          # Identity declaration template
│   ├── mcp_server.py          # MCP server skeleton
│   ├── handshake.py           # Handshake lifecycle skeleton
│   ├── enforcement.py         # Enforcement pipeline skeleton
│   └── validation.py          # Validation fixture generator
├── schemas/
│   └── extension-package.schema.json
└── README.md
```

**Generator flow:**
```
python -m src.sdk.generator --name my-extension --domain my_domain
    │
    ├── creates extension/my-extension/
    │   ├── identity.json
    │   ├── contract.json
    │   ├── capabilities.json
    │   ├── permissions.json
    │   ├── src/mcp/server.py
    │   ├── src/handshake/
    │   └── tests/fixtures/
    │
    └── returns: Package created at extension/my-extension/
```

**Constraints:**
- Generated code must pass the validation suite
- Templates follow EXTENSION-SPECIFICATION-v1.md
- Generated extension must be a valid L1 (Contract) extension
- Generator must produce all required artifacts

**Acceptance criteria:**
- Generator produces a complete extension scaffold
- Generated identity.json passes identity validation
- Generated contract.json passes contract validation
- Generated capabilities.json passes capability validation
- Generated permissions.json passes permission validation
- Generated MCP skeleton is syntax-valid Python
- Extension author needs only to: rename, implement MCP tools, run validation
- Receipts generated for SDK creation

---

## Execution Sequence

```
MILESTONE 4 — CONSUMER EXTENSION AWARENESS

Sprint 1: WB-CONSUMER-CAPABILITY-DISCOVERY-1        ⏳  Docs (contract-first)
    ↓ (defines the model)
Sprint 2: WB-LIBRARIAN-CAPABILITY-PROJECTION-1        ⏳  Librarian MCP tool
    ↓ (exposes the projection)
Sprint 3: WB-CONSUMER-CONTEXT-HARNESS-1              ⏳  Conformance test
    ↓ (proves consumer-side behavior)
Sprint 4: WB-CONTEXT-COMPOSITION-1                    ⏳  Multi-extension
    ↓ (proves ecosystem reasoning)
Sprint 5: WB-EXTENSION-SDK-1                          ⏳  Reusable package
```

## Complete Project State

```
Milestone 1 — Contract Reference        ✅
  Identity, Architecture, Artifact Model, Contract, 8 ADRs

Milestone 2 — Runtime Governance        ✅
  MCP Interface, Handshake, Enforcement, Drift, Revocation

Milestone 3 — Public Extension          ✅
  Specification, Developer Guide, Compliance Matrix, Examples

Milestone 4 — Consumer Awareness        ⏳  (current)
  ├── Consumer Capability Discovery       ⏳
  ├── Librarian Capability Projection     ⏳
  ├── Consumer Context Harness            ⏳
  ├── Multi-Extension Composition         ⏳
  └── Extension SDK                       ⏳
```

The final architecture:

```
                  Any Consumer
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

Consumer never trusts extension directly. Extension never controls consumer. Librarian is the custody and authorization boundary.
