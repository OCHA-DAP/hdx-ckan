import logging
import json
import urlparse
import requests

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


def _ga_dataset_type(is_indicator, is_cod):
    '''
    :param is_indicator:
    :type is_indicator: bool
    :param is_cod:
    :type is_cod: bool
    :return:  standard / indicator / cod / cod~indicator
    :rtype: str
    '''

    type = 'standard'
    if is_indicator:
        type = 'indicator'
    if is_cod:
        type = 'cod~indicator' if type == 'indicator' else 'cod'

    return type


def _ga_location(location_names):
    '''
    :param location_names:
    :type location_names: list[str]
    :return:
    :rtype: str
    '''
    limit = 15
    if len(location_names) >= limit:
        result = 'many'
    else:
        result = "~".join(location_names)

    if not result:
        result = 'none'

    return result


def wrap_resource_download_function():
    original_resource_download = package_controller.PackageController.resource_download

    def new_resource_download(self, id, resource_id, filename=None):
        send_event = True

        referer_url = request.referer
        remote_addr = request.remote_addr
        request_url = request.url

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

                dataset_title = dataset_dict.get('title', dataset_dict.get('name'))
                dataset_is_cod = is_cod(dataset_dict) == 'true'
                dataset_is_indicator = is_indicator(dataset_dict) == 'true'

                analytics_enqueue_url = config.get('hdx.analytics.enqueue_url')
                analytics_dict = {
                    'event_name': 'resource download',
                    'mixpanel_tracking_id': 'anonymous',
                    'mixpanel_token': config.get('hdx.analytics.mixpanel.token'),
                    'send_mixpanel': True,
                    'send_ga': True,
                    'mixpanel_meta': {
                        "resource name": resource_dict.get('name'),
                        "resource id": resource_dict.get('id'),
                        "dataset name": dataset_dict.get('title'),
                        "dataset id": dataset_dict.get('id'),
                        "org name": dataset_dict.get('organization', {}).get('name'),
                        "org id": dataset_dict.get('organization', {}).get('id'),
                        "group names": location_names,
                        "group ids": location_ids,
                        "is cod": dataset_is_cod,
                        "is indicator": dataset_is_indicator,
                        "event source": "direct",
                        "referer url": referer_url
                    },
                    'ga_meta': {
                        'v': '1',
                        't': 'event',
                        'cid': 'anonymous',
                        'tid': config.get('hdx.analytics.ga.token'),
                        'ds': 'direct',
                        'uip': remote_addr,
                        'ec': 'resource',  # event category
                        'ea': 'download',  # event action
                        'dl': request_url,
                        'el': '{} ({})'.format(resource_dict.get('name'), dataset_title),  # event label
                        'cd1': dataset_dict.get('organization', {}).get('name'),
                        'cd2': _ga_dataset_type(dataset_is_indicator, dataset_is_cod),  # type
                        'cd3': _ga_location(location_names),  # locations




                    }
                }

                response = requests.post(analytics_enqueue_url, allow_redirects=True, timeout=2,
                                         data=json.dumps(analytics_dict), headers={'Content-type': 'application/json'})
                response.raise_for_status()
                enq_result = response.json()
                log.info('Enqueuing result was: {}'.format(enq_result.get('success')))
        except logic.NotFound:
            base.abort(404, _('Resource not found'))
        except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to read resource %s') % id)
        except requests.ConnectionError, e:
            log.error("There was a connection error to the analytics enqueuing service: {}".format(str(e)))
        except requests.HTTPError, e:
            log.error("Bad HTTP response from analytics enqueuing service: {}".format(str(e)))
        except requests.Timeout, e:
            log.error("Request timed out: {}".format(str(e)))
        except Exception, e:
            log.error('Unexpected error {}'.format(e))

        return original_resource_download(self, id, resource_id, filename)

    package_controller.PackageController.resource_download = new_resource_download
