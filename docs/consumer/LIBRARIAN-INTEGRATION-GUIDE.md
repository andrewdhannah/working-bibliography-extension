# Librarian Integration Guide — Wiring the Capability Projection

**Sprint:** WB-LIBRARIAN-CAPABILITY-PROJECTION-1
**Status:** Reference for Librarian core maintainers
**Date:** 2026-07-21

---

## 1. Overview

The capability projection service (`src/projection/`) implements the projection logic that belongs on Librarian core. This guide documents exactly what needs to change in Librarian's `MCPController.swift` and `CapabilityMCPHandlers.swift` to wire the `librarian_capability_projection` tool.

---

## 2. Required Changes

### 2.1 Add Tool Definition to `buildToolList()`

In `MCPController.swift`, add the projection tool to the `buildToolList()` function:

```swift
// In buildToolList(), add:
MCPToolDefinition(
    name: "librarian_capability_projection",
    description: "Returns the current set of governed extensions with their lifecycle state and declared capabilities. Consumer-agnostic — works with AI agents, CLIs, applications, and services.",
    inputSchema: .object([
        "projection_id": .string(description: "Optional — if provided and still current, returns 'unchanged' with no extension data")
    ])
)
```

### 2.2 Add Handler to `handleCallTool()` Switch

Add a case to the `handleCallTool()` switch statement:

```swift
case "librarian_capability_projection":
    let projectionId = arguments?.value["projection_id"]?.stringValue
    let projection = try await capabilityProjectionService.buildProjection(
        knownProjectionId: projectionId
    )
    return projection.toJSONRPCResult()
```

### 2.3 Create Projection Service

Add a new service class `CapabilityProjectionService`:

```swift
// Sources/App/Services/CapabilityProjectionService.swift

actor CapabilityProjectionService {
    private let lifecycleStore: ExtensionLifecycleStore
    private let registryStore: ExtensionRegistryStore
    private var lastProjectionId: String = ""
    
    func buildProjection(knownProjectionId: String?) async throws -> CapabilityProjection {
        // 1. Collect all registered extensions
        let extensions = try await collectExtensions()
        
        // 2. Build projection
        let projection = CapabilityProjection(
            projectionId: generateProjectionId(extensions: extensions),
            generatedAt: ISO8601DateFormatter().string(from: Date()),
            authority: "librarian-core",
            extensions: extensions
        )
        
        // 3. Check staleness
        if let knownId = knownProjectionId, knownId == projection.projectionId {
            return CapabilityProjection.unchanged(projectionId: projection.projectionId)
        }
        
        return projection
    }
    
    private func collectExtensions() async throws -> [ExtensionProjection] {
        // Read from lifecycle store + capability registry
        // See schema definitions in src/projection/schema.py
    }
}
```

### 2.4 Data Models

Swift versions of the Python data models:

```swift
struct CapabilityProjection: Codable {
    let projectionId: String
    let generatedAt: String
    let authority: String
    let status: String       // "current" or "unchanged"
    let extensionCount: Int
    let extensions: [ExtensionProjection]
    
    static func unchanged(projectionId: String) -> CapabilityProjection {
        CapabilityProjection(
            projectionId: projectionId,
            generatedAt: ISO8601DateFormatter().string(from: Date()),
            authority: "librarian-core",
            status: "unchanged",
            extensionCount: 0,
            extensions: []
        )
    }
}

struct ExtensionProjection: Codable {
    let extensionId: String
    let displayName: String
    let lifecycle: String         // "active", "suspended", etc.
    let contractId: String?
    let contractVersion: String?
    let registrationReceipt: String?
    let capabilities: [CapabilityProjectionEntry]?
    let historicalReceiptsAvailable: Bool?
    let revokedAt: String?
    let suspendedAt: String?
}

struct CapabilityProjectionEntry: Codable {
    let name: String
    let tools: [String]
    let risk: String
    let status: String
    let availability: String
}
```

---

## 3. Projection Logic (Reference)

The projection logic is implemented in `src/projection/service.py`. The key rules are:

| Extension State | In Projection? | Capabilities Listed? | Availability |
|---|---|---|---|
| ACTIVE | Yes | Yes (active only) | `available` |
| SUSPENDED | Yes | No | `suspended` |
| REVOKED | Yes (historical) | No | `revoked` |
| REGISTERED | Yes (info only) | No | `not_approved` |
| CONTRACT_VERIFIED | Yes (info only) | No | `not_approved` |
| OWNER_APPROVED | Yes (info only) | No | `unavailable` |
| Not registered | No | — | — |

### Staleness Detection

The projection ID changes whenever:
- An extension transitions lifecycle state
- A new extension is registered
- An extension changes its capability manifest

Format: `CP-{yyyymmdd}-{sha256hash[:16]}`

When `knownProjectionId` matches the current projection ID, return `status: "unchanged"` with no extension data to minimize response size.

---

## 4. Source Locations

| Data Source | Librarian Equivalent | Notes |
|---|---|---|
| Extension lifecycle state | `receipts/handshake/*_lifecycle.json` | Per-extension lifecycle files |
| Capability manifest | `mcp/capabilities.json` | Per-extension capability declarations |
| Extension identity | Project registry / node registry | Extension registration records |
| Projection schema | `src/projection/schema.py` | Python reference (port to Swift) |
| Projection logic | `src/projection/service.py` | Python reference (port to Swift) |

---

## 5. Testing Without Librarian Changes

Run the standalone projection server for testing:

```bash
# With default fixture (reads from live file system)
python3 -m src.projection.adapter

# Or with a specific fixture
python3 -c "
from src.projection.adapter import start_projection_server
from src.projection.tests.fixtures import basic_fixture
start_projection_server(state_source=basic_fixture())
"
```

Then query as any consumer would:

```bash
# Get full projection
curl -X POST http://127.0.0.1:8766/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"librarian_capability_projection","arguments":{}}}'

# Check staleness
curl -X POST http://127.0.0.1:8766/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":2,"params":{"name":"librarian_capability_projection","arguments":{"projection_id":"CP-20260721-..."}}}'

# List available tools
curl -X POST http://127.0.0.1:8766/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":3}'
```

---

## 6. Integration Checklist

- [ ] `MCPToolDefinition` added to `buildToolList()`
- [ ] `case "librarian_capability_projection":` in `handleCallTool()` switch
- [ ] `CapabilityProjectionService` created
- [ ] Extension lifecycle state readable from handshake store
- [ ] Capability manifests readable from registered extensions
- [ ] Projection ID generation with staleness detection
- [ ] All 7 extension states represented
- [ ] Consumer-agnostic — no consumer identity assumptions
- [ ] Tested with standalone server before Librarian integration
