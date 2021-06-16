import logging
import ckan.model as model
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.base as base
from flask import Blueprint
from ckan.common import _, request, g, asbool
from ckanext.ytp.request.tools import get_user_member
from ckan.logic import tuplize_dict, clean_dict, parse_params, ValidationError

get_action = tk.get_action
check_access = tk.check_access
render = base.render
abort = tk.abort
_ = tk._
url_for = tk.url_for
config = tk.config
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound
log = logging.getLogger(__file__)
ytp_request = Blueprint(u'ytp_request', __name__, url_prefix=u'/member-request')

NOT_AUTH_MESSAGE = _('Unauthorized')


def show(member_id):
    """ viewing member request """
    try:
        member = model.Session.query(model.Member).get(member_id)
        if not member or member.state != 'pending':
            abort(404, _('Request not found'))

        role = request.params.get('role', None)
        if role:
            check_access('member_request_process', {'member': member_id})
            member.capacity = role
            revision = model.repo.new_revision()
            revision.author = g.user
            revision.message = u'Changed member request role'
            member.save()

        member_user = model.Session.query(model.User).get(member.table_id)
        extra_vars = {"member": member, "member_user": member_user,
                      "roles": _get_available_roles(member_user.name)}
        return render('request/show.html', extra_vars=extra_vars)
    except NotFound:
        abort(404, _('Request not found'))
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)


def list():
    """ List member requests """
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author}
    try:
        member_requests = get_action('member_request_list')(context, {})
        extra_vars = {'member_requests': member_requests}
        return render('request/list.html', extra_vars=extra_vars)
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)


def new(data=None, errors=None, error_summary=None):
    """ new member request """
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author,
               'save': 'save' in request.form,
               'parent': request.params.get('parent', None)}
    try:
        check_access('member_request_create', context)
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)

    if context['save'] and not data:
        return _save_new(context)

    data = data or {}

    extra_vars = {'data': data, 'errors': errors or {}, 'error_summary': error_summary or {}, 'action': 'new',
                  'selected_organization': request.params.get('selected_organization', None)}

    g.roles = _get_available_roles()
    g.user_role = 'editor'

    redirect_to_src_page = asbool(config.get('ytp.requests.redirect_to_src_page', 'true'))
    if redirect_to_src_page:
        return h.redirect_to(request.referrer)
    else:
        g.form = render("request/new_request_form.html", extra_vars=extra_vars)
        return render("request/new.html")


def reject(member_id):
    """ reject member request """
    return _process(member_id, False)


def approve(member_id):
    """ approve member request """
    return _process(member_id, True)


def process():
    """ Process (reject or approve) membership request """
    member_id = request.params.get('member_id')
    approve_status = request.params.get('approve')
    return _process(member_id, approve_status == 'true')


def cancel(member_id):
    """ cancel membership request """
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author}
    try:
        get_action('member_request_cancel')(context, {"member": member_id})
        return h.redirect_to('organizations_index')
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)
    except NotFound:
        abort(404, _('Request not found'))


def show_organization(organization_id):
    try:
        member = get_user_member(organization_id)
        if not member:
            raise NotFound
        h.redirect_to('ytp_request.show', member_id=member.id)
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)
    except NotFound:
        abort(404, _('Request not found'))


def membership_cancel(organization_id):
    """ cancel membership (not request). """
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author}
    try:
        get_action('member_request_membership_cancel')(context, {"organization_id": organization_id})
        h.redirect_to('organizations_index')
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)
    except NotFound:
        abort(404, _('Request not found'))


ytp_request.add_url_rule(u'/show/<member_id>', view_func=show)
ytp_request.add_url_rule(u'/list', view_func=list)
ytp_request.add_url_rule(u'/new', view_func=new, methods=[u'GET', u'POST'])
ytp_request.add_url_rule(u'/reject/<member_id>', view_func=reject)
ytp_request.add_url_rule(u'/approve/<member_id>', view_func=approve)
ytp_request.add_url_rule(u'/process', view_func=process)
ytp_request.add_url_rule(u'/cancel/<member_id>', view_func=cancel)
ytp_request.add_url_rule(u'/show-organization/<organization_id>', view_func=show_organization)
ytp_request.add_url_rule(u'/membership-cancel/<organization_id>', view_func=membership_cancel)


def _process(member_id, approve_status):
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author}
    data_dict = {"member": member_id, "approve": approve_status}
    try:
        get_action('member_request_process')(context, data_dict)
        h.redirect_to('member_request_list')
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)
    except NotFound:
        abort(404, _('Request not found'))


def _get_available_roles(user=None, context=None):
    roles = []
    hide_member_role = asbool(config.get('ytp.requests.hide_member_role', 'true'))
    for role in get_action('member_roles_list')(context or _basic_context(user), {}):
        if not hide_member_role or role['value'] != 'member':
            roles.append(role)
    return roles


def _basic_context(user=None):
    return {'model': model, 'session': model.Session, 'user': user or g.user}


def _save_new(context):
    try:
        data_dict = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.form))))
        data_dict['group'] = data_dict['organization']
        member = get_action('member_request_create')(context, data_dict)
        redirect_to_src_page = asbool(config.get('ytp.requests.redirect_to_src_page', 'true'))
        if redirect_to_src_page and request.referrer:
            h.flash_success(_('Thank you for your request. The organisation admins were notified.'))
            return h.redirect_to(request.referrer)
        else:
            response = h.redirect_to('organization_members', id=data_dict['organization'])
            return response
    except NotAuthorized:
        abort(403, NOT_AUTH_MESSAGE)
    except NotFound:
        abort(404, _('Item not found'))
    except dict_fns.DataError:
        abort(400, _(u'Integrity Error'))
    except ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        h.flash_error(_('There was an error saving your request. Please try again.'))
        return new(data_dict, errors, error_summary)
