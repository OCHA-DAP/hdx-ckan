'''
Created on Jun 10, 2014

@author: Dan
'''
import ckan.lib.helpers as h
import ckan.controllers.organization as organization
import ckan.plugins.toolkit as tk
from ckan.common import c, request, _
import ckan.lib.base as base
import ckanext.hdx_theme.helpers as hdx_h
import ckan.lib.mailer as mailer
import ckan.model as model

class HDXOrgController(base.BaseController):

    def _send_mail(self, user, sys_admin, org, message = ''):
        body = _('New request membership\n' \
        'Full Name: {fn}\n' \
        'Username: {username}\n' \
        'Email: {mail}\n' \
        'Organization: {org}\n' \
        'Message from user: {msg}\n' \
        '(This is an automated mail)' \
        '').format(fn=user['display_name'], username=user['name'], mail=user['email'], org=org, msg=message)
        
        mailer.mail_recipient(sys_admin['display_name'], sys_admin['email'], _('New Request Membership'), body)
        return

    def request_membership(self, id):
        '''
            user_email, name of user, username, organization name,  list with sys-admins emails,
        '''
        try:
            msg = request.params.get('message', '')
            user = hdx_h.hdx_get_user_info(c.user)
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}
            org_admins = tk.get_action('member_list')(context,{'id':id,'capacity':'admin','object_type':'user'})
            admins=[]
            for admin_tuple in org_admins:
                admin_id = admin_tuple[0]
                admins.append(hdx_h.hdx_get_user_info(admin_id))
            admins_with_email = (admin for admin in admins if admin['email'])
            for admin in admins_with_email :
                self._send_mail(user, admin, id, msg)
            h.flash_success(_('Message sent'))
        except:
            h.flash_error(_('Request can not be sent. Contact an administrator'))
        h.redirect_to(controller='organization', action='read', id=id)
    

    
    