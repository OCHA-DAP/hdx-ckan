#!/bin/bash
#
# Run GitHub Actions tests locally using 'act'
# This simulates the full CI environment on your local machine
#
# Prerequisites:
#   brew install act
#
# Usage:
#   ./run-tests-local.sh                    # Run all tests
#   ./run-tests-local.sh hdx_smtp_assumerole # Run specific plugin tests
#

set -e
export DOCKER_API_VERSION=1.44

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}Error: 'act' is not installed${NC}"
    echo -e "${YELLOW}Install it with: brew install act${NC}"
    echo ""
    echo "For more info: https://github.com/nektos/act"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}===========================================================${NC}"
echo -e "${GREEN}  Running GitHub Actions Tests Locally (using act)${NC}"
echo -e "${GREEN}===========================================================${NC}"
echo ""

# Determine which workflow to run
WORKFLOW=".github/workflows/run-tests.yml"
PLUGIN_NAME="${1:-}"

if [ -n "$PLUGIN_NAME" ]; then
    echo -e "${BLUE}Running tests for plugin: ${PLUGIN_NAME}${NC}"
    echo ""
    # Run act with environment variable to specify plugin
    act -W "$WORKFLOW" --env PLUGIN_NAME="$PLUGIN_NAME" --pull=false
else
    echo -e "${BLUE}Running all tests${NC}"
    echo ""
    # Run the full test workflow
    act -W "$WORKFLOW" --pull=false
fi

EXIT_CODE=$?

echo ""
echo -e "${GREEN}===========================================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}  ✓ Tests passed!${NC}"
else
    echo -e "${RED}  ✗ Tests failed (exit code: ${EXIT_CODE})${NC}"
fi
echo -e "${GREEN}===========================================================${NC}"
echo ""

exit $EXIT_CODE
