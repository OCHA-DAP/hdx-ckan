import json
import logging
import uuid

from ckanext.hdx_theme.helpers.uploader import GlobalUpload

import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, request, response, g, c
from ckan.controllers.api import CONTENT_TYPES

log = logging.getLogger(__name__)
abort = base.abort


class CustomSettingsController(base.BaseController):

    def show_pages(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'for_view': True, 'with_related': True}

        try:
            logic.check_access('admin_page_list', context, {})
        except Exception, ex:
            abort(404, 'Page not found')

        page_list = logic.get_action('admin_page_list')(context, {})

        template_data = {
            'page_list': page_list
        }

        return base.render('admin/pages.html', extra_vars=template_data)
