import json
import logging
import requests
from flask import Blueprint
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.faq_wordpress as fw
import ckanext.hdx_users.helpers.mailer as hdx_mailer
from ckan.common import _, c, config, request
from ckanext.hdx_theme.util.mail import hdx_validate_email
import ckanext.hdx_users.helpers.helpers as usr_h

render = tk.render
hdx_faqs = Blueprint(u'hdx_faqs', __name__, url_prefix=u'/faqs')
hdx_main_faq = Blueprint(u'hdx_main_faq', __name__, url_prefix=u'/faq')
log = logging.getLogger(__name__)
get_action = tk.get_action
ValidationError = tk.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = {'success': True}
FaqCaptchaErr = {'success': False, 'error': {'message': CaptchaNotValid}}
is_valid_captcha = usr_h.validate_captcha

def read(category):
    fullname = c.userobj.display_name if c.userobj and c.userobj.display_name is not None else ''
    email = c.userobj.email if c.userobj and c.userobj.email is not None else ''
    wp_category_terms = config.get('hdx.wordpress.category.' + category)
    data = fw.faq_for_category(wp_category_terms)
    template_data = {
        'data': {
            'faq_data': data['faq_data'],
            'topics': data['topics'],
            'fullname': fullname,
            'email': email,
        },
        'capcha_api_key': config.get('ckan.recaptcha.publickey'),
        'errors': '',
        'error_summary': '',
    }

    return render('faq_others/'+category+'/main.html', template_data)

def main_faq():
    return read('faq')

def contact_us():
    '''
    Send a contact request form
    :return:
    '''

    try:
        topic = request.form.get('topic')
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        msg = request.form.get('faq-msg')
        hdx_email = config.get('hdx.faqrequest.email', 'hdx@humdata.org')

        test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
        if not test:
            captcha_response = request.form.get('g-recaptcha-response')
            if not is_valid_captcha(response=captcha_response):
                raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)

        hdx_validate_email(email)

    except ValidationError as e:
        error_summary = e.error_summary
        if error_summary == CaptchaNotValid:
            return FaqCaptchaErr
        return error_message(error_summary)
    except Exception as e:
        error_summary = str(e)
        return error_message(error_summary)

    try:
        email_data = {
            'user_display_name': fullname,
            'user_email': email,
            'msg': msg,
        }

        if topic is None:
            subject = u'HDX contact form submission (COVID-19 data responsibility)'
            snippet = 'email/content/data_responsability_faq_request.html'
        else:
            subject = u'HDX contact form submission'
            email_data['topic'] = topic
            snippet = 'email/content/faq_request.html'

        hdx_mailer.mail_recipient([{'display_name': 'Humanitarian Data Exchange (HDX)', 'email': hdx_email}],
                                  subject, email_data, sender_name=fullname, sender_email=email,
                                  snippet=snippet)

        email_data = {
            'user_fullname': fullname,
            'msg': msg,
        }
        if topic is None:
            subject = u'Confirmation of your contact form submission (COVID-19 data responsibility)'
            snippet = 'email/content/data_responsability_faq_request_user_confirmation.html'
        else:
            subject = u'Confirmation of your contact form submission'
            email_data['topic'] = topic
            snippet = 'email/content/faq_request_user_confirmation.html'

        hdx_mailer.mail_recipient([{'display_name': fullname, 'email': email}],
                                  subject, email_data, snippet=snippet)

    except Exception as e:
        error_summary = str(e)
        return error_message(error_summary)
    return FaqSuccess

def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})

def is_valid_captcha(response):
    url = config.get('hdx.captcha.url')
    secret = config.get('ckan.recaptcha.privatekey')
    params = {'secret': secret, "response": response}
    r = requests.get(url, params=params, verify=True)
    res = json.loads(r.content)
    return 'success' in res and res['success']

hdx_faqs.add_url_rule(u'/<category>', view_func=read)
hdx_main_faq.add_url_rule(u'', view_func=main_faq)
hdx_main_faq.add_url_rule(u'/contact_us', view_func=contact_us, methods=[u'POST'])
