"""
reCreated on 19 Sep, 2023

@author: dan
"""

import pytest
import logging as logging

from ckanext.hdx_org_group.actions.get import get_toplines_for_active_country

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context
import ckan.lib.helpers as h
import ckan.tests.factories as factories
from ckanext.hdx_org_group.tests.conftest import LOCATION

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
log = logging.getLogger(__name__)


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
class TestActions(object):

    def test_hdx_datasets_for_group(self, app):

        orgadmin = 'orgadmin'
        context: Context = {'model': model, 'session': model.Session, 'user': orgadmin}
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        try:
            followers_list = _get_action('hdx_organization_follower_list')(context, {'id': 'hdx-test-org'})
            assert False
        except NotAuthorized:
            assert True

        followers_list = _get_action('hdx_organization_follower_list')(sysadmin_context, {'id': 'hdx-test-org'})

        org_dict = _get_action('hdx_datasets_for_group')(context, {'id': 'some_location'})
        assert 'dataset111-category1' in  org_dict.get('results')[0].get('name')

    def test_org_not_existing(self, app):

        orgadmin = 'orgadmin'
        context: Context = {'model': model, 'session': model.Session, 'user': orgadmin}
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        test_orgadmin_token = factories.APIToken(user=orgadmin, expires_in=2, unit=60 * 60)['token']
        test_sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']

        org_url = h.url_for('hdx_org.read', id='hdx-test-org3')
        result = app.get(org_url)
        assert result.status_code == 404
        assert result.status == '404 NOT FOUND'

        org_url = h.url_for('hdx_org.read', id='hdx-test-org2')
        result = app.get(org_url, headers={'Authorization': test_sysadmin_token})
        assert result.status_code == 200

        org_url = h.url_for('organization.delete', id='hdx-test-org2')
        result = app.post(org_url, headers={'Authorization': test_sysadmin_token})

        org_dict = _get_action('organization_show')(context, {'id': 'hdx-test-org2'})
        assert org_dict.get('state') == 'deleted'

        org_dict = _get_action('organization_show')(sysadmin_context, {'id': 'hdx-test-org2'})
        assert org_dict.get('state') == 'deleted'

        org_url = h.url_for('hdx_org.restore', id=org_dict.get('id'))
        result = app.post(org_url, headers={'Authorization': test_orgadmin_token})
        assert result.status_code == 404

        org_url = h.url_for('hdx_org.restore', id=org_dict.get('id'))
        result = app.post(org_url, headers={'Authorization': test_sysadmin_token})
        assert result.status_code == 200

        org_dict = _get_action('organization_show')(sysadmin_context, {'id': 'hdx-test-org2'})
        assert org_dict.get('name') == 'hdx-test-org2'
        assert org_dict.get('state') == 'active'

    def test_org_activity_offset(self, app):

        org_url = h.url_for('hdx_org.activity_offset', id='hdx-test-org', offset=0)
        result = app.get(org_url)
        assert result.status_code == 200

    def test_group_toplines(self):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        group_dict = _get_action('group_show')(sysadmin_context, {'id': LOCATION})
        group_dict['activity_level'] = 'active'
        group_dict['name'] = 'alb'
        topline = get_toplines_for_active_country(group_dict, True)
        assert topline==[]
