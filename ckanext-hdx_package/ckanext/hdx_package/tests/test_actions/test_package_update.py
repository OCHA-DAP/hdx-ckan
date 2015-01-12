'''
Created on Sep 9, 2014

@author: alexandru-m-g
'''

# -*- coding: utf-8 -*-

import logging as logging
import ckan.plugins.toolkit as tk
import ckan.tests as tests
import ckan.model as model
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)

package = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "01/01/1960-12/31/2012",
    "indicator": "1",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "World Bank",
    "license_id": "hdx-other",
    "name": "test_activity_1",
    "notes": "This is a test activity",
    "title": "Test Activity 1",
    "indicator": 1,
    "groups": [{"name": "roger"}]
}

log = logging.getLogger(__name__)


class TestHDXPackageUpdate(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_hdx_package_update_metadata(self):
        global package

        testsysadmin = model.User.by_name('testsysadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'nouser'}
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        modified_fields = {'id': 'test_activity_1', 'name': 'test_activity_1_modified',
                           'indicator': '2',
                           'title': "Modified Test Activity 1",
                           'dataset_source': 'Modified source',
                           'last_metadata_update_date': 'last_metadata_update_date test',
                           'last_data_update_date': 'last_data_update_date test',
                           'dataset_date': '11/02/2014-11/20/2014',
                           'dataset_source': 'dataset_source test',
                           'dataset_source_code': 'dataset_source_code test',
                           'indicator_type': 'indicator_type test',
                           'indicator_type_code': 'indicator_type_code test',
                           'dataset_summary': 'dataset_summary test',
                           'methodology': 'methodology test',
                           'more_info': 'more_info test',
                           'terms_of_use': 'terms_of_use test',
                           'validation_notes_and_comments': 'validation_notes_and_comments test'
                           }

        self._get_action('hdx_package_update_metadata')(
            context, modified_fields)

        tests.call_action_api(self.app, 'package_show', id='test_activity_1',
                              apikey=testsysadmin.apikey, status=404)
        modified_package = tests.call_action_api(self.app, 'package_show', id='test_activity_1_modified',
                                                 apikey=testsysadmin.apikey, status=200)

        modified_fields.pop('id')

        # Checking that all fields in the modified_package come either
        # from original package or were modified
        for key, value in modified_package.iteritems():
            if key not in modified_fields.keys():
                if key != 'groups' and key in package:
                    assert package[key] == value, 'Problem with key {}: has value {} instead of {}'.format(
                        key, value, package[key])
            else:
                assert value == modified_fields[key], 'Problem with key {}: has value {} instead of {}'.format(
                    key, value, modified_fields[key])

        # Checking that all modifications were applied
        for key, value in modified_fields.iteritems():
            assert value == modified_package[key], 'Problem with key {}: has value {} instead of {}'.format(
                key, modified_package[key], value)

        assert len(modified_package['groups']) == len(package['groups']), 'There should be {} item in groups but instead there is {}'.format(
            len(package['groups']), len(modified_package['groups']))
