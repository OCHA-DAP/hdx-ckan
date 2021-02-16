#!/bin/bash
PYTEST='pytest --cov-config=.coveragerc '\
'--cov=ckanext-hdx_search --cov=ckanext-hdx_pages --cov=ckanext-hdx_crisis --cov=ckanext-hdx_hxl_preview '\
'--cov=ckanext-hdx_org_group --cov=ckanext-hdx_package --cov=ckanext-hdx_theme --cov=ckanext-hdx_users '\
'--cov=ckanext-hdx_user_extra --cov=ckanext-sitemap --cov=ckanext-ytp-request '\
'--cov-append --ckan-ini=hdx-test-core.ini'

$PYTEST ./ckanext-$1/ckanext/$1/tests
