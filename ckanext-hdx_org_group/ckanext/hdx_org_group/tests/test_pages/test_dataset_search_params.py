'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util
from ckan.lib.helpers import Page

log = logging.getLogger(__name__)


class TestDatasetSearchParams(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_theme')

    def test_search_params(self):
        url = h.url_for(
            controller='organization', action='read', id='hdx-test-org')

        result = self.app.get(url)
        page = str(result.response)

        begin_str = '<form class="list-items search-form"'
        end_str = '</form>'
        search_item = 'name="q"'

        count = hdx_test_util.count_string_occurences(page, search_item,
                                                      begin_str, end_str)

        assert count == 1, 'There should be exactly one input with name q in the form'
