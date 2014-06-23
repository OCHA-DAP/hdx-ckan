'''
Created on Jun 14, 2014

@author: alexandru-m-g

'''

import ckan.controllers.organization as org
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base

from ckan.common import c, request, _

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized


class HDXOrgMemberController(org.OrganizationController):

    def members(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        q = c.q = request.params.get('q', '')
        sort = request.params.get('sort', '')
        reverse = True if sort == u'name desc' else False

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
    