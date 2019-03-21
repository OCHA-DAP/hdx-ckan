'''
Created on March 21, 2019

@author: dan mihaila
'''

import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXControllerPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_pages hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXControllerPage, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_statistics(self):

        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        usr_stats = self._get_action('hdx_user_statistics')(context_sysadmin, {})
        assert usr_stats
        assert len(usr_stats) == 9

        org_stats = self._get_action('hdx_organization_statistics')(context_sysadmin, {})
        assert org_stats
        assert len(org_stats) == 2
        assert 'active_organizations' in org_stats
        assert 'inactive_organizations' in org_stats

        hdx_general_statistics = self._get_action('hdx_general_statistics')(context_sysadmin, {})
        assert hdx_general_statistics
        assert len(hdx_general_statistics) == 3
        assert 'datasets' in hdx_general_statistics
        assert 'organizations' in hdx_general_statistics
        assert 'users' in hdx_general_statistics
