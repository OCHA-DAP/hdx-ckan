import pytest
import logging as logging
import six


import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

config = tk.config


class TestResourceViewActions(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestResourceViewActions, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_resource_default_views(self):
        context = {
            'ignore_auth': True,
            'model': model,
            'session': model.Session,
            'user': 'testsysadmin'
        }

        resource_info = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'data1.csv',
            'package_id': 'test_dataset_1',
        }

        # Create resource and get views
        created_resource_data = self._get_action('resource_create')(context, resource_info)
        created_resource_views = self._get_action('resource_view_list')(context, {'id': created_resource_data.get('id')})

        # Assert default view is created for CSV files on resource_create
        assert created_resource_views[0], 'A default "Data Explorer" view should be created for .CSV files on resource_create'
        assert created_resource_views[0].get('title') == 'Data Explorer'
        assert created_resource_views[0].get('view_type') == 'recline_view'

        # Clean up - delete the created view
        self._get_action('resource_view_delete')(context, {'id': created_resource_views[0]['id']})

        # Update resource format to XLSX and get views again
        resource_info['id'] = created_resource_data.get('id')
        resource_info['format'] = 'XLSX'
        updated_resource_data = self._get_action('resource_update')(context, resource_info)
        updated_resource_views = self._get_action('resource_view_list')(context, {'id': updated_resource_data.get('id')})

        # Assert default view is created for XLSX files on resource_update
        assert updated_resource_views[0], 'A default "Data Explorer" view should be created for .XLSX files on resource_update'
        assert updated_resource_views[0].get('id') != created_resource_views[0].get('id'), 'A different view must have been created'
        assert updated_resource_views[0].get('title') == 'Data Explorer'
        assert updated_resource_views[0].get('view_type') == 'recline_view'
