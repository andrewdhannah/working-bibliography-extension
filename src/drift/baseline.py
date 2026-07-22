"""
Baseline Capture — Freeze Approved Extension State

Captures the extension's approved state at handshake completion (OWNER_APPROVED
or ACTIVE). This baseline is the reference point for all future drift comparisons.

Baseline stores hashes of:
  - Extension identity (extension_id, version, contract_id)
  - Capability manifest (tool names, risk levels, status)
  - Permission config (allowed operations, risk classifications)
  - Contract document (full contract hash)

The baseline is captured once and compared on every drift scan.
"""

import json
import os
import hashlib
from datetime import datetime, timezone


BASELINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "baseline")


class Baseline:
    """Captured approved state of the extension at a point in time."""

    def __init__(self, extension_id: str, contract_id: str, contract_version: str,
                 manifest: dict, permissions: dict, contract: dict):
        self.extension_id = extension_id
        self.contract_id = contract_id
        self.contract_version = contract_version
        self.captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Identity baseline
        self.identity = {
            "extension_id": extension_id,
            "contract_id": contract_id,
            "contract_version": contract_version
        }
        self.identity_hash = self._hash_dict(self.identity)

        # Capability manifest baseline
        self.manifest_tools = self._extract_tools(manifest)
        self.manifest_risks = self._extract_risks(manifest)
        self.manifest_statuses = self._extract_statuses(manifest)
        self.manifest_hash = self._hash_dict({
            "tools": self.manifest_tools,
            "risks": self.manifest_risks,
            "statuses": self.manifest_statuses
        })

        # Permission baseline
        self.allowed_operations = self._extract_permissions(permissions)
        self.forbidden_operations = permissions.get("forbidden_operations", [])
        self.permissions_hash = self._hash_dict({
            "allowed": self.allowed_operations,
            "forbidden": self.forbidden_operations
        })

        # Contract baseline
        self.contract_document = contract
        self.contract_hash = self._hash_dict(contract)

    def _hash_dict(self, data: dict) -> str:
        """Generate a SHA-256 hash of a dictionary."""
        serialized = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _extract_tools(self, manifest: dict) -> dict:
        """Extract tool names grouped by capability ID."""
        tools = {}
        for cap in manifest.get("capabilities", []):
            tools[cap.get("id")] = sorted(cap.get("tools", []))
        return tools

    def _extract_risks(self, manifest: dict) -> dict:
        """Extract risk levels per capability."""
        risks = {}
        for cap in manifest.get("capabilities", []):
            risks[cap.get("id")] = cap.get("risk")
        return risks

    def _extract_statuses(self, manifest: dict) -> dict:
        """Extract status per capability."""
        statuses = {}
        for cap in manifest.get("capabilities", []):
            statuses[cap.get("id")] = cap.get("status")
        return statuses

    def _extract_permissions(self, permissions: dict) -> dict:
        """Extract allowed operations with their risk levels."""
        ops = {}
        for scope, config in permissions.get("allowed_operations", {}).items():
            ops[scope] = {
                "tools": config.get("tools", []),
                "risk": config.get("risk")
            }
        return ops

    def to_dict(self) -> dict:
        """Serialize baseline for storage."""
        return {
            "extension_id": self.extension_id,
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "captured_at": self.captured_at,
            "identity": self.identity,
            "identity_hash": self.identity_hash,
            "manifest_hash": self.manifest_hash,
            "manifest_tools": self.manifest_tools,
            "manifest_risks": self.manifest_risks,
            "manifest_statuses": self.manifest_statuses,
            "permissions_hash": self.permissions_hash,
            "allowed_operations": self.allowed_operations,
            "forbidden_operations": self.forbidden_operations,
            "contract_hash": self.contract_hash,
            "contract_document": self.contract_document,
            "enforcement": self.contract_document.get("enforcement", {}),
            "baseline_hash": self._hash_dict({
                "identity_hash": self.identity_hash,
                "manifest_hash": self.manifest_hash,
                "permissions_hash": self.permissions_hash,
                "contract_hash": self.contract_hash
            })
        }


def capture_baseline(extension_id: str = "working-bibliography-extension") -> Baseline:
    """Capture the current extension state as an approved baseline.

    Reads the contract, manifest, and permissions from their canonical
    locations and freezes them as the reference state.

    Called once at handshake completion (OWNER_APPROVED → ACTIVE transition).
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Load contract
    contract_path = os.path.join(root, "docs", "contracts", "WB-LIBRARIAN-CONTRACT-v1.json")
    with open(contract_path) as f:
        contract = json.load(f)

    # Load manifest
    manifest_path = os.path.join(root, "mcp", "capabilities.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Load permissions
    permissions_path = os.path.join(root, "mcp", "permissions.json")
    with open(permissions_path) as f:
        permissions = json.load(f)

    baseline = Baseline(
        extension_id=extension_id,
        contract_id=contract.get("contract_id", "wb-librarian-contract-v1"),
        contract_version=contract.get("version", "1.0.0"),
        manifest=manifest,
        permissions=permissions,
        contract=contract
    )

    return baseline


def store_baseline(baseline: Baseline):
    """Persist a baseline to disk."""
    os.makedirs(BASELINE_DIR, exist_ok=True)
    path = os.path.join(BASELINE_DIR, f"{baseline.extension_id}_baseline.json")
    with open(path, "w") as f:
        json.dump(baseline.to_dict(), f, indent=2)
    return path


def load_baseline(extension_id: str = "working-bibliography-extension") -> dict:
    """Load the stored baseline for an extension."""
    path = os.path.join(BASELINE_DIR, f"{extension_id}_baseline.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def baseline_exists(extension_id: str = "working-bibliography-extension") -> bool:
    """Check if a baseline exists for the extension."""
    return load_baseline(extension_id) is not None
