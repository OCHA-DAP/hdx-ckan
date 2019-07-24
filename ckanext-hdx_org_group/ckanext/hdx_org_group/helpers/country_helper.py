import ckan.model as model
import ckan.common as common

import ckanext.hdx_search.controllers.search_controller as search_controller

from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING

c = common.c


def get_latest_cod_datatset(country_name):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'for_view': True,
               'auth_user_obj': c.userobj}

    search = search_controller.HDXSearchController()

    fq = 'groups:"{}" tags:cod +dataset_type:dataset'.format(country_name)
    query_result = search._performing_search(u'', fq, ['organization', 'tags'], 1, 1, DEFAULT_SORTING, None,
                                             None, context)

    return next(iter(query_result.get('results', [])), None)
