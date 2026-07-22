"""
Multi-Extension Composition Fixtures — Three Extension Domains

Working Bibliography (knowledge.reference)
Runtime Node (model.execution)
QA Pilot (validation.testing)
"""


def all_active():
    """All three extensions active with capabilities."""
    return {
        "projection_id": "CP-20260721-100",
        "generated_at": "2026-07-21T18:00:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "knowledge.search", "tools": ["wb_search"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "knowledge.retrieve", "tools": ["wb_retrieve"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "knowledge.provenance", "tools": ["wb_get_provenance"], "risk": "R0", "status": "active", "availability": "available"},
                ]
            },
            {
                "extension_id": "runtime-node",
                "display_name": "Runtime Node",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "model.list", "tools": ["model_list"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "model.qualify", "tools": ["model_qualify"], "risk": "R1", "status": "active", "availability": "available"},
                    {"name": "model.execute", "tools": ["model_execute"], "risk": "R1", "status": "active", "availability": "available"},
                ]
            },
            {
                "extension_id": "qa-pilot",
                "display_name": "QA Pilot",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "test.run", "tools": ["test_run"], "risk": "R1", "status": "active", "availability": "available"},
                    {"name": "test.report", "tools": ["test_report"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "test.validate", "tools": ["test_validate"], "risk": "R1", "status": "active", "availability": "available"},
                ]
            },
        ]
    }


def mixed_lifecycle():
    """Extensions in different lifecycle states."""
    return {
        "projection_id": "CP-20260721-101",
        "generated_at": "2026-07-21T18:05:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "knowledge.search", "tools": ["wb_search"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "knowledge.retrieve", "tools": ["wb_retrieve"], "risk": "R0", "status": "active", "availability": "available"},
                ]
            },
            {
                "extension_id": "runtime-node",
                "display_name": "Runtime Node",
                "lifecycle": "suspended",
                "suspended_at": "2026-07-21T18:05:00Z",
            },
            {
                "extension_id": "qa-pilot",
                "display_name": "QA Pilot",
                "lifecycle": "contract_verified",
            },
        ]
    }


def collision():
    """Two extensions claiming the same capability name."""
    return {
        "projection_id": "CP-20260721-102",
        "generated_at": "2026-07-21T18:10:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "extension-a",
                "display_name": "Extension A",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "document.search", "tools": ["doc_search"], "risk": "R0", "status": "active", "availability": "available"},
                ]
            },
            {
                "extension_id": "extension-b",
                "display_name": "Extension B",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "document.search", "tools": ["doc_search_v2"], "risk": "R0", "status": "active", "availability": "available"},
                ]
            },
        ]
    }


def wb_removed():
    """Working Bibliography removed from projection entirely."""
    return {
        "projection_id": "CP-20260721-103",
        "generated_at": "2026-07-21T18:15:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "runtime-node",
                "display_name": "Runtime Node",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "model.execute", "tools": ["model_execute"], "risk": "R1", "status": "active", "availability": "available"},
                ]
            },
        ]
    }
