#!/bin/bash

mv -f requirements.txt requirements-tmp.txt
grep -v "github" requirements-tmp.txt >> requirements.txt
python setup.py develop
mv -f requirements-tmp.txt requirements.txt

plugins="hdx_service_checker sitemap ytp-request hdx_hxl_preview hdx_dataviz hdx_pages hdx_theme hdx_package hdx_search hdx_org_group hdx_users hdx_user_extra hdx_office_preview"
for p in $plugins; do cd /srv/ckan/ckanext-$p || exit; python setup.py develop; done
cd /srv/ckan || exit
