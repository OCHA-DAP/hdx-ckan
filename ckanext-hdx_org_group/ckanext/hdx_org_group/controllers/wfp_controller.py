'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''


import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h

import ckanext.hdx_search.controllers.simple_search_controller as simple_search_controller

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)

class WfpController(simple_search_controller.HDXSimpleSearchController):

    def read(self):

        top_line_numbers = self.get_top_line_numbers()
        dataset_results = self.get_dataset_search_results('wfp')


        template_data = {
            'data': {
                'message' : 'Test message',
                'top_line_numbers': top_line_numbers,
                'dataset_results': dataset_results
            },
            'errors': None,
            'error_summary': None,
            }



        result = render('organization/custom/wfp.html', extra_vars=template_data)

        return result


    def get_top_line_numbers(self):
        return None

    def get_dataset_search_results(self, org_code):
        fq = u'organization:"{}" +dataset_type:dataset'.format(org_code)
        facets = ['vocab_Topics']
        suffix = '#datasets-section'

        search_extras = {}
        ext_indicator = request.params.get('ext_indicator', None)
        if ext_indicator:
            search_extras['ext_indicator'] = ext_indicator

        #limit = self._allowed_num_of_items(search_extras)
        limit = 8
        page = self._page_number()
        params_nopage = {k:v for k, v in request.params.items() if k != 'page' }

        sort_by = request.params.get('sort', None)

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page']=page
            return h.url_for('wfp_read', id=org_code, **params) + suffix

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        self._set_other_links(suffix=suffix, other_params_dict={'id':org_code})
        self._which_tab_is_selected(search_extras)
        (query, all_results) = self._performing_search('', fq, facets, limit, page, sort_by,
                                    search_extras, pager_url, context)

        return query, all_results

