import json
import mimetypes
import pylons.config as config

import paste.fileapp as fileapp

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model

from ckan.common import _, c, g, request, response
from ckan.controllers.api import CONTENT_TYPES

from ckanext.hdx_theme.helpers.uploader import GlobalUpload


class CustomSettingsController(base.BaseController):
    def show(self):

        logic.check_access('config_option_show', {}, {})

        setting_value = model.get_system_info('hdx.carousel.config', config.get('hdx.carousel.config'))
        template_data = {
            'data': {
                'hdx.carousel.config': setting_value
            }
        }

        return base.render('settings/carousel_settings.html', extra_vars=template_data)

    def update(self):
        logic.check_access('config_option_update', {}, {})

        field_storage = request.params.get('image_1')
        settings_value = request.params.get('hdx.carousel.config')

        upload = GlobalUpload({
            'filename': None,
            'upload': field_storage
        })

        upload.upload()

        model.set_system_info('hdx.carousel.config', settings_value)

