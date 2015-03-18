'''
Created on Mar 16, 2015

@author: alexandru-m-g
'''

import ckan.model as model
import logging as logging

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_org_group.controllers.browse_controller as browse_controller


class TestHDXBrowseController(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_theme')

    def _create_world(self):
        group = {'name': 'world',
                    'title': 'World',
                    'description': 'This is a test group for world',
                }
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._get_action('group_create')(context, group)

    def test_get_countries(self):
        self._create_world()
        controller = browse_controller.BrowseController()
        groups = controller.get_countries('testsysadmin')
        assert len(groups) == 3, 'There are 3 groups in the test data'
        assert groups[0]['name'] == 'world', 'Even sorted, world needs to be the first in the list'
        for group in groups:
            indicator_count = group.get('indicator_count', None)
            indicator_count = indicator_count if indicator_count else 0
            dataset_count = group.get('dataset_count', None)
            dataset_count = dataset_count if dataset_count else 0
            total = group.get('packages', None)
            total = total if total else 0
            assert indicator_count+dataset_count == total
            if group['name'] == 'roger':
                assert indicator_count == 2, 'There are 2 indicators for group david'
        pass

    def _create_additional_org(self):
        organization = {'name': 'additional-test-org',
                    'title': 'This is an additional org',
                    'org_url': 'http://test-org.test',
                    'description': 'This is an additional org',
                    'users': [{'name': 'testsysadmin'}]}
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._get_action('organization_create')(context, organization)

    def test_get_organizations(self):
        self._create_additional_org()

        request_params = {
            'sort_option': 'title asc',
            'page': 1
        }
        controller = browse_controller.BrowseController()
        orgs, len = controller.get_organizations('testsysadmin', request_params)
        assert len == 2, 'There are 2 organizations in the test data'
        assert orgs[1]['name'] == 'additional-test-org'

        request_params['sort_option'] = 'title desc'
        orgs, len = controller.get_organizations('testsysadmin', request_params)
        assert len == 2, 'There are 2 organizations in the test data'
        assert orgs[0]['name'] == 'additional-test-org'
