import logging
from typing import cast

from flask import Blueprint

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import current_user
from ckan.types import Context

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
url_for = tk.url_for
check_access = tk.check_access
abort = tk.abort
render = tk.render
g = tk.g
_ = tk._
request = tk.request

hdx_org_request = Blueprint(u'hdx_org_request', __name__, url_prefix=u'/org/request')


def _prepare_and_check_access() -> Context:
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
        u'save': u'save' in request.form,
    })
    try:
        check_access(u'hdx_send_new_org_request', context)
    except NotAuthorized:
        abort(403, _(u'Page not found'))
    return context


def org_request() -> str:
    return redirect(url_for('hdx_org_request.org_new_request'))


def org_new_request() -> str:
    context = _prepare_and_check_access()

    template_data = {
        'data': {
        }
    }
    return render('org/request/org_new_request.html', extra_vars=template_data)


hdx_org_request.add_url_rule(u'/', view_func=org_request, strict_slashes=False)
hdx_org_request.add_url_rule(u'/new/', view_func=org_new_request, methods=[u'GET'], strict_slashes=False)
# hdx_org_request.add_url_rule(u'/completed/', view_func=completed_request, methods=[u'POST'], strict_slashes=False)
