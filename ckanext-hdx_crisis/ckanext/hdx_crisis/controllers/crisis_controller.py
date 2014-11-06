'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import datetime as dt

import pylons.config as config
import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h

render = base.render
get_action = logic.get_action
c = common.c
request = common.request

log = logging.getLogger(__name__)


class CrisisController(base.BaseController):

    def show(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        datastore_resource_id = self._get_datastore_resource_id(
            context, config.get('hdx.crisis.ebola_dataset', None), config.get('hdx.crisis.ebola_resource_title', None))
        if datastore_resource_id:
            c.top_line_items = self._get_top_line_items(
                context, datastore_resource_id)

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
            return h.url_for('show_crisis', page=page)

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

    def _get_top_line_items(self, context, datastore_resource_id):
        result = get_action('datastore_search')(
            context, {'resource_id': datastore_resource_id})
        if 'records' in result:
            for r in result['records']:
                d = dt.datetime.strptime(
                    r[u'latest_date'], '%Y-%m-%dT%H:%M:%S')
                r[u'latest_date'] = dt.datetime.strftime(d, '%d-%b-%Y')
            return result['records']
        return []

    def _get_datastore_resource_id(self, context, dataset_id, resource_name):
        try:
            dataset = get_action('package_show')(
                context, {'id': dataset_id})

            if 'resources' in dataset:
                for r in dataset['resources']:
                    if 'datastore_active' in r and r['datastore_active'] \
                            and r['name'] == resource_name:
                        return r['id']
            return None
        except:
            log.warning('No dataset with id ' + dataset_id)
            return None
