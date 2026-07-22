# Working Bibliography Extension

**Reference implementation of the Librarian extension model.** A governed knowledge custody provider that demonstrates how external capabilities attach to the Librarian governance kernel through contracts, handshakes, and lifecycle management.

## What This Proves

An extension can be independently developed, governed, attached, detached, and validated **without becoming part of Librarian core**. The extension contract is the experiment — code only proves the contract is implementable.

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

## Architecture

```
Contract → Capability Declaration → Permission Validation
    ↓
Lifecycle Check (REGISTERED → ACTIVE → SUSPENDED → REVOKED)
    ↓
Enforcement (validator + boundary + drift)
    ↓
Tool Execution → Receipt Generation
```

### Key Documents

| Document | What It Defines |
|---|---|
| [EXTENSION-DEVELOPER-GUIDE.md](EXTENSION-DEVELOPER-GUIDE.md) | Step-by-step extension authoring guide |
| [docs/EXTENSION-SPECIFICATION-v1.md](docs/EXTENSION-SPECIFICATION-v1.md) | Formal extension compliance specification |
| [docs/COMPLIANCE-MATRIX.md](docs/COMPLIANCE-MATRIX.md) | Requirement-to-validator mapping |
| [MILESTONE-ROADMAP.md](MILESTONE-ROADMAP.md) | Project milestones and progress |
| [docs/identity/PROJECT-IDENTITY.md](docs/identity/PROJECT-IDENTITY.md) | Extension identity, purpose, non-goals |
| [docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json](docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json) | Formal contract with Librarian core |
| [docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md](docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md) | Handshake protocol specification |
| [docs/contracts/CAPABILITY-MANIFEST.md](docs/contracts/CAPABILITY-MANIFEST.md) | Capability declaration format |
| [docs/contracts/CONTRACT-BOUNDARIES.md](docs/contracts/CONTRACT-BOUNDARIES.md) | Ownership and prohibited domains |
| [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | System design and data flow |
| [docs/architecture/EXTENSION-PORT-MODEL.md](docs/architecture/EXTENSION-PORT-MODEL.md) | Extension port model |
| [docs/schemas/wb-artifact.schema.json](docs/schemas/wb-artifact.schema.json) | Artifact JSON Schema |
| [examples/minimal-extension/](examples/minimal-extension/) | Reusable extension starter template |

### Key Decisions (ADRs)

| ADR | Decision |
|---|---|
| ADR-WB-001 | The embedding is not the artifact |
| ADR-WB-002 | No custom custody model |
| ADR-WB-003 | Contract lives in extension repo |
| ADR-WB-004 | No Owner decisions from extension |
| ADR-WB-005 | Extension can mutate its own domain |
| ADR-WB-006 | EXTERNAL_REFERENCE custody mode |
| ADR-WB-007 | Embedding capability boundary |

## Extension Lifecycle

```
REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE
                                                     → SUSPENDED → REVOKED
```

Capabilities are only available in ACTIVE state. REVOKED is terminal.

## Relationship to Librarian

```
github.com/andrewdhannah/librarian                   ← Governance kernel
github.com/andrewdhannah/working-bibliography-extension  ← This repo (reference impl)
```

Librarian core validates extensions against contracts. This repository is the first proof that the extension contract is implementable by an independently developed capability.

## License

This project is a reference implementation of the Librarian extension model.
