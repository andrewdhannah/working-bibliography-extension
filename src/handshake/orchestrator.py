"""
Handshake Orchestrator — Full Sequence from Discovery to Activation

Implements the 6-step handshake sequence from EXTENSION-HANDSHAKE-CONTRACT.md:

  1. Announce identity          → REGISTERED
  2. Present contract           → (validation)
  3. Validate capabilities     → CONTRACT_VERIFIED
  4. Request activation         → (Owner review)
  5. Owner approves             → OWNER_APPROVED
  6. Capabilities active        → ACTIVE

Returns structured results at each step including validation details
and receipts.
"""

from . import identity, validator, lifecycle as lifecycle_module
from . import receipts as handshake_receipts

# The expected identity for this extension
EXPECTED_IDENTITY = {
    "extension_id": "working-bibliography-extension",
    "contract_id": "wb-librarian-contract-v1",
    "contract_version": "1.0.0"
}


def execute_full_handshake(announcement: dict) -> dict:
    """Execute the complete handshake sequence and return results.

    Combines steps 1-3 (identity → contract verification → approval → activation).
    Owner approval is simulated for testing — real approval requires Owner action.

    Returns:
        dict with sequence of steps, each containing result, state, and receipt.
    """
    results = {
        "extension_id": announcement.get("extension_id"),
        "steps": [],
        "current_state": None,
        "overall_valid": False
    }

    # Step 1: Announce identity → REGISTERED
    try:
        reg = identity.register_extension(announcement)
        reg_receipt = handshake_receipts.generate_registration_receipt(announcement)
        state = lifecycle_module.initialize_state(
            announcement["extension_id"],
            reason="Identity announcement validated"
        )
        results["steps"].append({
            "step": 1,
            "action": "announce_identity",
            "state": "REGISTERED",
            "success": True,
            "receipt": reg_receipt["receipt_id"]
        })
        results["current_state"] = "REGISTERED"
    except identity.IdentityError as e:
        results["steps"].append({
            "step": 1,
            "action": "announce_identity",
            "state": "REJECTED",
            "success": False,
            "error": str(e)
        })
        results["overall_valid"] = False
        return results

    # Step 2-3: Present contract + validate → CONTRACT_VERIFIED
    manifest = _load_manifest()
    if not manifest:
        results["steps"].append({
            "step": 2,
            "action": "present_contract",
            "state": "FAILED",
            "success": False,
            "error": "Capability manifest not found"
        })
        return results

    contract_validation = validator.validate_contract_compatibility(
        announcement.get("contract_version", "")
    )
    manifest_validation = validator.validate_capability_manifest(manifest)

    combined_valid = contract_validation.valid and manifest_validation.valid

    cv_receipt = handshake_receipts.generate_contract_verification_receipt({
        "valid": combined_valid,
        "checks_passed": contract_validation.to_dict()["checks_passed"] +
                        manifest_validation.to_dict()["checks_passed"],
        "checks_total": contract_validation.to_dict()["checks_total"] +
                       manifest_validation.to_dict()["checks_total"],
        "errors": contract_validation.errors + manifest_validation.errors,
        "warnings": contract_validation.warnings + manifest_validation.warnings
    })

    if combined_valid:
        lifecycle_module.transition_to(
            announcement["extension_id"],
            "CONTRACT_VERIFIED",
            reason="Contract and capability manifest validated",
            authority="automated"
        )
        results["steps"].append({
            "step": 2,
            "action": "validate_contract_and_capabilities",
            "state": "CONTRACT_VERIFIED",
            "success": True,
            "receipt": cv_receipt["receipt_id"],
            "contract_checks": contract_validation.to_dict(),
            "manifest_checks": manifest_validation.to_dict()
        })
        results["current_state"] = "CONTRACT_VERIFIED"
    else:
        results["steps"].append({
            "step": 2,
            "action": "validate_contract_and_capabilities",
            "state": "FAILED",
            "success": False,
            "receipt": cv_receipt["receipt_id"],
            "contract_errors": contract_validation.errors,
            "manifest_errors": manifest_validation.errors
        })
        results["overall_valid"] = False
        return results

    # Steps 4-6: Owner approves → ACTIVE
    # Note: In a real system, this requires Librarian-side Owner action.
    # For the handshake implementation, we provide the framework.
    results["steps"].append({
        "step": 3,
        "action": "await_owner_approval",
        "state": "CONTRACT_VERIFIED",
        "success": True,
        "message": "Awaiting Owner approval. Call approve_and_activate() to continue.",
        "next_action": "approve_and_activate(extension_id, approved_by='owner')"
    })
    results["current_state"] = "CONTRACT_VERIFIED"
    results["overall_valid"] = True

    return results


def approve_and_activate(extension_id: str, approved_by: str = "owner") -> dict:
    """Simulate Owner approval and activation.

    In a real Librarian integration, this would be triggered by the
    Librarian Owner decision mechanism. For the handshake implementation,
    it provides the state transitions for testing.
    """
    result = {"extension_id": extension_id}

    # Check current state
    current = lifecycle_module.get_current_state(extension_id)
    if not current:
        result["error"] = f"No lifecycle state for extension '{extension_id}'"
        result["success"] = False
        return result

    if current["state"] not in ("CONTRACT_VERIFIED", "OWNER_APPROVED"):
        result["error"] = f"Cannot activate from state '{current['state']}'. Must be CONTRACT_VERIFIED."
        result["success"] = False
        return result

    # Owner approves
    try:
        lifecycle_module.transition_to(
            extension_id, "OWNER_APPROVED",
            reason=f"Owner authorization by {approved_by}",
            authority="owner"
        )
    except lifecycle_module.LifecycleError as e:
        result["error"] = str(e)
        result["success"] = False
        return result

    approval_receipt = handshake_receipts.generate_approval_receipt(extension_id, approved_by)

    # Activate
    try:
        lifecycle_module.transition_to(
            extension_id, "ACTIVE",
            reason="Owner approval granted, activating capabilities",
            authority="automated"
        )
    except lifecycle_module.LifecycleError as e:
        result["error"] = str(e)
        result["success"] = False
        return result

    activation_receipt = handshake_receipts.generate_activation_receipt(extension_id)

    result["success"] = True
    result["state"] = "ACTIVE"
    result["steps"] = [
        {"state": "OWNER_APPROVED", "receipt": approval_receipt["receipt_id"]},
        {"state": "ACTIVE", "receipt": activation_receipt["receipt_id"]}
    ]
    return result


def get_handshake_status(extension_id: str) -> dict:
    """Get the current handshake status for an extension."""
    reg = identity.get_registration(extension_id)
    life = lifecycle_module.get_current_state(extension_id)

    return {
        "extension_id": extension_id,
        "registered": reg is not None,
        "registration": reg,
        "lifecycle_state": life["state"] if life else None,
        "lifecycle": life,
        "can_execute": lifecycle_module.can_execute(extension_id) if life else False
    }


def _load_manifest() -> dict:
    """Load the capability manifest."""
    import json, os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "mcp", "capabilities.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
