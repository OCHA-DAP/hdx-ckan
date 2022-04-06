from flask import Blueprint

import ckan.views.resource as resource_view
import ckanext.s3filestore.view as s3_resource_view

from ckanext.hdx_package.helpers.analytics import resource_download_with_analytics
from ckanext.hdx_package.helpers.quarantine import resource_download_with_quarantine_check
from ckanext.hdx_theme.helpers.config import is_s3filestore_enabled

view = s3_resource_view if is_s3filestore_enabled() else resource_view
before_download_functions = [resource_download_with_quarantine_check, resource_download_with_analytics]

hdx_download_wrapper = Blueprint(u'hdx_download_wrapper', __name__)


def download(id, resource_id, filename=None):
    for f in before_download_functions:
        f(id, resource_id, filename)

    return view.download(id, resource_id, filename)


hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download', view_func=download)
hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download/<filename>', view_func=download)
