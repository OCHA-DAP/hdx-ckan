'''
Created on Jun 14, 2014

@author: alexandru-m-g

'''

import ckan.controllers.organization as org
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base

from ckan.common import c, request, _
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckanext.hdx_org_group.helpers.organization_helper as org_helper
import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
import ckanext.hdx_theme.helpers.helpers as hdx_h

abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params


class HDXOrgMemberController(org.OrganizationController):
    def members(self, id):
        '''
        Modified core method from 'group' controller.
        Added search & sort functionality.

        :param id: id of the organization for which the member list is requested
        :type id: string
        :return: the rendered template
        :rtype: unicode
        '''
        context = self._get_context()

        q, sort = self._find_filter_params()
        reverse = True if sort == u'title desc' else False

        org_meta = org_meta_dao.OrgMetaDao(id)
        org_meta.fetch_all()

        try:
            member_list = self._action('member_list')(
                context, {'id': id, 'object_type': 'user',
                          'q': q, 'user_info': True}
            )
            member_list.sort(key=lambda y: y[4].lower(), reverse=reverse)
            data_dict = {'id': id}
            data_dict['include_datasets'] = False
            c_params = {
                'sort': sort,
                'members': [a[0:4] for a in member_list],
                'org_meta': org_meta
            }
            self._set_c_params(c_params)
        except NotAuthorized:
            base.abort(401, _('Unauthorized to delete group %s') % '')
        except NotFound:
            base.abort(404, _('Group not found'))
        if org_meta.is_custom:
            return self._render_template('group/custom_members.html')
        else:
            return self._render_template('group/members.html')

    def _get_context(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        return context

    def _set_c_params(self, params):
        c.sort_by_selected = params.get('sort')
        c.members = params.get('members')
        c.org_meta = params.get('org_meta')
        c.group_dict = c.org_meta.org_dict

    def _find_filter_params(self):
        q = c.q = request.params.get('q', '')
        sort = request.params.get('sort', '')
        return q, sort

    def member_new(self, id):
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
        context = self._get_context()

        # self._check_access('group_delete', context, {'id': id})
        try:
            if request.method == 'POST':

                data_dict = clean_dict(dict_fns.unflatten(
                    tuplize_dict(parse_params(request.params))))
                data_dict['id'] = id
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
                                self._redirect_to(controller='group', action='members', id=id)
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
                            user_dict = self._action('user_invite')(context, user_data_dict)
                            data_dict['username'] = user_dict['name']
                            h.flash_success(email + ' has been invited as ' + data_dict['role'])
                    else:
                        flash_message = data_dict['username'] + ' has been added as ' + data_dict['role']
                    c.group_dict = self._action('group_member_create')(context, data_dict)

                    self.notify_admin_users(context, data_dict)

                    h.flash_success(flash_message)
                else:
                    h.flash_error(_('''You need to either fill the username or
                        the email of the person you wish to invite'''))
                self._redirect_to(controller='group', action='members', id=id)

            if not request.params['username']:
                abort(404, _('User not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to add member to group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        except ValidationError, e:
            h.flash_error(e.error_summary)
        self._redirect_to(controller='group', action='members', id=id)

    def notify_admin_users(self, context, data_dict):
        org_obj = model.Group.get(data_dict.get('id'))
        user_obj = model.User.get(data_dict['username'])
        org_admins = self._action('member_list')(context, {'id': data_dict.get('id'), 'capacity': 'admin',
                                                           'object_type': 'user'})
        admins = []
        for admin_tuple in org_admins:
            admin_id = admin_tuple[0]
            admins.append(hdx_h.hdx_get_user_info(admin_id))
        admins_with_email = [admin for admin in admins if admin['email']]
        data_dict['message'] = '{user} has been added to {org_name} as {role}'.format(user=user_obj.display_name,
                                                                                      org_name=org_obj.display_name,
                                                                                      role=data_dict.get('role'))
        data_dict['subject'] = 'HDX Notification: new user was added to {org_name}'.format(
            org_name=org_obj.display_name)
        data_dict['admins'] = admins_with_email
        org_helper.notify_admins(data_dict)

    def member_delete(self, id):
        ''' This is a modified version of the member_delete from the
            ckan group controller.
            The changes are: ( if you modify this function please add below)
            - flash msg changed to reflect it's an org member ( not group member )
            - the delete confirmation is done with js ( DHTML )
        '''
        if 'cancel' in request.params:
            self._redirect_to(controller='group', action='members', id=id)

        context = self._get_context()

        try:
            self._check_access('group_member_delete', context, {'id': id})
        except NotAuthorized:
            abort(401, _('Unauthorized to delete group %s members') % '')

        try:
            user_id = request.params.get('user')
            if request.method == 'POST':
                self._action('group_member_delete')(
                    context, {'id': id, 'user_id': user_id})
                # modified by HDX
                h.flash_notice(_('Organization member has been deleted.'))
                self._redirect_to(controller='group', action='members', id=id)
            c.user_dict = self._action('user_show')(context, {'id': user_id})
            c.user_id = user_id
            c.group_id = id
        except NotAuthorized:
            abort(401, _('Unauthorized to delete group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        # modified by HDX
        self._redirect_to(controller='group', action='members', id=id)
