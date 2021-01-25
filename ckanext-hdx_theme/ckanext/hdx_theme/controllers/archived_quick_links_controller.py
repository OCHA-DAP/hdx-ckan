import json
import logging
import pylons.configuration as configuration

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckanext.hdx_theme.helpers.faq_wordpress as fw
from ckan.common import _, c

abort = base.abort
log = logging.getLogger(__name__)
get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})


def _prepare_pages(page_list):
    res = []
    for page in page_list:
        if page.get('status') == 'archived':
            res.append(page)
    return res


class ArchivedQuickLinksController(base.BaseController):
    def show(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'for_view': True, 'with_related': True}
        try:
            logic.check_access('page_list', context, {})
        except Exception, ex:
            abort(404, 'Page not found')

        page_list = logic.get_action('page_list')(context, {})
        _pages = _prepare_pages(page_list)
        wp_category_faq = configuration.config.get('hdx.wordpress.category.faq')
        faq_data = fw.faq_for_category(wp_category_faq)

        template_data = {
            'data': {
                'faq_data': faq_data,
                'pages': _pages
                # 'topics': _get_topics(),
                # 'fullname': fullname,
                # 'email': email,
            },
            # 'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey'),
            'errors': '',
            'error_summary': '',
        }

        return base.render('archived_quick_links/main.html', extra_vars=template_data)

    # def about(self):
    #     import ckan.lib.helpers as h
    #     return h.redirect_to(controller='ckanext.hdx_theme.controllers.faq:FaqController', action='show')

    # def contact_us(self):
    #     '''
    #     Send a contact request form
    #     :return:
    #     '''
    #     response.headers['Content-Type'] = CONTENT_TYPES['json']
    #     try:
    #         topic = request.params.get('topic')
    #         fullname = request.params.get('fullname')
    #         email = request.params.get('email')
    #         msg = request.params.get('faq-msg')
    #         hdx_email = configuration.config.get('hdx.faqrequest.email', 'hdx@un.org')
    #
    #         test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    #         if not test:
    #             captcha_response = request.params.get('g-recaptcha-response')
    #             if not self.is_valid_captcha(response=captcha_response):
    #                 raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
    #
    #         simple_validate_email(email)
    #
    #     except ValidationError, e:
    #         error_summary = e.error_summary
    #         if error_summary == CaptchaNotValid:
    #             return FaqCaptchaErr
    #         return self.error_message(error_summary)
    #     except exceptions.Exception, e:
    #         error_summary = e.error or str(e)
    #         return self.error_message(error_summary)
    #
    #     try:
    #         subject = u'Faq: request from user'
    #         html = u"""\
    #             <html>
    #               <head></head>
    #               <body>
    #                 <p>A user sent the following question using the FAQ contact us form.</p>
    #                 <p>Name: {fullname}</p>
    #                 <p>Email: {email}</p>
    #                 <p>Section: {topic}</p>
    #                 <p>Message: {msg}</p>
    #               </body>
    #             </html>
    #             """.format(fullname=fullname, email=email, topic=topic, msg=msg)
    #         hdx_mailer.mail_recipient([{'display_name': 'HDX', 'email': hdx_email}], subject, html)
    #
    #     except exceptions.Exception, e:
    #         error_summary = e.error or str(e)
    #         return self.error_message(error_summary)
    #     return FaqSuccess
    #
    # def error_message(self, error_summary):
    #     return json.dumps({'success': False, 'error': {'message': error_summary}})
    #
    # def is_valid_captcha(self, response):
    #     url = configuration.config.get('hdx.captcha.url')
    #     secret = configuration.config.get('ckan.recaptcha.privatekey')
    #     params = {'secret': secret, "response": response}
    #     r = requests.get(url, params=params, verify=True)
    #     res = json.loads(r.content)
    #     return 'success' in res and res['success']
