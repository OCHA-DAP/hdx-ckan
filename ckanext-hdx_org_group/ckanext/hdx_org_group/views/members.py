import collections
import logging

from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_users.helpers.mailer as hdx_mailer

import ckanext.hdx_org_group.helpers.analytics as analytics
import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
import ckanext.hdx_org_group.helpers.organization_helper as org_helper

log = logging.getLogger(__name__)

_ = tk._
g = tk.g
h = tk.h
abort = tk.abort
redirect = tk.redirect_to
get_action = tk.get_action
check_access = tk.check_access
render = tk.render
request = tk.request
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized

hdx_members = Blueprint(u'hdx_members', __name__, url_prefix=u'/organization')


def members(id):
    '''
    Modified core method from 'group' controller.
    Added search & sort functionality.

    :param id: id of the organization for which the member list is requested
    :type id: string
    :return: the rendered template
    :rtype: unicode
    '''
    context = _get_context()

    q, sort = _find_filter_params()
    reverse = True if sort == u'title desc' else False

    org_meta = org_meta_dao.OrgMetaDao(id, g.user, g.userobj)
    org_meta.fetch_all()

    try:
        member_list = get_action('member_list')(
            context, {'id': id, 'object_type': 'user',
                      'q': q, 'user_info': True}
        )
        member_list.sort(key=lambda y: y[4].lower(), reverse=reverse)

        member_groups = {}
        for m in member_list:
            role = m[3]
            if not member_groups.get(role):
                member_groups[role] = []
            member_groups[role].append(m)

        member_groups = collections.OrderedDict(sorted(member_groups.items()))

        data_dict = {'id': id}
        data_dict['include_datasets'] = False
        current_user = _current_user_info(member_list)
        is_sysadmin = g.userobj and g.userobj.sysadmin
        template_dict = {
            'q': q,
            'sort_by_selected': sort,
            'members': [a[0:4] for a in member_list],
            'member_groups': member_groups,
            'allow_view_right_side': is_sysadmin or bool(current_user.get('role')),
            'allow_approve': is_sysadmin or current_user.get('role') == 'admin',
            'current_user': current_user,
            'org_meta': org_meta,
            'group_dict': org_meta.org_dict,
            'request_list': _get_member_requests_for_org(id),
        }
    except NotAuthorized:
        return abort(403, _('Unauthorized to view member list %s') % '')
    except NotFound:
        return abort(404, _('Group not found'))
    except Exception as ex:
        log.error(str(ex))
        return  abort(404, _('Server error'))
    if org_meta.is_custom:
        return render('organization/custom_members.html', template_dict)
    else:
        return render('organization/members.html', template_dict)


def _get_context():
    context = {'model': model, 'session': model.Session,
               'user': g.user}
    return context


def _find_filter_params():
    q = request.args.get('q', '')
    sort = request.args.get('sort', '')
    return q, sort


def _current_user_info(member_list):
    if g.userobj:
        member_info = h.hdx_get_user_info(g.userobj.id)
        member_info['role'] = None
        for m in member_list:
            if m[0] == member_info['id']:
                member_info['role'] = m[3]

        return member_info
    return {}


def _get_member_requests_for_org(org_id):
    context = _get_context()
    req_list = get_action('member_request_list')(context, {'group': org_id})
    for req in req_list:
        req['revision_last_updated'] = ''
        user_dict = get_action('user_show')(context, {'id': req.get('user_name')})
        req['user_display_name'] = user_dict.get('display_name', user_dict.get('name'))

    return req_list


def member_delete(id):
    ''' This is a modified version of the member_delete from the
        ckan group controller.
        The changes are: ( if you modify this function please add below)
        - flash msg changed to reflect it's an org member ( not group member )
        - the delete confirmation is done with js ( DHTML )
    '''
    if 'cancel' in request.params:
        return redirect('hdx_members.members', id=id)

    context = _get_context()
    try:
        check_access('group_member_delete', context, {'id': id})
    except NotAuthorized:
        abort(403, _('Unauthorized to delete group %s members') % '')

    try:
        user_id = request.params.get('user')
        if request.method == 'POST':
            get_action('group_member_delete')(
                context, {'id': id, 'user_id': user_id})
            # modified by HDX
            h.flash_notice(_('Organization member has been deleted.'))

            org_obj = model.Group.get(id)
            analytics.RemoveMemberAnalyticsSender(org_obj.id, org_obj.name).send_to_queue()
            usr_obj = model.User.get(user_id)
            org_admins = get_action('member_list')(context, {'id': org_obj.id, 'capacity': 'admin',
                                                               'object_type': 'user'})
            admins = []
            for admin_tuple in org_admins:
                admin_id = admin_tuple[0]
                admins.append(h.hdx_get_user_info(admin_id))
            admins_with_email = [{'display_name': admin.get('display_name'), 'email': admin.get('email')} for
                                 admin in admins if admin['email']]
            user_display_name = usr_obj.display_name or usr_obj.fullname
            subject = u'HDX Organisation ' + org_obj.display_name + ' membership removal'
            email_data = {
                'user_fullname': user_display_name,
                'user_username': usr_obj.name,
                'org_name': org_obj.display_name,
            }
            hdx_mailer.mail_recipient(admins_with_email, subject,
                                      email_data,
                                      snippet='email/content/membership_removal_to_admins.html')

            hdx_mailer.mail_recipient([{'display_name': user_display_name, 'email': usr_obj.email}], subject,
                                      email_data,
                                      snippet='email/content/membership_removal_to_user.html')

            return redirect('hdx_members.members', id=id)
        # c.user_dict = self._action('user_show')(context, {'id': user_id})
        # c.user_id = user_id
        # c.group_id = id
    except NotAuthorized:
        return abort(403, _('Unauthorized to delete group %s') % '')
    except NotFound:
        return abort(404, _('Group not found'))
    # modified by HDX
    return redirect('hdx_members.members', id=id)


hdx_members.add_url_rule(u'/members/<id>', view_func=members)
hdx_members.add_url_rule(u'/member_delete/<id>', view_func=member_delete)
