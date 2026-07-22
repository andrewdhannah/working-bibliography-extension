"""
Fixture Runner — Load and Execute Validation Fixtures

Loads fixture files from tests/fixtures/validation/ and runs them through
the validation suite. Supports valid, invalid, and boundary categories.

Each fixture is a JSON file containing:
  - description: Human-readable test description
  - category: valid, invalid, or boundary
  - expected: Expected validation result (pass or fail)
  - data: The extension data to validate
"""

import json
import os
import glob
from datetime import datetime, timezone

from . import validator as v
from . import report as vr
from . import receipts as v_rec


FIXTURE_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "tests", "fixtures", "validation")


class FixtureResult:
    """Result of running a single fixture through validation."""

    def __init__(self, fixture_path: str):
        self.fixture_path = fixture_path
        self.fixture_name = os.path.basename(fixture_path).replace(".json", "")
        self.description = ""
        self.category = ""
        self.expected_pass = False
        self.actual = None
        self.receipt_id = None
        self.passed = False

    def to_dict(self) -> dict:
        return {
            "fixture": self.fixture_name,
            "description": self.description,
            "category": self.category,
            "expected_pass": self.expected_pass,
            "actual_pass": self.actual.all_passed if self.actual else None,
            "result": "PASS" if self.passed else "FAIL",
            "receipt_id": self.receipt_id,
            "details": self.actual.to_dict() if self.actual else None
        }


def load_fixture(path: str) -> dict:
    """Load a single fixture file."""
    with open(path) as f:
        return json.load(f)


def run_fixture(fixture_data: dict, fixture_path: str = "") -> FixtureResult:
    """Run a single fixture through the full validation suite.

    Args:
        fixture_data: The parsed fixture JSON
        fixture_path: Path to the fixture file (for reference)

    Returns:
        FixtureResult with validation outcome
    """
    result = FixtureResult(fixture_path)
    result.description = fixture_data.get("description", "")
    result.category = fixture_data.get("category", "unknown")
    result.expected_pass = fixture_data.get("expected", {}).get("pass", True)

    # Run validation
    data = fixture_data.get("data", {})
    result.actual = v.run_full_validation(data)

    # Check if actual matches expected
    result.passed = (result.actual.all_passed == result.expected_pass)

    # Generate receipt
    receipt = v_rec.generate_validation_receipt(
        fixture_name=result.fixture_name,
        category=result.category,
        passed=result.passed,
        domains_passed=result.actual.to_dict()["domains_passed"],
        domains_total=result.actual.to_dict()["domains_total"]
    )
    result.receipt_id = receipt["receipt_id"]

    return result


def run_all_fixtures(categories: list = None) -> list:
    """Run all validation fixtures (or a subset of categories).

    Args:
        categories: List of category dirs to scan (default: all)

    Returns:
        List of FixtureResult objects
    """
    if categories is None:
        categories = ["valid", "invalid", "boundary"]

    results = []

    for category in categories:
        pattern = os.path.join(FIXTURE_BASE, category, "*.json")
        for fixture_path in sorted(glob.glob(pattern)):
            fixture_data = load_fixture(fixture_path)
            fr = run_fixture(fixture_data, fixture_path)
            results.append(fr)

    return results


def print_summary(results: list):
    """Print a human-readable summary of fixture results."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print(f"\nValidation Results: {passed}/{total} passed")
    print(f"{'='*50}")

    for r in results:
        status = "✅" if r.passed else "❌"
        expected = "PASS" if r.expected_pass else "FAIL"
        got = "PASS" if r.actual.all_passed else "FAIL"
        print(f"  {status} [{r.category}] {r.fixture_name}")
        print(f"      Expected: {expected} | Got: {got}")
        print(f"      {r.description[:80]}")
        if not r.passed:
            # Show what went wrong
            for domain_name, domain_res in r.actual.domains.items():
                if not domain_res.passed:
                    failed = [c for c in domain_res.checks if not c["passed"]]
                    for f in failed[:2]:
                        print(f"      → {domain_name}: {f['detail'][:80]}")

    return passed == total
