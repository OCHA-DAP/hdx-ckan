import pytest
import six

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

config = tk.config
h = tk.h


class TestHDXUpdateResourceFormat(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_resource_create(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset = self._get_action('package_show')(context, {'id': 'test_dataset_1'})

        resource = {
            'package_id': dataset['id'],
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test_file.geojson',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'resource_create_test1.geojson'
        }

        r1 = self._get_action('resource_create')(context, resource)
        for key, value in resource.items():
            assert value == r1.get(key), "The pair {} - {} should appear in the resource data".format(key, value)
        assert resource.get('format') == r1.get('format')

        resource['name'] = 'resource_create_test2.geojson'
        resource['format'] = 'GeoJSON'

        r2 = self._get_action('resource_create')(context, resource)
        # assert 'shape_info' in r2, "shape_info should exist since 'hdx.gis.layer_import_url' config is set"
        for key, value in resource.items():
            assert value == r2.get(key), "The pair {} - {} should appear in the resource data".format(key, value)

        test_client = self.get_backwards_compatible_test_client()
        read_pkg_url = h.url_for('dataset.read', id=dataset['id'])

        result = test_client.get(read_pkg_url)
        assert 'resource_create_test1.geojson' in result.body
        assert 'humanitarianicons-Out-of-platform' in result.body
        assert '/images/homepage/download.svg' in result.body
        assert 'resource_create_test2.geojson' in result.body
