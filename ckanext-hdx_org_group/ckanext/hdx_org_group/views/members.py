import collections
import logging

from flask import Blueprint
from six.moves import range

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic

import ckanext.hdx_theme.util.mail as mailutil

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
Invalid = tk.Invalid
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError

tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

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

    try:
        context = _get_context()
        if not g.user:
            raise NotAuthorized('Only logged in users can see the list of members')

        q, sort = _find_filter_params()
        reverse = True if sort == u'title desc' else False

        org_meta = org_meta_dao.OrgMetaDao(id, g.user, g.userobj)
        org_meta.fetch_all()

        member_list = get_action('member_list')(
            context, {'id': id, 'object_type': 'user',
                      'q': q, 'user_info': True, 'sysadmin_info': True}
        )
        member_list.sort(key=lambda y: y[4].lower(), reverse=reverse)

        non_sysadmin_admins = 0
        member_groups = {}
        for m in member_list:
            role = m[3]
            if not member_groups.get(role):
                member_groups[role] = []
            member_groups[role].append(m)
            if role == 'admin' and m[5] == False:
                non_sysadmin_admins+=1

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
            'non_sysadmin_admins': non_sysadmin_admins,
        }
    except NotAuthorized:
        return abort(403, _('Unauthorized to view member list %s') % '')
    except NotFound:
        return abort(404, _('Group not found'))
    except Exception as ex:
        log.error(str(ex))
        return abort(404, _('Server error'))
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
        user_id = request.form.get('user')
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


def member_new(id):
    '''
    Modified core method from 'group' controller.

    Added the 'user_invite' functionality. Expects POST request.
    If there's an 'email' parameter in the request and the email
    is not associated with any user account, a new user account with that
    email will be created and added as a member with the specific 'role'
    to the organization.
    Otherwise a 'username' is expected as a request parameter

    :param id: id of the organization to which a member should be added.
    :type id: string
    :return: the rendered template
    :rtype: unicode
    '''
    context = _get_context()

    try:
        if request.method == 'POST':

            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.form))))
            data_dict['id'] = id
            invited = False
            if data_dict.get('email', '').strip() != '' or \
                            data_dict.get('username', '').strip() != '':
                email = data_dict.get('email')
                flash_message = None
                if email:
                    # Check if email is used
                    user_dict = model.User.by_email(email.strip())
                    if user_dict:
                        # Is user deleted?
                        if user_dict[0].state == 'deleted':
                            h.flash_error(_('This user no longer has an account on HDX'))
                            return redirect('hdx_members.members', id=id)
                        # Add user
                        data_dict['username'] = user_dict[0].name
                        flash_message = 'That email is already associated with user ' + data_dict[
                            'username'] + ', who has been added as ' + data_dict['role']
                    else:
                        user_data_dict = {
                            'email': email,
                            'group_id': id,
                            'role': data_dict['role'],
                            'id': id  # This is something staging/prod need
                        }
                        del data_dict['email']
                        user_dict = get_action('hdx_user_invite')(context, user_data_dict)
                        invited = True
                        data_dict['username'] = user_dict['name']
                        h.flash_success(email + ' has been invited as ' + data_dict['role'])
                else:
                    flash_message = data_dict['username'] + ' has been added as ' + data_dict['role']
                get_action('group_member_create')(context, data_dict)

                user_obj = model.User.get(data_dict['username'])
                # display_name = user_obj.display_name or user_obj.name

                org_obj = model.Group.get(id)
                # self.notify_admin_users(org_obj, None if invited else [display_name],
                #                         [email] if invited else None, data_dict['role'])
                _send_membership_confirmation(org_obj.display_name, org_obj.id, data_dict['role'], user_obj)

                h.flash_success(flash_message)
                org_obj = model.Group.get(id)
                analytics.ChangeMemberAnalyticsSender(org_obj.id, org_obj.name).send_to_queue()
            else:
                h.flash_error(_('''You need to either fill the username or
                    the email of the person you wish to invite'''))
            return redirect('hdx_members.members', id=id)

        if not request.params['username']:
            return abort(404, _('User not found'))
    except NotAuthorized:
        return abort(403, _('Unauthorized to add member to group %s') % '')
    except NotFound:
        return abort(404, _('Group not found'))
    except ValidationError as e:
        h.flash_error(e.error_summary)
    return redirect('hdx_members.members', id=id)


