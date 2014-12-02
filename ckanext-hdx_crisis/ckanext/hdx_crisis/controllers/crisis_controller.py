'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h

import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_crisis.formatters.top_line_items_formatter as formatters

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

        crisis_data_access = data_access.EbolaCrisisDataAccess()
        crisis_data_access.fetch_data(context)
        c.top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsFormatter(c.top_line_items)
        formatter.format_results()

        search_term = u'ebola'

        self._generate_dataset_results(context, search_term)

        self._generate_other_links(search_term)

        return render('crisis/crisis.html')

    def _generate_dataset_results(self, context, search_term):
        limit = 25
        c.q = search_term

        page = int(request.params.get('page', 1))
        data_dict = {'sort': u'metadata_modified desc',
                     'fq': '+dataset_type:dataset',
                     'rows': limit,
                     'q': c.q,
                     'start': (page - 1) * limit
                     }
        query = get_action("package_search")(context, data_dict)

        def pager_url(q=None, page=None):
            url = h.url_for('show_crisis', page=page) + '#datasets-section'
            return url

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )
        c.items = query['results']
        c.item_count = query['count']

    def _generate_other_links(self, search_term):
        c.other_links = {}
        c.other_links['show_more'] = h.url_for(
            "search", **{'q': search_term, 'sort': u'metadata_modified desc',
                         'ext_indicator': '0'})
