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
import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)

suffix = '#datasets-section'


class WfpController(simple_search_controller.HDXSimpleSearchController):

    def org_read(self):

        top_line_items = self.get_top_line_numbers()

        req_params = self.process_req_params(request.params)

        tab_results, all_results = self.get_dataset_search_results('wfp', request.params)
        tab = self.get_tab_name(request.params.get('ext_indicator', None))

        facets = self.get_facet_information(tab_results, all_results, tab, req_params)

        template_data = {
            'data': {
                'message': 'Test message',
                'top_line_items': top_line_items,
                'dataset_results': {
                    'facets': facets
                },
                "request_params": request.params
            },
            'errors': None,
            'error_summary': None,
            }

        result = render('organization/custom/wfp.html', extra_vars=template_data)

        return result

    def get_top_line_numbers(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        top_line_src_dict = {
            'top-line-numbers': {
                'dataset': 'wfp-topline-figures',
                'resource': 'wfp-topline-figures.csv'
            }
        }
        datastore_access = data_access.CrisisDataAccess(top_line_src_dict)
        datastore_access.fetch_data(context)
        top_line_items = datastore_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        return top_line_items

    def get_tab_name(self, ext_indicator):
        if ext_indicator:
            tab = 'indicators' if ext_indicator == '1' else 'datasets'
        else:
            tab = 'all'

        return tab

    def process_req_params(self, params):
        req_params = {}
        accepted_params = ['sort', 'q', 'organization', 'tags',
                           'vocab_Topics', 'license_id', 'groups',
                           'res_format', '_show_filters']
        for k, v in params.items():
            if k in accepted_params:
                if k in req_params:
                    req_params[k].append(v)
                else:
                    req_params[k] = [v]

        return req_params

    def get_facet_information(self, tab_results, all_results, tab, req_params):
        search_facets = None
        result_facets = {}
        if tab == 'indicators' or tab == 'datasets':
            search_facets = tab_results['search_facets']
        else:
            search_facets = all_results['search_facets']

        self._add_facet(result_facets, search_facets, 'groups', _('Locations'))
        self._add_facet(result_facets, search_facets, 'tags', _('Tags'))
        self._add_facet(result_facets, search_facets, 'res_format', _('Formats'))
        self._add_facet(result_facets, search_facets, 'license_id', _('Licenses'))

        self._populate_facet_links(result_facets, req_params)

        return result_facets


    def _add_facet(self, facet_dict, search_facets, facet_code, facet_name):
        if facet_code in search_facets:
            facet_dict[facet_name] = {
                'value_items': search_facets.get(facet_code, {}).get('items', []),
                'code': search_facets.get(facet_code, {}).get('title', '')
            }
            facet_dict[facet_name]['count'] = len(facet_dict[facet_name]['value_items'])

    def _populate_facet_links(self, facets, params):
        for facet in facets.itervalues():
            params_copy = params.copy()
            code = facet['code']
            if code in params:
                facet['is_used'] = True
                params_copy.pop(code)
                facet['clear_link'] = h.url_for(self._get_named_route(), **params_copy) + suffix
            else:
                facet['is_used'] = False

            for item in facet['value_items']:
                params_item_copy = params.copy()
                if code in params:
                    if item['name'] in params[code]:
                        # user already filtered by this item
                        params_item_copy[code] = [el for el in params_item_copy[code] if el != item['name']]
                        item['remove_link'] = h.url_for(self._get_named_route(), **params_item_copy) + suffix
                        item['is_used'] = True
                    else:
                        params_item_copy[code] = params_item_copy[code] + [item['name']]
                        item['filter_link'] = h.url_for(self._get_named_route(), **params_item_copy) + suffix
                        item['is_used'] = False
                else:
                    params_item_copy[code] = [item['name']]
                    item['filter_link'] = h.url_for(self._get_named_route(), **params_item_copy) + suffix
                    item['is_used'] = False




    def get_dataset_search_results(self, org_code, req_params):
        facets = ['groups', 'tags', 'res_format', 'license_id', 'extras_indicator']

        fq = u'organization:"{}" +dataset_type:dataset'.format(org_code)
        for (param, value) in req_params.items():
            is_fq_param = param in facets and param != 'ext_indicator'
            if is_fq_param and len(value):
                fq += u' {}:"{}"'.format(param, value)

        search_extras = {}
        ext_indicator = req_params.get('ext_indicator', None)
        if ext_indicator:
            search_extras['ext_indicator'] = ext_indicator

        # limit = self._allowed_num_of_items(search_extras)
        limit = 8
        page = self._page_number()
        params_nopage = {k: v for k, v in req_params.items() if k != 'page'}

        sort_by = req_params.get('sort', None)

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('wfp_read', **params) + suffix

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        self._set_other_links(suffix=suffix, other_params_dict={'id': org_code})
        self._which_tab_is_selected(search_extras)
        (query, all_results) = self._performing_search(req_params.get('q',''), fq, facets, limit, page, sort_by,
                                                       search_extras, pager_url, context)

        return query, all_results

    def _set_other_links(self, suffix='', other_params_dict=None):
        super(WfpController, self)._set_other_links(suffix=suffix, other_params_dict=other_params_dict)
        c.other_links['advanced_search'] = h.url_for('search', organization=other_params_dict['id'])

    def _get_named_route(self):
        return 'wfp_read'