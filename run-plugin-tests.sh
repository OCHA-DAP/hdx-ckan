#!/bin/bash
#
# Quick test runner for HDX plugins using docker compose
# Much faster than running full CI - good for rapid iteration
#
# Usage:
#   ./run-plugin-tests.sh --init-only          # Only initialize test environment
#   ./run-plugin-tests.sh hdx_smtp_assumerole  # Initialize (if needed) and run tests for specific plugin
#   ./run-plugin-tests.sh --all                # Initialize (if needed) and run tests for all plugins
#   ./run-plugin-tests.sh                      # Show this help
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Available plugins
AVAILABLE_PLUGINS=(
    "hdx_smtp_assumerole"
    "hdx_service_checker"
    "hdx_pages"
    "hdx_theme"
    "hdx_package"
    "hdx_search"
    "hdx_users"
    "hdx_user_extra"
    "hdx_org_group"
    "hdx_dataviz"
    "sitemap"
    "ytp-request"
)

show_help() {
    echo -e "${GREEN}HDX Plugin Test Runner${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 --init-only          # Only initialize test environment"
    echo "  $0 <plugin_name>        # Initialize (if needed) and run tests for specific plugin"
    echo "  $0 --all                # Initialize (if needed) and run tests for all plugins"
    echo "  $0                      # Show this help"
    echo ""
    echo -e "${YELLOW}Available plugins:${NC}"
    for plugin in "${AVAILABLE_PLUGINS[@]}"; do
        echo "  - $plugin"
    done
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 --init-only                    # Just setup the test environment"
    echo "  $0 hdx_smtp_assumerole            # Test hdx_smtp_assumerole plugin"
    echo "  $0 --all                          # Test all plugins"
}

init_test_environment() {
    echo -e "${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  Initializing Test Environment${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo ""

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi

    # Check if docker compose stack is running
    if ! docker compose ps | grep -q "ckan.*Up"; then
        echo -e "${YELLOW}Docker compose stack not running. Starting it...${NC}"
        echo ""

        # Build and start stack
        echo -e "${BLUE}Building CKAN docker image...${NC}"
        docker compose build ckan

        echo -e "${BLUE}Starting docker compose stack...${NC}"
        docker compose up -d

        echo -e "${BLUE}Waiting for services to be ready...${NC}"
        sleep 10

        # Initialize Solr
        echo -e "${BLUE}Creating Solr collection...${NC}"
        docker compose exec -T solr curl -s 'http://solr:8983/solr/admin/collections?action=CREATE&name=ckan&numShards=1&replicationFactor=1&collection.configName=_default' || true

        # Setup filestore
        docker compose exec -T ckan sh -c "mkdir -p /srv/filestore/storage/uploads/group"
        docker compose exec -T ckan sh -c "touch /srv/filestore/storage/uploads/group/david_thumbnail.png"

        # Generate test config
        docker compose exec -T ckan sh -c "envsubst < /srv/ckan/docker/hdx-test-core.ini.tpl > /srv/ckan/hdx-test-core.ini"

        # Install dev requirements
        echo -e "${BLUE}Installing dev requirements...${NC}"
        docker compose exec -T ckan pip install -r /srv/ckan/dev-requirements.txt

        # Prepare database
        echo -e "${BLUE}Setting up database...${NC}"
        docker compose exec -T ckan /usr/bin/bash -c \
            'echo "db:5432:ckan:ckan:ckan" > /root/.pgpass && chmod 600 /root/.pgpass'
        docker compose exec -T db psql -U ckan -c "CREATE DATABASE IF NOT EXISTS datastore OWNER ckan;" 2>/dev/null || \
            docker compose exec -T db psql -U ckan -c "create database datastore owner ckan;" || true
        docker compose exec -T db psql -U ckan -c "CREATE ROLE IF NOT EXISTS datastore WITH LOGIN;" 2>/dev/null || \
            docker compose exec -T db psql -U ckan -c "create role datastore with login;" || true
        docker compose exec -T db psql -U ckan -c "alter role datastore with password 'datastore';" || true

        # Build UI search index
        echo -e "${BLUE}Building search index...${NC}"
        docker compose exec -T ckan bash -c "INI_FILE=/srv/ckan/hdx-test-core.ini hdxckantool feature" || true

        echo ""
        echo -e "${GREEN}Test environment initialized successfully!${NC}"
        echo ""
    else
        echo -e "${GREEN}Docker compose stack is already running${NC}"
        echo ""
    fi
}

