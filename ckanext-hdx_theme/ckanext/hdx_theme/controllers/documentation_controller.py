import json
import pylons.configuration as configuration
import pylons.config as config
import ckan.lib.base as base
import ckan.logic as logic
import ckanext.hdx_theme.helpers.faq_wordpress as fw
from ckan.common import _,c

get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})

class DocumentationController(base.BaseController):
    def show(self):
        wp_category_devs = config.get('hdx.wordpress.category.devs')
        data = fw.faq_for_category(wp_category_devs)
        fullname = c.userobj.display_name if c.userobj and c.userobj.display_name is not None else ''
        email = c.userobj.email if c.userobj and c.userobj.email is not None else ''
        template_data = {
            'data': {
                'faq_data': data['faq_data'],
                'topics': data['topics'],
                'fullname': fullname,
                'email': email
            },
            'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey'),
            'errors': '',
            'error_summary': '',
        }

        return base.render('documentation/main.html', extra_vars=template_data)

