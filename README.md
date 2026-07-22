# Librarian Extension Reference Implementation

**First reference implementation of the Librarian extension governance model.** This repository proves that external capabilities can attach to the Librarian governance kernel through contracts, handshakes, lifecycle management, and continuous compliance — without becoming part of Librarian core.

Originally built as the Working Bibliography Extension (a governed knowledge custody provider), this repository evolved into the **canonical reference architecture** for the entire Librarian extension ecosystem. It contains the specification, implementation, validation suite, consumer awareness model, and extension SDK.

---

## What This Repository Contains

```
Specification          → docs/EXTENSION-SPECIFICATION-v1.md
Contract               → docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json
Lifecycle              → src/handshake/ (6-state state machine)
Execution              → src/mcp/ (MCP server, 3 active tools)
Enforcement            → src/enforcement/ (3-stage pipeline)
Drift Detection        → src/drift/ (7-domain comparison)
Revocation             → src/revocation/ (SUSPENDED/REVOKED/ACTIVE)
Validation             → src/validation/ (5 domains, 14 fixtures)
Capability Projection  → src/projection/ (consumer-agnostic MCP tool)
Consumer Awareness     → src/consumer/ (context builder + harness)
Composition            → src/composition/ (multi-extension, 50 tests)
Extension SDK          → src/sdk/generator.py + templates/
Ecosystem Model        → docs/LIBRARIAN-EXTENSION-ECOSYSTEM-MODEL-v1.md
ADR Archive            → docs/decisions/ (9 ADRs)
Integration Guide      → docs/consumer/LIBRARIAN-INTEGRATION-GUIDE.md
Platform Epic          → EPIC-INTEGRATION-PLAN.md
```

---

## Architecture

```
                  Any Consumer (AI agent, CLI, app, service)
                       |
                       |  capability_projection()
                       v
            Librarian Governance Kernel
                       |
        +--------------+--------------+
        |              |              |
 Capability       Contracts       Receipts
 Projection       Lifecycle       Evidence
        |              |              |
        +--------------+--------------+
                       |
                       v
         Independent Extensions
    +----------+------------+----------+
    | Working  |  Runtime   |  Future  |
    |  Bib     |   Node     |   Ext    |
    +----------+------------+----------+
```

### Key Invariants

| Invariant | Enforced By |
|---|---|
| No capability without a contract | Handshake validation |
| No trust without lifecycle progression | 6-state state machine |
| No execution without authorization | Permission + enforcement checks |
| No silent drift | 7-domain drift detection |
| No automatic restoration after violation | Owner-only suspension/revocation |
| No consumer-side capability invention | Consumer context harness |
| No direct provider-to-consumer authority | Capability projection (ADR-WB-009) |

---

## Proven Claims

| Claim | Evidence |
|---|---|
| An extension can be independently developed and governed | Full reference implementation with 9 ADRs |
| The contract is the integration point, not the code | Contract defined before implementation |
| Trust is established through lifecycle, not assumed | 6-state machine with explicit approval gate |
| Unavailable is a valid state | SUSPENDED/REVOKED: no capabilities, evidence preserved |
| Consumers safely discover capabilities | Consumer harness: 46 tests, no tool invention |
| Multiple extensions compose without leakage | Composition: 50 tests, namespace isolation |
| New extensions generated without platform knowledge | SDK produces contract-compliant scaffold |
| Governance kernel survives extension removal | Revocation: core unaffected, receipts preserved |

---

## Quick Start

```bash
# Start the MCP server (identity registered, capabilities LOCKED)
python3 src/mcp/server.py

# Or start with auto-handshake for testing
python3 src/mcp/server.py --handshake

# Check lifecycle state
curl http://127.0.0.1:8765/health

# List available tools
curl -X POST http://127.0.0.1:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Register an artifact (requires ACTIVE state)
curl -X POST http://127.0.0.1:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":2,"params":{"name":"wb_register_artifact","arguments":{"source":{"retrieved_at":"2026-07-21T14:25:00Z"},"content":{"canonical_text":"Your content here.","raw_format":"text"}}}}'
```

---

## Extension Lifecycle

```
REGISTERED -> CONTRACT_VERIFIED -> OWNER_APPROVED -> ACTIVE
                                                     -> SUSPENDED -> REVOKED
```

Capabilities are only available in **ACTIVE** state. **REVOKED** is terminal.

### State Authority

| Transition | Authority |
|---|---|
| REGISTERED -> CONTRACT_VERIFIED | Automated (validation passes) |
| CONTRACT_VERIFIED -> OWNER_APPROVED | **Owner only** |
| OWNER_APPROVED -> ACTIVE | Automated (activation) |
| ACTIVE -> SUSPENDED | Automated (drift) or Owner |
| ACTIVE -> REVOKED | **Owner only** |
| SUSPENDED -> ACTIVE | **Owner only** |
| SUSPENDED -> REVOKED | **Owner only** |

