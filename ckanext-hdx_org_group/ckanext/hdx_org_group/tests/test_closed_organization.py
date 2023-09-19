'''
reCreated on 19 Sep, 2023

@author: dan
'''

import pytest
import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
log = logging.getLogger(__name__)


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestClosedOrg(object):

    def test_closed_organization(self, app):

        orgadmin = 'orgadmin'
        context = {'model': model, 'session': model.Session, 'user': orgadmin}

        org_dict = _get_action('organization_show')(context, {'id': 'hdx-test-org', 'include_users':True})

        org_dict['closed_organization'] = True
        result = _get_action('organization_update')(context, org_dict)
        org_dict = _get_action('organization_show')(context, {'id': 'hdx-test-org', 'include_users':True})
        assert '(inactive)' in org_dict.get('title')

        org_dict['closed_organization'] = False
        context = {'model': model, 'session': model.Session, 'user': orgadmin}
        result = _get_action('organization_update')(context, org_dict)
        org_dict = _get_action('organization_show')(context, {'id': 'hdx-test-org', 'include_users':True})
        assert '(inactive)' not in org_dict.get('title')

        org_dict['closed_organization'] = True
        org_dict['title'] = 'HDX TEST ORG 123 (closed)'
        context = {'model': model, 'session': model.Session, 'user': orgadmin}
        result = _get_action('organization_update')(context, org_dict)
        org_dict = _get_action('organization_show')(context, {'id': 'hdx-test-org'})
        assert '(inactive)' in org_dict.get('title')
        assert '123' in org_dict.get('title')
