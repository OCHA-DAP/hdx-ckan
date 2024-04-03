import logging
from typing import cast

from flask import Blueprint

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import current_user
from ckan.types import Context
from ckanext.hdx_org_group.controller_logic.organization_join_logic import  OrgJoinLogic

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

hdx_org_join = Blueprint(u'hdx_org_join', __name__, url_prefix=u'/org/join')


def _prepare_and_check_access() -> Context:
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
        u'save': u'save' in request.form,
    })
    try:
        check_access(u'hdx_org_join_request', context)
    except NotAuthorized:
        abort(403, _(u'Page not found'))
    return context


def org_join() -> str:
    return redirect(url_for('hdx_org_join.find_organisation'))


def find_organisation() -> str:

    context = _prepare_and_check_access()

    org_join_logic = OrgJoinLogic(context)
    org_join_logic.read()

    template_data = {
        'data': {
            'org_list': org_join_logic.active_org_list,
        }
    }
    return render('onboarding/org-join/find-organisation.html', extra_vars=template_data)

def confirm_organisation() -> str:

    context = _prepare_and_check_access()

    org_id = request.form.get('org_id') or 'hdx'

    org_dict = get_action(u'organization_show')(context, {'id':org_id})

    template_data = {
        'data': {
            'org_dict': org_dict,
        }
    }
    return render('onboarding/org-join/find-organisation.html', extra_vars=template_data)

hdx_org_join.add_url_rule(u'/', view_func=org_join, strict_slashes=False)
hdx_org_join.add_url_rule(u'/find/', view_func=find_organisation, methods=[u'GET'], strict_slashes=False)
hdx_org_join.add_url_rule(u'/confirm/', view_func=confirm_organisation, methods=[u'GET', u'POST'], strict_slashes=False)
