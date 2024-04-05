import logging
from typing import cast
import json
from flask import Blueprint

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import current_user
from ckan.types import Context
from ckanext.hdx_org_group.controller_logic.organization_join_logic import OrgJoinLogic

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
        check_access(u'hdx_send_new_org_request', context)
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
            'org_dict': org_join_logic.active_org_dict,
        }
    }
    return render('org/join/find_organisation.html', extra_vars=template_data)



def _set_custom_rect_logo_url(org_dict):
    if 'customization' in org_dict and org_dict.get('customization'):
        customization = json.loads(org_dict.get('customization'))
        if customization and customization.get('image_rect', None):
            org_dict['custom_rect_logo_url'] = url_for('hdx_local_image_server.org_file',
                                                       filename=customization.get('image_rect'), qualified=True)
def confirm_organisation() -> str:
    context = _prepare_and_check_access()

    org_dict = None
    try:
        org_id = request.form.get('org_id')
        if org_id is not None:
            org_dict = get_action(u'organization_show')(context, {'id':org_id})
            _set_custom_rect_logo_url(org_dict)
        else:
            return redirect(url_for('hdx_org_join.find_organisation'))
    except Exception as ex:
        log.info("Organization not found or not accessible")



    template_data = {
        'data': {
            'org_dict': org_dict,
        }
    }
    return render('org/join/confirm_organisation.html', extra_vars=template_data)

def reason_request() -> str:
    context = _prepare_and_check_access()

    org_dict = None
    try:
        org_id = request.form.get('org_id')
        if org_id is not None:
            org_dict = get_action(u'organization_show')(context, {'id':org_id})
        else:
            return redirect(url_for('hdx_org_join.find_organisation'))
    except Exception as ex:
        log.info("Organization not found or not accessible")

    template_data = {
        'data': {
            'org_dict': org_dict,
        }
    }
    return render('org/join/reason_request.html', extra_vars=template_data)

def completed_request() -> str:
    context = _prepare_and_check_access()

    org_dict = None
    try:
        org_id = request.form.get('org_id')
        msg = request.form.get('message')
        if org_id is not None:
            org_dict = get_action(u'organization_show')(context, {'id':org_id})
        else:
            return redirect(url_for('hdx_org_join.find_organisation'))

        data_dict = {
            'organization': org_id,
            'message': msg,
            'save': u'save',
            'role': u'member',
            'group': org_id
        }
        member = get_action('member_request_create')(context, data_dict)

    except NotFound:
        log.info("Organization not found or not accessible")
    except ValidationError as ex:
        log.error(ex)
    except Exception as ex:
        log.error(ex)
        log.error("Something went wrong with your request. Please contact us.")

    template_data = {
        'data': {
        }
    }
    return redirect(url_for('hdx_org_join.find_organisation'))
    # return render('org/join/completed.html', extra_vars=template_data)


hdx_org_join.add_url_rule(u'/', view_func=org_join, strict_slashes=False)
hdx_org_join.add_url_rule(u'/find/', view_func=find_organisation, methods=[u'GET'], strict_slashes=False)
hdx_org_join.add_url_rule(u'/confirm/', view_func=confirm_organisation, methods=[u'POST'], strict_slashes=False)
hdx_org_join.add_url_rule(u'/reason-request/', view_func=reason_request, methods=[u'POST'], strict_slashes=False)
hdx_org_join.add_url_rule(u'/completed/', view_func=completed_request, methods=[u'GET', u'POST'], strict_slashes=False)
