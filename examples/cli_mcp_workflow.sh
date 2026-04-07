#!/bin/bash
#
# UITestFlow CLI MCP Workflow Example
#
# This script demonstrates the complete MCP CLI workflow:
# 1. Check MCP status
# 2. Generate tests from natural language
# 3. Run tests with Claude guidance
# 4. View results
#
# Requirements:
# - UITestFlow installed (pip install uitestflow)
# - ANTHROPIC_API_KEY environment variable set
# - Playwright browsers installed (playwright install)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="./generated_tests"
RESULTS_DIR="./test_results"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if uitestflow is installed
    if ! command -v uitestflow &> /dev/null; then
        print_error "UITestFlow is not installed"
        echo "Install with: pip install uitestflow"
        exit 1
    fi
    print_success "UITestFlow is installed"

    # Check API key
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_error "ANTHROPIC_API_KEY environment variable is not set"
        echo "Set it with: export ANTHROPIC_API_KEY='your-key-here'"
        exit 1
    fi
    print_success "ANTHROPIC_API_KEY is set"

    echo ""
}

# Step 1: Check MCP status
check_mcp_status() {
    print_header "Step 1: Check MCP Status"

    uitestflow mcp-status --verbose

    echo ""
}

# Step 2: Generate test from natural language
generate_login_test() {
    print_header "Step 2: Generate Login Test"

    print_info "Generating test from description..."

    mkdir -p "$OUTPUT_DIR"

    uitestflow generate \
        "Login to the application with username 'admin' and password 'admin123', then verify the dashboard loads" \
        --output "$OUTPUT_DIR/login_test.yaml" \
        --model claude-3-5-haiku-20241022 \
        --verbose

    if [ -f "$OUTPUT_DIR/login_test.yaml" ]; then
        print_success "Login test generated successfully"
        echo ""
        print_info "Generated test file:"
        cat "$OUTPUT_DIR/login_test.yaml"
    else
        print_error "Failed to generate login test"
        exit 1
    fi

    echo ""
}

# Step 3: Generate search test
generate_search_test() {
    print_header "Step 3: Generate Search Test"

    print_info "Generating search test..."

    uitestflow generate \
        "Navigate to google.com, search for 'UITestFlow', and verify results appear" \
        --output "$OUTPUT_DIR/search_test.yaml" \
        --model claude-3-5-haiku-20241022

    if [ -f "$OUTPUT_DIR/search_test.yaml" ]; then
        print_success "Search test generated successfully"
    else
        print_error "Failed to generate search test"
        exit 1
    fi

    echo ""
}

# Step 4: Generate form test
generate_form_test() {
    print_header "Step 4: Generate Form Submission Test"

    print_info "Generating form test..."

    uitestflow generate \
        "Fill out a contact form with name 'John Doe', email 'john@example.com', message 'Test message', and submit" \
        --output "$OUTPUT_DIR/form_test.yaml" \
        --dry-run  # Preview only, don't save

    echo ""
}

# Step 5: List generated tests
list_generated_tests() {
    print_header "Step 5: Review Generated Tests"

    if [ -d "$OUTPUT_DIR" ]; then
        print_info "Generated test files:"
        ls -lh "$OUTPUT_DIR"/*.yaml 2>/dev/null || echo "No test files found"
    fi

    echo ""
}

# Step 6: Run test with Claude guidance (simulation)
run_with_claude_guidance() {
    print_header "Step 6: Run Test with Claude Guidance"

    if [ ! -f "$OUTPUT_DIR/search_test.yaml" ]; then
        print_error "Search test not found, skipping execution"
        return
    fi

    print_info "This would run the test with Claude guidance:"
    echo "  uitestflow run-with-claude $OUTPUT_DIR/search_test.yaml --model claude-3-5-haiku-20241022"

    print_info "Skipping actual execution to avoid browser automation"
    print_info "To run for real, execute the command above"

    echo ""
}

# Step 7: Demonstrate MCP server (simulation)
demonstrate_mcp_server() {
    print_header "Step 7: MCP Server (Simulation)"

    print_info "The MCP server exposes browser automation to Claude"
    print_info "Start it with:"
    echo "  uitestflow mcp-server --transport stdio"

    print_info "Or with HTTP (when implemented):"
    echo "  uitestflow mcp-server --transport http --port 3001"

    print_info "Skipping actual server start to keep demo non-blocking"

    echo ""
}

# Step 8: Summary
print_summary() {
    print_header "Workflow Complete!"

    echo "Summary of what we did:"
    echo ""
    echo "1. ✓ Checked MCP status and configuration"
    echo "2. ✓ Generated login test from natural language"
    echo "3. ✓ Generated search test"
    echo "4. ✓ Previewed form test generation (dry-run)"
    echo "5. ✓ Listed all generated tests"
    echo "6. ✓ Demonstrated Claude-guided execution (simulation)"
    echo "7. ✓ Explained MCP server usage"
    echo ""

    print_info "Generated test files are in: $OUTPUT_DIR"
    echo ""

    print_success "Next steps:"
    echo "  - Review the generated test files"
    echo "  - Customize tests as needed"
    echo "  - Run tests with: uitestflow run <test-file>"
    echo "  - Run with Claude guidance: uitestflow run-with-claude <test-file>"
    echo ""
}

# Main execution
main() {
    echo ""
    print_header "UITestFlow MCP CLI Workflow Demo"
    echo ""

    check_prerequisites
    check_mcp_status
    generate_login_test
    generate_search_test
    generate_form_test
    list_generated_tests
    run_with_claude_guidance
    demonstrate_mcp_server
    print_summary
}

# Run main function
main
