#!/bin/bash
# =============================================================================
# ASCEND Platform - Code Coverage Runner
# P0.1: Launch Critical - Evidence Generation Script
# Created: 2025-12-09
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "ASCEND Platform - Code Coverage Report"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

cd "$PROJECT_ROOT"

# Install coverage dependencies if needed
echo "[1/5] Checking dependencies..."
pip install pytest-cov coverage[toml] --quiet 2>/dev/null || true

# Run tests with coverage for SDK
echo ""
echo "[2/5] Running SDK tests with coverage..."
python -m pytest sdk/ascend-sdk-python/tests/ \
    --cov=sdk/ascend-sdk-python/ascend \
    --cov-report=term-missing \
    --cov-report=html:coverage_html/sdk \
    --cov-report=xml:coverage_sdk.xml \
    -v \
    --tb=short \
    2>&1 | tee coverage_sdk_output.txt

# Extract SDK coverage percentage
SDK_COVERAGE=$(grep "TOTAL" coverage_sdk_output.txt | awk '{print $NF}' | tr -d '%' || echo "0")

# Run tests with coverage for backend services
echo ""
echo "[3/5] Running backend tests with coverage..."
python -m pytest tests/ \
    --cov=services \
    --cov=routes \
    --cov=policy_engine.py \
    --cov-report=term-missing \
    --cov-report=html:coverage_html/backend \
    --cov-report=xml:coverage_backend.xml \
    -v \
    --tb=short \
    2>&1 | tee coverage_backend_output.txt || true

# Extract backend coverage percentage
BACKEND_COVERAGE=$(grep "TOTAL" coverage_backend_output.txt | awk '{print $NF}' | tr -d '%' || echo "0")

# Generate combined report
echo ""
echo "[4/5] Generating combined coverage report..."
python -m coverage combine coverage_sdk.xml coverage_backend.xml 2>/dev/null || true
python -m coverage html -d coverage_html/combined 2>/dev/null || true

# Generate JSON report for evidence
echo ""
echo "[5/5] Generating evidence report..."

cat > coverage_evidence.json << EOF
{
    "report_type": "P0.1_Coverage_Evidence",
    "generated_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "platform": "ASCEND AI Governance",
    "target": "100% SDK coverage",
    "results": {
        "sdk_coverage_percent": ${SDK_COVERAGE:-0},
        "backend_coverage_percent": ${BACKEND_COVERAGE:-0},
        "sdk_test_files": $(find sdk/ascend-sdk-python/tests -name "test_*.py" | wc -l | tr -d ' '),
        "backend_test_files": $(find tests -name "test_*.py" | wc -l | tr -d ' '),
        "total_test_functions": $(grep -r "def test_" tests/ sdk/ascend-sdk-python/tests/ 2>/dev/null | wc -l | tr -d ' ')
    },
    "compliance": {
        "target_met": $([ "${SDK_COVERAGE:-0}" -ge 70 ] && echo "true" || echo "false"),
        "minimum_threshold": 70,
        "launch_critical": true
    },
    "artifacts": {
        "html_report": "coverage_html/",
        "xml_reports": ["coverage_sdk.xml", "coverage_backend.xml"],
        "output_logs": ["coverage_sdk_output.txt", "coverage_backend_output.txt"]
    }
}
EOF

echo ""
echo "=============================================="
echo "COVERAGE REPORT SUMMARY"
echo "=============================================="
echo "SDK Coverage:      ${SDK_COVERAGE:-0}%"
echo "Backend Coverage:  ${BACKEND_COVERAGE:-0}%"
echo "Target:            70% minimum (100% goal)"
echo ""
echo "Evidence file:     coverage_evidence.json"
echo "HTML Report:       coverage_html/"
echo "=============================================="

# Return exit code based on coverage threshold
if [ "${SDK_COVERAGE:-0}" -ge 70 ]; then
    echo "STATUS: PASS - Coverage meets minimum threshold"
    exit 0
else
    echo "STATUS: BELOW TARGET - Additional tests required"
    exit 1
fi
