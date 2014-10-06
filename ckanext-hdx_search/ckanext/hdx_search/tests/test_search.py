'''
Created on September 18, 2014

@author: Marianne, Alex, Dan


'''
import logging as logging
import ckan.lib.helpers as h
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestHDXSearch(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_theme')

    def test_search(self):
        user = model.User.by_name('tester')
        offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health'})
        assert '200' in response.status

    def test_indicators(self):
    	user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_indicator':1})
        assert '200' in response.status

    def test_datasets(self):
    	user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_indicator':0})
        assert '200' in response.status

	def test_features(self):
		user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_feature':1})
        assert '200' in response.status

    def test_sort(self):
        import ckanext.hdx_search.controllers.search_controller as search
        features = [{'count': 1, 'display_name': u'Sierra Leone', 'feature_type': 'country', 'url': '/group/sle', 'description': u'', 'name': 'sle'}, {'count': 1, 'display_name': u'Senegal', 'feature_type': 'country', 'url': '/group/sen', 'description': u'', 'name': 'sen'}, {'count': 50, 'display_name': u'World', 'feature_type': 'country', 'url': '/group/world', 'description': u'', 'name': 'world'}, {'count': 1, 'display_name': u'Nigeria', 'feature_type': 'country', 'url': '/group/nga', 'description': u'', 'name': 'nga'}, {'count': 1, 'display_name': u'Liberia', 'feature_type': 'country', 'url': '/group/lbr', 'description': u'', 'name': 'lbr'}, {'count': 1, 'display_name': u'Kenya', 'feature_type': 'country', 'url': '/group/ken', 'description': u'', 'name': 'ken'}, {'count': 1, 'display_name': u'Guinea', 'feature_type': 'country', 'url': '/group/gin', 'description': u'', 'name': 'gin'}, {'count': 2, 'display_name': u'Colombia', 'feature_type': 'country', 'url': '/group/col', 'description': u'', 'name': 'col'}]
        sorted_features = search.sort_features(features)
        assert sorted_features[0]['name'] == 'world'

    def test_package_search(self):
        import ckanext.hdx_search.controllers.search_controller as search
        user = model.User.by_name('hdx')
        data_dict = {
                'q': '',
                'fq': '',
                'facet.field': ['vocab_Topics','groups','organizations'],
                'rows': 25,
                'start': (1 - 1) * 25,
                'sort': None,
                'extras': {}
            }
        context = {'model': model, 'session': model.Session,
                       'user': user, 'for_view': True, 'auth_user_obj': user}
        s = search.package_search(context, data_dict)
        assert len(s['results']) > 0
