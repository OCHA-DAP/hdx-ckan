'''
Created on Jun 10, 2014

@author: Dan, alexandru-m-g
'''

import logging as logging

import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.lib.base as base
import ckan.plugins.toolkit as tk
from ckan.common import c, request, _
import ckan.model as model

import ckanext.hdx_org_group.helpers.static_lists as static_lists
import ckanext.hdx_theme.helpers.helpers as hdx_h
import ckanext.hdx_theme.util.mail as hdx_mail

log = logging.getLogger(__name__)


class HDXReqsOrgController(base.BaseController):

    def request_editor_for_org(self, org_id):
        '''
            user_email, name of user, username, organization name,  list with org-admins emails,
        '''
        try:
            msg = _('Please allow me to submit data to this organization ')
            user = hdx_h.hdx_get_user_info(c.user)
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}
            org_admins = tk.get_action('member_list')(context,{'id':org_id,'capacity':'admin','object_type':'user'})
            admins=[]
            for admin_tuple in org_admins:
                admin_id = admin_tuple[0]
                admins.append(hdx_h.hdx_get_user_info(admin_id))
            admins_with_email = [admin for admin in admins if admin['email']]

            data_dict = {'display_name': user['display_name'], 'name': user['name'],
                         'email': user['email'], 'organization': org_id,
                         'message': msg, 'admins': admins_with_email}
            tk.get_action('hdx_send_editor_request_for_org')(context, data_dict)
            h.flash_success(_('Message sent'))
        except hdx_mail.NoRecipientException, e:
            h.flash_error(_(str(e)))
        except:
            h.flash_error(_('Request can not be sent. Contact an administrator'))
        if 'from' in request.params:
            h.redirect_to(request.params.get('from'))
        h.redirect_to(controller='organization', action='read', id=org_id)


