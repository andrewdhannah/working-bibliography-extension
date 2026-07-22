# EPIC-LIBRARIAN-CAPABILITY-PROJECTION-INTEGRATION-1

**Status:** Defined — requires Owner authorization
**Advancement:** `owner_must_confirm_each`
**Purpose:** Expose governed extension capability state through Librarian's MCP surface without making Librarian aware of extension implementations.

---

## Non-Goals

| Non-Goal | Rationale |
|---|---|
| No extension imports into Librarian core | Boundary integrity — Librarian never depends on extensions |
| No WB-specific capability logic | Projection is generic, not WB-specific |
| No consumer-specific logic | Per ADR-WB-008 — consumers are requesting actors |
| No duplicated lifecycle engine | Use existing handshake lifecycle state |
| No direct extension discovery by consumers | Per ADR-WB-009 — projection is the sole discovery path |

---

## Dependency

```
Working Bibliography Extension Repository
    │
    │ proves the projection contract, provides Python reference
    ▼
Capability Projection Contract (docs/consumer/CAPABILITY-PROJECTION-CONTRACT.md)
    │
    │ consumed by Swift implementation in Librarian core
    ▼
Librarian MCP Surface (MCPController.swift)
    │
    │ exposed to any MCP client
    ▼
Any Consumer (AI agent, CLI, app, service)
```

---

## Sprint 1: LIBRARIAN-CAPABILITY-PROJECTION-SCHEMA-ALIGNMENT-1

**Purpose:** Ensure the contract boundary is language-neutral.

**Validate:**

```
Python Projection Model (src/projection/schema.py)
          =
Capability Projection Contract (docs/consumer/CAPABILITY-PROJECTION-CONTRACT.md)
          =
Swift Projection Model (to be implemented)
```

**Outputs:**
- Swift `Codable` models matching the projection contract
- Enum mappings for `ExtensionState` and `CapabilityAvailability`
- Serialization fixtures for all 6 extension states
- Cross-language contract compatibility tests

**Acceptance:**

| Case | Expected |
|---|---|
| Empty registry | Valid empty projection |
| REGISTERED | Visible, unavailable |
| CONTRACT_VERIFIED | Visible, unavailable |
| OWNER_APPROVED | Visible, unavailable |
| ACTIVE | Capabilities exposed |
| SUSPENDED | Unavailable |
| REVOKED | Historical only |

**Constraints:**
- No MCP changes yet
- No Librarian core modification yet
- Models only

**Reference:** `src/projection/schema.py`, `src/projection/service.py`

---

## Sprint 2: LIBRARIAN-CAPABILITY-PROJECTION-MCP-WIRING-1

**Purpose:** Expose the capability projection through the existing MCP transport.

**Changes in `MCPController.swift`:**

```
buildToolList()
    ↓
    add: librarian_capability_projection

handleCallTool()
    ↓
    add case: "librarian_capability_projection"
        → return capabilityProjectionService.project()
```

**Acceptance:**

```
tools/list → includes librarian_capability_projection
tools/call { name: "librarian_capability_projection" }
    → returns governed projection
```

**Important invariant:** The tool returns what Librarian knows, not what extensions claim.

**Reference:** `docs/consumer/LIBRARIAN-INTEGRATION-GUIDE.md`

---

## Sprint 3: LIBRARIAN-CAPABILITY-PROJECTION-CONFORMANCE-1

**Purpose:** Prevent implementation divergence between the Python reference and the Swift implementation.

**Cross-language validation:**

```
Python Reference Projection (src/projection/tests.py)
          == semantic match ==
Swift Librarian Projection (to be implemented)
```

**Test dimensions:**

| Dimension | Python Reference | Swift Implementation |
|---|---|---|
| Zero extensions | ✅ | Must match |
| One active extension | ✅ | Must match |
| Mixed lifecycle states | ✅ | Must match |
| Multiple extensions | ✅ | Must match |
| Capability collisions | ✅ | Must match |
| Suspended extension | ✅ | Must match |
| Revoked extension | ✅ | Must match |

**Acceptance:** Identical semantic projection. Minor JSON ordering differences are irrelevant; meaning must match.

---

## Sprint 4: CONSUMER-END-TO-END-PROOF-1

**Purpose:** Prove the complete lifecycle from consumer through Librarian to extension.

**Scenario:**

```
Consumer starts
    ↓
Requests capability projection
    ↓
Discovers WB capabilities
    ↓
Uses WB capability
    ↓
WB enters SUSPENDED (drift detected)
    ↓
Consumer refreshes projection
    ↓
Consumer explains unavailable capability
```

**Proof points:**

| Claim | Verification |
|---|---|
| No invented tools | Consumer harness: 46/46 tests |
| No stale assumptions | Staleness detection via projection_id |
| No direct extension trust | Projection is sole discovery path |
| No capability leakage | Composition: 50/50 tests |
| Graceful degradation | Absence handling: 5-state matrix |

---

## Integration Checklist

- [ ] Swift Codable models match Python schema
- [ ] All 6 extension states mapped correctly
- [ ] `librarian_capability_projection` added to `buildToolList()`
- [ ] Handler case added to `handleCallTool()`
- [ ] Cross-language conformance tests pass
- [ ] End-to-end scenario completes
- [ ] No extension code imported into Librarian core
- [ ] No consumer-specific logic in projection
- [ ] Projection returns authority-derived availability only

---

## Resulting Architecture

```
                  Any Consumer
                       |
                       |
                  MCP Protocol
                       |
                       ↓
             Librarian Governance Kernel
                       |
       ┌───────────────┼────────────────┐
       |               |                |
 Capability       Contracts         Receipts
 Projection       Lifecycle         Evidence
       |
       ↓
 Independent Extensions

 ┌──────────┬───────────┬──────────┐
 │ Working  │ Runtime   │ Future   │
 │ Bib      │ Node      │ Ext      │
 └──────────┴───────────┴──────────┘
```

Claim after integration:

> Librarian exposes a governed capability ecosystem boundary.
> Extensions are independently developed, contract-bound capability providers.
> Consumers discover capabilities through a governed projection, not direct extension trust.
