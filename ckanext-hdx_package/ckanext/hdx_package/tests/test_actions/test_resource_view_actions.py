import pytest
import logging as logging
import six


import ckan.model as model
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestResourceViewActions(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_package hdx_theme')

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestResourceViewActions, cls)._create_test_data(create_datasets=True, create_members=True)

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
