import exceptions as exceptions
import json
import logging
import pylons.configuration as configuration
import pylons.config as config
import requests

import ckan.lib.base as base
import ckan.logic as logic
import ckanext.hdx_theme.helpers.faq_wordpress as fw
import ckanext.hdx_users.controllers.mailer as hdx_mailer

from ckan.common import _, c, request, response
from ckan.controllers.api import CONTENT_TYPES
from ckanext.hdx_theme.util.mail import hdx_validate_email

log = logging.getLogger(__name__)
get_action = logic.get_action
ValidationError = logic.ValidationError
CaptchaNotValid = _('Captcha is not valid')
FaqSuccess = json.dumps({'success': True})
FaqCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})

class DatavizController(base.BaseController):
    def show(self):
        template_data = {
            'data': {
                'total_items': 10,
                'full_facet_info': {
                    'num_of_selected_filters': 1,
                    'filters_selected': True
                },
                'page': [
                    {
                        'id': 1,
                        'title': 'Displaced in Yemen',
                        'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
                        'date': '1 Dec 2020',
                        'label': 'Yemen',
                        'org': {
                            'name': 'HDX',
                            'url': 'https://data.humdata.local/org/hdx'
                        },
                        'image': 'https://data.humdata.local/org/hdx'
                    },
                    {
                        'id': 2,
                        'title': 'Cambodia - 4W Flood Response',
                        'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
                        'date': '1 Dec 2020',
                        'label': 'Cambodia',
                        'org': {
                            'name': 'HDX',
                            'url': 'https://data.humdata.local/org/hdx'
                        },
                        'image': 'https://data.humdata.local/org/hdx'
                    },
                ]
            },
            'errors': '',
            'error_summary': '',
        }

        return base.render('dataviz/index.html', extra_vars=template_data)
