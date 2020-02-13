'''
Created on September 18, 2014

@author: Marianne, Alex, Dan


'''
import logging as logging
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as p
import ckan.tests.legacy as tests
import json
import unicodedata
import ckanext.hdx_search.actions.actions as actions
from ckan.common import config

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestHDXSearch(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXSearch, cls)._create_test_data(create_datasets=True, create_members=True)

    def _get_url(self, url, apikey=None):
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page

    def test_qa_dashboard(self):

        user = model.User.by_name('tester')
        user.email = 'test@test.com'

        url = h.url_for(controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='search')
        try:
            qa_dashboard_result = self._get_url(url, user.apikey)
        except Exception, ex:
            assert True
            assert '404' in ex.message
            assert '/qa_dashboard' in ex.message

        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        url = h.url_for(controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='search', page=2)
        try:
            qa_dashboard_result = self._get_url(url, user.apikey)
        except Exception, ex:
            assert False
        assert '200' in qa_dashboard_result.status
        assert '/qa_dashboard' in qa_dashboard_result.body

        config['hdx.qadashboard.enabled'] = 'false'
        try:
            qa_dashboard_result = self._get_url(url, user.apikey)
            assert False
        except Exception, ex:
            assert True
        config['hdx.qadashboard.enabled'] = 'true'
        try:
            qa_dashboard_result = self._get_url(url, user.apikey)
        except Exception, ex:
            assert False
        assert True