run_plugin_tests() {
    local plugin_name="$1"

    echo -e "${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  Running Tests for: ${plugin_name}${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo ""

    # Run the tests with coverage ONLY for this plugin
    echo -e "${BLUE}Running tests for ${plugin_name} (with plugin-specific coverage)...${NC}"
    echo ""

    docker compose exec -T ckan sh -c "pytest --cov-config=.coveragerc --cov=ckanext-${plugin_name} --cov-report=term-missing --ckan-ini=hdx-test-core.ini ./ckanext-${plugin_name}/ckanext/${plugin_name}/tests"

    local exit_code=$?

    echo ""
    echo -e "${GREEN}===========================================================${NC}"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✓ Tests passed for ${plugin_name}!${NC}"
    else
        echo -e "${RED}  ✗ Tests failed for ${plugin_name} (exit code: ${exit_code})${NC}"
    fi
    echo -e "${GREEN}===========================================================${NC}"
    echo ""

    return $exit_code
}

run_all_plugins() {
    echo -e "${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  Running Tests for All Plugins${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo ""

    local failed_plugins=()
    local passed_plugins=()

    for plugin in "${AVAILABLE_PLUGINS[@]}"; do
        echo -e "${BLUE}Testing plugin: ${plugin}${NC}"
        echo ""

        if run_plugin_tests "$plugin"; then
            passed_plugins+=("$plugin")
        else
            failed_plugins+=("$plugin")
        fi

        echo ""
    done

    # Summary
    echo -e "${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  Test Summary${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo ""
    echo -e "${GREEN}Passed (${#passed_plugins[@]}):${NC}"
    for plugin in "${passed_plugins[@]}"; do
        echo -e "  ${GREEN}✓${NC} $plugin"
    done
    echo ""

    if [ ${#failed_plugins[@]} -gt 0 ]; then
        echo -e "${RED}Failed (${#failed_plugins[@]}):${NC}"
        for plugin in "${failed_plugins[@]}"; do
            echo -e "  ${RED}✗${NC} $plugin"
        done
        echo ""
        return 1
    else
        echo -e "${GREEN}All plugins passed!${NC}"
        echo ""
        return 0
    fi
}

# Main logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --init-only)
        init_test_environment
        echo -e "${YELLOW}Tip:${NC} Stack is running. Use ${BLUE}docker compose down${NC} to stop it."
        echo ""
        exit 0
        ;;
    --all)
        init_test_environment
        run_all_plugins
        exit_code=$?
        echo -e "${YELLOW}Tip:${NC} Stack is still running. Use ${BLUE}docker compose down${NC} to stop it."
        echo ""
        exit $exit_code
        ;;
    *)
        PLUGIN_NAME="$1"

        # Validate plugin name
        plugin_valid=false
        for plugin in "${AVAILABLE_PLUGINS[@]}"; do
            if [ "$plugin" = "$PLUGIN_NAME" ]; then
                plugin_valid=true
                break
            fi
        done

        if [ "$plugin_valid" = false ]; then
            echo -e "${RED}Error: Unknown plugin '${PLUGIN_NAME}'${NC}"
            echo ""
            show_help
            exit 1
        fi

        init_test_environment
        run_plugin_tests "$PLUGIN_NAME"
        exit_code=$?
        echo -e "${YELLOW}Tip:${NC} Stack is still running. Use ${BLUE}docker compose down${NC} to stop it."
        echo ""
        exit $exit_code
        ;;
esac
