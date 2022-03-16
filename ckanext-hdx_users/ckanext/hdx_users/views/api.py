from flask import Blueprint, jsonify

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import request

# shortcuts
get_action = tk.get_action
g = tk.g

hdx_user_autocomplete = Blueprint(u'hdx_user_autocomplete', __name__)


# @jsonp.jsonpify
def user_autocomplete():
    q = request.params.get(u'q', u'')
    org = request.params.get(u'org', None)
    limit = request.params.get(u'limit', 20)
    ignore_self = request.args.get(u'ignore_self', False)
    user_list = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

        data_dict = {u'q': q, u'limit': limit, u'ignore_self': ignore_self, u'org': org}

        user_list = get_action(u'hdx_user_autocomplete')(context, data_dict)
    return jsonify(user_list)


hdx_user_autocomplete.add_url_rule(u'/util/user/hdx_autocomplete', view_func=user_autocomplete)
