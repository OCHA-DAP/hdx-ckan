'''
Created on Dec 24, 2014

@author: alexandru-m-g
'''

import logging as logging
import pylons.config as config

import ckan.model as model
from ckan.common import c
import ckan.logic as logic
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXCreateResourceForRequestData(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_create_resource_for_requestdata_dataset(self):
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
            "name": "test_activity_request_data",
            "notes": "This is a test activity",
            "title": "Test Activity 3 request data",
            "owner_org": "hdx-test-org",
            "groups": [{"name": "roger"}],
            "is_requestdata_type": True,
            "file_types": ["csv"],
            "field_names": ["field1", "field2"]
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            self._get_action('package_create')(context, package)
            assert True
        except logic.ValidationError, ex:
            assert False

        dataset = self._get_action('package_show')(context, {'id': 'test_activity_request_data'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'GeoJSON',
            'name': 'resource_create_test1.geojson'
        }
        try:
            r1 = self._get_action('resource_create')(context, resource)
            assert False
        except logic.ValidationError:
            assert True
