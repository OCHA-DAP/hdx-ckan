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

class FaqController(base.BaseController):

    def about(self):
        import ckan.lib.helpers as h
        return h.redirect_to(controller='ckanext.hdx_theme.controllers.faq:FaqController', action='show')

