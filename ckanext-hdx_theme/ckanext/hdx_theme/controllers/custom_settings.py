import requests
import json
import pylons.configuration as configuration

import ckan.lib.base as base
from ckan.common import _, c, g, request, response
from ckan.controllers.api import CONTENT_TYPES



class CustomSettingsController(base.BaseController):
    def show(self):
        template_data = {}

        return base.render('settings/carousel_settings.html', extra_vars=template_data)