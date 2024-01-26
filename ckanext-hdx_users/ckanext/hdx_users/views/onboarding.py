import logging

from flask import Blueprint

import ckan.authz as new_authz
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.permissions as ph
from ckan.views.home import CACHE_PARAMETERS
from ckanext.hdx_users.helpers.permissions import Permissions

log = logging.getLogger(__name__)

# shortcuts
h = tk.h
get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
redirect = h.redirect_to
check_access = tk.check_access
abort = tk.abort
render = tk.render
g = tk.g
_ = tk._
request = tk.request

hdx_user_onboarding = Blueprint(u'hdx_user_onboarding', __name__, url_prefix=u'/signup')


def _extra_template_variables(context, data_dict):
    """
    This is no longer inspired from ckan's UserController -> _setup_template_variables()
    but from the new flask controller views/users -> _extra_template_variables()
    """

    extra = {
    }
    return extra


def read():
    context = {u'model': model, u'session': model.Session,
               u'user': g.user, u'auth_user_obj': g.userobj,
               u'for_view': True, u'with_related': True}

    data_dict = {
                 }
    extra_vars = _extra_template_variables(context, data_dict)

    return render('onboarding/signup/user-info.html', extra_vars=extra_vars)


hdx_user_onboarding.add_url_rule(u'user-info', methods=[u'GET', u'POST'], view_func=read)
