"""
Projection Schema — Data Models for Capability Projection

Defines the canonical data model for the capability projection artifact.
Every field and structure is documented for both machine and human readers.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import hashlib
import json
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────

class ExtensionState(str, Enum):
    """Lifecycle states an extension can be in, as seen by the projection."""
    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    CONTRACT_VERIFIED = "contract_verified"
    OWNER_APPROVED = "owner_approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CapabilityAvailability(str, Enum):
    """Whether a capability is available for use."""
    AVAILABLE = "available"        # Extension is ACTIVE, capability is declared
    UNAVAILABLE = "unavailable"     # Extension exists but not in ACTIVE state
    SUSPENDED = "suspended"         # Extension was ACTIVE, now suspended
    REVOKED = "revoked"            # Extension was terminated
    NOT_APPROVED = "not_approved"   # Extension registered but not yet approved
    UNKNOWN = "unknown"            # State cannot be determined


# ─── Data Models ─────────────────────────────────────────────────────

@dataclass
class CapabilityEntry:
    """A single declared capability within an extension."""
    name: str                              # Capability identifier (e.g., "artifact.read")
    tools: list[str] = field(default_factory=list)   # MCP tool names
    risk: str = "R0"                       # Risk classification
    status: str = "active"                 # active or pending
    availability: CapabilityAvailability = CapabilityAvailability.UNAVAILABLE

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tools": self.tools,
            "risk": self.risk,
            "status": self.status,
            "availability": self.availability.value
        }


@dataclass
class ExtensionEntry:
    """An extension registered in the governance system."""
    extension_id: str
    display_name: str = ""
    lifecycle: ExtensionState = ExtensionState.NOT_REGISTERED
    contract_id: str = ""
    contract_version: str = ""
    registration_receipt: str = ""
    capabilities: list[CapabilityEntry] = field(default_factory=list)
    revoked_at: Optional[str] = None
    suspended_at: Optional[str] = None
    historical_receipts_available: bool = False

    def to_dict(self) -> dict:
        result = {
            "extension_id": self.extension_id,
            "display_name": self.display_name,
            "lifecycle": self.lifecycle.value,
        }
        # Only include contract info if available
        if self.contract_id:
            result["contract_id"] = self.contract_id
        if self.contract_version:
            result["contract_version"] = self.contract_version
        if self.registration_receipt:
            result["registration_receipt"] = self.registration_receipt

        # Include capabilities only if active
        if self.lifecycle == ExtensionState.ACTIVE:
            result["capabilities"] = [c.to_dict() for c in self.capabilities]
        elif self.lifecycle == ExtensionState.REVOKED:
            result["historical_receipts_available"] = self.historical_receipts_available
            if self.revoked_at:
                result["revoked_at"] = self.revoked_at
        elif self.lifecycle == ExtensionState.SUSPENDED:
            if self.suspended_at:
                result["suspended_at"] = self.suspended_at

        return result


@dataclass
class CapabilityProjection:
    """The canonical capability projection artifact.
    
    This is a governance artifact, not an agent-specific protocol.
    Any consumer (AI agent, CLI, application, service) can read it.
    """
    projection_id: str = ""
    generated_at: str = ""
    authority: str = "librarian-core"
    extensions: list[ExtensionEntry] = field(default_factory=list)
    status: str = "current"
    extension_count: int = 0

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.projection_id:
            raw = f"CP:{self.generated_at}:{json.dumps([e.extension_id for e in self.extensions], sort_keys=True)}"
            h = hashlib.sha256(raw.encode()).hexdigest()[:16]
            date_part = self.generated_at[:10].replace("-", "")
            self.projection_id = f"CP-{date_part}-{h}"
        self.extension_count = len(self.extensions)

    def to_dict(self) -> dict:
        return {
            "projection_id": self.projection_id,
            "generated_at": self.generated_at,
            "authority": self.authority,
            "status": self.status,
            "extension_count": self.extension_count,
            "extensions": [e.to_dict() for e in self.extensions]
        }
