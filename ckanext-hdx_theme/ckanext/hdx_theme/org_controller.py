'''
Created on Jun 10, 2014

@author: Dan, alexandru-m-g
'''
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckan.common import c, request, _
import ckan.lib.base as base
import ckanext.hdx_theme.helpers as hdx_h
import ckan.lib.mailer as mailer
import ckan.model as model
import logging as logging
import exceptions as exceptions

log = logging.getLogger(__name__)

def send_mail(recipients, subject, body):
    if recipients and len(recipients) > 0:
        log.info('\nSending email to {recipients} with subject "{subject}" with body: {body}'
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject, body=body))
        for recipient in recipients:
            mailer.mail_recipient(recipient['display_name'], recipient['email'],
                                  subject, body)
    else:
        h.flash_error(_('The are no recipients for this request. Contact an administrator '))
        raise exceptions.Exception('No recipients')
    


class HDXReqsOrgController(base.BaseController):

    def _send_mail(self, user, admins, org, message=''):
        body = _('New request membership\n' \
        'Full Name: {fn}\n' \
        'Username: {username}\n' \
        'Email: {mail}\n' \
        'Organization: {org}\n' \
        'Message from user: {msg}\n' \
        '(This is an automated mail)' \
        '').format(fn=user['display_name'], username=user['name'],
                   mail=user['email'], org=org, msg=message)

        send_mail(admins, _('New Request Membership'), body)
        return

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

            self._send_mail(user, admins_with_email, org_id, msg)
            h.flash_success(_('Message sent'))
        except exceptions.Exception, e:
            log.error(str(e))
            h.flash_error(_('Request can not be sent. Contact an administrator.'))
        h.redirect_to(controller='organization', action='read', id=org_id)
    
    def _send_mail_req_editor(self, user, admins, org, message = ''):
        body = _('New request editor/admin role\n' \
        'Full Name: {fn}\n' \
        'Username: {username}\n' \
        'Email: {mail}\n' \
        'Organization: {org}\n' \
        'Message from user: {msg}\n' \
        '(This is an automated mail)' \
        '').format(fn=user['display_name'], username=user['name'], mail=user['email'], org=org, msg=message)
        
        send_mail(admins, _('New Request Membership'), body)

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
            
            self._send_mail_req_editor(user, admins_with_email, org_id, msg)
            h.flash_success(_('Message sent'))
        except:
            h.flash_error(_('Request can not be sent. Contact an administrator'))
        if 'from' in request.params:
            h.redirect_to(request.params.get('from'))
        h.redirect_to(controller='organization', action='read', id=org_id)

    def request_new_organization(self):
        errors = {}
        error_summary = {}
        data = {'from': request.params.get('from','')}
        from_url = ''

        if 'save' in request.params:
            try:
                data = self._process_new_org_request()
                self._validate_new_org_request_field(data)
                self._send_new_org_request(data)
                from_url = data.get('from','')
                data.clear()
                h.flash_success(_('Request sent successfully'))
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
            except exceptions.Exception, e:
                log.error(str(e))
                h.flash_error(_('Request can not be sent. Contact an administrator'))
            if from_url and len(from_url) > 0:
                h.redirect_to(from_url)
            else:
                h.redirect_to('/error')

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
                'from': request.params.get('from', '')
                }

        return data

    def _validate_new_org_request_field(self, data):
        errors = {}
        for field in ['title', 'description', 'your_email', 'your_name']:
            if data[field].strip() == '':
                errors[field] = [_('should not be empty')]

        if len(errors) > 0:
            raise logic.ValidationError(errors)

    def _send_new_org_request(self, data):

        sys_admins = tk.get_action('hdx_get_sys_admins')()
        sys_admins =[sys_admin for sys_admin in sys_admins if sys_admin['email']]

        subject = _('New organization request:') + ' ' \
            + data['title']
        body = _('New organization request \n' \
            'Organization Name: {org_name}\n' \
            'Organization Description: {org_description}\n' \
            'Organization URL: {org_url}\n' \
            'Person requesting: {person_name}\n' \
            'Person\'s email: {person_email}\n' \
            '(This is an automated mail)' \
        '').format(org_name=data['title'], org_description = data['description'],
                   org_url = data['org_url'], person_name = data['your_name'], person_email = data['your_email'])

        send_mail(sys_admins, subject, body)
        