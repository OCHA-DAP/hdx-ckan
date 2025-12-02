# Testing Guide for HDX/CKAN

This guide explains how to run tests locally for HDX/CKAN plugins.

## Quick Start

### Run tests for a specific plugin (FAST ⚡)

```bash
./run-plugin-tests.sh hdx_smtp_assumerole
```

This script:
- Uses docker compose (same as CI)
- Starts stack automatically if needed
- Runs only the specified plugin tests
- **Much faster** than full CI (~1-2 min vs 10-15 min)
- Perfect for rapid iteration during development

### Run full CI suite locally (SLOW 🐢)

```bash
./run-tests-local.sh
```

This script:
- Uses `act` to run GitHub Actions locally
- Mimics the exact CI environment
- Runs ALL plugin tests sequentially
- Takes 10-15 minutes
- Good for final validation before push

## Available Test Scripts

### 1. `run-plugin-tests.sh` - Quick Plugin Tests

**Best for:** Daily development, rapid iteration, debugging specific plugin

```bash
# Show help and available options
./run-plugin-tests.sh

# Only initialize test environment (useful for manual testing)
./run-plugin-tests.sh --init-only

# Run tests for specific plugin (auto-initializes if needed)
./run-plugin-tests.sh hdx_smtp_assumerole
./run-plugin-tests.sh hdx_pages

# Run tests for ALL plugins
./run-plugin-tests.sh --all
```

**Features:**
- ✅ Automatic stack setup (if not running)
- ✅ Reuses running stack (very fast subsequent runs)
- ✅ Colored output
- ✅ Shows coverage for ONLY the specified plugin (clean, focused results)
- ✅ Stack stays running after tests (good for debugging)
- ✅ `--init-only` flag to setup environment without running tests
- ✅ `--all` flag to test all plugins with summary report

**Available options:**
- `./run-plugin-tests.sh` - Show help
- `./run-plugin-tests.sh --init-only` - Initialize test environment only
- `./run-plugin-tests.sh <plugin_name>` - Test specific plugin
- `./run-plugin-tests.sh --all` - Test all plugins

**Available plugins:**
- `hdx_smtp_assumerole`
- `hdx_service_checker`
- `hdx_pages`
- `hdx_theme`
- `hdx_package`
- `hdx_search`
- `hdx_users`
- `hdx_user_extra`
- `hdx_org_group`
- `hdx_dataviz`
- `sitemap`
- `ytp-request`

### 2. `run-tests-local.sh` - Full CI Simulation

**Best for:** Pre-push validation, ensuring CI will pass

```bash
# Run complete test suite
./run-tests-local.sh

# Note: You can Ctrl+C after your plugin tests complete
./run-tests-local.sh
```

**Prerequisites:**
```bash
# Install act (GitHub Actions runner)
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or visit: https://github.com/nektos/act
```

**Features:**
- ✅ Exact CI environment
- ✅ Runs all workflows
- ✅ Validates GitHub Actions syntax
- ✅ Catches CI-specific issues

### 3. Manual Docker Compose Testing

**For complete control:**

```bash
# Start the stack
docker compose up -d

# Initialize (first time only)
docker compose exec -T solr curl -s 'http://solr:8983/solr/admin/collections?action=CREATE&name=ckan&numShards=1&replicationFactor=1&collection.configName=_default'
docker compose exec -T ckan sh -c "mkdir -p /srv/filestore/storage/uploads/group"
docker compose exec -T ckan sh -c "touch /srv/filestore/storage/uploads/group/david_thumbnail.png"
docker compose exec -T ckan sh -c "envsubst < /srv/ckan/docker/hdx-test-core.ini.tpl > /srv/ckan/hdx-test-core.ini"
docker compose exec -T ckan pip install -r /srv/ckan/dev-requirements.txt

# Setup database
docker compose exec -T ckan /usr/bin/bash -c 'echo "db:5432:ckan:ckan:ckan" > /root/.pgpass && chmod 600 /root/.pgpass'
docker compose exec -T db psql -U ckan -c "create database datastore owner ckan;"
docker compose exec -T db psql -U ckan -c "create role datastore with login;"
docker compose exec -T db psql -U ckan -c "alter role datastore with password 'datastore';"

# Build search index
docker compose exec -T ckan bash -c "INI_FILE=/srv/ckan/hdx-test-core.ini hdxckantool feature"

# Run tests
docker compose exec -T ckan sh -c "./run_pytest_with_coverage.sh hdx_smtp_assumerole"

# Stop stack when done
docker compose down
```

