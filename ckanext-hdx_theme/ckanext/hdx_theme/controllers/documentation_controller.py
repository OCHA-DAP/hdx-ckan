import json

from ckanext.hdx_theme.helpers.resources_for_developers_data import rfd_data

import ckan.lib.base as base
import ckan.logic as logic
from ckan.common import _

get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})

for section in rfd_data:
    s_id = ''.join(i if i.isalnum() else '_' for i in section['title'])
    s_id = 'faq-{}'.format(s_id)
    section['id'] = s_id
    for question in section['questions']:
        q_id = ''.join(i if i.isalnum() else '_' for i in question['q'])
        question['id'] = q_id

topics = {}
for f in rfd_data:
    topics[f.get('id')] = f.get('title')


class DocumentationController(base.BaseController):
    def show(self):
        template_data = {
            'data': {
                'faq_data': rfd_data,
                'topics': topics,
            },
            'errors': '',
            'error_summary': '',
        }

        return base.render('documentation/main.html', extra_vars=template_data)

