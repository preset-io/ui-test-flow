#!/bin/bash
# UITestFlow Setup Validation Script
# This script checks that all required configuration files are in place

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}UITestFlow Setup Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if file exists
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file ${RED}(MISSING)${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to check if command exists
check_command() {
    local cmd=$1
    local description=$2

    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} $description: ${version}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $cmd ${RED}(NOT FOUND)${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

echo -e "${YELLOW}Checking Configuration Files...${NC}"
echo ""

# Python project files
check_file "pyproject.toml" "Project configuration"
check_file "requirements.txt" "Production dependencies"
check_file "requirements-dev.txt" "Development dependencies"

# Docker files
check_file "Dockerfile" "Docker image definition"
check_file "docker-compose.yml" "Docker Compose configuration"
check_file ".dockerignore" "Docker ignore patterns"

# Development tooling
check_file ".pre-commit-config.yaml" "Pre-commit hooks configuration"
check_file "ruff.toml" "Ruff linter configuration"
check_file "mypy.ini" "MyPy type checker configuration"
check_file "pytest.ini" "Pytest configuration"
check_file ".yamllint.yaml" "YAML linter configuration"
check_file ".gitignore" "Git ignore patterns"
check_file ".env.example" "Environment variables template"

# Build files
check_file "Makefile" "Build automation"

# Documentation
check_file "README.md" "Project README"
check_file "SETUP.md" "Setup guide"
check_file "project.md" "Project specification"

echo ""
echo -e "${YELLOW}Checking System Dependencies...${NC}"
echo ""

# Check for required tools
check_command "python3" "Python"
check_command "pip3" "pip"
check_command "docker" "Docker"
check_command "docker-compose" "Docker Compose"
check_command "git" "Git"
check_command "make" "Make"

echo ""
echo -e "${YELLOW}Checking Python Version...${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION (>= $REQUIRED_VERSION)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Python version: $PYTHON_VERSION ${RED}(requires >= $REQUIRED_VERSION)${NC}"
    ((CHECKS_FAILED++))
fi

echo ""
echo -e "${YELLOW}Checking Virtual Environment...${NC}"
echo ""

if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists: .venv"
    ((CHECKS_PASSED++))

    if [ -f ".venv/bin/python" ]; then
        VENV_VERSION=$(.venv/bin/python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo -e "${GREEN}✓${NC} Virtual environment Python: $VENV_VERSION"
        ((CHECKS_PASSED++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not created yet"
    echo -e "    Run: ${BLUE}make setup${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e ""
    echo -e "Next steps:"
    echo -e "  1. Copy .env.example to .env and configure"
    echo -e "  2. Run: ${BLUE}make setup${NC}"
    echo -e "  3. Run: ${BLUE}make docker-up${NC}"
    echo -e "  4. Visit: ${BLUE}http://localhost:8080${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo -e ""
    echo -e "Please review the errors above and:"
    echo -e "  1. Install missing system dependencies"
    echo -e "  2. Create missing configuration files"
    echo -e "  3. Run this script again"
    echo ""
    exit 1
fi