---

## Ecosystem Roles

| Role | Owns | Does Not Own |
|---|---|---|
| **Provider (Extension)** | Domain logic, artifacts, domain lifecycle | Authority, decisions, projection |
| **Governance Kernel** | Registry, contracts, receipts, projection, enforcement | Domain logic, consumer behavior |
| **Consumer** | Its own reasoning, execution decisions | Capability availability, extension trust |

---

## Key Documents

| Document | What It Defines |
|---|---|
| [EXTENSION-DEVELOPER-GUIDE.md](EXTENSION-DEVELOPER-GUIDE.md) | Step-by-step implementation guide |
| [docs/EXTENSION-SPECIFICATION-v1.md](docs/EXTENSION-SPECIFICATION-v1.md) | Formal compliance requirements (L1-L4) |
| [docs/EXTENSION-SDK-GUIDE.md](docs/EXTENSION-SDK-GUIDE.md) | SDK usage guide |
| [docs/COMPLIANCE-MATRIX.md](docs/COMPLIANCE-MATRIX.md) | Requirement-to-validator mapping |
| [docs/LIBRARIAN-EXTENSION-ECOSYSTEM-MODEL-v1.md](docs/LIBRARIAN-EXTENSION-ECOSYSTEM-MODEL-v1.md) | Complete ecosystem architecture |
| [docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json](docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json) | Formal contract (reference) |
| [docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md](docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md) | Handshake protocol |
| [docs/contracts/CAPABILITY-MANIFEST.md](docs/contracts/CAPABILITY-MANIFEST.md) | Capability declaration format |
| [docs/contracts/CONTRACT-BOUNDARIES.md](docs/contracts/CONTRACT-BOUNDARIES.md) | Ownership and prohibited domains |
| [docs/consumer/CAPABILITY-PROJECTION-CONTRACT.md](docs/consumer/CAPABILITY-PROJECTION-CONTRACT.md) | Consumer-facing projection contract |
| [docs/consumer/LIBRARIAN-INTEGRATION-GUIDE.md](docs/consumer/LIBRARIAN-INTEGRATION-GUIDE.md) | Librarian MCP wiring guide |
| [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | System design and data flow |
| [docs/architecture/EXTENSION-PORT-MODEL.md](docs/architecture/EXTENSION-PORT-MODEL.md) | Extension port model |
| [docs/schemas/wb-artifact.schema.json](docs/schemas/wb-artifact.schema.json) | Artifact JSON Schema |
| [EPIC-INTEGRATION-PLAN.md](EPIC-INTEGRATION-PLAN.md) | Platform integration roadmap |
| [MILESTONE-ROADMAP.md](MILESTONE-ROADMAP.md) | Milestone tracker |

### Architectural Decisions

| ADR | Decision |
|---|---|
| ADR-WB-001 | The embedding is not the artifact |
| ADR-WB-002 | No custom custody model |
| ADR-WB-003 | Contract lives in extension repo |
| ADR-WB-004 | No Owner decisions from extension |
| ADR-WB-005 | Extension can mutate its own domain |
| ADR-WB-006 | EXTERNAL_REFERENCE custody mode |
| ADR-WB-007 | Embedding capability boundary (shared model, owned store) |
| ADR-WB-008 | Consumers are not governance participants |
| ADR-WB-009 | Librarian is sole authority for capability projection |

---

## SDK -- Create a New Extension

```bash
python3 -m src.sdk.generator \
    --name my-extension \
    --domain knowledge.reference \
    --capability "search,Search Items,R0,read:items,item_search"
```

Generates: identity, contract, capabilities, permissions, MCP scaffold, validation fixture, README. All start in `REGISTERED` state -- no bypass.

---

## Validation

```bash
# Run all validation fixtures
python3 -m src.validation.fixture_runner

# Run capability projection tests
python3 src/projection/tests.py

# Run consumer harness tests
python3 src/consumer/tests.py

# Run composition tests
python3 src/composition/tests.py
```

---

## Relationship to Librarian

```
github.com/andrewdhannah/librarian                   <- Governance kernel
github.com/andrewdhannah/working-bibliography-extension  <- This repo
```

This repository is the **reference architecture and specification** for the Librarian extension model. Librarian core validates extensions against the contract defined here. The remaining integration -- wiring `librarian_capability_projection()` into Librarian's MCP surface -- is documented in `EPIC-INTEGRATION-PLAN.md`.

---

## License

Reference implementation of the Librarian extension governance model.

Extensions are not granted access. They establish a contract, declare capabilities, pass validation, and operate within defined ownership boundaries.
