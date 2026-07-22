"""
Composition Validator — Capability Isolation and Collision Detection
"""

from typing import Optional


class CompositionError(Exception):
    """Raised when a composition rule is violated."""
    pass


def validate_extension_namespace(projection_data: dict) -> list[str]:
    """Validate that no two extensions share a capability name.
    
    Returns list of collision descriptions (empty if valid).
    """
    collisions = []
    capability_map = {}  # capability_name -> extension_id

    for ext in projection_data.get("extensions", []):
        ext_id = ext.get("extension_id", "unknown")
        for cap in ext.get("capabilities", []):
            cap_name = cap.get("name")
            if cap_name in capability_map:
                collisions.append(
                    f"Capability name collision: '{cap_name}' claimed by "
                    f"'{capability_map[cap_name]}' and '{ext_id}'"
                )
            else:
                capability_map[cap_name] = ext_id

    return collisions


def get_capabilities_by_extension(projection_data: dict) -> dict[str, list[str]]:
    """Get mapping of extension_id -> list of capability names."""
    result = {}
    for ext in projection_data.get("extensions", []):
        ext_id = ext.get("extension_id", "unknown")
        result[ext_id] = [c.get("name") for c in ext.get("capabilities", [])]
    return result


def get_tools_by_extension(projection_data: dict) -> dict[str, list[str]]:
    """Get mapping of extension_id -> list of tool names."""
    result = {}
    for ext in projection_data.get("extensions", []):
        ext_id = ext.get("extension_id", "unknown")
        tools = []
        for c in ext.get("capabilities", []):
            tools.extend(c.get("tools", []))
        result[ext_id] = tools
    return result


def has_namespace_isolation(projection_data: dict) -> bool:
    """Check that each extension's tools use unique prefixes per extension."""
    tools_by_ext = get_tools_by_extension(projection_data)

    # Check tool prefix uniqueness — tools should start with extension's prefix
    ext_prefixes = {}
    for ext_id, tools in tools_by_ext.items():
        if not tools:
            continue
        # Derive prefix from first tool
        prefixes = set()
        for t in tools:
            prefix = t.split("_")[0] if "_" in t else t[:3]
            prefixes.add(prefix)
        ext_prefixes[ext_id] = prefixes

    # Check no prefix is shared across extensions
    all_prefixes = {}
    for ext_id, prefixes in ext_prefixes.items():
        for p in prefixes:
            if p in all_prefixes:
                return False  # Two extensions share a tool prefix
            all_prefixes[p] = ext_id

    return True


def compute_composition(projection_data: dict) -> dict:
    """Compute the composed consumer view from a multi-extension projection.
    
    Returns dict with:
      - available: capabilities ready for use
      - pending: capabilities not yet active
      - unavailable: capabilities from now-suspended extensions
      - total_extensions: count
      - active_extensions: count
    """
    composition = {
        "available": [],
        "pending": [],
        "unavailable": [],
        "total_extensions": 0,
        "active_extensions": 0,
    }

    for ext in projection_data.get("extensions", []):
        ext_id = ext.get("extension_id", "unknown")
        lifecycle = ext.get("lifecycle", "unknown")
        composition["total_extensions"] += 1

        if lifecycle == "active":
            composition["active_extensions"] += 1
            for cap in ext.get("capabilities", []):
                if cap.get("availability") == "available":
                    composition["available"].append({
                        "extension_id": ext_id,
                        "capability": cap.get("name"),
                        "tool": cap.get("tools", [None])[0]
                    })
        elif lifecycle == "suspended":
            for cap in ext.get("capabilities", []):
                composition["unavailable"].append({
                    "extension_id": ext_id,
                    "capability": cap.get("name"),
                    "reason": "SUSPENDED"
                })
        elif lifecycle in ("contract_verified", "owner_approved"):
            for cap in ext.get("capabilities", []):
                composition["pending"].append({
                    "extension_id": ext_id,
                    "capability": cap.get("name"),
                    "reason": lifecycle
                })
        elif lifecycle == "revoked":
            composition["unavailable"].append({
                "extension_id": ext_id,
                "reason": "REVOKED"
            })
        else:
            # registered, but no capabilities listed
            pass

    return composition
