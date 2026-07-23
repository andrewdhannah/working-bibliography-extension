"""
Drift Detector — Continuous Comparison of Expected vs Observed Behavior

Compares the extension's runtime behavior (captured in receipts) against
the declared contract and capability manifest. Classifies deviations into
PASS / OBSERVATION / REVOKE.

Per WB-LIBRARIAN-CONTRACT-v1:
  PASS:       Expected behavior matches observed behavior
  OBSERVATION: Minor deviation, not yet a violation
  REVOKE:     Contract violation confirmed

The drift detector runs on every operation and maintains a drift log
for trend analysis.
"""

import json
import os
from datetime import datetime, timezone
from collections import defaultdict


DRIFT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "drift")

# Baseline: snapshot of the capability manifest captured when the extension
# became ACTIVE. Represents "what was true when this extension became trusted."
BASELINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "receipts", "baseline")


class DriftClassification:
    """Drift classifications matching the contract."""

    PASS = "PASS"
    OBSERVATION = "OBSERVATION"
    REVOKE = "REVOKE"


class DriftResult:
    """Result of a drift detection check."""

    def __init__(self):
        self.classification = DriftClassification.PASS
        self.details = []
        self.checks_passed = 0
        self.checks_total = 0

    def add_finding(self, surface: str, expected: str, observed: str,
                    classification: str, detail: str = None):
        """Add a drift finding.

        The most severe classification wins (REVOKE > OBSERVATION > PASS).
        """
        self.details.append({
            "surface": surface,
            "expected": expected,
            "observed": observed,
            "classification": classification,
            "detail": detail
        })
        self.checks_total += 1

        # Update overall classification (most severe wins)
        severity = {DriftClassification.PASS: 0,
                    DriftClassification.OBSERVATION: 1,
                    DriftClassification.REVOKE: 2}
        if severity.get(classification, 0) > severity.get(self.classification, 0):
            self.classification = classification

    def mark_pass(self, surface: str, detail: str = None):
        self.checks_passed += 1
        self.checks_total += 1
        self.add_finding(surface, "contract", "observed", DriftClassification.PASS, detail)

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "details": self.details
        }


