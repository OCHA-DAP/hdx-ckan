import logging

import ckan.lib.base as base
import ckan.lib.jsonp as jsonp
import ckan.lib.navl.dictization_functions
import ckan.logic as logic
import ckan.model as model
from ckan.common import c, request

log = logging.getLogger(__name__)

# shortcuts
get_action = logic.get_action
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound
ValidationError = logic.ValidationError
DataError = ckan.lib.navl.dictization_functions.DataError

IGNORE_FIELDS = ['q']
CONTENT_TYPES = {
    'text': 'text/plain;charset=utf-8',
    'html': 'text/html;charset=utf-8',
    'json': 'application/json;charset=utf-8',
}


class APIExtensionController(base.BaseController):


    @jsonp.jsonpify
    def hdx_user_autocomplete(self):
        q = request.params.get('q', '')
        org = request.params.get('org', None)
        limit = request.params.get('limit', 20)
        user_list = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'auth_user_obj': c.userobj}

            data_dict = {'q': q, 'limit': limit, 'org': org}

            user_list = get_action('hdx_user_autocomplete')(context, data_dict)
        return user_list


