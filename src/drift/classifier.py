"""
Drift Classifier — Deterministic PASS / OBSERVATION / REVOKE

Takes comparison results from all drift domains and produces a single
classified scan result. Classification is deterministic based on the
type and severity of detected drift.

Classification rules:

  PASS:
    All domains match baseline.
    Only ordering changes detected.

  OBSERVATION:
    Capability removed (tool no longer present).
    Contract version changed (re-handshake needed).
    Risk de-escalated (R1 → R0).
    Permission scope narrowed.

  REVOKE:
    Extension ID changed.
    Contract ID changed.
    Unexpected capability added.
    Risk escalated (R0 → R1).
    Forbidden operations removed from contract.
"""

from . import comparison as drift_comparison


class DriftClassification:
    """Classification results for a full drift scan."""

    PASS = "PASS"
    OBSERVATION = "OBSERVATION"
    REVOKE = "REVOKE"

    def __init__(self):
        self.classification = self.PASS
        self.reason = None
        self.findings = []
        self.domain_results = {}

    def add_domain_result(self, domain: str, result: drift_comparison.ComparisonResult):
        """Add a domain comparison result and classify it."""
        self.domain_results[domain] = result.to_dict()

        if result.match:
            return  # PASS — no findings

        for diff in result.differences:
            finding = self._classify_finding(domain, diff)
            self.findings.append({
                "domain": domain,
                "field": diff.get("field"),
                "description": diff.get("description"),
                "classification": finding
            })

            # Update overall classification (most severe wins)
            if self._severity(finding) > self._severity(self.classification):
                self.classification = finding
                self.reason = diff.get("description")

    def _classify_finding(self, domain: str, diff: dict) -> str:
        """Determine classification for a single difference.

        Rules are deterministic:
          - Identity changes → REVOKE
          - Added capabilities → REVOKE
          - Risk escalation → REVOKE
          - Forbidden ops removed → REVOKE
          - Removed capabilities → OBSERVATION
          - Contract version change → OBSERVATION
          - Risk de-escalation → OBSERVATION
          - Permission scope change → OBSERVATION
        """
        field = diff.get("field", "")
        desc = diff.get("description", "")

        # REVOKE triggers
        if "_added" in field and "unexpected" in desc.lower():
            return self.REVOKE
        if "_escalation" in field:
            return self.REVOKE
        if "forbidden_removed" in field:
            return self.REVOKE
        if "extension_id" in field.lower() and "changed" in desc.lower():
            return self.REVOKE
        if "contract_id" in field.lower() and "changed" in desc.lower():
            return self.REVOKE

        # OBSERVATION triggers
        if "_removed" in field:
            return self.OBSERVATION
        if "_deescalation" in field:
            return self.OBSERVATION
        if "contract_version" in field.lower():
            return self.OBSERVATION
        if "forbidden_added" in field:
            return self.OBSERVATION

        # Default for unclassified drift
        return self.OBSERVATION

    @staticmethod
    def _severity(cls: str) -> int:
        severity_map = {
            DriftClassification.PASS: 0,
            DriftClassification.OBSERVATION: 1,
            DriftClassification.REVOKE: 2,
        }
        return severity_map.get(cls, 0)

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "reason": self.reason,
            "finding_count": len(self.findings),
            "findings": self.findings,
            "domain_results": self.domain_results
        }


def classify_drift(identity_result, manifest_tools_result, manifest_risks_result,
                   contract_version_result, permissions_result,
                   boundary_result=None, receipt_result=None) -> DriftClassification:
    """Run classification across all drift domains.

    Takes ComparisonResult objects from each domain and produces a
    single DriftClassification with the most severe finding.
    """
    classifier = DriftClassification()

    # Evaluate each domain
    classifier.add_domain_result("identity", identity_result)
    classifier.add_domain_result("capability_tools", manifest_tools_result)
    classifier.add_domain_result("capability_risk", manifest_risks_result)
    classifier.add_domain_result("contract_version", contract_version_result)
    classifier.add_domain_result("permissions", permissions_result)

    if boundary_result:
        classifier.add_domain_result("boundary", boundary_result)
    if receipt_result:
        classifier.add_domain_result("receipt_evidence", receipt_result)

    return classifier
