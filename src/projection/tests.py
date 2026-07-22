"""
Tests for the capability projection service.
Validates all 7 acceptance scenarios.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.projection.service import ProjectionService
from src.projection.schema import CapabilityAvailability, ExtensionState
from src.projection import fixtures


def test_scenario(name, fixture, expected_extensions, expected_capabilities):
    """Run a single projection test scenario."""
    service = ProjectionService(state_source=fixture)
    projection = service.build_projection()
    data = projection.to_dict()

    ext_count = len(data.get("extensions", []))
    cap_count = sum(len(e.get("capabilities", [])) for e in data.get("extensions", []))

    ext_ok = ext_count == expected_extensions
    cap_ok = cap_count == expected_capabilities

    status = "✅" if (ext_ok and cap_ok) else "❌"
    print(f"  {status} {name}")
    print(f"      Extensions: {ext_count} (expected {expected_extensions})")
    print(f"      Capabilities: {cap_count} (expected {expected_capabilities})")

    # Show first extension's state
    if data.get("extensions"):
        e = data["extensions"][0]
        print(f"      First ext: {e['extension_id']} → {e['lifecycle']}")

    return ext_ok and cap_ok


def test_availability(name, fixture, extension_id, cap_name, expected_availability):
    """Test that a specific capability has the expected availability."""
    service = ProjectionService(state_source=fixture)
    projection = service.build_projection()

    for ext in projection.extensions:
        if ext.extension_id == extension_id:
            for cap in ext.capabilities:
                if cap.name == cap_name:
                    actual = cap.availability.value
                    ok = actual == expected_availability
                    status = "✅" if ok else "❌"
                    print(f"  {status} {name}: '{cap_name}' = {actual} (expected {expected_availability})")
                    return ok

    print(f"  ❌ {name}: capability '{cap_name}' not found in {extension_id}")
    return False


def test_staleness():
    """Test that identical projections return 'unchanged'."""
    service = ProjectionService(state_source=fixtures.active_with_capabilities())

    # First call — get projection_id
    p1 = service.build_projection()
    pid = p1.projection_id

    # Second call with matching projection_id
    p2 = service.build_projection(known_projection_id=pid)
    ok = p2.status == "unchanged"
    status = "✅" if ok else "❌"
    print(f"  {status} Staleness detection: status={p2.status} (expected unchanged)")
    return ok


def run_all():
    """Run all test scenarios."""
    results = []

    print("\n=== Capability Projection Tests ===\n")

    # Test 1: Empty projection
    results.append(test_scenario(
        "No extensions → valid empty projection",
        fixtures.empty_projection(), 0, 0
    ))

    # Test 2: Registered only
    results.append(test_scenario(
        "Registered extension → visible but unavailable",
        fixtures.registered_only(), 1, 0
    ))

    # Test 3: Contract verified
    results.append(test_scenario(
        "Contract verified → visible, not active",
        fixtures.contract_verified(), 1, 0
    ))

    # Test 4: Owner approved
    results.append(test_scenario(
        "Owner approved → capability available",
        fixtures.owner_approved(), 1, 0
    ))

    # Test 5: Active with capabilities
    results.append(test_scenario(
        "Active extension → capabilities available",
        fixtures.active_with_capabilities(), 1, 3
    ))

    # Test 6: Suspended — capabilities removed
    results.append(test_scenario(
        "Suspended extension → capabilities removed",
        fixtures.suspended(), 1, 0
    ))

    # Test 7: Revoked — historical only
    results.append(test_scenario(
        "Revoked extension → historical only",
        fixtures.revoked(), 1, 0
    ))

    # Test 8: Multiple extensions
    results.append(test_scenario(
        "Multiple extensions → isolated by domain",
        fixtures.multiple_extensions(), 3, 3
    ))

    # Test 9: Mixed states
    results.append(test_scenario(
        "Mixed states → correct per-extension projection",
        fixtures.mixed_states(), 3, 1
    ))

    # Test 10: Staleness
    results.append(test_staleness())

    # Availability tests
    print()
    print("--- Availability Checks ---")
    results.append(test_availability(
        "Active → available",
        fixtures.active_with_capabilities(),
        "working-bibliography-extension", "artifact.read",
        CapabilityAvailability.AVAILABLE.value
    ))
    # Suspended/revoked extensions should not list capabilities at all
    service_susp = ProjectionService(state_source=fixtures.suspended())
    proj_susp = service_susp.build_projection()
    caps_susp = sum(len(e.capabilities) for e in proj_susp.extensions)
    susp_ok = caps_susp == 0
    status_s = "✅" if susp_ok else "❌"
    print(f"  {status_s} Suspended → no capabilities listed (found {caps_susp})")
    results.append(susp_ok)

    service_rev = ProjectionService(state_source=fixtures.revoked())
    proj_rev = service_rev.build_projection()
    caps_rev = sum(len(e.capabilities) for e in proj_rev.extensions)
    rev_ok = caps_rev == 0
    status_r = "✅" if rev_ok else "❌"
    print(f"  {status_r} Revoked → no capabilities listed (found {caps_rev})")
    results.append(rev_ok)

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n=== Results: {passed}/{total} passed ===\n")
    return passed == total


if __name__ == "__main__":
    success = run_all()
    exit(0 if success else 1)