def bulk_member_new(id):

    try:
        req_dict = clean_dict(dict_fns.unflatten(
            tuplize_dict(parse_params(request.params or request.form))))
        role = req_dict.get('role')
        emails = req_dict.get('emails', '').strip()
        new_members = []
        invited_members = []
        org_obj = model.Group.get(id)
        if emails and role:
            for email in emails.split(','):
                context = _get_context()
                email = email.strip()
                try:
                    if email:
                        # Check if email is used
                        _user_obj = _get_user_obj(email)
                        if _user_obj:
                            added = _add_existing_user_as_member(context, id, role, _user_obj, org_obj.display_name)
                            if added:
                                new_members.append(_user_obj)
                        else:
                            user_data_dict = {
                                'email': email,
                                'group_id': id,
                                'role': role,
                                'id': id  # This is something staging/prod need
                            }
                            user_dict = get_action('hdx_user_invite')(context, user_data_dict)
                            invited_members.append(email)
                            # h.flash_success(email + ' has been invited as ' + role)
                            log.info('{} was invited as a new user'.format(email))
                except Invalid as e:
                    h.flash_error(_('Invalid email address or unknown username provided: ') + email)

            # if new_members:
            #     new_members_msg = _(' were added to the organization.') if len(new_members) != 1 else _(
            #         ' was added to the organization.')
            #     h.flash_success(', '.join([m.display_name for m in new_members]) + new_members_msg)
            #
            # if invited_members:
            #     invited_members_msg = _(
            #         ' were invited to join the organization. An account was created for them.') if len(
            #         invited_members) != 1 else _(
            #         ' was invited to join the organization. An account was created for her/him.')
            #     h.flash_success(', '.join(invited_members) + invited_members_msg)


            # self.notify_admin_users(org_obj, new_members, invited_members, role)
            _send_analytics_info(org_obj, new_members, invited_members)
        else:
            h.flash_error(_('''No user or role was specified'''))
        return redirect('hdx_members.members', id=id)

    except NotAuthorized:
        return abort(403, _('Unauthorized to add member to group %s') % '')
    except NotFound:
        return  abort(404, _('Group not found'))
    except ValidationError as e:
        h.flash_error(e.error_summary)
    return redirect('hdx_members.members', id=id)


def _add_existing_user_as_member(context, org_id, role, user_info, org_display_name):
    email = user_info.email
    # Is user deleted?
    if user_info.state == 'deleted':
        h.flash_error(_('Following user no longer has an account on HDX: ') + email)
        return False
    log.info('{} already exists as a user'.format(email))
    user_data_dict = {
        'id': org_id,
        'username': user_info.name,
        'role': role
    }
    get_action('group_member_create')(context, user_data_dict)

    _send_membership_confirmation(org_display_name, org_id, role, user_info)
    return True


def _get_user_obj(mail_or_username):
    userobj = None
    try:
        if mailutil.hdx_validate_email(mail_or_username):
            users = model.User.by_email(mail_or_username)
            if users:
                userobj = users[0]
    except Invalid as e:
        userobj = model.User.get(mail_or_username)
        if not userobj:
            raise
    return userobj


def _send_analytics_info(org_obj, new_members, invited_members):
    for i in range(0, len(new_members) + len(invited_members)):
        analytics.AddMemberAnalyticsSender(org_obj.id, org_obj.name).send_to_queue()


def _send_membership_confirmation(org_display_name, org_id, role, user_info):
    subject = u'Confirmation of HDX organisation membership'
    email_data = {
        'user_fullname': user_info.display_name or user_info.fullname,
        'org_name': org_display_name,
        'capacity': role,
    }
    hdx_mailer.mail_recipient(
        [{'display_name': user_info.display_name or user_info.fullname, 'email': user_info.email}], subject,
        email_data, footer=user_info.email,
        snippet='email/content/membership_confirmation_to_user.html')
    context = _get_context()
    org_admins = get_action('member_list')(context, {'id': org_id, 'capacity': 'admin',
                                                       'object_type': 'user'})
    admins = []
    for admin_tuple in org_admins:
        admin_id = admin_tuple[0]
        admins.append(h.hdx_get_user_info(admin_id))
    admins_with_email = [{'display_name': admin.get('display_name'), 'email': admin.get('email')} for admin in
                         admins if admin['email']]
    subject = u'New ' + role + ' added to HDX organisation ' + org_display_name
    email_data = {
        'user_fullname': user_info.display_name or user_info.fullname,
        'user_username': user_info.name,
        'org_name': org_display_name,
        'capacity': role,
    }
    hdx_mailer.mail_recipient(admins_with_email, subject,
                              email_data,
                              snippet='email/content/membership_confirmation_to_admins.html')


hdx_members.add_url_rule(u'/members/<id>', view_func=members)
hdx_members.add_url_rule(u'/member_delete/<id>', view_func=member_delete, methods=[u'POST'])
hdx_members.add_url_rule(u'/member_new/<id>', view_func=member_new, methods=[u'POST'])
hdx_members.add_url_rule(u'/bulk_member_new/<id>', view_func=bulk_member_new, methods=[u'POST'])
