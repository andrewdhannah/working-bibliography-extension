"""
Runtime Observer — Capture Current Extension State

Captures the extension's current runtime state for drift comparison.
This is the "what exists now?" step in the drift detection pipeline.

Observed state includes:
  - Identity (extension_id, version, contract_id)
  - Capability manifest (tools, risks, statuses)
  - Permissions config (allowed operations, forbidden list)
  - Contract document (version, document)
  - Lifecycle state
"""

import json
import os
from datetime import datetime, timezone


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class ObservedState:
    """Captured runtime state of the extension at a point in time."""

    def __init__(self):
        self.captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.identity = {}
        self.manifest = {}
        self.permissions = {}
        self.contract = {}
        self.lifecycle_state = "UNKNOWN"

    def to_dict(self) -> dict:
        return {
            "captured_at": self.captured_at,
            "identity": self.identity,
            "manifest": self.manifest,
            "permissions": self.permissions,
            "contract": self.contract,
            "lifecycle_state": self.lifecycle_state
        }


def observe() -> ObservedState:
    """Capture current runtime state of the extension."""
    state = ObservedState()

    # Identity from manifest
    manifest = _load_json("mcp", "capabilities.json")
    if manifest:
        state.manifest = manifest
        state.identity = manifest.get("identity", {})

    # Permissions
    permissions = _load_json("mcp", "permissions.json")
    if permissions:
        state.permissions = permissions

    # Contract document
    contract = _load_json("docs", "contracts", "WB-LIBRARIAN-CONTRACT-v1.json")
    if contract:
        state.contract = {
            "contract_id": contract.get("contract_id"),
            "contract_version": contract.get("version"),
            "contract_document": contract
        }

    # Lifecycle state
    state.lifecycle_state = _get_lifecycle_state()

    return state


def _load_json(*path_parts: str) -> dict:
    """Load a JSON file relative to project root."""
    path = os.path.join(PROJECT_ROOT, *path_parts)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _get_lifecycle_state() -> str:
    """Get the current lifecycle state from the handshake module."""
    try:
        import sys
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        from src.handshake import lifecycle
        state = lifecycle.get_current_state("working-bibliography-extension")
        return state["state"] if state else "UNKNOWN"
    except Exception:
        return "UNKNOWN"
