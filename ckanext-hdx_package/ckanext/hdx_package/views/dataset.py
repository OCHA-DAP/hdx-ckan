from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckan.logic as logic

from ckanext.hdx_package.views.light_dataset import generic_search
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
_ = tk._

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_dataset = Blueprint(u'hdx_dataset', __name__, url_prefix=u'/dataset')
hdx_search = Blueprint(u'hdx_search', __name__, url_prefix=u'/search')


@check_redirect_needed
def search():
    return generic_search(u'search/search.html')


hdx_search.add_url_rule(u'', view_func=search)
hdx_dataset.add_url_rule(u'', view_func=search)
