'''
Created on Dec 24, 2014

@author: alexandru-m-g
'''

import logging as logging
import pylons.config as config

import ckan.model as model
from ckan.common import c

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

        package = self._get_action('package_show')(
            context, {'id': 'test_private_dataset_1'})

        resource = self._get_action('resource_show')(
            context, {'id': package['resources'][0]['id']})

        original = resource.get(field, None)

        self._get_action('hdx_resource_update_metadata')(
            context, {'id': resource['id'], field: new_field_value})

        changed_resource = self._get_action('resource_show')(
            context, {'id': package['resources'][0]['id']})
        modified = changed_resource[field]

        assert original != modified, '{} should have been changed by action'.format(
            field)

    def test_resource_delete_metadata(self):
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        package = self._get_action('package_show')(
            context, {'id': 'test_private_dataset_1'})

        resource = self._get_action('resource_show')(
            context, {'id': package['resources'][0]['id']})

        resource_v2 = self._get_action('hdx_resource_update_metadata')(
            context, {'id': resource['id'], 'test_field': 'test_extra_value'})

        # resource_v2 = self._get_action('resource_show')(
        #     context, {'id': package['resources'][0]['id']})

        assert len(resource_v2) - len(resource) == 1, "Test added just one field to the resource"

        resource_v3 = self._get_action('hdx_resource_delete_metadata')(
            context, {'id': resource['id'], 'field_list': ['test_field']})

        assert len(resource_v3) - len(resource) == 0, "Resources should be identical"

        try:
            resource_v4 = self._get_action('hdx_resource_delete_metadata')(
                context, {'id': resource['id'], 'field_list': ['shape']})
            assert True
        except:
            assert False, 'Exception when deleting nonexistent field'

    def test_resource_create(self):
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset = self._get_action('package_show')(context, {'id': 'test_dataset_1'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'GeoJSON',
            'name': 'resource_create_test1.geojson'
        }

        r1 = self._get_action('resource_create')(context, resource)
        for key, value in resource.iteritems():
            assert value == r1.get(key), "The pair {} - {} should appear in the resource data".format(key, value)
        assert 'shape_info' not in r1, "shape_info should be missing since 'hdx.gis.layer_import_url' config is missing"

        config['hdx.gis.layer_import_url'] = 'http://import.local/'
        resource['name'] = 'resource_create_test2.geojson'

        r2 = self._get_action('resource_create')(context, resource)
        assert 'shape_info' in r2, "shape_info should exist since 'hdx.gis.layer_import_url' config is set"
        del resource['shape_info']
        for key, value in resource.iteritems():
            assert value == r2.get(key), "The pair {} - {} should appear in the resource data".format(key, value)

        context['do_geo_preview'] = False
        r3 = self._get_action('resource_create')(context, resource)
        assert 'shape_info' not in r3, "shape_info should be missing since 'do_geo_preview' is False"
        for key, value in resource.iteritems():
            assert value == r3.get(key), "The pair {} - {} should appear in the resource data".format(key, value)

        del config['hdx.gis.layer_import_url']

        assert 'hdx.gis.layer_import_url' not in config

    def test_resource_update(self):
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset = self._get_action('package_show')(context, {'id': 'test_dataset_1'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'GeoJSON',
            'name': 'resource_create_test2.geojson'
        }

        resource_data = self._get_action('resource_create')(context, resource)

        r1 = self._get_action('resource_update')(context, resource_data)
        for key, value in resource.iteritems():
            assert value == r1.get(key), "The pair {} - {} should appear in the resource data".format(key, value)
        assert 'shape_info' not in r1, "shape_info should be missing since 'hdx.gis.layer_import_url' config is missing"

        config['hdx.gis.layer_import_url'] = 'http://import.local/'
        context['do_geo_preview'] = False

        r2 = self._get_action('resource_update')(context, resource_data)
        assert 'shape_info' not in r2, "shape_info should be missing since 'do_geo_preview' is False"
        for key, value in resource.iteritems():
            assert value == r2.get(key), "The pair {} - {} should appear in the resource data".format(key, value)

        context['do_geo_preview'] = True
        r3 = self._get_action('resource_create')(context, resource)
        assert 'shape_info' in r3, "shape_info should exist since 'hdx.gis.layer_import_url' config is set"
        del resource['shape_info']
        for key, value in resource.iteritems():
            assert value == r3.get(key), "The pair {} - {} should appear in the resource data".format(key, value)