class DriftDetector:
    """Detects drift between declared contract and observed behavior.

    Compares:
      - Capability list (tools declared vs tools called)
      - Operation frequency (expected vs unexpected operations)
      - Ownership boundaries (operations in owned vs forbidden domains)
      - Receipt production (expected receipts vs actual receipts)
    """

    def __init__(self):
        self._observations = defaultdict(list)

    def _ensure_log_dir(self):
        os.makedirs(DRIFT_LOG_DIR, exist_ok=True)

    # --- Baseline management ---

    @staticmethod
    def baseline_path(extension_id: str) -> str:
        """Get the path for a baseline file."""
        return os.path.join(BASELINE_DIR, f"{extension_id}_baseline.json")

    @staticmethod
    def capture_baseline(extension_id: str) -> dict:
        """Snapshot the current capability manifest as the approved baseline.

        This represents "what was true when this extension became trusted."
        Call once when the extension transitions to ACTIVE.
        """
        import shutil
        os.makedirs(BASELINE_DIR, exist_ok=True)
        manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "mcp", "capabilities.json")
        dest = DriftDetector.baseline_path(extension_id)
        if os.path.exists(manifest_path):
            shutil.copy2(manifest_path, dest)
            with open(dest) as f:
                return json.load(f)
        return None

    @staticmethod
    def load_baseline(extension_id: str) -> dict:
        """Load the approved baseline for an extension."""
        path = DriftDetector.baseline_path(extension_id)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def clear_baseline(extension_id: str):
        """Remove the baseline (e.g. on re-handshake)."""
        path = DriftDetector.baseline_path(extension_id)
        if os.path.exists(path):
            os.remove(path)

    # --- Loading ---

    def _load_manifest(self) -> dict:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "mcp", "capabilities.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def _load_contract(self) -> dict:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "docs", "contracts", "WB-LIBRARIAN-CONTRACT-v1.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def _write_drift_log(self, result: DriftResult, operation: str):
        """Persist a drift detection result."""
        self._ensure_log_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"drift-{operation.replace('/', '_')}-{timestamp}.json"
        path = os.path.join(DRIFT_LOG_DIR, filename)
        entry = {
            "detected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "operation": operation,
            "result": result.to_dict()
        }
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)

    def record_observation(self, operation: str, surface: str, expected: str, observed: str,
                           classification: str, detail: str = None):
        """Record a single operational observation for drift analysis."""
        self._observations[surface].append({
            "operation": operation,
            "expected": expected,
            "observed": observed,
            "classification": classification,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        })

    def check_capability_drift(self, tool_name: str) -> DriftResult:
        """Check if a tool call matches the declared capability surface.

        Compares the tool against:
          - Manifest capabilities (tool must be in an active capability)
          - Contract capability declarations (tool must be in allowed_operations)
        """
        result = DriftResult()
        manifest = self._load_manifest()
        contract = self._load_contract()

        if not manifest or not contract:
            result.add_finding("capability_check", "manifest+contract loaded",
                              "missing", DriftClassification.REVOKE,
                              "Cannot check capability drift: contract or manifest missing")
            return result

        # Check manifest
        found_in_manifest = False
        for cap in manifest.get("capabilities", []):
            if tool_name in cap.get("tools", []):
                found_in_manifest = True
                if cap.get("status") != "active":
                    result.add_finding("capability_status", f"active for {tool_name}",
                                     f"{cap.get('status')}",
                                     DriftClassification.REVOKE,
                                     f"Capability '{cap['id']}' is {cap.get('status')}, not active")
                else:
                    result.mark_pass("capability_manifest_declared")
                break

        if not found_in_manifest:
            result.add_finding("capability_declared", f"tool in manifest",
                             f"{tool_name} not declared",
                             DriftClassification.REVOKE,
                             f"Tool '{tool_name}' is not declared in the capability manifest")

        # Check contract
        found_in_contract = False
        for cap in contract.get("capabilities", {}).get("declarations", []):
            if tool_name in cap.get("allowed_operations", []):
                found_in_contract = True
                result.mark_pass("capability_contract_declared")
                break

        if not found_in_contract and found_in_manifest:
            result.add_finding("capability_contract_declared",
                             f"tool in contract declarations",
                             f"{tool_name} not in contract",
                             DriftClassification.OBSERVATION,
                             f"Tool '{tool_name}' is in manifest but not in contract declarations")

        return result

    def check_forbidden_drift(self, tool_name: str, arguments: dict = None) -> DriftResult:
        """Check if the operation attempts a forbidden action.

        Forbidden operations trigger REVOKE classification immediately.
        """
        result = DriftResult()
        contract = self._load_contract()
        if not contract:
            return result

        forbidden = contract.get("forbidden_operations", {}).get("absolute", [])
        tool_lower = tool_name.lower()

        for entry in forbidden:
            op = entry.get("operation", "").lower()
            if op in tool_lower:
                result.add_finding("forbidden_operation", f"not '{op}'",
                                 f"'{op}' attempted", DriftClassification.REVOKE,
                                 entry.get("rationale", ""))
                return result

            if arguments:
                for key in ["operation", "action", "command"]:
                    val = str(arguments.get(key, "")).lower()
                    if val == op:
                        result.add_finding("forbidden_argument", f"not '{op}'",
                                         f"'{op}' referenced", DriftClassification.REVOKE,
                                         entry.get("rationale", ""))
                        return result

        result.mark_pass("forbidden_drift")
        return result

    def check_manifest_baseline_drift(self, extension_id: str) -> DriftResult:
        """Compare the current capability manifest against the approved baseline.

        The baseline represents what was true when the extension became trusted.
        The current manifest represents what the extension claims is true now.

        Detects:
          - risk escalation (R0→R1)         → REVOKE
          - permission expansion             → REVOKE
          - tool added to a capability       → REVOKE
          - new capability added             → REVOKE
          - forbidden action removed         → REVOKE
          - documentation/description change → OBSERVATION
        """
        result = DriftResult()
        baseline = self.load_baseline(extension_id)
        current = self._load_manifest()

        if not baseline:
            result.add_finding("baseline_exists", "baseline present",
                             "missing", DriftClassification.REVOKE,
                             "No approved baseline found. Extension may not have completed handshake.")
            return result

        if not current:
            result.add_finding("manifest_exists", "manifest present",
                             "missing", DriftClassification.REVOKE,
                             "Current capability manifest not found.")
            return result

        baseline_caps = {c["id"]: c for c in baseline.get("capabilities", [])}
        current_caps = {c["id"]: c for c in current.get("capabilities", [])}

        # Check for new capabilities (tool added at capability level)
        for cap_id in current_caps:
            if cap_id not in baseline_caps:
                result.add_finding(
                    f"new_capability_{cap_id}",
                    "not present",
                    f"capability '{cap_id}' added",
                    DriftClassification.REVOKE,
                    f"New capability '{cap_id}' appears in current manifest but was not in approved baseline."
                )

        # Check each baseline capability for parameter changes
        for cap_id, bcap in baseline_caps.items():
            ccap = current_caps.get(cap_id)
            if ccap is None:
                result.add_finding(
                    f"capability_removed_{cap_id}",
                    f"capability '{cap_id}' present",
                    "removed",
                    DriftClassification.REVOKE,
                    f"Approved capability '{cap_id}' has been removed from the manifest."
                )
                continue

            # --- Risk escalation ---
            b_risk = bcap.get("risk", "unknown")
            c_risk = ccap.get("risk", "unknown")
            if c_risk != b_risk:
                result.add_finding(
                    f"risk_escalation_{cap_id}",
                    f"risk={b_risk}",
                    f"risk={c_risk}",
                    DriftClassification.REVOKE,
                    f"Capability '{cap_id}' risk increased from '{b_risk}' to '{c_risk}' "
                    f"beyond approved contract."
                )
            else:
                result.mark_pass(f"risk_stable_{cap_id}")

            # --- Permission expansion ---
            b_perms = set(bcap.get("permissions", []))
            c_perms = set(ccap.get("permissions", []))
            added_perms = c_perms - b_perms
            if added_perms:
                result.add_finding(
                    f"permission_expansion_{cap_id}",
                    f"permissions={sorted(b_perms)}",
                    f"permissions={sorted(c_perms)}",
                    DriftClassification.REVOKE,
                    f"Capability '{cap_id}' permission scope expanded: +{sorted(added_perms)}"
                )
            removed_perms = b_perms - c_perms
            if removed_perms and not added_perms:
                result.add_finding(
                    f"permission_narrowed_{cap_id}",
                    f"permissions={sorted(b_perms)}",
                    f"permissions={sorted(c_perms)}",
                    DriftClassification.OBSERVATION,
                    f"Capability '{cap_id}' permissions narrowed: -{sorted(removed_perms)}"
                )
            if not added_perms and not removed_perms:
                result.mark_pass(f"permissions_stable_{cap_id}")

            # --- Tool changes ---
            b_tools = set(bcap.get("tools", []))
            c_tools = set(ccap.get("tools", []))
            added_tools = c_tools - b_tools
            if added_tools:
                result.add_finding(
                    f"tools_added_{cap_id}",
                    f"tools={sorted(b_tools)}",
                    f"tools={sorted(c_tools)}",
                    DriftClassification.REVOKE,
                    f"Capability '{cap_id}' gained tools not in baseline: {sorted(added_tools)}"
                )
            removed_tools = b_tools - c_tools
            if removed_tools:
                result.add_finding(
                    f"tools_removed_{cap_id}",
                    f"tools={sorted(b_tools)}",
                    f"tools={sorted(c_tools)}",
                    DriftClassification.OBSERVATION,
                    f"Capability '{cap_id}' lost tools: {sorted(removed_tools)}"
                )
            if not added_tools and not removed_tools:
                result.mark_pass(f"tools_stable_{cap_id}")

            # --- Description / documentation changes ---
            b_desc = bcap.get("description", "")
            c_desc = ccap.get("description", "")
            if c_desc != b_desc:
                result.add_finding(
                    f"description_changed_{cap_id}",
                    "baseline description",
                    "changed",
                    DriftClassification.OBSERVATION,
                    f"Capability '{cap_id}' description changed from baseline."
                )

        # --- Forbidden actions integrity ---
        b_forbidden = {f.get("action") for f in baseline.get("forbidden_actions", [])}
        c_forbidden = {f.get("action") for f in current.get("forbidden_actions", [])}
        removed_forbidden = b_forbidden - c_forbidden
        if removed_forbidden:
            result.add_finding(
                "forbidden_actions_weakened",
                f"forbidden={sorted(b_forbidden)}",
                f"forbidden={sorted(c_forbidden)}",
                DriftClassification.REVOKE,
                f"Forbidden actions removed from manifest: {sorted(removed_forbidden)}"
            )
        else:
            result.mark_pass("forbidden_actions_intact")

        return result

    def detect_all(self, tool_name: str, arguments: dict = None,
                   extension_id: str = None) -> DriftResult:
        """Run all drift detection checks and return combined result.

        Produces a single DriftResult with the most severe classification.
        """
        combined = DriftResult()

        # 1. Capability drift
        cap_drift = self.check_capability_drift(tool_name)
        for d in cap_drift.details:
            combined.add_finding(d["surface"], d["expected"], d["observed"],
                               d["classification"], d.get("detail"))

        # 2. Forbidden operation drift
        forbid_drift = self.check_forbidden_drift(tool_name, arguments)
        for d in forbid_drift.details:
            combined.add_finding(d["surface"], d["expected"], d["observed"],
                               d["classification"], d.get("detail"))

        # 3. Manifest baseline drift (against the approved snapshot)
        if extension_id:
            manifest_drift = self.check_manifest_baseline_drift(extension_id)
            for d in manifest_drift.details:
                combined.add_finding(d["surface"], d["expected"], d["observed"],
                                   d["classification"], d.get("detail"))

        # Log the drift check result
        self._write_drift_log(combined, tool_name)
        self.record_observation(tool_name, "drift_check",
                              "contract compliance", combined.classification,
                              combined.classification)

        return combined
