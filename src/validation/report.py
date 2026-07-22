"""
Validation Report — Structured Compliance Documentation

Generates reports from validation results. Reports include:
  - Per-domain pass/fail status
  - Failed check details
  - Receipt references
  - Overall compliance verdict
"""

from datetime import datetime, timezone


class ValidationReport:
    """Structured validation report for compliance documentation."""

    def __init__(self, subject: str = "working-bibliography-extension"):
        self.subject = subject
        self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.fixture_results = []
        self.overall_verdict = None

    def add_fixture_result(self, fixture_result):
        """Add a fixture result to the report."""
        self.fixture_results.append(fixture_result)

    def generate(self) -> dict:
        """Generate the final report.

        Returns:
            dict with summary, per-domain results, and verdict
        """
        total = len(self.fixture_results)
        passed = sum(1 for r in self.fixture_results if r.passed)

        if total == 0:
            self.overall_verdict = "NO_TESTS_RUN"
        elif passed == total:
            self.overall_verdict = "COMPLIANT"
        elif passed >= total * 0.8:
            self.overall_verdict = "PARTIALLY_COMPLIANT"
        else:
            self.overall_verdict = "NON_COMPLIANT"

        # Aggregate domain results
        domain_stats = {}
        for r in self.fixture_results:
            if r.actual:
                for domain_name, domain_res in r.actual.domains.items():
                    if domain_name not in domain_stats:
                        domain_stats[domain_name] = {"passed": 0, "failed": 0, "total": 0}
                    ds = domain_stats[domain_name]
                    ds["total"] += 1
                    if domain_res.passed:
                        ds["passed"] += 1
                    else:
                        ds["failed"] += 1

        return {
            "report_subject": self.subject,
            "generated_at": self.generated_at,
            "overall_verdict": self.overall_verdict,
            "summary": {
                "fixtures_total": total,
                "fixtures_passed": passed,
                "fixtures_failed": total - passed,
                "pass_rate": f"{passed / total * 100:.0f}%" if total > 0 else "N/A"
            },
            "domain_statistics": domain_stats,
            "fixture_results": [
                {
                    "name": r.fixture_name,
                    "category": r.category,
                    "expected": "PASS" if r.expected_pass else "FAIL",
                    "actual": "PASS" if r.actual.all_passed else "FAIL",
                    "result": "PASS" if r.passed else "FAIL",
                    "receipt": r.receipt_id
                }
                for r in self.fixture_results
            ],
            "failed_fixtures": [
                {
                    "name": r.fixture_name,
                    "expected": "PASS" if r.expected_pass else "FAIL",
                    "actual": "PASS" if r.actual.all_passed else "FAIL",
                    "receipt": r.receipt_id
                }
                for r in self.fixture_results if not r.passed
            ]
        }
