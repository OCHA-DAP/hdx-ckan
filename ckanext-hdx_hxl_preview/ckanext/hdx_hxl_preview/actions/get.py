import logging
import urllib
import urlparse

from pylons import config

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit

_get_action = toolkit.get_action
log = logging.getLogger(__name__)


def hxl_preview_iframe_url_show(context, data_dict):

    resource_dict = data_dict.get('resource')
    resource_view_dict = data_dict.get('resource_view')
    # hxl_preview_mode = data_dict.get('hxl_preview_mode')
    #
    # only_view_mode = 'false'
    # start_edit_mode = 'false'
    #
    # if hxl_preview_mode == 'onlyView':
    #     only_view_mode = 'true'
    #     start_edit_mode = 'false'
    # elif hxl_preview_mode == 'edit':
    #     only_view_mode = 'false'
    #     start_edit_mode = 'true'

    # only_view_mode = 'true' if hxl_preview_mode == 'onlyView' else 'false'
    # start_edit_mode = 'true' if hxl_preview_mode == 'edit' else 'false'

    # start_edit_mode = 'true' if self.__is_allowed_to_edit(resource_dict) and \
    #                   not self.__is_hxl_preview_config_saved(resource_view_dict) else 'false'

    has_modify_permission = 'true' if context.get('has_modify_permission', False) else 'false'

    package_id = resource_dict.get('package_id')
    package_dict = _get_action('package_show')(context, {'id': package_id})
    package_source = package_dict.get('dataset_source', '')

    package_url = h.url_for('dataset_read', id=package_id, qualified=True)
    resource_last_modified = h.render_datetime(resource_dict.get('last_modified') or resource_dict.get('created'))
    params = {
        'hxl_preview_app': config.get('hdx.hxl_preview_app.url'),
        'resource_url': urllib.urlencode({'url': resource_dict.get('url')}),
        'resource_view_id': urllib.urlencode({'resource_view_id': resource_view_dict.get('id')}),
        'hdx_domain': urllib.urlencode({'hdx_domain': __get_ckan_domain_without_protocol()}),
        'has_modify_permission': urllib.urlencode({'has_modify_permission': has_modify_permission}),
        'embedded_source': urllib.urlencode({'embeddedSource': urllib.quote(package_source.encode('utf-8'))}),
        'embedded_url': urllib.urlencode({'embeddedUrl': package_url}),
        'embedded_date': urllib.urlencode({'embeddedDate': urllib.quote(resource_last_modified.encode('utf-8'))})
        # 'edit_mode': urllib.urlencode({'editMode': start_edit_mode}),
        # 'only_view_mode': urllib.urlencode({'onlyViewMode': only_view_mode}),
    }

    url = '{hxl_preview_app}/show;{resource_url};{hdx_domain};{embedded_source};{embedded_url};{embedded_date};{resource_view_id};{has_modify_permission}'.format(
        **params)
    return url


def __get_ckan_domain_without_protocol():
    ckan_site_url = config.get('ckan.site_url')
    url_parts = urlparse.urlsplit(ckan_site_url)

    return urlparse.urlunsplit([''] + list(url_parts[1:]))
