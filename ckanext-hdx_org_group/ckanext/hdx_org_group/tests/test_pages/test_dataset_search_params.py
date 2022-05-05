'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)


class TestDatasetSearchParams(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_request_data requestdata hdx_pages hdx_search hdx_org_group hdx_package hdx_user_extra hdx_users hdx_theme')

    @classmethod
    def setup_class(cls):
        from ckanext.hdx_users.model import setup as users_setup
        from ckanext.hdx_user_extra.model import setup as ue_setup
        from ckanext.hdx_pages.model import setup as pages_setup
        from ckanext.requestdata.model import setup as requestdata_setup

        super(TestDatasetSearchParams, cls).setup_class()
        # users_setup()
        # ue_setup()
        # pages_setup()
        # requestdata_setup()

    def test_search_params(self):
        url = h.url_for(
            controller='organization', action='read', id='hdx-test-org')

        result = self.app.get(url, extra_environ={'REMOTE_USER': 'testsysadmin'})
        page = result.body

        begin_str = '<section class="search-list list-items">'
        end_str = '</section>'
        search_item = 'name="q"'

        count = hdx_test_util.count_string_occurences(page, search_item,
                                                      begin_str, end_str)

        assert count == 1, 'There should be exactly one input with name q in the form'
