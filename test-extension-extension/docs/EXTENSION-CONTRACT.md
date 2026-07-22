{
  "contract_id": "test-extension-extension-contract-v1",
  "contract_type": "connector_custody",
  "version": "1.0.0",
  "stability": "MAJOR",
  "title": "Test Extension — Librarian Contract",
  "description": "Formal contract governing the test-extension-extension extension.",
  "parties": [
    {
      "role": "extension",
      "id": "test-extension-extension",
      "domain": "knowledge.testing"
    },
    {
      "role": "core",
      "id": "librarian",
      "domain": "governance_kernel"
    }
  ],
  "identity": {
    "extension_id": "test-extension-extension",
    "contract_id": "test-extension-extension-contract-v1",
    "contract_version": "1.0.0"
  },
  "capabilities": {
    "declarations": [
      {
        "capability_id": "search",
        "allowed_operations": ["item_search"],
        "risk_classification": "R0",
        "required_permissions": ["read:items"]
      }{% if not loop.last %},{% endif %}
    ]
  },
  "ownership": {
    "extension_owns": {
      "domains": ["knowledge.testing_artifacts", "knowledge.testing_metadata"]
    },
    "core_owns": {
      "domains": ["governance_authority", "owner_decisions", "project_lifecycle"]
    }
  },
  "forbidden_operations": {
    "absolute": [
      { "operation": "modify_librarian_authority_state", "rationale": "Never write governance state", "violation_outcome": "REVOKE" },
      { "operation": "create_owner_decisions", "rationale": "Owner decisions are core-only", "violation_outcome": "REVOKE" },
      { "operation": "mutate_sprint_ledger", "rationale": "Sprint ledger is core-controlled", "violation_outcome": "REVOKE" },
      { "operation": "delete_knowledge.testing_artifacts", "rationale": "Artifacts persist for audit", "violation_outcome": "SUSPENDED" }
    ]
  },
  "lifecycle": {
    "state_machine": [
      { "state": "REGISTERED", "meaning": "Identity known", "capabilities_active": false },
      { "state": "CONTRACT_VERIFIED", "meaning": "Contract validated", "capabilities_active": false },
      { "state": "OWNER_APPROVED", "meaning": "Owner authorized", "capabilities_active": false },
      { "state": "ACTIVE", "meaning": "Capabilities accessible", "capabilities_active": true },
      { "state": "SUSPENDED", "meaning": "Drift investigation", "capabilities_active": false },
      { "state": "REVOKED", "meaning": "Permanent termination", "capabilities_active": false }
    ],
    "transitions": [
      { "from": "REGISTERED", "to": "CONTRACT_VERIFIED", "trigger": "validation", "authority": "automated" },
      { "from": "CONTRACT_VERIFIED", "to": "OWNER_APPROVED", "trigger": "approval", "authority": "owner" },
      { "from": "OWNER_APPROVED", "to": "ACTIVE", "trigger": "activation", "authority": "automated" },
      { "from": "ACTIVE", "to": "SUSPENDED", "trigger": "drift", "authority": "automated_notify_owner" },
      { "from": "ACTIVE", "to": "REVOKED", "trigger": "violation", "authority": "owner" },
      { "from": "SUSPENDED", "to": "ACTIVE", "trigger": "restore", "authority": "owner" },
      { "from": "SUSPENDED", "to": "REVOKED", "trigger": "terminate", "authority": "owner" }
    ],
    "terminal_states": ["REVOKED"]
  },
  "evidence": {
    "receipt_types": [
      { "type": "operation_receipt", "required_fields": ["operation", "timestamp", "result"] }
    ]
  },
  "enforcement": {
    "drift_monitoring": "active",
    "review_frequency": "per_operation",
    "violation_outcomes": {
      "drift": "SUSPENDED",
      "contract_breach": "REVOKED"
    }
  }
}
