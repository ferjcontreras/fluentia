#!/bin/bash
# Code quality check script
# Runs ruff, mypy, and pylint with clear pass/fail indicators
#
# Usage: ./check_code.sh
#
# Prerequisites: uv must be installed and `uv sync --group dev` must have been run

set -o pipefail  # Catch errors in pipelines

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Track overall status
OVERALL_STATUS=0

# Print section header
print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Print success message
print_success() {
    echo ""
    echo -e "${GREEN}${BOLD}✓ $1 PASSED${NC}"
}

# Print failure message
print_failure() {
    echo ""
    echo -e "${RED}${BOLD}✗ $1 FAILED${NC}"
}

# Print final summary
print_summary() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $OVERALL_STATUS -eq 0 ]; then
        echo -e "${GREEN}${BOLD}  ALL CHECKS PASSED ✓${NC}"
    else
        echo -e "${RED}${BOLD}  SOME CHECKS FAILED ✗${NC}"
    fi
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Run ruff format
print_header "1/4: Running ruff format"
if uv run ruff format .; then
    print_success "ruff format"
else
    print_failure "ruff format"
    OVERALL_STATUS=1
fi

# Run ruff check --fix
print_header "2/4: Running ruff check --fix"
if uv run ruff check --fix .; then
    print_success "ruff check"
else
    print_failure "ruff check"
    OVERALL_STATUS=1
fi

# Run mypy
print_header "3/4: Running mypy"
if uv run mypy src/fluentia tests; then
    print_success "mypy"
else
    print_failure "mypy"
    OVERALL_STATUS=1
fi

# Run pylint
print_header "4/4: Running pylint"
if uv run pylint src/fluentia; then
    print_success "pylint"
else
    print_failure "pylint"
    OVERALL_STATUS=1
fi

# Print final summary
print_summary

# Exit with overall status
exit $OVERALL_STATUS
