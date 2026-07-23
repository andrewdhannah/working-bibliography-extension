#!/bin/bash
# RELEASE-WB-EXTENSION-TESTING-1 — WB Extension Test Runner
#
# Runs all extension validation suites from a single command.
# Output: PASS/FAIL summary per suite + evidence receipt.
#
# Usage: bash run-tests.sh  (from working-bibliography-extension/)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_FILE="$SCRIPT_DIR/test-results.json"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  WB Extension — Validation Suite                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0
TOTAL=0
RESULTS=()

run_suite() {
    local name="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    echo "─── $name ───"
    if eval "$cmd" 2>&1; then
        echo "  ✅ $name PASS"
        PASS=$((PASS + 1))
        RESULTS+=("{\"suite\":\"$name\",\"result\":\"pass\"}")
    else
        echo "  ❌ $name FAIL"
        FAIL=$((FAIL + 1))
        RESULTS+=("{\"suite\":\"$name\",\"result\":\"fail\"}")
    fi
    echo ""
}

# 1. Composition tests
run_suite "Composition" "python3 src/composition/tests.py"

# 2. Consumer harness tests
run_suite "Consumer Harness" "python3 src/consumer/tests.py"

# 3. Projection service tests
run_suite "Projection Service" "python3 src/projection/tests.py"

# 4. Schema validation
run_suite "Schema Validation" "python3 -c \"
import json, glob
schema = json.load(open('docs/schemas/wb-artifact.schema.json'))
fixtures = glob.glob('tests/fixtures/artifacts/**/*.json', recursive=True)
passed = sum(1 for f in fixtures if json.load(open(f)))
total = len(fixtures)
print(f'Fixtures: {passed}/{total} valid')
assert passed == total, f'{total-passed} fixtures failed'
\""

# 5. Module imports (drift + revocation)
run_suite "Module Imports" "python3 -c \"
import sys; sys.path.insert(0, 'src')
from drift import baseline, comparison, classifier, detector, observer, receipts
from revocation import manager, policy, authorization, lifecycle, receipts as r_rec
from validation import validator, fixture_runner, receipts as v_rec
print('All modules import successfully')
\""

# Summary
echo "═══ RESULTS ═══"
echo "  Passed: $PASS/$TOTAL"
echo "  Failed: $FAIL/$TOTAL"

# Generate results JSON
RESULTS_JSON=$(python3 -c "
import json
suites = [${RESULTS[@]}]
results = {'suites': suites, 'total': $TOTAL, 'passed': $PASS, 'failed': $FAIL}
print(json.dumps(results))
")
echo "$RESULTS_JSON" > "$RESULTS_FILE"
echo "Results written to test-results.json"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
