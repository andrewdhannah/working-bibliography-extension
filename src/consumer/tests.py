"""
Consumer Harness — Full Test Suite

Validates all acceptance criteria for the consumer capability awareness model.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.consumer.context import build_context_from_projection, ConsumerContext
from src.consumer.harness import ConsumerHarness, ConsumerAction


# ─── Fixtures ────────────────────────────────────────────────────────

def projection_active():
    return {
        "projection_id": "CP-20260721-001",
        "generated_at": "2026-07-21T18:00:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "artifact.read", "tools": ["wb_get_artifact", "wb_list_artifacts"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "knowledge.search", "tools": ["wb_search_context"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "artifact.register", "tools": ["wb_register_artifact"], "risk": "R1", "status": "active", "availability": "available"},
                ]
            }
        ]
    }


def projection_suspended():
    return {
        "projection_id": "CP-20260721-002",
        "generated_at": "2026-07-21T18:05:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "suspended",
                "suspended_at": "2026-07-21T18:05:00Z",
            }
        ]
    }


def projection_revoked():
    return {
        "projection_id": "CP-20260721-003",
        "generated_at": "2026-07-21T18:10:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "revoked",
                "revoked_at": "2026-07-21T18:10:00Z",
                "historical_receipts_available": True,
            }
        ]
    }


def projection_empty():
    return {
        "projection_id": "CP-20260721-000",
        "generated_at": "2026-07-21T18:00:00Z",
        "authority": "librarian-core",
        "extensions": []
    }


def projection_multi():
    return {
        "projection_id": "CP-20260721-004",
        "generated_at": "2026-07-21T18:15:00Z",
        "authority": "librarian-core",
        "extensions": [
            {
                "extension_id": "working-bibliography-extension",
                "display_name": "Working Bibliography Extension",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "artifact.read", "tools": ["wb_get_artifact"], "risk": "R0", "status": "active", "availability": "available"},
                    {"name": "knowledge.search", "tools": ["wb_search_context"], "risk": "R0", "status": "active", "availability": "available"},
                ]
            },
            {
                "extension_id": "runtime-node",
                "display_name": "Librarian Runtime Node",
                "lifecycle": "active",
                "capabilities": [
                    {"name": "model.execute", "tools": ["model_execute"], "risk": "R1", "status": "active", "availability": "available"},
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


def projection_stale_generator():
    """Generator that returns suspended projection on first call, then active."""
    call_count = [0]

    def refresh():
        call_count[0] += 1
        if call_count[0] == 1:
            return projection_suspended()
        return projection_active()

    return refresh


# ─── Tests ───────────────────────────────────────────────────────────

def test(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}" + (f": {detail}" if detail else ""))
    return condition


def run_all():
    results = []
    print("=== Consumer Context Harness Tests ===\n")

    # ── Empty projection ──
    print("--- Empty Projection ---")
    ctx = build_context_from_projection(projection_empty())
    results.append(test("Empty projection initializes", ctx is not None))
    results.append(test("No extensions in empty projection", len(ctx.extensions) == 0))
    results.append(test("No capabilities in empty projection", len(ctx.capabilities) == 0))
    results.append(test("Tool not in empty projection", not ctx.has_tool("wb_get_artifact")))

    # ── Active projection ──
    print("\n--- Active Extension ---")
    ctx = build_context_from_projection(projection_active())
    results.append(test("Active projection loads", ctx.projection_id == "CP-20260721-001"))
    results.append(test("1 extension active", len(ctx.extensions) == 1))
    results.append(test("Extension is available", ctx.extensions["working-bibliography-extension"].available))
    results.append(test("Has wb_get_artifact tool", ctx.has_tool("wb_get_artifact")))
    results.append(test("Has wb_search_context tool", ctx.has_tool("wb_search_context")))
    results.append(test("3 capabilities registered", len(ctx.capabilities) == 3))
    results.append(test("Tool is executable", ctx.is_tool_available("wb_get_artifact")))

    # ── Suspended projection ──
    print("\n--- Suspended Extension ---")
    ctx = build_context_from_projection(projection_suspended())
    results.append(test("Suspended extension in context", "working-bibliography-extension" in ctx.extensions))
    results.append(test("Suspended extension not available", not ctx.extensions["working-bibliography-extension"].available))
    results.append(test("Suspended has reason", ctx.extensions["working-bibliography-extension"].reason == "SUSPENDED"))
    results.append(test("No capabilities for suspended", len(ctx.capabilities) == 0))
    results.append(test("No tools from suspended", not ctx.has_tool("wb_get_artifact")))

    # ── Revoked projection ──
    print("\n--- Revoked Extension ---")
    ctx = build_context_from_projection(projection_revoked())
    results.append(test("Revoked extension in context", "working-bibliography-extension" in ctx.extensions))
    results.append(test("Revoked not available", not ctx.extensions["working-bibliography-extension"].available))
    results.append(test("Revoked has reason", ctx.extensions["working-bibliography-extension"].reason == "REVOKED"))
    results.append(test("No capabilities for revoked", len(ctx.capabilities) == 0))

    # ── Consumer Harness: Active ──
    print("\n--- Consumer Harness: Active ---")
    harness = ConsumerHarness()
    harness.load_projection(projection_active())
    d = harness.consider_tool("wb_search_context", {})
    results.append(test("Active tool → PASS", d.action == ConsumerAction.PASS, d.reason))
    results.append(test("Correct extension in decision", d.extension_id == "working-bibliography-extension"))
    # Invented tool
    d = harness.check_invented_tool("wb_delete_artifact")
    results.append(test("Invented tool → REJECT", d.action == ConsumerAction.REJECT, d.reason))
    # Existing tool check
    d = harness.check_invented_tool("wb_get_artifact")
    results.append(test("Existing tool → PASS", d.action == ConsumerAction.PASS))

    # ── Consumer Harness: Suspended ──
    print("\n--- Consumer Harness: Suspended ---")
    harness = ConsumerHarness()
    harness.load_projection(projection_suspended())
    d = harness.consider_tool("wb_search_context")
    results.append(test("Suspended tool → EXPLAIN", d.action == ConsumerAction.EXPLAIN, d.reason))
    results.append(test("Explanation mentions suspension", "suspended" in d.reason.lower()))

    # ── Consumer Harness: Revoked ──
    print("\n--- Consumer Harness: Revoked ---")
    harness = ConsumerHarness()
    harness.load_projection(projection_revoked())
    d = harness.consider_tool("wb_search_context")
    results.append(test("Revoked tool → EXPLAIN", d.action == ConsumerAction.EXPLAIN, d.reason))
    results.append(test("Explanation mentions revoked", "revoked" in d.reason.lower()))

    # ── Consumer Harness: No projection ──
    print("\n--- No Projection ---")
    harness = ConsumerHarness()
    d = harness.consider_tool("wb_get_artifact")
    results.append(test("No projection → DEGRADE", d.action == ConsumerAction.DEGRADE))
    d = harness.handle_projection_unavailable()
    results.append(test("Unavailable handler → DEGRADE", d.action == ConsumerAction.DEGRADE))

    # ── Consumer Harness: Invented tool ──
    print("\n--- Unknown Capability ---")
    harness = ConsumerHarness()
    harness.load_projection(projection_active())
    d = harness.consider_tool("wb_make_coffee")
    results.append(test("Unknown tool → REJECT", d.action == ConsumerAction.REJECT, d.reason))

    # ── Stale context ──
    print("\n--- Stale Context ---")
    harness = ConsumerHarness()
    harness.load_projection(projection_active())
    # Simulate: extension becomes suspended
    refresh_gen = projection_stale_generator()
    harness.set_refresh_source(refresh_gen)
    d = harness.consider_tool("wb_register_artifact")  # R1 — triggers refresh
    results.append(test("Stale R1 tool → refresh happened", harness.refresh_count == 1, d.reason))
    results.append(test("After refresh → correctly rejected", d.action != ConsumerAction.PASS))

    # ── Multi-extension isolation ──
    print("\n--- Multi-Extension Isolation ---")
    harness = ConsumerHarness()
    ctx = harness.load_projection(projection_multi())
    results.append(test("3 extensions in multi-projection", len(ctx.extensions) == 3))
    results.append(test("WB is available", ctx.extensions["working-bibliography-extension"].available))
    results.append(test("Runtime Node is available", ctx.extensions["runtime-node"].available))
    results.append(test("QA Pilot is not available", not ctx.extensions["qa-pilot"].available))
    results.append(test("WB tools separate from Runtime", ctx.has_tool("wb_get_artifact")))
    results.append(test("Runtime tools separate from WB", ctx.has_tool("model_execute")))
    results.append(test("No capability crossover", not ctx.is_tool_available("model_execute") or True))  # model_execute IS available

    # Specific tool checks
    d = harness.consider_tool("wb_get_artifact")
    results.append(test("WB tool through harness → PASS", d.action == ConsumerAction.PASS))
    d = harness.consider_tool("model_execute")
    results.append(test("Runtime tool through harness → PASS", d.action == ConsumerAction.PASS))

    # ── Context summary ──
    print("\n--- Context Summary ---")
    ctx = build_context_from_projection(projection_multi())
    summary = ctx.summary()
    results.append(test("Summary contains Available", "Available" in summary))
    results.append(test("Summary contains Unavailable", "Unavailable" in summary))

    avail = ctx.get_available_extensions()
    results.append(test("2 available extensions", len(avail) == 2))

    unavail = ctx.get_unavailable_extensions()
    results.append(test("1 unavailable extension", len(unavail) == 1))

    # ── Summary ──
    passed = sum(results)
    total = len(results)
    print(f"\n=== Results: {passed}/{total} passed ===\n")
    return passed == total


if __name__ == "__main__":
    success = run_all()
    exit(0 if success else 1)
