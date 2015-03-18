'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h
import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

render = base.render
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)


class CrisisController(base.BaseController):

    def show(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_res_id = config.get('hdx.ebola.datastore.top_line_num')
        cases_res_id = config.get('hdx.ebola.datastore.cases')
        appeal_res_id = config.get('hdx.ebola.datastore.appeal')

        crisis_data_access = data_access.EbolaCrisisDataAccess(top_line_res_id, cases_res_id, appeal_res_id)
        crisis_data_access.fetch_data(context)
        top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        search_params = {'q': u'ebola'}

        self._generate_dataset_results(context, search_params)

        self._generate_other_links(search_params)

        template_data = {
            'data': {
                'top_line_items': top_line_items,
                'cases_datastore_id': cases_res_id
            },
            'errors': None,
            'error_summary': None,
        }

        return render('crisis/crisis-ebola.html', extra_vars=template_data)

    def _generate_dataset_results(self, context, search_params, action_alias='show_crisis'):
        limit = 25

        sort_option = request.params.get('sort', None)

        page = int(request.params.get('page', 1))
        data_dict = {'sort': sort_option if sort_option else u'metadata_modified desc',
                     'rows': limit,
                     'start': (page - 1) * limit,
                     'ext_indicator': u'0'
                     }

        search_param_list = [
            key + ":" + value for key, value in search_params.iteritems() if key != 'q']
        if 'q' in search_params:
            data_dict['q'] = search_params['q']
            c.q = search_params['q']
        if search_param_list != None:
            data_dict['fq'] = " ".join(
                search_param_list) + ' +dataset_type:dataset'

        query = get_action("package_search")(context, data_dict)

        def pager_url(q=None, page=None):
            if sort_option:
                url = h.url_for(
                    action_alias, page=page, sort=sort_option) + '#datasets-section'
            else:
                url = h.url_for(action_alias, page=page) + '#datasets-section'
            return url

        get_action('populate_related_items_count')(context, {'pkg_dict_list':query['results']})

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )
        c.items = query['results']
        c.item_count = query['count']

    def _generate_other_links(self, search_params):
        c.other_links = {}
        sort_option = request.params.get('sort', None)

        show_more_params = {'sort': sort_option if sort_option else u'metadata_modified desc',
                            'ext_indicator': '0'}
        show_more_params.update(search_params)
        c.other_links['show_more'] = h.url_for(
            "search", **show_more_params)
