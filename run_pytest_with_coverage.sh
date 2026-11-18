#!/bin/sh
# Usage: run_pytest_with_coverage.sh <plugin> [pytest args]
# Extra args (test paths, --ignore=...) replace the default target, the plugin's whole tests folder.
PYTEST='pytest --cov-config=.coveragerc '\
'--cov=ckanext-hdx_search --cov=ckanext-hdx_pages --cov=ckanext-hdx_hxl_preview '\
'--cov=ckanext-hdx_org_group --cov=ckanext-hdx_package --cov=ckanext-hdx_theme --cov=ckanext-hdx_users '\
'--cov=ckanext-hdx_user_extra --cov=ckanext-hdx_service_checker --cov=ckanext-sitemap --cov=ckanext-ytp-request  '\
'--cov=ckanext-hdx_dataviz --cov=ckanext-hdx_smtp_assumerole  '\
'--cov-append --ckan-ini=hdx-test-core.ini'

plugin=$1
shift
if [ $# -eq 0 ]; then
    set -- ./ckanext-$plugin/ckanext/$plugin/tests
fi

# --durations lists the slowest setup/call/teardown phases, to find slow tests and fixtures
$PYTEST --durations=25 "$@"
