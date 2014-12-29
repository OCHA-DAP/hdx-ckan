'''
Created on Dec 24, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXUpdateResource(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_resource_update_metadata(self):

        field = 'last_data_update_date'
        new_field_value = '2014-12-10T23:04:22.596156'

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        resource = self._get_action('resource_show')(
            context, {'id': 'hdx_test.csv'})

        original = resource.get(field, None)

        self._get_action('hdx_resource_update_metadata')(
            context, {'id': resource['id'], field: new_field_value})

        changed_resource = self._get_action('resource_show')(
            context, {'id': 'hdx_test.csv'})
        modified = changed_resource[field]

        assert original != modified, '{} should have been changed by action'.format(
            field)
