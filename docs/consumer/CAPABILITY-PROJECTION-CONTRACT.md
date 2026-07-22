# Capability Projection Contract — Consumer-Extension Awareness Protocol

**Sprint:** WB-CONSUMER-CAPABILITY-DISCOVERY-1 (definition) / WB-LIBRARIAN-CAPABILITY-PROJECTION-1 (implementation)
**Status:** Draft — requires Owner authorization
**Date:** 2026-07-21

---

## 1. Purpose

Defines the contract between the Librarian core (as capability authority) and any consumer (AI agent, CLI, application, service) that needs to discover available governed extensions and their lifecycle state.

Per ADR-WB-008: The consumer is not part of the trust chain. It is a requesting actor.

---

## 2. Protocol

### MCP Tool: `librarian_capability_projection`

**Risk classification:** R0 (read-only, no state mutation)

**Purpose:** Returns the current set of governed extensions with their lifecycle state and declared capabilities. Any MCP client can call this tool — it is not specific to any agent or application.

**Input:**

```json
{
  "projection_id": "optional — if provided, returns unchanged status if still current"
}
```

**Output:**

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
        }
      ]
    }
  ]
}
```

### Conditionals

| Input | Response |
|---|---|
| No projection_id | Full projection returned |
| projection_id matches current | `{"status": "unchanged", "projection_id": "CP-..."}` — no extension data |
| projection_id does not match current | Full projection returned with new ID |

---

## 3. Projection Rules

### Inclusion Rules

| Extension State | Included? | Capabilities Listed? | Executable? |
|---|---|---|---|
| ACTIVE | Yes | Yes (active only) | Yes |
| SUSPENDED | Yes | No | No |
| REVOKED | Yes (historical marker) | No | No |
| REGISTERED | Yes (info only) | No | No |
| CONTRACT_VERIFIED | Yes (info only) | No | No |
| OWNER_APPROVED | Yes (info only) | No | No |
| Not registered | No | — | — |

### Historical Access

When an extension is REVOKED, the projection includes:

```json
{
  "extension_id": "working-bibliography-extension",
  "lifecycle": "REVOKED",
  "revoked_at": "2026-07-21T18:00:00Z",
  "historical_receipts_available": true
}
```

No capabilities are listed. The consumer cannot execute any operations but can reference historical receipts.

---

## 4. Staleness Detection

### Projection ID

Each projection has a unique `projection_id`:

```
CP-{yyyymmdd}-{seq}
```

The ID changes whenever:
- An extension transitions lifecycle state
- A new extension is registered
- An extension's capability manifest changes
- An extension's contract version changes

### Consumer Detection

The consumer detects staleness by:
1. **Caching** the `projection_id` from the last fetch
2. **Comparing** on next call with `projection_id` parameter
3. **Refreshing** if the server returns a new projection (or `status: "unchanged"` if still current)

---

## 5. Pre-Execution Verification

For R1+ capabilities, the consumer should verify before execution:

```
Consumer has cached: WB is ACTIVE, wb_search_context is available

Consumer wants to call wb_search_context()

Verification step:
    1. Check projection freshness (or call with current projection_id)
    2. Confirm extension is still ACTIVE
    3. Confirm capability is still in projection
    4. Confirm capability is executable

    ├── All pass → Execute via MCP
    │
    └── Any fail → Do not execute, explain limitation
```

---

## 6. Error Handling

| Scenario | Projection Response | Consumer Behavior |
|---|---|---|
| Librarian unreachable | No response | Assume no capabilities, proceed with available context |
| Projection service unavailable | Timeout or error | Use last known projection (mark as potentially stale) |
| Extension in invalid state | Not in projection | Don't use, don't mention |
| Requested tool not in projection | Not returned | Don't use |
| projection_id mismatch | New projection returned | Refresh and re-evaluate |

---

## 7. Contract Invariants

| Invariant | Description |
|---|---|
| CP-001 | The projection is the single source of truth for capability awareness |
| CP-002 | Extensions do not appear in the projection until registered in Librarian |
| CP-003 | Extensions do not appear as executable until ACTIVE |
| CP-004 | SUSPENDED extensions lose executable capabilities immediately |
| CP-005 | REVOKED extensions appear as historical only |
| CP-006 | Consumer must never use a capability not in its current projection |
| CP-007 | Projection staleness must be detectable via projection_id |
| CP-008 | R1+ capabilities should trigger pre-execution verification |
| CP-009 | The projection is consumer-agnostic — any MCP client can request it |
