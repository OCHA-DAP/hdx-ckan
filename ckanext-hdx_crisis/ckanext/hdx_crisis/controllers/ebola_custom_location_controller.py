'''
Created on Dec 2, 2014

@author: alexandru-m-g
updated by dan on Jun 22, 2015
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.lib.helpers as h

import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_crisis.dao.ebola_crisis_data_access as ebola_crisis_data_access
import ckanext.hdx_search.controllers.search_controller as search_controller

from ckan.controllers.api import CONTENT_TYPES

EbolaCrisisDataAccess = ebola_crisis_data_access.EbolaCrisisDataAccess

render = base.render
c = common.c
request = common.request
response = common.response
get_action = logic.get_action
json = common.json
_ = common._

log = logging.getLogger(__name__)

IndicatorAccess = indicator_access.IndicatorAccess


class EbolaCustomLocationController(search_controller.HDXSearchController):
    '''
    Extends Group and Crisis Controller and is used by custom locations to populate
    and compute the data to be displayed
    '''

    def read(self):
        if (self._is_facet_only_request()):
            c.full_facet_info = self._generate_dataset_results()
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            template_data = self._generate_ebola_template_data()
            return render('crisis/crisis-ebola.html', extra_vars=template_data)

    def _generate_ebola_template_data(self):
        '''
        Compute all the data related to Ebola crisis.
        :return: renders the crisis-ebola.html template with data computed about Ebola
        '''

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_res_id = config.get('hdx.ebola.datastore.top_line_num')
        cases_res_id = config.get('hdx.ebola.datastore.cases')
        appeal_res_id = config.get('hdx.ebola.datastore.appeal')

        crisis_data_access = EbolaCrisisDataAccess(top_line_res_id, cases_res_id, appeal_res_id)
        crisis_data_access.fetch_data(context)
        top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        c.full_facet_info = self._generate_dataset_results()

        # self._generate_other_links(search_params)

        template_data = {
            'data': {
                'top_line_items': top_line_items,
                'cases_datastore_id': cases_res_id
            },
            'errors': None,
            'error_summary': None,
        }

        return template_data

    def _generate_dataset_results(self):

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            url = h.url_for('show_crisis', **params) + '#datasets-section'
            return url

        package_type = 'dataset'
        full_facet_info = self._search(package_type, pager_url)

        c.other_links['current_page_url'] = h.url_for('show_crisis')

        return full_facet_info

    def _performing_search(self, q, fq, facet_keys, limit, page, sort_by,
                           search_extras, pager_url, context):

        # c.q = 'ebola'
        fq = fq or ''
        fq = u'ebola ' + fq
        return super(EbolaCustomLocationController, self)._performing_search(c.q, fq, facet_keys, limit, page, sort_by,
                                                                             search_extras, pager_url, context)
