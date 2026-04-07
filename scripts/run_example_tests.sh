#!/bin/bash

set -e

echo "========================================"
echo "UITestFlow MCP Example Tests Runner"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EXAMPLES_DIR="examples/tests"
RESULTS_DIR="reports/example_runs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$RESULTS_DIR/$TIMESTAMP"

# Test files
TESTS=(
    "login_flow.yaml"
    "form_submission.yaml"
    "navigation_flow.yaml"
    "search_workflow.yaml"
    "e2e_shopping.yaml"
)

# Stats
TOTAL_TESTS=${#TESTS[@]}
PASSED=0
FAILED=0
FAILED_TESTS=()

# Create results directory
echo "Creating results directory: $RUN_DIR"
mkdir -p "$RUN_DIR"
echo ""

# Function to run a single test
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file" .yaml)
    local test_path="$EXAMPLES_DIR/$test_file"

    echo "----------------------------------------"
    echo -e "${YELLOW}Running test: $test_name${NC}"
    echo "----------------------------------------"

    # Check if test file exists
    if [ ! -f "$test_path" ]; then
        echo -e "${RED}ERROR: Test file not found: $test_path${NC}"
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("$test_name (file not found)")
        return 1
    fi

    # Run the test
    local result_file="$RUN_DIR/${test_name}_result.json"
    local log_file="$RUN_DIR/${test_name}.log"

    if uitestflow run "$test_path" --output "$result_file" > "$log_file" 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Log: $log_file"
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("$test_name")

        # Show last 10 lines of log
        echo "  Last 10 lines of log:"
        tail -n 10 "$log_file" | sed 's/^/    /'
    fi

    echo ""
}

# Check if uitestflow command is available
if ! command -v uitestflow &> /dev/null; then
    echo -e "${RED}ERROR: uitestflow command not found${NC}"
    echo "Please install UITestFlow first:"
    echo "  pip install -e ."
    exit 1
fi

# Check if examples directory exists
if [ ! -d "$EXAMPLES_DIR" ]; then
    echo -e "${RED}ERROR: Examples directory not found: $EXAMPLES_DIR${NC}"
    exit 1
fi

# Run all tests
echo "Running $TOTAL_TESTS example tests..."
echo ""

for test in "${TESTS[@]}"; do
    run_test "$test"
done

# Summary
echo "========================================"
echo "Test Run Summary"
echo "========================================"
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED${NC}"
echo -e "Failed:       ${RED}$FAILED${NC}"
echo ""
echo "Results saved to: $RUN_DIR"
echo ""

# List failed tests
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed Tests:${NC}"
    for failed_test in "${FAILED_TESTS[@]}"; do
        echo "  - $failed_test"
    done
    echo ""
fi

# Generate HTML report
echo "Generating HTML report..."
REPORT_FILE="$RUN_DIR/index.html"

cat > "$REPORT_FILE" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>UITestFlow Example Tests Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            color: #666;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 1px;
        }
        .passed { color: #10b981; }
        .failed { color: #ef4444; }
        .test-list {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .test-item {
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-item:last-child {
            border-bottom: none;
        }
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge.passed {
            background: #d1fae5;
            color: #065f46;
        }
        .badge.failed {
            background: #fee2e2;
            color: #991b1b;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>UITestFlow MCP Example Tests</h1>
        <p>Automated test execution report</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">Total Tests</div>
            <div class="stat-value">TOTAL_TESTS_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Passed</div>
            <div class="stat-value passed">PASSED_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Failed</div>
            <div class="stat-value failed">FAILED_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Success Rate</div>
            <div class="stat-value">SUCCESS_RATE_PLACEHOLDER%</div>
        </div>
    </div>

    <div class="test-list">
        <h2>Test Results</h2>
        TEST_RESULTS_PLACEHOLDER
    </div>

    <div class="footer">
        <p>Generated on TIMESTAMP_PLACEHOLDER</p>
        <p>UITestFlow MCP Integration - Phase 6</p>
    </div>
</body>
</html>
EOF

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL_TESTS))
else
    SUCCESS_RATE=0
fi

# Build test results HTML
TEST_RESULTS_HTML=""
for test in "${TESTS[@]}"; do
    test_name=$(basename "$test" .yaml)

    # Check if test passed or failed
    if [[ " ${FAILED_TESTS[@]} " =~ " ${test_name} " ]]; then
        status="failed"
        badge_text="FAILED"
    else
        status="passed"
        badge_text="PASSED"
    fi

    TEST_RESULTS_HTML+="<div class=\"test-item\">"
    TEST_RESULTS_HTML+="<span>$test_name</span>"
    TEST_RESULTS_HTML+="<span class=\"badge $status\">$badge_text</span>"
    TEST_RESULTS_HTML+="</div>"
done

# Replace placeholders in HTML
sed -i.bak "s/TOTAL_TESTS_PLACEHOLDER/$TOTAL_TESTS/g" "$REPORT_FILE"
sed -i.bak "s/PASSED_PLACEHOLDER/$PASSED/g" "$REPORT_FILE"
sed -i.bak "s/FAILED_PLACEHOLDER/$FAILED/g" "$REPORT_FILE"
sed -i.bak "s/SUCCESS_RATE_PLACEHOLDER/$SUCCESS_RATE/g" "$REPORT_FILE"
sed -i.bak "s|TEST_RESULTS_PLACEHOLDER|$TEST_RESULTS_HTML|g" "$REPORT_FILE"
sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date)/g" "$REPORT_FILE"
rm -f "$REPORT_FILE.bak"

echo -e "${GREEN}Report generated: $REPORT_FILE${NC}"
echo ""

# Open report in browser if requested
if [ "$1" == "--open-report" ] || [ "$1" == "-o" ]; then
    echo "Opening report in browser..."

    if command -v open &> /dev/null; then
        # macOS
        open "$REPORT_FILE"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "$REPORT_FILE"
    elif command -v start &> /dev/null; then
        # Windows
        start "$REPORT_FILE"
    else
        echo "Could not detect browser opener. Please open manually:"
        echo "  file://$(pwd)/$REPORT_FILE"
    fi
fi

# Exit with error code if any tests failed
if [ $FAILED -gt 0 ]; then
    exit 1
fi

exit 0
