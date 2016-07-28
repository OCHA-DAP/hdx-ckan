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
            'hdx.carousel.config': setting_value
        }

        return base.render('settings/carousel_settings.html', extra_vars=template_data)

    def update(self):
        field_storage = request.params.get('image_1')
        upload = GlobalUpload({
            'filename': None,
            'upload': field_storage
        })

        upload.upload()



    def global_file_download(self, filename):
        upload = GlobalUpload({
            'filename': filename,
            'upload': None
        })
        filepath = upload.get_path(filename)
        fapp = fileapp.FileApp(filepath)
        try:
            status, headers, app_iter = request.call_application(fapp)
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type(filename)
            if content_type:
                response.headers['Content-Type'] = content_type
            response.status = status
            return app_iter
        except OSError:
            base.abort(404, _('Resource data not found'))
