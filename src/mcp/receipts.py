"""
Receipt generation for Working Bibliography MCP operations.

Receipts are evidence artifacts that record every governed operation.
They are stored in the extension's local receipt store and follow the
receipt types defined in WB-LIBRARIAN-CONTRACT-v1.

Receipt types:
  - capture_receipt:  Artifact creation
  - retrieval_receipt: Knowledge retrieval
  - lifecycle_receipt: Lifecycle transition
  - drift_receipt:     Drift detection
  - embedding_receipt: Embedding generation
"""

import json
import hashlib
import os
from datetime import datetime, timezone


RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "operations")


def _ensure_receipts_dir():
    """Create receipts directory if it doesn't exist."""
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def _generate_receipt_id(receipt_type: str) -> str:
    """Generate a unique receipt ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    hash_input = f"{receipt_type}:{timestamp}:{os.urandom(8).hex()}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    return f"rcp-wb-{receipt_type}-{timestamp}-{short_hash}"


def generate_capture_receipt(artifact_id: str, content_hash: str, source: dict) -> dict:
    """Generate a capture receipt for a new artifact.

    Contract reference: WB-LIBRARIAN-CONTRACT-v1 → evidence.receipt_types.capture_receipt
    Required fields: artifact_id, content_hash, source, captured_at
    """
    receipt = {
        "receipt_id": _generate_receipt_id("capture"),
        "receipt_type": "capture_receipt",
        "artifact_id": artifact_id,
        "content_hash": content_hash,
        "source": source,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write_receipt(receipt)
    return receipt


def generate_retrieval_receipt(query: str, artifact_references: list) -> dict:
    """Generate a retrieval receipt for a search operation.

    Contract reference: evidence.receipt_types.retrieval_receipt
    Required fields: query, results, artifact_references, retrieved_at
    """
    receipt = {
        "receipt_id": _generate_receipt_id("retrieval"),
        "receipt_type": "retrieval_receipt",
        "query": query,
        "result_count": len(artifact_references),
        "artifact_references": artifact_references,
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write_receipt(receipt)
    return receipt


def generate_lifecycle_receipt(artifact_id: str, from_state: str, to_state: str, reason: str) -> dict:
    """Generate a lifecycle receipt for a state transition.

    Contract reference: evidence.receipt_types.lifecycle_receipt
    Required fields: artifact_id, from_state, to_state, transitioned_at, reason
    """
    receipt = {
        "receipt_id": _generate_receipt_id("lifecycle"),
        "receipt_type": "lifecycle_receipt",
        "artifact_id": artifact_id,
        "from_state": from_state,
        "to_state": to_state,
        "transitioned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "schema_version": "1.0.0"
    }
    _write_receipt(receipt)
    return receipt


def generate_drift_receipt(expected_behavior: str, observed_behavior: str, classification: str) -> dict:
    """Generate a drift receipt when drift is detected.

    Contract reference: evidence.receipt_types.drift_receipt
    Required fields: expected_behavior, observed_behavior, classification, detected_at
    """
    receipt = {
        "receipt_id": _generate_receipt_id("drift"),
        "receipt_type": "drift_receipt",
        "expected_behavior": expected_behavior,
        "observed_behavior": observed_behavior,
        "classification": classification,
        "detected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": "1.0.0"
    }
    _write_receipt(receipt)
    return receipt


def generate_embedding_receipt(artifact_id: str, embedding_model: str, model_revision: str, source_hash: str) -> dict:
    """Generate an embedding receipt when an embedding is created.

    Contract reference: evidence.receipt_types.embedding_receipt
    Required fields: artifact_id, embedding_model, model_revision, generated_at, source_hash
    """
    receipt = {
        "receipt_id": _generate_receipt_id("embedding"),
        "receipt_type": "embedding_receipt",
        "artifact_id": artifact_id,
        "embedding_model": embedding_model,
        "model_revision": model_revision,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_hash": source_hash,
        "schema_version": "1.0.0"
    }
    _write_receipt(receipt)
    return receipt


def _write_receipt(receipt: dict) -> str:
    """Write receipt to disk and return the file path."""
    _ensure_receipts_dir()
    filename = f"{receipt['receipt_id']}.json"
    filepath = os.path.join(RECEIPTS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(receipt, f, indent=2)
    return filepath


def get_receipt(receipt_id: str) -> dict:
    """Retrieve a receipt by its ID."""
    _ensure_receipts_dir()
    filepath = os.path.join(RECEIPTS_DIR, f"{receipt_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return json.load(f)


def list_receipts(receipt_type: str = None, limit: int = 100, offset: int = 0) -> list:
    """List receipts with optional type filter."""
    _ensure_receipts_dir()
    receipts = []
    for fname in sorted(os.listdir(RECEIPTS_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(RECEIPTS_DIR, fname)) as f:
            receipt = json.load(f)
        if receipt_type and receipt.get("receipt_type") != receipt_type:
            continue
        receipts.append(receipt)
    return receipts[offset:offset + limit]
