# Capability Manifest — Extension Declaration Format

**Sprint:** WB-EXTENSION-CONTRACT-1
**Status:** Ratified
**Contract:** `WB-LIBRARIAN-CONTRACT-v1`
**Date:** 2026-07-21

---

## 1. Purpose

The capability manifest is the extension's declaration of what it can do, what it requires, and what it will never do. It is presented during the handshake and verified against actual runtime behavior.

---

## 2. Manifest Structure

```json
{
  "manifest_version": "1.0.0",
  "extension_id": "working-bibliography-extension",
  "declared_at": "2026-07-21T18:00:00Z",

  "identity": {
    "extension_id": "working-bibliography-extension",
    "display_name": "Working Bibliography Extension",
    "version": "0.1.0",
    "classification": "knowledge_custody_provider",
    "domain": "knowledge_custody",
    "contract_id": "wb-librarian-contract-v1"
  },

  "capabilities": [ ... ],

  "forbidden_actions": [ ... ],

  "receipt_types": [ ... ],

  "dependencies": [
    { "type": "optional", "capability": "embedding_generation" }
  ]
}
```

---

## 3. Capability Declaration Fields

Each capability in the manifest must declare:

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | Yes | string | Unique capability identifier within extension |
| `display_name` | No | string | Human-readable name |
| `tools` | Yes | string[] | MCP tool names implementing this capability |
| `risk` | Yes | string | Risk classification (R0 or R1) |
| `description` | Yes | string | What this capability does |
| `permissions` | Yes | string[] | Required permission scopes |
| `input_schema` | No | object | Expected input structure (for verification) |
| `output_schema` | No | object | Expected output structure (for verification) |

### Risk Classifications

| Classification | Meaning | Gate |
|---|---|---|
| **R0** | Read-only, no state mutation | None |
| **R1** | State mutation within extension domain | Advisory — evidence logged |

### Permission Scopes

| Scope | Meaning |
|---|---|
| `read:artifacts` | Read artifact metadata and content |
| `read:index` | Search and read from knowledge index |
| `read:receipts` | Read receipt and history records |
| `write:artifacts` | Create new artifacts |
| `write:storage` | Write to extension storage domain |

---

## 4. Forbidden Action Declaration

Forbidden actions are declared statically in the manifest and enforced dynamically by the contract enforcer.

Each forbidden action entry includes:

| Field | Required | Description |
|---|---|---|
| `action` | Yes | The operation that is forbidden |
| `rationale` | Yes | Why this operation is forbidden |
| `violation_outcome` | Yes | SUSPENDED or REVOKED |

### Declared Forbidden Actions

```json
{
  "forbidden_actions": [
    {
      "action": "modify_librarian_authority_state",
      "rationale": "Extension must not write governance state",
      "violation_outcome": "REVOKE"
    },
    {
      "action": "create_owner_decisions",
      "rationale": "Extension must not originate authority actions",
      "violation_outcome": "REVOKE"
    },
    {
      "action": "mutate_sprint_ledger",
      "rationale": "Sprint ledger is core-controlled record",
      "violation_outcome": "REVOKE"
    },
    {
      "action": "accept_mutation_allowance",
      "rationale": "Extension operates in addon-owned space",
      "violation_outcome": "REVOKE"
    },
    {
      "action": "seal_production_receipts",
      "rationale": "Sealing is authority act",
      "violation_outcome": "REVOKE"
    },
    {
      "action": "delete_artifact_content",
      "rationale": "Content must persist for audit",
      "violation_outcome": "SUSPENDED"
    },
    {
      "action": "modify_artifact_provenance",
      "rationale": "Provenance is immutable after capture",
      "violation_outcome": "SUSPENDED"
    }
  ]
}
```

---

## 5. Working Bibliography Capability Manifest

The complete capability manifest for the current extension version:

