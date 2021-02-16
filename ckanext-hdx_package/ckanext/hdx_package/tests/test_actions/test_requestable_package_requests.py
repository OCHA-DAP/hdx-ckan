'''
Created on Sep 9, 2014

@author: alexandru-m-g
'''

# -*- coding: utf-8 -*-

import logging as logging
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model
import mock

import ckanext.hdx_theme.tests.mock_helper as mock_helper
from ckanext.requestdata.model import ckanextRequestdata
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from nose.tools import assert_raises
from ckan import logic

log = logging.getLogger(__name__)

# package = {
#     "package_creator": "test function",
#     "private": False,
#     "dataset_date": "01/01/1960-12/31/2012",
#     "caveats": "These are the caveats",
#     "license_other": "TEST OTHER LICENSE",
#     "methodology": "This is a test methodology",
#     "dataset_source": "World Bank",
#     "license_id": "hdx-other",
#     "name": "test_activity_1",
#     "notes": "This is a test activity",
#     "title": "Test Activity 1",
#     "indicator": 0,
#     "groups": [{"name": "roger"}],
#     "owner_org": "hdx-test-org",
# }

organization = {
    'name': 'hdx-test-org',
    'title': 'Hdx Test Org',
    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
    'org_acronym': 'HTO',
    'org_url': 'http://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'testsysadmin'}, {'name': 'tester', 'capacity': 'member'}]
}


class TestHDXPackageUpdate(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('dcat hdx_org_group hdx_package hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestHDXPackageUpdate, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    @mock.patch('ckanext.requestdata.plugin.c')
    def test_create_and_delete_requestable_dataset(self, plugin_c_mock):
        test_username = 'testsysadmin'
        mock_helper.populate_mock_as_c(plugin_c_mock, test_username)

        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "indicator": "0",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "name": "test_activity_3",
            "notes": "This is a test activity",
            "title": "Test Activity 3",
            "groups": [{"name": "roger"}],
            "owner_org": "hdx-test-org",
            "maintainer": "tester",
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        }

        testsysadmin = model.User.by_name('testsysadmin')

        # Real username is still needed even with ignore_auth otherwise
        # some fields ( like groups ) will not be saved
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        self._get_action('organization_create')(context, organization)

        self._get_action('package_create')(context, package)

        p = self._get_action('package_show')(context, {"id": package['name']})

        test_url = h.url_for(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                             action='read', id=package['name'])
        result = self.app.post(test_url, extra_environ={'Authorization': str(testsysadmin.apikey)})
        assert result.status_code == 200

        assert 'Request data directly from the maintainer of this dataset.' in result.data

        assert 'This data is by request only' in result.data

        context['user'] = 'tester'
        data_dict = {
            'package_id': p['id'],
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'Google',
            'email_address': 'test@test.com',
        }

        req_result = self._get_action('requestdata_request_create')(context, data_dict)

        assert 'requestdata_id' in req_result

        requestdata_id = req_result.get('requestdata_id')

        data_dict_show = {
            'id': requestdata_id,
            'package_id': data_dict['package_id']
        }

        context['user'] = 'testsysadmin'
        result = self._get_action('requestdata_request_show')(context, data_dict_show)

        assert result['package_id'] == data_dict['package_id']
        assert result['sender_name'] == data_dict['sender_name']
        assert result['message_content'] == data_dict['message_content']
        assert result['email_address'] == data_dict['email_address']
        assert result['data_shared'] is False
        assert result['state'] == 'new'

        result = self._get_action('hdx_dataset_purge')(context, {'id': data_dict['package_id']})

        assert result is None

        with assert_raises(logic.NotFound) as cm:
            self._get_action('package_show')( context,  {'id': data_dict['package_id']})

        ex = cm.exception
        assert ex.message == ""
        # result = self._get_action('package_show')(context, {'id': data_dict['package_id']})

        rq = ckanextRequestdata.get(id=requestdata_id)
        assert rq is None

