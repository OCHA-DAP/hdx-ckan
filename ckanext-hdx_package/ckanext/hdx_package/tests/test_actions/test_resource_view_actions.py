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

    def test_resource_view_create_hdx_hxl_preview(self):
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        resource = {
            'package_id': 'test_dataset_1',
            'url': 'https://test.com/test.csv',
            'resource_type': 'api',
            'url_type': 'api',
            'format': 'CSV',
            'name': 'test.csv'
        }

        r = self._get_action('resource_create')(context, resource)

        normal_user = factories.User()
        self._get_action('group_member_create')(context, {
            'id': 'hdx-test-org',
            'username': normal_user['name'],
            'role': 'editor'
        })
        resource_view = {
            "description": "",
            "title": "Quick Charts",
            "resource_id": r['id'],
            "view_type": "hdx_hxl_preview",
            "hxl_preview_config": 'test'
        }

        def run_deletion_creation_as(username):
            user_context = {
                'model': model,
                'session': model.Session,
                'user': username
            }
            rv = self._get_action('resource_view_create')(user_context, resource_view)

            search_dict = {
                'extras': {
                    'ext_quickcharts': u'1'
                },
                'fq': '+dataset_type:dataset name:test_dataset_1'
            }
            results1 = self._get_action('package_search')(user_context, search_dict)

            assert results1['count'] == 1, 'our dataset should be indexed as having quickcharts'

            self._get_action('resource_view_delete')(user_context, {'id': rv['id']})

            results2 = self._get_action('package_search')(user_context, search_dict)

            assert results2['count'] == 0, 'our dataset should be indexed as NOT having quickcharts anymore'

        run_deletion_creation_as(normal_user['name'])
        run_deletion_creation_as('testsysadmin')
