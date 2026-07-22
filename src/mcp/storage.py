"""
Artifact storage for Working Bibliography.

File-based JSON storage simulating the SQLite artifact registry defined
in the storage architecture. Artifacts are stored as individual JSON files
in the artifacts/ directory under the project root.

Per ADR-WB-007: Working Bibliography maintains an independent storage domain.
Librarian never accesses this storage directly — only through MCP tools.
"""

import json
import os
import hashlib
import re
from datetime import datetime, timezone


STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "storage")


def _ensure_storage_dir():
    """Create storage directories if they don't exist."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, "sources"), exist_ok=True)


def _artifact_path(artifact_id: str) -> str:
    """Get the filesystem path for an artifact."""
    return os.path.join(STORAGE_DIR, "artifacts", f"{artifact_id}.json")


def _sequence_path() -> str:
    """Get the path for the artifact sequence counter."""
    return os.path.join(STORAGE_DIR, "sequence.json")


def _get_next_artifact_id() -> str:
    """Generate the next sequential artifact ID (WB-XXXXX)."""
    seq_path = _sequence_path()
    if os.path.exists(seq_path):
        with open(seq_path) as f:
            seq = json.load(f)
    else:
        seq = {"next": 1}

    artifact_id = f"WB-{seq['next']:05d}"
    seq["next"] += 1

    with open(seq_path, "w") as f:
        json.dump(seq, f)

    return artifact_id


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of canonical text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def store_artifact(artifact: dict) -> dict:
    """Store a new artifact and return it with generated fields."""
    _ensure_storage_dir()

    # Generate identity
    artifact_id = _get_next_artifact_id()
    content_hash = compute_content_hash(artifact.get("content", {}).get("canonical_text", ""))

    # Build the full artifact record
    record = {
        "artifact_id": artifact_id,
        "spec_version": artifact.get("spec_version", "1.0.0"),
        "content_hash": content_hash,
        "content_hash_algorithm": "sha-256",
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": artifact.get("source", {"retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}),
        "content": {
            "canonical_text": artifact.get("content", {}).get("canonical_text", ""),
            "raw_format": artifact.get("content", {}).get("raw_format", "text")
        },
        "relationships": artifact.get("relationships", {}),
        "lifecycle": artifact.get("lifecycle", "active"),
        "metadata": artifact.get("metadata", {})
    }

    # Write artifact file
    with open(_artifact_path(artifact_id), "w") as f:
        json.dump(record, f, indent=2)

    return record


def get_artifact(artifact_id: str) -> dict:
    """Retrieve an artifact by ID."""
    path = _artifact_path(artifact_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def list_artifacts(filter_text: str = None, limit: int = 100, offset: int = 0) -> dict:
    """List artifacts with optional text filter and pagination.

    Returns:
        dict with 'artifacts' (list) and 'total' (int)
    """
    _ensure_storage_dir()
    artifacts_dir = os.path.join(STORAGE_DIR, "artifacts")
    if not os.path.exists(artifacts_dir):
        return {"artifacts": [], "total": 0}

    all_artifacts = []
    for fname in sorted(os.listdir(artifacts_dir), reverse=True):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(artifacts_dir, fname)) as f:
            artifact = json.load(f)
        # Simple text filter on artifact_id, title, or canonical_text
        if filter_text:
            text = json.dumps(artifact).lower()
            if filter_text.lower() not in text:
                continue
        all_artifacts.append(artifact)

    total = len(all_artifacts)
    page = all_artifacts[offset:offset + limit]

    return {
        "artifacts": page,
        "total": total,
        "limit": limit,
        "offset": offset
    }


def transition_lifecycle(artifact_id: str, to_state: str, reason: str) -> dict:
    """Transition an artifact's lifecycle state.

    Valid transitions:
      active   → archived (source no longer relevant)
      active   → revoked  (source untrustworthy)
      archived → active   (reactivated)

    Returns the updated artifact, or None if transition is invalid.
    """
    valid_transitions = {
        "active": ["archived", "revoked"],
        "archived": ["active"]
    }

    artifact = get_artifact(artifact_id)
    if not artifact:
        return None

    from_state = artifact.get("lifecycle")
    if from_state not in valid_transitions:
        return None
    if to_state not in valid_transitions[from_state]:
        return None

    artifact["lifecycle"] = to_state
    artifact["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Record transition
    if "lifecycle_transitions" not in artifact:
        artifact["lifecycle_transitions"] = []
    artifact["lifecycle_transitions"].append({
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": artifact["updated_at"],
        "reason": reason
    })

    with open(_artifact_path(artifact_id), "w") as f:
        json.dump(artifact, f, indent=2)

    return artifact
