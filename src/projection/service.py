"""
Projection Service — Builds the Capability Projection from Extension State

Reads extension lifecycle state and capability manifests from registered
sources and produces the canonical capability projection.

This service is designed to be used in two modes:
  1. Librarian core mode: reads from the actual extension registry and
     handshake lifecycle storage
  2. Test/fixture mode: reads from provided fixture data

The service itself is consumer-agnostic — it does not know or care who
is requesting the projection.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from .schema import (
    CapabilityProjection, ExtensionEntry, CapabilityEntry,
    ExtensionState, CapabilityAvailability
)


class ProjectionService:
    """Builds capability projections from extension state sources.
    
    In Librarian core mode, the service reads from:
      - Extension registry (project_registry or node_registry)
      - Handshake lifecycle state (per-extension lifecycle files)
      - Capability manifests (per-extension mcp/capabilities.json)
    
    In test mode, the service reads from provided fixture data.
    """

    def __init__(self, state_source: Optional[dict] = None):
        """Initialize the projection service.
        
        Args:
            state_source: Optional dict of extension states for testing.
                          If None, reads from actual file system.
        """
        self._state_source = state_source
        self._providers = {}  # extension_id -> state provider

    def build_projection(self, known_projection_id: Optional[str] = None) -> CapabilityProjection:
        """Build the current capability projection.
        
        Args:
            known_projection_id: If provided, the service checks whether
                                 the projection has changed. If unchanged,
                                 returns a minimal "unchanged" response.
        
        Returns:
            CapabilityProjection with current extension states.
        """
        extensions = self._collect_extensions()
        projection = CapabilityProjection(extensions=extensions)

        # Check staleness
        if known_projection_id and known_projection_id == projection.projection_id:
            projection.status = "unchanged"
            projection.extensions = []  # Don't send data if unchanged

        return projection

    def _collect_extensions(self) -> list[ExtensionEntry]:
        """Collect all registered extensions with their states."""
        if self._state_source:
            return self._from_fixture(self._state_source)
        return self._from_live_sources()

    def _from_fixture(self, source: dict) -> list[ExtensionEntry]:
        """Build extension entries from fixture data."""
        entries = []
        for ext_data in source.get("extensions", []):
            entry = ExtensionEntry(
                extension_id=ext_data.get("extension_id", "unknown"),
                display_name=ext_data.get("display_name", ""),
                lifecycle=ExtensionState(ext_data.get("lifecycle", "not_registered")),
                contract_id=ext_data.get("contract_id", ""),
                contract_version=ext_data.get("contract_version", ""),
                registration_receipt=ext_data.get("registration_receipt", ""),
                revoked_at=ext_data.get("revoked_at"),
                suspended_at=ext_data.get("suspended_at"),
                historical_receipts_available=ext_data.get("historical_receipts_available", False),
            )
            # Add capabilities
            for cap_data in ext_data.get("capabilities", []):
                cap = CapabilityEntry(
                    name=cap_data.get("name", cap_data.get("id", "unknown")),
                    tools=cap_data.get("tools", []),
                    risk=cap_data.get("risk", "R0"),
                    status=cap_data.get("status", "active"),
                    availability=self._compute_availability(entry.lifecycle, cap_data.get("status", "active")),
                )
                entry.capabilities.append(cap)
            entries.append(entry)
        return entries

    def _from_live_sources(self) -> list[ExtensionEntry]:
        """Read from the actual file system (Librarian core mode).
        
        This reads from:
          - The handshake lifecycle state (receipts/handshake/)
          - The capability manifest (mcp/capabilities.json)
          - The extension registry (project index)
        
        Returns:
            List of ExtensionEntry objects.
        """
        entries = []
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Look for handshake lifecycle files
        hs_dir = os.path.join(root, "receipts", "handshake")
        if not os.path.exists(hs_dir):
            return entries  # No registered extensions

        for fname in os.listdir(hs_dir):
            if not fname.endswith("_lifecycle.json"):
                continue

            path = os.path.join(hs_dir, fname)
            try:
                with open(path) as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            ext_id = state.get("extension_id", "")
            current_state = state.get("state", "REGISTERED")

            # Map handshake state to projection state
            lifecycle_map = {
                "REGISTERED": ExtensionState.REGISTERED,
                "CONTRACT_VERIFIED": ExtensionState.CONTRACT_VERIFIED,
                "OWNER_APPROVED": ExtensionState.OWNER_APPROVED,
                "ACTIVE": ExtensionState.ACTIVE,
                "SUSPENDED": ExtensionState.SUSPENDED,
                "REVOKED": ExtensionState.REVOKED,
            }

            entry = ExtensionEntry(
                extension_id=ext_id,
                display_name=ext_id.replace("-", " ").title(),
                lifecycle=lifecycle_map.get(current_state, ExtensionState.UNKNOWN),
            )

            # Try to read capability manifest for this extension
            if entry.lifecycle == ExtensionState.ACTIVE:
                mcp_dir = os.path.join(root, "mcp", "capabilities.json")
                if os.path.exists(mcp_dir):
                    try:
                        with open(mcp_dir) as f:
                            manifest = json.load(f)
                        for cap in manifest.get("capabilities", []):
                            entry.capabilities.append(CapabilityEntry(
                                name=cap.get("id", "unknown"),
                                tools=cap.get("tools", []),
                                risk=cap.get("risk", "R0"),
                                status=cap.get("status", "active"),
                                availability=CapabilityAvailability.AVAILABLE,
                            ))
                    except (json.JSONDecodeError, IOError):
                        pass

            entries.append(entry)

        return entries

    def _compute_availability(self, state: ExtensionState, cap_status: str) -> CapabilityAvailability:
        """Compute capability availability from extension state."""
        if state == ExtensionState.ACTIVE and cap_status == "active":
            return CapabilityAvailability.AVAILABLE
        elif state == ExtensionState.SUSPENDED:
            return CapabilityAvailability.SUSPENDED
        elif state == ExtensionState.REVOKED:
            return CapabilityAvailability.REVOKED
        elif state in (ExtensionState.REGISTERED, ExtensionState.CONTRACT_VERIFIED):
            return CapabilityAvailability.NOT_APPROVED
        elif state == ExtensionState.OWNER_APPROVED:
            return CapabilityAvailability.UNAVAILABLE
        return CapabilityAvailability.UNKNOWN
