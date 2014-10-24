'''
Created on Oct 15, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base
import ckan.lib.helpers as h
from ckan.common import c

import ckanext.hdx_search.controllers.search_controller as search_controller


class HDXSimpleSearchController(search_controller.HDXSearchController):

    def package_search(self):
        return search_controller.HDXSearchController.search(self)

    def _search_url(self, params, package_type=None):
        if not package_type or package_type == 'dataset':
            url = h.url_for('simple_search')
        else:
            url = h.url_for('{0}_search'.format(package_type))
        return search_controller.url_with_params(url, params)

    def _decide_adding_dataset_criteria(self, data_dict):
        pass

    def _allowed_num_of_items(self, search_extras):
        return search_controller.LARGE_NUM_OF_ITEMS

    def _search_template(self):
        return base.render('search/simple_search.html')

    def _set_remove_field_function(self):
        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='ckanext.hdx_search.controllers.simple_search_controller:HDXSimpleSearchController', action='package_search')

        c.remove_field = remove_field
    
    def _get_named_route(self):
        return 'simple_search'