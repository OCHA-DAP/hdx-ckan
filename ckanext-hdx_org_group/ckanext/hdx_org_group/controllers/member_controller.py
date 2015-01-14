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

abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params


class HDXOrgMemberController(org.OrganizationController):

    def members(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        q = c.q = request.params.get('q', '')
        sort = request.params.get('sort', '')
        reverse = True if sort == u'title desc' else False

        c.sort_by_selected = sort

        try:
            member_list = self._action('member_list')(
                context, {'id': id, 'object_type': 'user',
                          'q': q, 'user_info': True}
            )
            member_list.sort(key=lambda y: y[4].lower(), reverse=reverse)
            c.members = [a[0:4] for a in member_list]
            c.group_dict = self._action('group_show')(context, {'id': id})
        except NotAuthorized:
            base.abort(401, _('Unauthorized to delete group %s') % '')
        except NotFound:
            base.abort(404, _('Group not found'))
        return self._render_template('group/members.html')

    def member_new(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        #self._check_access('group_delete', context, {'id': id})
        try:
            if request.method == 'POST':

                data_dict = clean_dict(dict_fns.unflatten(
                    tuplize_dict(parse_params(request.params))))
                data_dict['id'] = id
                if data_dict.get('email', '').strip() != '' or \
                        data_dict.get('username', '').strip() != '':
                    email = data_dict.get('email')
                    #Check if email is used
                    if email:
                        #Check if email is used
                        user_dict = model.User.by_email(email)
                        if user_dict:
                            #Add user
                            print user_dict
                            data_dict['username'] = user_dict[0].name
                        else:
                            user_data_dict = {
                                'email': email,
                                'group_id': id,
                                'role': data_dict['role'],
                                'id': id  # This is something staging/prod need
                            }
                            del data_dict['email']
                            user_dict = self._action('user_invite')(context,
                                                                user_data_dict)
                            data_dict['username'] = user_dict['name']
                        c.group_dict = self._action(
                        'group_member_create')(context, data_dict)
                else:
                    h.flash_error(_('''You need to either fill the username or
                        the email of the person you wish to invite'''))
                self._redirect_to(controller='group', action='members', id=id)

            # I think the 'else' is not used. We should consider removing it.
            else:
                user = request.params.get('user')
                if user:
                    c.user_dict = get_action('user_show')(
                        context, {'id': user})
                    c.user_role = new_authz.users_role_for_group_or_org(
                        id, user) or 'member'
                else:
                    c.user_role = 'member'
                c.group_dict = self._action('group_show')(context, {'id': id})
                group_type = 'organization' if c.group_dict[
                    'is_organization'] else 'group'
                c.roles = self._action('member_roles_list')(
                    context, {'group_type': group_type}
                )
            if not request.params['username']:
                abort(404, _('User not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to add member to group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        except ValidationError, e:
            h.flash_error(e.error_summary)
        self._redirect_to(controller='group', action='members', id=id)

    def member_delete(self, id):
        ''' This is a modified version of the member_delete from the 
            ckan group controller. 
            The changes are: ( if you modify this function please add below)
            - flash msg changed to reflect it's an org member ( not group member )
            - the delete confirmation is done with js ( DHTML )
        '''
        if 'cancel' in request.params:
            self._redirect_to(controller='group', action='members', id=id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

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
