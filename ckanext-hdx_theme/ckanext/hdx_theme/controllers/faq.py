import requests
import ckan.lib.base as base
from ckan.common import _, c, g, request, response
import exceptions as exceptions
import ckan.logic as logic
import json
import pylons.configuration as configuration

import ckanext.hdx_users.controllers.mailer as hdx_mailer
from ckanext.hdx_theme.helpers.faq_data import faq_data

get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})

topics = {}
for f in faq_data:
    topics[f.get('id')] = f.get('title')


class FaqController(base.BaseController):
    def show(self):
        fullname = c.userobj.display_name or ''
        email = c.userobj.email or ''
        template_data = {
            'data': {
                'faq_data': faq_data,
                'topics': topics,
                'fullname': fullname,
                'email': email,
            },
            'errors': '',
            'error_summary': '',
        }

        return base.render('faq/main.html', extra_vars=template_data)

    def contact_us(self):
        '''
        Send a contact request form
        :return:
        '''
        try:
            topic = request.params.get('topic')
            fullname = request.params.get('fullname')
            email = request.params.get('email')
            msg = request.params.get('faq-msg')
            hdx_email = configuration.config.get('hdx.faqrequest.email', 'hdx.feedback@gmail.com')

            captcha_response = request.params.get('g-recaptcha-response')
            if not self.is_valid_captcha(response=captcha_response):
                raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
        except ValidationError, e:
            error_summary = e.error_summary
            if error_summary == CaptchaNotValid:
                return FaqCaptchaErr
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)

        try:
            subject = 'Faq: request from user'
            html = """\
                <html>
                  <head></head>
                  <body>
                    <p>An user sent a request using contact us form.</p>
                    <p>Name: {fullname}</p>
                    <p>Email: {email}</p>
                    <p>Section: {topic}</p>
                    <p>Message: {msg}</p>
                  </body>
                </html>
                """.format(fullname=fullname, email=email, topic=topic, msg=msg)
            hdx_mailer.mail_recipient('Humanitarian Data Exchange', hdx_email, subject, html)

        except exceptions.Exception, e:
            error_summary = str(e)
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
