'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h

render = base.render
get_action = logic.get_action
c = common.c


class CrisisController(base.BaseController):

    def show(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        limit = 25
        c.q = u'ebola'
        data_dict = {'sort': u'metadata_modified desc',
                     'fq': '+dataset_type:dataset',
                     'rows': limit,
                     'q': c.q,
                     'start': 0,
                     }
        query = get_action("package_search")(context, data_dict)

#         c.page = h.Page(
#             collection=query['results'],
#             page=page,
#             url=pager_url,
#             item_count=query['count'],
#             items_per_page=limit
#         )
        c.items = query['results']

        c.other_links = {}
        c.other_links['show_more'] = h.url_for(
            "search", **{'q': u'ebola', 'sort': u'metadata_modified desc'})

        return render('crisis/crisis.html')
