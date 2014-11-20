'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import logging
import datetime as dt
import decimal
import json

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h

import ckanext.hdx_crisis.dao.data_access as data_access

render = base.render
get_action = logic.get_action
c = common.c
request = common.request
_ = common._

Decimal = decimal.Decimal

log = logging.getLogger(__name__)


class CrisisController(base.BaseController):

    def show(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        crisis_data_access = data_access.EbolaCrisisDataAccess()
        crisis_data_access.fetch_data(context)
        c.top_line_items = crisis_data_access.get_top_line_items()
        self._format_results(c.top_line_items)

        limit = 25
        c.q = u'ebola'

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

        c.other_links = {}
        c.other_links['show_more'] = h.url_for(
            "search", **{'q': u'ebola', 'sort': u'metadata_modified desc',
                         'ext_indicator': '0'})

        return render('crisis/crisis.html')

    def _get_decimal_value(self, value):
        decimal_value = Decimal(str(value)).quantize(
            Decimal('.1'), rounding=decimal.ROUND_HALF_UP)
        return decimal_value

    def _format_results(self, records):
        for r in records:
            if 'sparklines' in r:
                r['sparklines_json'] = json.dumps(r['sparklines'])

            d = dt.datetime.strptime(r[u'latest_date'], '%Y-%m-%dT%H:%M:%S')
            r[u'latest_date'] = dt.datetime.strftime(d, '%b %d, %Y')

            modified_value = r[u'value']
            if r[u'units'] == 'ratio':
                modified_value *= 100.0
            elif r[u'units'] == 'million':
                modified_value /= 1000000.0

            int_value = int(modified_value)
            if int_value == modified_value:
                r[u'formatted_value'] = '{:,}'.format(int_value)
            else:
                if r[u'units'] == 'ratio':
                    r[u'formatted_value'] = '{:,.1f}'.format(
                        self._get_decimal_value(modified_value))
                elif r[u'units'] == 'million':
                    r[u'formatted_value'] = '{:,.1f}'.format(
                        self._get_decimal_value(modified_value))
                    #r[u'formatted_value'] += ' ' + _('million')
