'''
Created on September 18, 2014

@author: Marianne

'''
import logging as logging
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestHDXSearch(hdx_test_base.HdxBaseTest):

    @classmethod
    
    def test_search(self):
        user = model.User.by_name('tester')
        offset = h.url_for(controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={q:'test'})
        assert '200' in response.status