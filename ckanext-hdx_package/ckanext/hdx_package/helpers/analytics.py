import logging
import json
import urlparse
import mixpanel
import pylons.config as config

import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import ckan.controllers.package as package_controller

from ckan.common import _, c, request

log = logging.getLogger(__name__)


def is_indicator(pkg_dict):
    if int(pkg_dict.get('indicator', 0)) == 1:
        return 'true'
    return 'false'


def is_cod(pkg_dict):
    tags = [tag.get('name', '') for tag in pkg_dict.get('tags', [])]
    if 'cod' in tags:
        return 'true'
    return 'false'


def extract_locations(pkg_dict):
    locations = pkg_dict.get('groups', [])
    location_names = []
    location_ids = []
    for l in sorted(locations, key=lambda item: item.get('name', '')):
        location_names.append(l.get('name', ''))
        location_ids.append(l.get('id', ''))

    return location_names, location_ids


def extract_locations_in_json(pkg_dict):
    locations = pkg_dict.get('groups', [])
    location_names = []
    location_ids = []
    for l in sorted(locations, key=lambda item: item.get('name', '')):
        location_names.append(l.get('name', ''))
        location_ids.append(l.get('id', ''))

    return json.dumps(location_names), json.dumps(location_ids)


def wrap_resource_download_function():
    original_resource_download = package_controller.PackageController.resource_download

    def new_resource_download(self, id, resource_id, filename=None):
        send_event = True
        referer_url = request.referer
        if referer_url:
            ckan_url = config.get('ckan.site_url', '//localhost:5000')
            ckan_parsed_url = urlparse.urlparse(ckan_url)
            referer_parsed_url = urlparse.urlparse(referer_url)

            if ckan_parsed_url.hostname == referer_parsed_url.hostname:
                send_event = False
        try:
            if send_event:
                context = {'model': model, 'session': model.Session,
                           'user': c.user or c.author, 'auth_user_obj': c.userobj}
                resource_dict = logic.get_action('resource_show')(context, {'id': resource_id})
                dataset_dict = logic.get_action('package_show')(context, {'id': id})
                location_names, location_ids = extract_locations(dataset_dict)

                mp = mixpanel.Mixpanel(config.get('hdx.mixpanel.token'))
                event_dict = {
                    "resource name": resource_dict.get('name'),
                    "resource id": resource_dict.get('id'),
                    "dataset name": dataset_dict.get('title'),
                    "dataset id": dataset_dict.get('id'),
                    "org name": dataset_dict.get('organization', {}).get('name'),
                    "org id": dataset_dict.get('organization', {}).get('id'),
                    "group names": location_names,
                    "group ids": location_ids,
                    "is cod": is_cod(dataset_dict),
                    "is indicator": is_indicator(dataset_dict),
                    "event source": "direct",
                    "referer url": referer_url

                }
                mp.track('anonymous', 'resource download', event_dict)
        except logic.NotFound:
            base.abort(404, _('Resource not found'))
        except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to read resource %s') % id)
        return original_resource_download(self, id, resource_id, filename)

    package_controller.PackageController.resource_download = new_resource_download