```json
{
  "manifest_version": "1.0.0",
  "extension_id": "working-bibliography-extension",
  "declared_at": "2026-07-21T18:00:00Z",

  "identity": {
    "extension_id": "working-bibliography-extension",
    "display_name": "Working Bibliography Extension",
    "version": "0.1.0",
    "classification": "knowledge_custody_provider",
    "domain": "knowledge_custody",
    "contract_id": "wb-librarian-contract-v1",
    "contract_version": "1.0.0"
  },

  "capabilities": [
    {
      "id": "artifact.read",
      "display_name": "Read Artifact",
      "tools": ["wb_get_artifact", "wb_list_artifacts"],
      "risk": "R0",
      "description": "Read artifact metadata and content by ID. List all artifacts with optional filters.",
      "permissions": ["read:artifacts"]
    },
    {
      "id": "artifact.register",
      "display_name": "Register Artifact",
      "tools": ["wb_register_artifact"],
      "risk": "R1",
      "description": "Create a new governed artifact from captured source. Produces capture receipt.",
      "permissions": ["write:artifacts"]
    },
    {
      "id": "knowledge.search",
      "display_name": "Search Knowledge",
      "tools": ["wb_search_context"],
      "risk": "R0",
      "description": "Search governed knowledge artifacts. Returns matching content with artifact identity and provenance.",
      "permissions": ["read:index"]
    },
    {
      "id": "knowledge.retrieve",
      "display_name": "Retrieve Source",
      "tools": ["wb_retrieve_source"],
      "risk": "R0",
      "description": "Retrieve original source representation for a governed artifact.",
      "permissions": ["read:artifacts"]
    },
    {
      "id": "provenance.read",
      "display_name": "Read Provenance",
      "tools": ["wb_get_receipt", "wb_get_history"],
      "risk": "R0",
      "description": "Read evidence receipts and operational history for governed operations.",
      "permissions": ["read:receipts"]
    }
  ],

  "forbidden_actions": [
    { "action": "modify_librarian_authority_state", "rationale": "Extension must not write governance state", "violation_outcome": "REVOKE" },
    { "action": "create_owner_decisions", "rationale": "Extension must not originate authority actions", "violation_outcome": "REVOKE" },
    { "action": "mutate_sprint_ledger", "rationale": "Sprint ledger is core-controlled record", "violation_outcome": "REVOKE" },
    { "action": "accept_mutation_allowance", "rationale": "Extension operates in addon-owned space", "violation_outcome": "REVOKE" },
    { "action": "seal_production_receipts", "rationale": "Sealing is authority act", "violation_outcome": "REVOKE" },
    { "action": "delete_artifact_content", "rationale": "Content must persist for audit", "violation_outcome": "SUSPENDED" },
    { "action": "modify_artifact_provenance", "rationale": "Provenance is immutable after capture", "violation_outcome": "SUSPENDED" }
  ],

  "receipt_types": [
    {
      "type": "capture_receipt",
      "description": "Generated when a new artifact is captured",
      "key_fields": ["artifact_id", "content_hash", "source"]
    },
    {
      "type": "retrieval_receipt",
      "description": "Generated on knowledge retrieval",
      "key_fields": ["query", "artifact_references"]
    },
    {
      "type": "lifecycle_receipt",
      "description": "Generated on artifact lifecycle transition",
      "key_fields": ["artifact_id", "from_state", "to_state"]
    },
    {
      "type": "drift_receipt",
      "description": "Generated on drift detection",
      "key_fields": ["expected", "observed", "classification"]
    },
    {
      "type": "embedding_receipt",
      "description": "Generated on embedding creation",
      "key_fields": ["artifact_id", "model", "source_hash"]
    }
  ],

  "dependencies": [
    {
      "type": "optional",
      "capability": "embedding_generation",
      "description": "If an embedding capability provider is available, WB consumes it for vector generation. If absent, WB operates in text-only mode."
    }
  ]
}
```

---

## 6. Manifest Validation

The manifest is validated against the following rules at handshake time:

| Rule | What It Checks |
|---|---|
| M-001 | All required identity fields are present |
| M-002 | Extension_id matches the contract party |
| M-003 | Every declared tool in capabilities exists in `tools/list` |
| M-004 | No tool appears without a declared capability |
| M-005 | Forbidden actions match the contract |
| M-006 | Risk classification is valid (R0 or R1 only) |
| M-007 | Permission scopes are from the allowed set |
| M-008 | Receipt types match the contract |
| M-009 | Dependencies are optional — no hard requirements |

---

## 7. Manifest Evolution

| Version | Changes |
|---|---|
| 1.0.0 | Initial manifest — 5 capabilities, 7 forbidden actions, 5 receipt types |
