import logging
from typing import Any, Optional, Union, cast

from flask import Blueprint
from flask.views import MethodView

import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import current_user
from ckan.types import Context, Response
from ckanext.hdx_org_group.controller_logic.organization_request_logic import OrgRequestLogic

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
    return redirect(url_for('hdx_org_request.new'))


class OrgNewRequestView(MethodView):

    def post(self) -> Union[Response, str]:
        context = _prepare_and_check_access()
        data_dict = None
        org_request_logic = OrgRequestLogic(context, request)
        try:
            data_dict = org_request_logic.read()
        except dictization_functions.DataError:
            abort(400, _(u'Integrity Error'))

        data, errors = org_request_logic.validate(data_dict)
        if errors:
            return self.get(data, errors)

        get_action('hdx_send_new_org_request')(context, data)
        return redirect('hdx_org_request.completed_request')

    def get(self,
            data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None) -> str:
        context = _prepare_and_check_access()
        extra_vars = {
            u'data': data or {},
            u'errors': errors or {},
            u'error_summary': error_summary or {}
        }
        return render('org/request/org_new_request.html', extra_vars=extra_vars)


# created this method to allow mock in test
def _check_request_referrer_and_access(_request=None, url='/org/request/new'):
    if _request and _request.referrer and url in _request.referrer:
        _prepare_and_check_access()
        return True
    return False


def completed_request() -> str:
    if _check_request_referrer_and_access(request):
        return render('org/request/completed_request.html')
    else:
        abort(404, _(u'Page not found'))


hdx_org_request.add_url_rule(u'/', view_func=org_request, strict_slashes=False)
hdx_org_request.add_url_rule(u'/new/', view_func=OrgNewRequestView.as_view(str(u'new')),
                             methods=[u'GET', u'POST'], strict_slashes=False)
hdx_org_request.add_url_rule(u'/completed/', view_func=completed_request, methods=[u'GET'], strict_slashes=False)
