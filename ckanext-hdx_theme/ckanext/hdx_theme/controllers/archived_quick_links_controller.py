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


class ArchivedDatavizController(base.BaseController):
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

        template_data = {
            'data': {
                'pages': _pages
            },
            'errors': '',
            'error_summary': '',
        }

        return base.render('archived_quick_links/main.html', extra_vars=template_data)
