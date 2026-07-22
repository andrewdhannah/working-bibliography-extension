"""
Extension Identity — Announcement, Registration, and Verification

Implements the identity portion of the handshake protocol:
  1. Extension announces identity (extension_id, version, contract_id)
  2. Librarian validates identity format and uniqueness
  3. Registration receipt is produced

Per EXTENSION-HANDSHAKE-CONTRACT.md §2 (Step 1): Announce Identity
Per CONTRACT-BOUNDARIES.md §5: Identity integrity violation → REVOKED
"""

import json
import os
import re
from datetime import datetime, timezone


HANDSHAKE_STORAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "handshake")


# Contract identity requirements from WB-LIBRARIAN-CONTRACT-v1
EXPECTED_IDENTITY = {
    "extension_id": "working-bibliography-extension",
    "contract_id": "wb-librarian-contract-v1",
    "contract_version": "1.0.0"
}

IDENTITY_FIELD_PATTERNS = {
    "extension_id": r"^[a-z][a-z0-9_-]+$",
    "version": r"^\d+\.\d+\.\d+$",
    "contract_id": r"^[a-z][a-z0-9_-]+-v\d+$",
    "contract_version": r"^\d+\.\d+\.\d+$"
}


class IdentityError(Exception):
    """Raised when identity validation fails."""
    pass


def _ensure_storage():
    """Ensure handshake receipt directory exists."""
    os.makedirs(HANDSHAKE_STORAGE, exist_ok=True)


def _write_registration(record: dict):
    """Persist a registration record."""
    _ensure_storage()
    path = os.path.join(HANDSHAKE_STORAGE, f"{record['extension_id']}.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=2)


def _read_registration(extension_id: str) -> dict:
    """Read a registration record."""
    path = os.path.join(HANDSHAKE_STORAGE, f"{extension_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def validate_identity_announcement(announcement: dict) -> dict:
    """Validate an extension identity announcement.

    Checks:
      - All required fields are present
      - Field formats match expected patterns
      - extension_id matches the contract

    Returns:
        dict with 'valid' (bool) and 'errors' (list of str)

    Per EXTENSION-HANDSHAKE-CONTRACT.md §2 Step 1.
    """
    errors = []

    # Required fields per handshake contract
    required_fields = ["extension_id", "version", "contract_id", "contract_version", "declared_at"]
    for field in required_fields:
        if field not in announcement:
            errors.append(f"Missing required field: {field}")

    if errors:
        return {"valid": False, "errors": errors}

    # Format validation
    for field, pattern in IDENTITY_FIELD_PATTERNS.items():
        value = announcement.get(field, "")
        if not re.match(pattern, value):
            errors.append(f"Field '{field}' has invalid format: '{value}' (expected pattern: {pattern})")

    # extension_id must match contract
    declared_id = announcement.get("extension_id")
    expected_id = EXPECTED_IDENTITY.get("extension_id")
    if declared_id and declared_id != expected_id:
        errors.append(f"Extension ID '{declared_id}' does not match contract identity '{expected_id}'")

    # contract_id must match
    declared_contract = announcement.get("contract_id")
    expected_contract = EXPECTED_IDENTITY.get("contract_id")
    if declared_contract and declared_contract != expected_contract:
        errors.append(f"Contract ID '{declared_contract}' does not match expected '{expected_contract}'")

    return {"valid": len(errors) == 0, "errors": errors}


def register_extension(announcement: dict) -> dict:
    """Register an extension after identity validation.

    Returns:
        dict with registration record including registration_id and state.
        Or raises IdentityError if validation fails.
    """
    validation = validate_identity_announcement(announcement)
    if not validation["valid"]:
        raise IdentityError(f"Identity validation failed: {'; '.join(validation['errors'])}")

    record = {
        "extension_id": announcement["extension_id"],
        "version": announcement["version"],
        "contract_id": announcement["contract_id"],
        "contract_version": announcement["contract_version"],
        "owner_domain": announcement.get("owner_domain", "unknown"),
        "display_name": announcement.get("display_name", announcement["extension_id"]),
        "state": "REGISTERED",
        "registered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declared_at": announcement["declared_at"],
        "last_transition": None,
        "transitions": [
            {
                "from_state": None,
                "to_state": "REGISTERED",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reason": "Identity announcement validated"
            }
        ]
    }

    _write_registration(record)
    return record


def get_registration(extension_id: str) -> dict:
    """Get the current registration record for an extension."""
    return _read_registration(extension_id)


def is_registered(extension_id: str) -> bool:
    """Check if an extension is registered."""
    record = _read_registration(extension_id)
    return record is not None
