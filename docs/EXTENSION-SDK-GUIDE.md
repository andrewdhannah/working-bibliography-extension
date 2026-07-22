# Extension SDK Guide — Creating Librarian-Compatible Extensions

**Sprint:** WB-EXTENSION-SDK-1
**Status:** Draft
**Date:** 2026-07-21

---

## 1. Overview

The Extension SDK generates a contract-compliant Librarian extension skeleton. Generated extensions start in REGISTERED state and require handshake completion, contract verification, and owner approval before capabilities are activated.

### The SDK Flow

```
Developer Intent
    ↓
SDK Generator
    ↓
Extension Scaffold (REGISTERED)
    ↓
Developer Implements Capabilities
    ↓
Contract Verification
    ↓
Owner Approval
    ↓
ACTIVE — Ecosystem Participant
```

### Key Invariants

| Invariant | Description |
|---|---|
| SDK cannot bypass governance | Generated extensions start REGISTERED, not ACTIVE |
| Generated extensions inherit boundaries | Contract includes standard forbidden operations |
| SDK is not authority | SDK produces declarations; Librarian evaluates |

---

## 2. Quick Start

```bash
# Generate an extension
python3 -m src.sdk.generator \
    --name citation-manager \
    --domain knowledge.reference \
    --capability "search,Search Citations,R0,read:citations,citation_search" \
    --capability "export,Export Citations,R1,write:citations,citation_export" \
    --dependency embedding.generate

# Navigate to generated extension
cd citation-manager-extension

# Copy handshake implementation from reference
cp -r ../working-bibliography-extension/src/handshake/* src/handshake/

# Run validation
python3 -m src.validation.fixture_runner

# Start MCP server (REGISTERED state)
python3 src/mcp/server.py
```

---

## 3. Generator Inputs

| Input | Required | Description | Example |
|---|---|---|---|
| `--name` | Yes | Extension identifier | `citation-manager` |
| `--domain` | Yes | Capability domain | `knowledge.reference` |
| `--capability` | Repeatable | Capability definition | `search,Search,R0,read:items,item_search` |
| `--dependency` | Repeatable | Optional provider dependency | `embedding.generate` |
| `--output` | No | Output directory | `./extensions/` |
| `--port` | No | MCP server port | `9000` |

### Capability Format

```text
name,Display Name,Risk,Permission,Tool
```

| Field | Description | Example |
|---|---|---|
| `name` | Capability identifier | `search` |
| `Display Name` | Human-readable name | `Search Citations` |
| `Risk` | R0 or R1 | `R0` |
| `Permission` | Permission scope | `read:citations` |
| `Tool` | MCP tool name | `citation_search` |

### Namespace Rules

- Capability names should use `domain.action` format (e.g., `knowledge.search`)
- Tool names should use the extension's prefix (e.g., `citation_search`)
- Generic capability names (`search`, `read`, `write`) are discouraged

---

## 4. Generated Structure

```
my-extension-extension/
├── .librarian/
│   └── extension.json          # Extension registration
├── docs/
│   ├── PROJECT-IDENTITY.md     # Identity and purpose
│   ├── EXTENSION-CONTRACT.md   # Hardcoded contract
│   └── CAPABILITY-MANIFEST.md  # Capability descriptions
├── mcp/
│   ├── capabilities.json       # Capability manifest
│   └── permissions.json        # Permission boundaries
├── src/
│   ├── mcp/
│   │   └── server.py           # MCP server scaffold
│   ├── handshake/
│   │   └── README.md           # Reference to copy from
│   └── validation/
│       └── README.md           # Reference to copy from
├── tests/
│   └── fixtures/
│       └── identity-valid.json # Validation fixture
├── receipts/                   # Receipt storage
└── README.md                   # Quick start guide
```

### Files to Implement

| File | Action |
|---|---|
| `src/mcp/server.py` | Add domain logic to tool handlers |
| `src/handshake/` | Copy from Working Bibliography reference |
| `src/validation/` | Copy from Working Bibliography reference |

### Files That Are Ready

| File | Status |
|---|---|
| `mcp/capabilities.json` | Generated with declared capabilities (pending) |
| `mcp/permissions.json` | Generated with permission boundaries |
| `docs/EXTENSION-CONTRACT.md` | Generated with contract structure |
| `tests/fixtures/identity-valid.json` | Generated with extension identity |

---

## 5. Implementation Sequence

### Step 1 — Copy Handshake

```bash
cp -r ../working-bibliography-extension/src/handshake/* src/handshake/
```

Initialize lifecycle state:
```python
from handshake import lifecycle
lifecycle.initialize_state("my-extension-extension")
# → REGISTERED
```

### Step 2 — Implement MCP Tools

Edit `src/mcp/server.py`:
- Add domain logic to tool handlers
- Implement your extension's unique functionality
- Generate operation receipts for each tool call

### Step 3 — Run Validation

```bash
python3 -m src.validation.fixture_runner
```

Ensure all validation domains pass:
- Identity validation
- Contract validation
- Capability validation
- Lifecycle validation
- Permission validation

### Step 4 — Request Approval

The extension is now ready for contract verification and owner approval.
Submit to the Librarian governance kernel for evaluation.

---

## 6. Compliance Checklist

Before requesting activation:

- [ ] Identity document matches contract
- [ ] Capability manifest matches implementation
- [ ] Contract has all required sections
- [ ] MCP server starts and responds to `tools/list`
- [ ] Handshake completes to REGISTERED
- [ ] Forbidden operations are declared
- [ ] Receipts are generated per operation
- [ ] Validation suite passes all checks
- [ ] Extension starts in REGISTERED state

---

## 7. Reference Implementation

The complete reference implementation is the Working Bibliography Extension:

```
github.com/andrewdhannah/working-bibliography-extension
```

Use it for:
- Handshake implementation reference
- MCP server patterns
- Enforcement pipeline
- Drift detection
- Revocation handling
- Validation fixtures
