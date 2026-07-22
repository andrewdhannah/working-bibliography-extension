"""
Consumer Context — Internal Representation Built from Capability Projection

Defines how any consumer (AI agent, CLI, application, service) builds and
maintains its understanding of available governed capabilities from the
Librarian capability projection.

Key invariant (ADR-WB-009):
  Consumer context is DERIVED state. It is never authority.
  The projection is a snapshot. The Librarian always decides.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import json


@dataclass
class CapabilityRef:
    """A capability the consumer knows about from the projection."""
    extension_id: str
    capability_name: str
    tools: list[str]
    risk: str
    available: bool  # True if extension is ACTIVE and capability is active
    availability_reason: str = ""  # Why it's unavailable (suspended, revoked, etc.)

    def to_dict(self) -> dict:
        return {
            "extension_id": self.extension_id,
            "capability": self.capability_name,
            "tools": self.tools,
            "risk": self.risk,
            "available": self.available,
            "availability_reason": self.availability_reason
        }


@dataclass
class ExtensionInfo:
    """Information about an extension in the consumer's context."""
    extension_id: str
    display_name: str
    lifecycle: str
    available: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "extension_id": self.extension_id,
            "display_name": self.display_name,
            "lifecycle": self.lifecycle,
            "available": self.available,
            "reason": self.reason
        }

    def explanation(self) -> str:
        """Human-readable explanation of this extension's state."""
        if self.lifecycle == "active":
            return f"{self.display_name} is available."
        elif self.lifecycle == "suspended":
            return f"{self.display_name} is currently suspended and not available."
        elif self.lifecycle == "revoked":
            return f"{self.display_name} has been revoked. Historical records only."
        elif self.lifecycle == "registered":
            return f"{self.display_name} is discovered but not yet active."
        elif self.lifecycle == "contract_verified":
            return f"{self.display_name} contract verified, awaiting approval."
        elif self.lifecycle == "owner_approved":
            return f"{self.display_name} approved, not yet activated."
        else:
            return f"{self.display_name} is in unknown state ({self.lifecycle})."


@dataclass
class ConsumerContext:
    """The consumer's understanding of available governed capabilities.
    
    This is DERIVED state. It is built from the Librarian capability
    projection and is never authoritative. The consumer must refresh
    when the projection changes.
    """
    projection_id: str = ""
    projection_timestamp: str = ""
    capabilities: dict[str, CapabilityRef] = field(default_factory=dict)
    # index by extension_id
    extensions: dict[str, ExtensionInfo] = field(default_factory=dict)
    # Tools not in projection (to prevent invention)
    _known_tools: set[str] = field(default_factory=set)

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is in the current capability context."""
        return tool_name in self._known_tools

    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool can be executed right now."""
        for cap_ref in self.capabilities.values():
            if tool_name in cap_ref.tools:
                return cap_ref.available
        return False

    def get_extension_info(self, extension_id: str) -> Optional[ExtensionInfo]:
        """Get information about an extension by ID."""
        return self.extensions.get(extension_id)

    def get_unavailable_reason(self, tool_name: str) -> str:
        """Get the reason a tool is unavailable."""
        for cap_ref in self.capabilities.values():
            if tool_name in cap_ref.tools:
                return cap_ref.availability_reason
        return "Tool not found in any declared capability"

    def get_available_extensions(self) -> list[ExtensionInfo]:
        """Get list of extensions with currently available capabilities."""
        return [e for e in self.extensions.values() if e.available]

    def get_unavailable_extensions(self) -> list[ExtensionInfo]:
        """Get list of extensions that are registered but not available."""
        return [e for e in self.extensions.values() if not e.available]

    def to_dict(self) -> dict:
        return {
            "projection_revision": self.projection_timestamp,
            "projection_id": self.projection_id,
            "capabilities": [c.to_dict() for c in self.capabilities.values()],
            "extensions": [e.to_dict() for e in self.extensions.values()],
            "unavailable": [
                {
                    "extension_id": e.extension_id,
                    "reason": e.reason or e.lifecycle
                }
                for e in self.extensions.values() if not e.available
            ]
        }

    def summary(self) -> str:
        """Human-readable summary of the capability context."""
        available = self.get_available_extensions()
        unavailable = self.get_unavailable_extensions()

        parts = []
        if available:
            parts.append(f"Available: {', '.join(e.display_name for e in available)}")
        if unavailable:
            for e in unavailable:
                parts.append(f"Unavailable: {e.explanation()}")
        return "\n".join(parts) if parts else "No governed capabilities registered."


def build_context_from_projection(projection_data: dict) -> ConsumerContext:
    """Build a ConsumerContext from a capability projection.
    
    This is the consumer-side entry point. Any consumer (AI agent, CLI,
    application, service) calls this function with the projection data
    from librarian_capability_projection().
    
    Args:
        projection_data: The dict returned by the Librarian projection tool
    
    Returns:
        ConsumerContext with available capabilities and known tools.
    """
    ctx = ConsumerContext(
        projection_id=projection_data.get("projection_id", ""),
        projection_timestamp=projection_data.get("generated_at", ""),
    )

    for ext_data in projection_data.get("extensions", []):
        ext_id = ext_data.get("extension_id", "unknown")
        lifecycle = ext_data.get("lifecycle", "unknown")
        is_active = lifecycle == "active"

        info = ExtensionInfo(
            extension_id=ext_id,
            display_name=ext_data.get("display_name", ext_id),
            lifecycle=lifecycle,
            available=False,
        )

        if lifecycle == "active":
            info.available = True
            info.reason = ""
        elif lifecycle == "suspended":
            info.reason = "SUSPENDED"
        elif lifecycle == "revoked":
            info.reason = "REVOKED"
        elif lifecycle == "registered":
            info.reason = "not yet active"
        elif lifecycle == "contract_verified":
            info.reason = "contract verified, awaiting approval"
        elif lifecycle == "owner_approved":
            info.reason = "approved, not yet activated"
        else:
            info.reason = f"unknown state: {lifecycle}"

        ctx.extensions[ext_id] = info

        # Add capabilities
        for cap_data in ext_data.get("capabilities", []):
            cap_name = cap_data.get("name", "unknown")
            tools = cap_data.get("tools", [])
            risk = cap_data.get("risk", "R0")

            ref = CapabilityRef(
                extension_id=ext_id,
                capability_name=cap_name,
                tools=tools,
                risk=risk,
                available=is_active and cap_data.get("availability", "unavailable") == "available",
                availability_reason=info.reason if not is_active else ""
            )
            ctx.capabilities[f"{ext_id}.{cap_name}"] = ref
            ctx._known_tools.update(tools)

    return ctx
