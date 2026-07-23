# Librarian Extension Reference Implementation

**Reference implementation of the Librarian capability governance model.** This repository proves that independently developed capabilities can participate in a governed AI ecosystem through contracts, handshakes, lifecycle management, continuous compliance, and capability projection — without becoming part of Librarian core or a new trust boundary.

The bibliography workload (source ingestion, artifact custody, knowledge retrieval) is the demonstration vehicle. The governed capability path — from external knowledge through ingestion, projection, consumer reasoning, drift detection, suspension, and recovery — is the product concept.

The complete end-to-end chain:

```
External Sources
    ↓
Governed Ingestion
    ↓
Canonical Artifact + Provenance (SHA-256 hash, source URL, capture timestamp)
    ↓
Capability Projection  ← Librarian governance kernel decides availability
    ↓
Consumer Context       ← agent sees only available capabilities
    ↓
Agent Reasoning        ← answers grounded in governed sources, not model memory
    ↓
Evidence-backed Output
    ↓
Lifecycle Governance  ← drift detection, suspension, Owner recovery
```

Sealed in sprints [#542–#545](https://github.com/andrewdhannah/librarian) with 20/20 operational proof checks and 22/22 live consumer proof checks. The full custody loop — ingestion, retrieval, suspension, consumer refusal, Owner restoration — is demonstrated end-to-end.

---

## What This Repository Contains

```
Specification          → docs/EXTENSION-SPECIFICATION-v1.md
Contract               → docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json
Lifecycle              → src/handshake/ (6-state state machine)
Execution              → src/mcp/ (MCP server, 3 active tools)
Enforcement            → src/enforcement/ (3-stage pipeline)
Drift Detection        → src/enforcement/drift_detector.py (baseline comparison)
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

Three running services represent the three architectural roles:

| Service | Port | Role |
|---|---|---|
| **Librarian MCP** (Swift) | 3456 | Governance kernel — capability projection, extension registry, lifecycle authority |
| **WB MCP Server** (Python) | 8765 | Capability provider — artifact storage, search, retrieval |
| **Projection Reference** (Python) | 8766 | Cross-language conformance oracle |

The separation of concerns:

```
                  Any Consumer (AI agent, CLI, app, service)
                       |
                       |  librarian_capability_projection()
                       |  (consumer queries Librarian, not the extension directly)
                       v
            Librarian Governance Kernel (:3456)
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
    | (:8765)  |            |          |
    +----------+------------+----------+
```

### Key Invariants

| Invariant | Enforced By |
|---|---|
| No capability without a contract | Handshake validation |
| No trust without lifecycle progression | 6-state state machine |
| No execution without authorization | Permission + enforcement checks |
| No silent drift | Baseline comparison (risk, permissions, tools, forbidden actions) |
| No automatic restoration after violation | Owner-only SUSPENDED/REVOKED transitions (centralized AUTHORITY_POLICY) |
| No consumer-side capability invention | Consumer context harness |
| No direct provider-to-consumer authority | Capability projection (ADR-WB-009) |
| **Capability Absence Invariant**: a consumer must not execute, infer availability of, or rely upon a capability absent from the current projection | Projection-level governance: suspension removes capability from consumer context, agent refuses unavailable tools |

---

## Proven Claims

| Claim | Evidence |
|---|---|
| An extension can be independently developed and governed | Full reference implementation with 9 ADRs |
| The contract is the integration point, not the code | Contract defined before implementation |
| Trust is established through lifecycle, not assumed | 6-state machine with explicit Owner approval gate |
| Unavailable is a valid state | SUSPENDED/REVOKED: no capabilities, evidence preserved |
| Consumers safely discover capabilities | Consumer harness: 46 tests, no tool invention |
| Multiple extensions compose without leakage | Composition: 50 tests, namespace isolation |
| New extensions generated without platform knowledge | SDK produces contract-compliant scaffold |
| Governance kernel survives extension removal | Revocation: core unaffected, receipts preserved |
| **Agent knows only what Librarian projects** | Live consumer proof: WB suspended, projection refreshed, zero WB tool calls issued, Owner restoration required |
| **Knowledge grounded in governed sources** | Operational proof: 3 sources ingested, SHA-256 hashed, provenance preserved, answers reference specific artifacts |

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
github.com/andrewdhannah/librarian                           <- Governance kernel (port 3456)
github.com/andrewdhannah/working-bibliography-extension      <- This repo (port 8765)
```

This repository is the **reference architecture and specification** for the Librarian extension model. The capability projection integration (`librarian_capability_projection`, `librarian_extension_register`, `librarian_extension_transition`, `librarian_extension_set_capabilities`, `librarian_extension_list`) is wired into Librarian's MCP surface and sealed in sprint #543.

The standalone WB MCP server (`src/mcp/server.py`) is preserved as a reference provider implementation and SDK test target. The Librarian integration adds a governance path — it does not replace the extension contract.

### Running the Live Proof

```bash
# 1. Start Librarian MCP (port 3456) — governance kernel
cd active/librarian
swift run LibrarianServer serve --env dev --hostname 127.0.0.1 --port 3456

# 2. Start WB MCP server (port 8765) — capability provider
cd working-bibliography-extension
python3 src/mcp/server.py

# 3. Register WB in Librarian projection and activate it
#    (via librarian_extension_register / librarian_extension_transition MCP tools)

# 4. Ingest sources and query
python3 -m src.projection.adapter  # projection reference (port 8766)
```

---

## License

Reference implementation of the Librarian extension governance model.

Extensions are not granted access. They establish a contract, declare capabilities, pass validation, and operate within defined ownership boundaries. The extension does not decide when it is available. Consumers do not query extensions directly to determine trust. The governance kernel projects the current capability state.
