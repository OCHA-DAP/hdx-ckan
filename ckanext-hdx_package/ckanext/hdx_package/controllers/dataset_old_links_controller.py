'''
Created on Aug 7, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base

from ckan.common import _
from ckan.common import response


class DatasetOldLinks(base.BaseController):
    def _show_notification_page(self, message, id=None):
        template_data = {
            'data': {
                'notice': message,
                'dataset_id': "'{}'".format(id) if id else ""
            }
        }
        response.status_int = 300
        return base.render('contribute_flow/dataset_old_links.html', extra_vars=template_data)

    def new_notification_page(self, id=None):
        message = _('In order to create a new dataset please use the "ADD DATA" button at the top of the page or click ')
        return self._show_notification_page(message, id)

    def edit_notification_page(self, id=None):
        message = _('In order to edit this dataset please use the "EDIT" button on the dataset view page or click ')
        return self._show_notification_page(message, id)

    def resource_new_notification_page(self, id=None):
        message = _('In order to create a new resource please use the "EDIT" button on the dataset view page or click ')
        return self._show_notification_page(message, id)

    def resource_edit_notification_page(self, id=None, resource_id=None):
        message = _('In order to edit this resource please use the "EDIT" button on the dataset view page or click ')
        return self._show_notification_page(message, id)

    def resources_notification_page(self, id=None):
        return self._show_notification_page(None, id)
