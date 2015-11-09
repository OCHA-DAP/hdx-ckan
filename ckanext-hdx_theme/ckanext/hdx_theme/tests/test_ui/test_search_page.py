'''
Created on September 24, 2014

@author: alexandru-m-g

'''

import ckan.lib.helpers as h
import unicodedata

import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util


class TestSearchPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    # loads missing plugins
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_package hdx_theme')

    @classmethod
    def setup_class(cls):
        super(TestSearchPage, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    def test_active_tab(self):
        all_page = self._get_search_page('')

        page = str(all_page.response)
        begin_str = '<input id="show-indicators"'
        end_str = 'label'
        search_strings = ['checked="checked"']
        hdx_test_util.strings_not_in_text(page, search_strings, begin_str, end_str)

        indicator_page = self._get_search_page('', 1)
        page = str(indicator_page.response)
        begin_str = '<input id="show-indicators"'
        end_str = 'label'
        search_strings = ['checked="checked"']
        hdx_test_util.are_strings_in_text(page, search_strings, begin_str, end_str)

        dataset_page = self._get_search_page('', 0)
        page = str(dataset_page.response)
        begin_str = '<input id="show-indicators"'
        end_str = 'label'
        search_strings = ['checked="checked"']
        hdx_test_util.strings_not_in_text(page, search_strings, begin_str, end_str)

    def _get_search_page(self, query, ext_indicator=None, apikey=None):
        page = None
        if ext_indicator is not None:
            url = h.url_for('search', ext_indicator=ext_indicator)
        else:
            url = h.url_for('search')
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page