## Testing Workflow

### During Development (Iterating on Code)

1. **Start stack once:**
   ```bash
   docker compose up -d
   # Wait for initialization...
   ```

2. **Run tests repeatedly:**
   ```bash
   ./run-plugin-tests.sh hdx_smtp_assumerole
   # Edit code...
   ./run-plugin-tests.sh hdx_smtp_assumerole
   # Edit more...
   ./run-plugin-tests.sh hdx_smtp_assumerole
   ```

3. **Stop when done:**
   ```bash
   docker compose down
   ```

### Before Pushing Code

1. **Run full suite:**
   ```bash
   ./run-tests-local.sh
   ```

2. **Or push and check GitHub Actions** (if you're confident)

## Debugging Test Failures

### View logs
```bash
# Container logs
docker compose logs ckan
docker compose logs db
docker compose logs solr

# Follow logs
docker compose logs -f ckan
```

### Interactive shell
```bash
# Get shell in ckan container
docker compose exec ckan bash

# Run pytest manually with verbose output
cd /srv/ckan
pytest -vv ./ckanext-hdx_smtp_assumerole/ckanext/hdx_smtp_assumerole/tests/test_mailer_patches.py::TestMailerPatches::test_patched_mail_user_plain_text
```

### Run specific test
```bash
docker compose exec -T ckan sh -c "pytest -xvs ./ckanext-hdx_smtp_assumerole/ckanext/hdx_smtp_assumerole/tests/test_plugin.py::TestValidateRegion::test_valid_region_us_east_1"
```

### Check coverage
```bash
docker compose exec -T ckan sh -c "pytest --cov=ckanext-hdx_smtp_assumerole --cov-report=html ./ckanext-hdx_smtp_assumerole/ckanext/hdx_smtp_assumerole/tests/"
# Open htmlcov/index.html in browser
```

## Tips & Tricks

### Speed up testing
- Keep docker compose stack running between test runs
- Use `run-plugin-tests.sh` instead of full CI
- Run only specific test file: `pytest path/to/test_file.py`
- Run only specific test: `pytest path/to/test_file.py::TestClass::test_method`

### Clean slate
```bash
# Remove all containers and volumes
docker compose down -v

# Rebuild images
docker compose build --no-cache

# Start fresh
docker compose up -d
```

### Check what's running
```bash
docker compose ps
docker compose top
```

## Troubleshooting

### "Could not connect to Redis" warning
This is normal in test environment - tests don't need Redis.

### "Security TOTP table already exists"
This is normal - just a warning during initialization.

### Tests fail with "No module named 'ckanext.hdx_smtp_assumerole'"
```bash
# Make sure plugin is installed
docker compose exec ckan pip list | grep hdx-smtp
```

### Stack won't start
```bash
# Check Docker resources (needs ~4GB RAM)
docker stats

# Check for port conflicts
lsof -i :5000  # CKAN
lsof -i :5432  # PostgreSQL
lsof -i :8983  # Solr
```

### Tests pass locally but fail in CI
Use `./run-tests-local.sh` to exactly match CI environment.

## GitHub Actions Workflows

The project has several CI workflows:

- **`run-tests.yml`** - Main test suite (runs on every push)
- **`run-linter.yml`** - Code quality checks (ruff)
- **`run-types-checker.yml`** - Type checking (pyright)
- **`pytest.yml`** - Core CKAN tests

You can see results at: https://github.com/OCHA-DAP/hdx-ckan/actions
