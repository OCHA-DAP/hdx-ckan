"""
reCreated on 19 Sep, 2023

@author: dan
"""

import pytest
import logging as logging
import ckan.lib.helpers as h

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context
import ckanext.hdx_package.helpers.caching as caching
from ckanext.hdx_org_group.tests.conftest import ORG, LOCATION

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
log = logging.getLogger(__name__)


# User-Agent mobil (Android)
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36'}

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
class TestViews(object):

    def test_light_org(self,app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        caching.invalidate_cached_organization_list()

        url = h.url_for('hdx_light_org.light_index')
        result = app.get(url)
        assert result.status_code == 200
        result = app.get(url, headers=headers)
        assert result.status_code == 200

        url = h.url_for('hdx_light_org.light_read', id=ORG)
        result = app.get(url, status=200)
        assert result.status_code == 200
        result = app.get(url, status=200, headers=headers)
        assert result.status_code == 200

        url = h.url_for('hdx_light_org.light_fake', id=ORG)
        result = app.get(url, status=200)
        assert result.status_code == 200
        result = app.get(url, status=200, headers=headers)
        assert result.status_code == 200

    def test_redirect_org(self,app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        caching.invalidate_cached_organization_list()

        url = h.url_for('hdx_org_group_redirect.redirect_to_org_list', id=ORG)
        result = app.get(url)
        assert result.status_code == 200

        url = h.url_for('hdx_org_group_redirect.redirect_to_org_list2')
        result = app.get(url)
        assert result.status_code == 200

    def test_light_group(self,app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        url = h.url_for('hdx_light_group.light_index')
        result = app.get(url)
        assert result.status_code == 200
        result = app.get(url, headers=headers)
        assert result.status_code == 200

        url = h.url_for('hdx_light_group.light_read', id=LOCATION)
        result = app.get(url, status=200)
        assert result.status_code == 200
        result = app.get(url, status=200, headers=headers)
        assert result.status_code == 200
