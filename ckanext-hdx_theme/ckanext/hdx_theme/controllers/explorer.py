# import requests
import ckan.lib.base as base
# from ckan.common import _, c, g, request, response
# import exceptions as exceptions
import ckan.logic as logic
# import json
import pylons.configuration as configuration

# import ckanext.hdx_users.controllers.mailer as hdx_mailer
# from ckanext.hdx_theme.helpers.faq_data import faq_data

get_action = logic.get_action
ValidationError = logic.ValidationError


class ExplorerController(base.BaseController):
    def show(self):
        url = configuration.config.get('hdx.explorer.url')
        height = configuration.config.get('hdx.explorer.iframe.height')
        width = configuration.config.get('hdx.explorer.iframe.width')

        template_data = {
            'data': {
                'url': url,
                'height': height,
                'width': width,
            },
            'errors': '',
            'error_summary': '',
        }

        return base.render('explorer/main.html', extra_vars=template_data)
