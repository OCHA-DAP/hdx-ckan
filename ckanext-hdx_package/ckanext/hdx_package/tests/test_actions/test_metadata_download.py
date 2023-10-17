'''
Created on Dec 24, 2014

@author: alexandru-m-g
'''

import pytest
import logging as logging
import six
import ckan.logic as logic
from ckan.lib.helpers import url_for
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

config = tk.config
NotAuthorized = logic.NotAuthorized

class TestHDXMetadataDownload(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    def test_resource_create(self, app):
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
        for key, value in resource.items():
            assert value == r1.get(key), "The pair {} - {} should appear in the resource data".format(key, value)
        assert 'shape_info' not in r1, "shape_info should be missing since 'hdx.gis.layer_import_url' config is missing"

        # dataset download metadata
        url_json = url_for(u'hdx_dataset.package_metadata', id=dataset.get('id'), format='json')
        result_json = app.get(url_json)
        assert 'application/json' == result_json.content_type
        assert result_json.json['name'] == 'test_dataset_1'

        url_csv = url_for(u'hdx_dataset.package_metadata', id=dataset.get('id'), format='csv')
        result_csv = app.get(url_csv)
        assert 'text/csv' == result_csv.content_type
        assert 'test_dataset_1' in result_csv.body


        # resource download metadata
        url_json = url_for(u'hdx_dataset.resource_metadata', id=dataset.get('id'), resource_id=r1.get('id'), format='json')
        result_json = app.get(url_json)
        assert 'application/json' == result_json.content_type
        assert result_json.json['id'] == r1.get('id')

        url_csv = url_for(u'hdx_dataset.resource_metadata', id=dataset.get('id'), resource_id=r1.get('id'), format='csv')
        result_csv = app.get(url_csv)
        assert 'text/csv' == result_csv.content_type
        assert r1.get('id') in result_csv.body

        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        dataset_dict = self._get_action('package_patch')(context_sysadmin, {
            'id': dataset.get('id'),
            'private': True
        })

        # dataset download metadata
        url = url_for(u'hdx_dataset.package_metadata', id=dataset_dict.get('id'), format='json')
        result = app.get(url)
        assert result.status_code == 404

        url = url_for(u'hdx_dataset.package_metadata', id=dataset_dict.get('id'), format='csv')
        result = app.get(url)
        assert result.status_code == 404

        # resource download metadata
        url = url_for(u'hdx_dataset.resource_metadata', id=dataset.get('id'), resource_id=r1.get('id'), format='json')
        result = app.get(url)
        assert result.status_code == 404

        url = url_for(u'hdx_dataset.resource_metadata', id=dataset.get('id'), resource_id=r1.get('id'), format='csv')
        result = app.get(url)
        assert result.status_code == 404
