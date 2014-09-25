'''
Created on September 24, 2014

@author: alexandru-m-g

'''

import ckan.tests as tests
import ckan.lib.helpers as h
import ckan.model as model
import unicodedata

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

class TestSearchPage(hdx_test_base.HdxBaseTest):
    #loads missing plugins
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_theme')
        
    def test_active_tab(self):
        all_page = self._getSearchPage('')
        assert '<li class="mx-tab-item-all active">' in str(all_page.response), 'Page needs to have all tab selected'
        assert '<li class="mx-tab-item-indicators active">' not in str(all_page.response), 'Page needs to have all tab selected'
        assert '<li class="mx-tab-item-feature-pages active">' not in str(all_page.response), 'Page needs to have all tab selected'
        assert '<li class="mx-tab-item-datasets active">' not in str(all_page.response), 'Page needs to have all tab selected'
        
        indicator_page = self._getSearchPage('', 1)
        assert '<li class="mx-tab-item-all active">' not in str(indicator_page.response), 'Page needs to have indicators tab selected'
        assert '<li class="mx-tab-item-indicators active">' in str(indicator_page.response), 'Page needs to have indicators tab selected'
        assert '<li class="mx-tab-item-feature-pages active">' not in str(indicator_page.response), 'Page needs to have indicators tab selected'
        assert '<li class="mx-tab-item-datasets active">' not in str(indicator_page.response), 'Page needs to have indicators tab selected'
        
        dataset_page = self._getSearchPage('', 0)
        assert '<li class="mx-tab-item-all active">' not in str(dataset_page.response), 'Page needs to have datasets tab selected'
        assert '<li class="mx-tab-item-indicators active">' not in str(dataset_page.response), 'Page needs to have datasets tab selected'
        assert '<li class="mx-tab-item-feature-pages active">' not in str(dataset_page.response), 'Page needs to have datasets tab selected'
        assert '<li class="mx-tab-item-datasets active">' in str(dataset_page.response), 'Page needs to have datasets tab selected'
    
    def _getSearchPage(self, query, ext_indicator=None, apikey=None):
        page = None
        if ext_indicator != None:
            url = h.url_for('search', ext_indicator=ext_indicator)
        else:
            url = h.url_for('search')
        if apikey:
            page = self.app.get(url, headers={'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii','ignore')})
        else:
            page = self.app.get(url)
        return page