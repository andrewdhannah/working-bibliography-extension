"""
Test fixtures for capability projection scenarios.
Each fixture simulates a different extension state configuration.
"""


def empty_projection():
    """No extensions registered at all."""
    return {"extensions": []}


def registered_only():
    """Extension registered but not verified."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "registered",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "capabilities": []
            }
        ]
    }


def contract_verified():
    """Extension verified but not approved."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "contract_verified",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-test",
                "capabilities": []
            }
        ]
    }


def owner_approved():
    """Extension approved but not yet active."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "owner_approved",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-test",
                "capabilities": []
            }
        ]
    }


def active_with_capabilities():
    """Extension active with declared capabilities."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "active",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-test",
                "capabilities": [
                    {
                        "name": "artifact.read",
                        "tools": ["wb_get_artifact", "wb_list_artifacts"],
                        "risk": "R0",
                        "status": "active"
                    },
                    {
                        "name": "artifact.register",
                        "tools": ["wb_register_artifact"],
                        "risk": "R1",
                        "status": "active"
                    },
                    {
                        "name": "knowledge.search",
                        "tools": ["wb_search_context"],
                        "risk": "R0",
                        "status": "active"
                    }
                ]
            }
        ]
    }


def suspended():
    """Extension suspended due to drift."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "suspended",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-test",
                "suspended_at": "2026-07-21T18:00:00Z",
                "capabilities": []
            }
        ]
    }


def revoked():
    """Extension permanently revoked."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "revoked",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-test",
                "revoked_at": "2026-07-21T18:00:00Z",
                "historical_receipts_available": True,
                "capabilities": []
            }
        ]
    }


def multiple_extensions():
    """Multiple extensions in different lifecycle states."""
    return {
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "active",
                "contract_id": "wb-librarian-contract-v1",
                "contract_version": "1.0.0",
                "registration_receipt": "rcp-wb-registration-001",
                "capabilities": [
                    {
                        "name": "artifact.read",
                        "tools": ["wb_get_artifact"],
                        "risk": "R0",
                        "status": "active"
                    },
                    {
                        "name": "knowledge.search",
                        "tools": ["wb_search_context"],
                        "risk": "R0",
                        "status": "active"
                    }
                ]
            },
            {
                "extension_id": "runtime-node",
                "display_name": "Librarian Runtime Node",
                "lifecycle": "active",
                "capabilities": [
                    {
                        "name": "model.execute",
                        "tools": ["model_execute"],
                        "risk": "R1",
                        "status": "active"
                    }
                ]
            },
            {
                "extension_id": "qa-pilot",
                "display_name": "QA Pilot",
                "lifecycle": "registered",
                "capabilities": []
            }
        ]
    }


def mixed_states():
    """Extensions in various states — active, suspended, revoked."""
    return {
        "extensions": [
            {
                "extension_id": "extension-a",
                "display_name": "Extension A (Active)",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "a.read", "tools": ["a_get"], "risk": "R0", "status": "active"}
                ]
            },
            {
                "extension_id": "extension-b",
                "display_name": "Extension B (Suspended)",
                "lifecycle": "suspended",
                "suspended_at": "2026-07-21T18:00:00Z",
                "capabilities": []
            },
            {
                "extension_id": "extension-c",
                "display_name": "Extension C (Revoked)",
                "lifecycle": "revoked",
                "revoked_at": "2026-07-21T18:00:00Z",
                "historical_receipts_available": True,
                "capabilities": []
            }
        ]
    }
