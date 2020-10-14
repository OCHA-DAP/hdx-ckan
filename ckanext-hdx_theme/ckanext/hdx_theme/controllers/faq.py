import exceptions as exceptions
import json
import logging
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckan.lib.mailer as mailer
import pylons.configuration as configuration
import requests
import pylons.config as config
from ckanext.hdx_theme.helpers.faq_data import faq_data
from ckanext.hdx_theme.util.mail import simple_validate_email

import ckan.lib.base as base
import ckan.logic as logic
from ckan.common import _, c, request, response
from ckan.controllers.api import CONTENT_TYPES

log = logging.getLogger(__name__)
get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})

for section in faq_data:
    s_id = ''.join(i if i.isalnum() else '_' for i in section['title'])
    s_id = 'faq-{}'.format(s_id)
    section['id'] = s_id
    for question in section['questions']:
        try:
            q_id = ''.join(i if i.isalnum() else '_' for i in question['q'])
            question['id'] = q_id
        except Exception, ex:
            log.error(ex)

topics = {}
for f in faq_data:
    topics[f.get('id')] = f.get('title')


class FaqController(base.BaseController):
    def show(self):
        fullname = c.userobj.display_name if c.userobj and c.userobj.display_name is not None else ''
        email = c.userobj.email if c.userobj and c.userobj.email is not None else ''
        template_data = {
            'data': {
                'faq_data': faq_data,
                'topics': topics,
                'fullname': fullname,
                'email': email,
            },
            'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey'),
            'errors': '',
            'error_summary': '',
        }

        return base.render('faq/main.html', extra_vars=template_data)

    def about(self):
        import ckan.lib.helpers as h
        return h.redirect_to(controller='ckanext.hdx_theme.controllers.faq:FaqController', action='show')

    def contact_us(self):
        '''
        Send a contact request form
        :return:
        '''
        if request.params.get('topic') is None:
            return self._contact_us_data_responsability()
        response.headers['Content-Type'] = CONTENT_TYPES['json']
        try:
            topic = request.params.get('topic')
            fullname = request.params.get('fullname')
            email = request.params.get('email')
            msg = request.params.get('faq-msg')
            hdx_email = configuration.config.get('hdx.faqrequest.email', 'hdx@un.org')

            test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
            if not test:
                captcha_response = request.params.get('g-recaptcha-response')
                if not self.is_valid_captcha(response=captcha_response):
                    raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)

            simple_validate_email(email)

        except ValidationError, e:
            error_summary = e.error_summary
            if error_summary == CaptchaNotValid:
                return FaqCaptchaErr
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = e.error or str(e)
            return self.error_message(error_summary)

        try:
            subject = u'HDX contact form submission'
            email_data = {
                'user_display_name': fullname,
                'user_email': email,
                'topic': topic,
                'msg': msg,
            }
            hdx_mailer.mail_recipient([{'display_name': 'Humanitarian Data Exchange (HDX)', 'email': hdx_email}],
                                      subject, email_data, sender_name=fullname, sender_email=email,
                                      snippet='email/content/faq_request.html')

            subject = u'Confirmation of your contact form submission'
            email_data = {
                'user_fullname': fullname,
                'topic': topic,
                'msg': msg,
            }
            hdx_mailer.mail_recipient([{'display_name': fullname, 'email': email}],
                                      subject, email_data, snippet='email/content/faq_request_user_confirmation.html')

        except exceptions.Exception, e:
            error_summary = e.error or str(e)
            return self.error_message(error_summary)
        return FaqSuccess

    def error_message(self, error_summary):
        return json.dumps({'success': False, 'error': {'message': error_summary}})

    def is_valid_captcha(self, response):
        url = configuration.config.get('hdx.captcha.url')
        secret = configuration.config.get('ckan.recaptcha.privatekey')
        params = {'secret': secret, "response": response}
        r = requests.get(url, params=params, verify=True)
        res = json.loads(r.content)
        return 'success' in res and res['success']

    def _contact_us_data_responsability(self):
        '''
        Send a contact request form
        :return:
        '''
        response.headers['Content-Type'] = CONTENT_TYPES['json']
        try:
            fullname = request.params.get('fullname')
            email = request.params.get('email')
            msg = request.params.get('faq-msg')
            hdx_email = configuration.config.get('hdx.faqrequest.email', 'hdx@un.org')

            test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
            if not test:
                captcha_response = request.params.get('g-recaptcha-response')
                if not self.is_valid_captcha(response=captcha_response):
                    raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)

            simple_validate_email(email)

        except ValidationError, e:
            error_summary = e.error_summary
            if error_summary == CaptchaNotValid:
                return FaqCaptchaErr
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = e.error or str(e)
            return self.error_message(error_summary)

        try:
            subject = u'HDX contact form submission (COVID-19 data responsibility)'
            email_data = {
                'user_display_name': fullname,
                'user_email': email,
                'msg': msg,
            }
            hdx_mailer.mail_recipient([{'display_name': 'Humanitarian Data Exchange (HDX)', 'email': hdx_email}],
                                      subject, email_data, sender_name=fullname, sender_email=email,
                                      snippet='email/content/data_responsability_faq_request.html')

            subject = u'Confirmation of your contact form submission (COVID-19 data responsibility)'
            email_data = {
                'user_fullname': fullname,
                'msg': msg,
            }
            hdx_mailer.mail_recipient([{'display_name': fullname, 'email': email}],
                                      subject, email_data, snippet='email/content/data_responsability_faq_request_user_confirmation.html')

        except exceptions.Exception, e:
            error_summary = e.error or str(e)
            return self.error_message(error_summary)
        return FaqSuccess
