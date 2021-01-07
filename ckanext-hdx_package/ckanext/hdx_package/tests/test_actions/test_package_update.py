'''
Created on Sep 9, 2014

@author: alexandru-m-g
'''

# -*- coding: utf-8 -*-

import logging as logging
import pylons.config as config
import json
import ckan.plugins.toolkit as tk
import ckan.tests as tests
import ckan.tests.legacy as legacy_tests
import ckan.model as model
import ckan.lib.helpers as h
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model
import ckan.logic as logic

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from nose import tools as nosetools

log = logging.getLogger(__name__)


organization = {
    'name': 'hdx-test-org',
    'title': 'Hdx Test Org',
    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
    'org_acronym': 'HTO',
    'org_url': 'http://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'testsysadmin', 'capacity': 'admin'}, {'name': 'joeadmin', 'capacity': 'admin'}]
}


class TestHDXPackageUpdate(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestHDXPackageUpdate, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    def test_create_and_upload(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_2',
                   'title': 'Test Activity 2'
                   }

        resource = {
            'package_id': 'test_activity_2',
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test.csv'
        }

        testsysadmin = model.User.by_name('testsysadmin')

        # Real username is still needed even with ignore_auth otherwise
        # some fields ( like groups ) will not be saved
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        self._get_action('organization_create')(context, organization)

        self._get_action('package_create')(context, package)

        self._get_action('resource_create')(context, resource)

        test_url = h.url_for(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                             action='read', id=package['name'])
        result = self.app.post(
            test_url, extra_environ={'Authorization': str(testsysadmin.apikey)})
        assert result.status_code == 200
        assert '<a class="heading" title="hdx_test.csv">' in result.data

    def test_hdx_package_delete_redirect(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_3',
                   'title': 'Test Activity 3'
                   }

        testsysadmin = model.User.by_name('testsysadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        test_url = h.url_for(controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                             action='delete', id=package['name'])
        test_client = self.get_backwards_compatible_test_client()
        result = test_client.post(test_url, extra_environ={'Authorization': str(testsysadmin.apikey)})
        assert result.status_code == 302

    def test_hdx_solr_additions(self):
        testsysadmin = model.User.by_name('testsysadmin')
        legacy_tests.call_action_api(self.app, 'group_create', name="col", title="Colombia", apikey=testsysadmin.apikey,
                                     status=200)
        context = {'ignore_auth': True,
                                  'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            self._get_action('organization_create')(context, organization)
        except Exception, ex:
            log.error(ex)
        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "col"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_4',
                   'title': 'Test Activity 4',
                   'maintainer': testsysadmin.id,
                   'maintainer_email': None
                   }
        p = self._get_action('package_create')(context, package)
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'nouser'}
        s = self._get_action('package_show')(context, {"id": p.get('id')})
        assert json.loads(s['solr_additions'])['countries'] == ['Colombia']

    def test_hdx_package_update_metadata(self):

        testsysadmin = model.User.by_name('testsysadmin')

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_5',
                   'title': 'Test Activity 5',
                   'maintainer': testsysadmin.id,
                   'maintainer_email': None
                   }



        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        modified_fields = {'id': 'test_activity_5',
                           # 'name': 'test_activity_1_modified',
                           'indicator': '2',
                           # 'title': "Modified Test Activity 1",
                           # 'dataset_source': 'Modified source',
                           'last_metadata_update_date': 'last_metadata_update_date test',
                           'last_data_update_date': 'last_data_update_date test',
                           'dataset_date': '[2014-11-02T00:00:00 TO 2014-11-20T23:59:59]',
                           # 'dataset_source_code': 'dataset_source_code test',
                           'indicator_type': 'indicator_type test',
                           'indicator_type_code': 'indicator_type_code test',
                           # 'dataset_summary': 'dataset_summary test',
                           # 'methodology': 'methodology test',
                           'more_info': 'more_info test',
                           # 'terms_of_use': 'terms_of_use test',
                           'data_update_frequency': '7',
                           'maintainer': testsysadmin.id,
                           'maintainer_email': None
                           }

        self._get_action('hdx_package_update_metadata')(context, modified_fields)

        modified_package = legacy_tests.call_action_api(self.app, 'package_show', id='test_activity_5',
                                                        apikey=testsysadmin.apikey, status=200)
        modified_fields.pop('id')

        # Checking that all fields in the modified_package come either
        # from original package or were modified
        for key, value in modified_package.iteritems():
            if key not in modified_fields.keys():
                if key != 'groups' and key in package and key != 'owner_org':
                    assert package[key] == value, 'Problem with key {}: has value {} instead of {}'.format(
                        key, value, package[key])
            else:
                assert value == modified_fields[key], 'Problem with key {}: has value {} instead of {}'.format(
                    key, value, modified_fields[key])

        # Checking that all modifications were applied
        for key, value in modified_fields.iteritems():
            assert value == modified_package[key], 'Problem with key {}: has value {} instead of {}'.format(
                key, modified_package[key], value)

        assert len(modified_package['groups']) == len(
            package['groups']), 'There should be {} item in groups but instead there is {}'.format(
            len(package['groups']), len(modified_package['groups']))

        org_obj = model.Group.by_name('hdx-test-org')
        assert modified_package.get('owner_org') == org_obj.id

    def test_hdx_package_subnational_validation(self):
        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_6',
                   'title': 'Test Activity 6'
                   }

        testsysadmin = model.User.by_name('testsysadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'true')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'True')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', '1')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'false')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'False')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', '0')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'Dummy Text')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', None)
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

    def test_hdx_package_maintainer_validation(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_7',
                   'title': 'Test Activity 7',
                   'maintainer': 'testsysadmin'
                   }

        testsysadmin = model.User.by_name('testsysadmin')
        joeadmin = model.User.by_name('joeadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'testsysadmin')
        modified_package = data_dict.get('modified_package')
        # modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('maintainer') == testsysadmin.id

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'joeadmin')
        modified_package = data_dict.get('modified_package')
        # modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('maintainer') == joeadmin.id

        with nosetools.assert_raises(logic.ValidationError):
            data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'joeadmin no user')
            modified_package = data_dict.get('modified_package')
            # modified_package_obj = data_dict.get('modified_package_obj')
            assert modified_package.get('maintainer') == joeadmin.id

    def _modify_field(self, context, user, package_id, key, value):
        modified_fields = {'id': package_id,
                           key: value,
                           }
        self._get_action('package_patch')(context, modified_fields)
        modified_package = legacy_tests.call_action_api(self.app, 'package_show', id=package_id,
                                                        apikey=user.apikey, status=200)
        modified_package_obj = model.Package.by_name(package_id)
        return {
            "modified_package": modified_package,
            "modified_package_obj": modified_package_obj
        }
