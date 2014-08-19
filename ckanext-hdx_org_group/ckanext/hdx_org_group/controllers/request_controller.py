'''
Created on Jun 10, 2014

@author: Dan, alexandru-m-g
'''
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.lib.base as base
import ckan.plugins.toolkit as tk
from ckan.common import c, request, _
import ckan.lib.base as base
import ckanext.hdx_theme.helpers as hdx_h
import ckan.model as model
import logging as logging
import exceptions as exceptions

import ckanext.hdx_theme.util.mail as hdx_mail

log = logging.getLogger(__name__)


class HDXReqsOrgController(base.BaseController):

    def request_membership(self, org_id):
        '''
            user_email, name of user, username, organization name,  list with org-admins emails,
        '''
        try:
            msg = request.params.get('message', '')
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
            tk.get_action('hdx_send_request_membership')(context, data_dict)

            h.flash_success(_('Message sent'))
        except hdx_mail.NoRecipientException, e:
            h.flash_error(_(str(e)))
        except exceptions.Exception, e:
            log.error(str(e))
            h.flash_error(_('Request can not be sent. Contact an administrator.'))
        h.redirect_to(controller='organization', action='read', id=org_id)

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

    def request_new_organization(self):
        context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}
        try:
            tk.check_access('hdx_send_new_org_request',context)
        except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to send a new org request'))
            
        errors = {}
        error_summary = {}
        data = {'from': request.params.get('from','')}
        from_url = ''
        if 'save' in request.params:
            try:
                data = self._process_new_org_request()
                self._validate_new_org_request_field(data)
                
                tk.get_action('hdx_send_new_org_request')(context, data)
                
                #from_url = data.get('from','')
                data.clear()
                h.flash_success(_('Request sent successfully'))
            except hdx_mail.NoRecipientException, e:
                h.flash_error(_(str(e)))
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
            except exceptions.Exception, e:
                log.error(str(e))
                h.flash_error(_('Request can not be sent. Contact an administrator'))
            
            #Removing this because the form doesn't submit a from parameter
            h.redirect_to('user_dashboard_organizations')
            #if from_url and len(from_url) > 0:
            #    h.redirect_to(from_url)
            #else:
            #    h.redirect_to('/error')

        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        c.form = base.render('organization/request_organization_form.html', extra_vars=vars)
        return base.render('organization/request_new.html')

    def _process_new_org_request(self):
        data = {'name': request.params.get('name', ''), \
                'title': request.params.get('title', ''), \
                'org_url': request.params.get('org_url', ''), \
                'description': request.params.get('description', ''), \
                'your_email': request.params.get('your_email', ''), \
                'your_name': request.params.get('your_name', ''), \
                #'from': request.params.get('from', '')
                }
        print data
        return data

    def _validate_new_org_request_field(self, data):
        errors = {}
        for field in ['title', 'description', 'your_email', 'your_name']:
            if data[field].strip() == '':
                errors[field] = [_('should not be empty')]

        if len(errors) > 0:
            raise logic.ValidationError(errors)

        