"""
reCreated on 19 Sep, 2023

@author: dan
"""

import pytest
import logging as logging
from bs4 import BeautifulSoup
import ckan.lib.helpers as h

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.types import Context
import ckanext.hdx_package.helpers.caching as caching
from ckanext.hdx_org_group.tests.conftest import ORG, LOCATION, USER, SYSADMIN

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

    def test_edit_location_page_v2(self, app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
        sysadmin_auth = {'Authorization': factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']}
        user_auth = {'Authorization': factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']}
        location = _get_action('group_show')(sysadmin_context, {'id': LOCATION})
        edit_url = h.url_for('group.edit', id=LOCATION)
        new_url = h.url_for('hdx_group.new')
        delete_action = 'action="{}"'.format(h.url_for('group.delete', id=location['id']))

        result = app.get(edit_url, headers=sysadmin_auth)
        assert result.status_code == 200
        assert 'Edit location page' in result.body
        assert 'id="create-group-form"' in result.body
        assert 'id="delete-location-drawer"' in result.body
        assert delete_action in result.body
        assert 'group-form-scripts' not in result.body
        assert 'hdx_confirm-action' not in result.body

        result = app.post(edit_url, data={'name': ORG, 'save': 'save'}, headers=sysadmin_auth)
        assert result.status_code == 200
        assert 'Location name already exists in database' in result.body
        assert 'data-slug-preview-error' in result.body
        assert delete_action in result.body

        result = app.get(edit_url, headers=user_auth)
        assert result.status_code == 403

        result = app.get(new_url, headers=sysadmin_auth)
        assert result.status_code == 200
        assert 'Create location' in result.body
        assert 'id="create-group-form"' in result.body
        assert 'id="delete-location-drawer"' not in result.body

        result = app.get(new_url, headers=user_auth)
        assert result.status_code == 403

    def test_edit_location_unchanged_save(self, app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
        sysadmin_auth = {'Authorization': factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']}
        factories.Group(
            name='hdx-test-location-edit',
            title='HDX TEST LOCATION EDIT',
            description='A test location',
            image_url='https://hdx.hdxtest.org/location.png',
            language_code='fr',
            relief_web_url='https://reliefweb.hdxtest.org/',
            hr_info_url='https://hrinfo.hdxtest.org/',
            alert_bar_title='Test alert',
            alert_bar_url='https://alert.hdxtest.org/',
            geojson='{"type": "FeatureCollection", "features": []}',
            activity_level='active',
            key_figures='inactive',
            data_completeness='active',
        )
        fields = ['title', 'name', 'description', 'image_url', 'language_code', 'relief_web_url', 'hr_info_url',
                  'alert_bar_title', 'alert_bar_url', 'geojson', 'activity_level', 'key_figures', 'data_completeness']
        location_before = _get_action('group_show')(sysadmin_context, {'id': 'hdx-test-location-edit'})
        for field in fields:
            assert location_before.get(field)

        url = h.url_for('group.edit', id='hdx-test-location-edit')
        result = app.get(url, headers=sysadmin_auth)
        form = BeautifulSoup(result.body, 'html.parser').find('form', id='create-group-form')
        form_data = {}
        for field in form.find_all(['input', 'textarea', 'select']):
            if not field.get('name'):
                continue
            if field.name == 'textarea':
                form_data[field['name']] = field.text
            elif field.name == 'select':
                option = field.find('option', selected=True)
                form_data[field['name']] = option['value'] if option else ''
            else:
                form_data[field['name']] = field.get('value', '')

        result = app.post(url, data=form_data, headers=sysadmin_auth, follow_redirects=False)
        assert result.status_code == 302
        location_after = _get_action('group_show')(sysadmin_context, {'id': 'hdx-test-location-edit'})
        for field in fields:
            assert location_before.get(field) == location_after.get(field)

    def test_delete_location_invalidates_cache(self, app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
        sysadmin_auth = {'Authorization': factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']}
        location = _get_action('group_show')(sysadmin_context, {'id': LOCATION})

        caching.invalidate_group_caches()
        assert LOCATION in [group['name'] for group in caching.cached_group_list()]

        result = app.post(h.url_for('group.delete', id=location['id']), headers=sysadmin_auth,
                          follow_redirects=False)
        assert result.status_code == 302
        assert LOCATION not in [group['name'] for group in caching.cached_group_list()]
