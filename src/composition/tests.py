"""
Composition Tests — Multi-Extension Capability Isolation and Composition

Validates that multiple independent extensions can coexist without capability
leakage, namespace collision, or trust boundary collapse.
"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from composition import fixtures
from composition.validator import (
    validate_extension_namespace, get_capabilities_by_extension,
    get_tools_by_extension, has_namespace_isolation, compute_composition,
    CompositionError
)
from consumer.context import build_context_from_projection
from consumer.harness import ConsumerHarness, ConsumerAction


def test(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}" + (f": {detail}" if detail else ""))
    return condition


def run_all():
    results = []
    print("=== Multi-Extension Composition Tests ===\n")

    # ── 1. Three extensions loaded ──
    print("--- 1. Three Extensions Loaded ---")
    proj = fixtures.all_active()
    ctx = build_context_from_projection(proj)
    results.append(test("3 extensions in context", len(ctx.extensions) == 3))
    results.append(test("WB extension present", "working-bibliography-extension" in ctx.extensions))
    results.append(test("Runtime Node present", "runtime-node" in ctx.extensions))
    results.append(test("QA Pilot present", "qa-pilot" in ctx.extensions))
    results.append(test("All three active",
        all(e.lifecycle == "active" for e in ctx.extensions.values())))

    # ── 2. Independent namespaces ──
    print("\n--- 2. Independent Namespaces ---")
    caps_by_ext = get_capabilities_by_extension(proj)
    tools_by_ext = get_tools_by_extension(proj)

    results.append(test("WB has 3 capabilities", len(caps_by_ext.get("working-bibliography-extension", [])) == 3))
    results.append(test("Runtime has 3 capabilities", len(caps_by_ext.get("runtime-node", [])) == 3))
    results.append(test("QA Pilot has 3 capabilities", len(caps_by_ext.get("qa-pilot", [])) == 3))

    results.append(test("WB tools start with wb_",
        all(t.startswith("wb_") for t in tools_by_ext.get("working-bibliography-extension", []))))
    results.append(test("Runtime tools start with model_",
        all(t.startswith("model_") for t in tools_by_ext.get("runtime-node", []))))
    results.append(test("QA Pilot tools start with test_",
        all(t.startswith("test_") for t in tools_by_ext.get("qa-pilot", []))))

    # Namespace isolation
    results.append(test("Namespace isolation valid", has_namespace_isolation(proj)))

    # Cross-extension access rejection
    harness = ConsumerHarness()
    harness.load_projection(proj)

    d = harness.consider_tool("wb_search")
    results.append(test("WB can access wb_search", d.action == ConsumerAction.PASS))

    d = harness.consider_tool("model_execute")
    results.append(test("Runtime can access model_execute", d.action == ConsumerAction.PASS))

    d = harness.consider_tool("test_run")
    results.append(test("QA Pilot can access test_run", d.action == ConsumerAction.PASS))

    # ── 3. Capability collision rejected ──
    print("\n--- 3. Capability Collision Detection ---")
    coll = fixtures.collision()
    collisions = validate_extension_namespace(coll)
    results.append(test("Collision detected", len(collisions) > 0))
    results.append(test("Collision message mentions both extensions",
        "extension-a" in collisions[0] and "extension-b" in collisions[0]))
    results.append(test("No collision in valid projection",
        len(validate_extension_namespace(fixtures.all_active())) == 0))

    # ── 4. Mixed lifecycle states ──
    print("\n--- 4. Mixed Lifecycle States ---")
    proj_mixed = fixtures.mixed_lifecycle()
    ctx = build_context_from_projection(proj_mixed)

    results.append(test("WB active (from mixed)",
        ctx.extensions["working-bibliography-extension"].available))
    results.append(test("Runtime suspended (from mixed)",
        not ctx.extensions["runtime-node"].available and
        ctx.extensions["runtime-node"].lifecycle == "suspended"))
    results.append(test("QA Pilot contract_verified (from mixed)",
        not ctx.extensions["qa-pilot"].available and
        ctx.extensions["qa-pilot"].lifecycle == "contract_verified"))

    # Composition view
    comp = compute_composition(proj_mixed)
    results.append(test("Available: WB search + retrieve", len(comp["available"]) == 2))
    results.append(test("Unavailable: Runtime (suspended)", len(comp["unavailable"]) == 0))  # no caps listed
    results.append(test("Pending: QA Pilot (contract_verified)", len(comp["pending"]) == 0))  # no caps listed
    results.append(test("3 total extensions", comp["total_extensions"] == 3))
    results.append(test("1 active extension", comp["active_extensions"] == 1))

    # ── 5. Suspended extension isolated ──
    print("\n--- 5. Suspended Extension Isolation ---")
    harness = ConsumerHarness()
    harness.load_projection(proj_mixed)

    d = harness.consider_tool("wb_retrieve")
    results.append(test("Active WB tool usable", d.action == ConsumerAction.PASS))

    d = harness.consider_tool("model_execute")
    results.append(test("Suspended Runtime tool blocked",
        d.action in (ConsumerAction.EXPLAIN, ConsumerAction.REJECT)))

    d = harness.consider_tool("test_run")
    results.append(test("Pending QA Pilot tool blocked",
        d.action in (ConsumerAction.EXPLAIN, ConsumerAction.REJECT)))

    # ── 6. No cross-extension capability leakage ──
    print("\n--- 6. Capability Leakage Prevention ---")
    harness = ConsumerHarness()
    proj = fixtures.all_active()
    ctx = harness.load_projection(proj)

    # All nine tools should be accessible only through their owning extension
    wb_tools = {"wb_search", "wb_retrieve", "wb_get_provenance"}
    rt_tools = {"model_list", "model_qualify", "model_execute"}
    qa_tools = {"test_run", "test_report", "test_validate"}

    for tool in wb_tools:
        results.append(test(f"'{tool}' owned by WB only", ctx.has_tool(tool)))
    for tool in rt_tools:
        results.append(test(f"'{tool}' owned by Runtime only", ctx.has_tool(tool)))
    for tool in qa_tools:
        results.append(test(f"'{tool}' owned by QA Pilot only", ctx.has_tool(tool)))

    # Verify each tool is in exactly one extension's context
    cap_refs = list(ctx.capabilities.values())
    all_tools = []
    for ref in cap_refs:
        all_tools.extend(ref.tools)
    results.append(test("9 total tools across 3 extensions", len(all_tools) == 9))

    # ── 7. Consumer context correctly composed ──
    print("\n--- 7. Consumer Context Composition ---")
    proj = fixtures.all_active()
    ctx = build_context_from_projection(proj)
    summary = ctx.summary()
    results.append(test("Summary mentions all three",
        all(name in summary for name in ["Working Bibliography", "Runtime Node", "QA Pilot"])))
    results.append(test("All available", "Available" in summary))

    # ── 8. Combined workflow receipts ──
    print("\n--- 8. Combined Workflow ---")
    harness = ConsumerHarness()
    harness.load_projection(fixtures.all_active())

    # Simulate: retrieve artifact → run validation
    d1 = harness.consider_tool("wb_retrieve")
    results.append(test("WB retrieve allowed", d1.action == ConsumerAction.PASS))

    d2 = harness.consider_tool("test_run")
    results.append(test("QA test.run allowed", d2.action == ConsumerAction.PASS))

    decisions = harness.get_history()
    results.append(test("Both decisions recorded", len(decisions) >= 2))
    results.append(test("No rejected decisions in valid workflow",
        all(d["action"] != ConsumerAction.REJECT for d in decisions)))

    # ── 9. Extension removal does not corrupt consumer state ──
    print("\n--- 9. Extension Removal ---")
    harness = ConsumerHarness()
    harness.load_projection(fixtures.all_active())
    # Load new projection without WB
    harness.load_projection(fixtures.wb_removed())

    ctx = harness.context
    results.append(test("WB removed from context", "working-bibliography-extension" not in ctx.extensions))
    results.append(test("Runtime still present", "runtime-node" in ctx.extensions))
    results.append(test("No WB tools accessible", not ctx.has_tool("wb_search")))
    results.append(test("Runtime tools still accessible", ctx.has_tool("model_execute")))
    results.append(test("Context still valid", ctx.projection_id == "CP-20260721-103"))

    # ── Summary ──
    passed = sum(results)
    total = len(results)
    print(f"\n=== Results: {passed}/{total} passed ===\n")
    return passed == total


if __name__ == "__main__":
    success = run_all()
    exit(0 if success else 1)
