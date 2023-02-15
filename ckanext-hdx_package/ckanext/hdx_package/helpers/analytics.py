import json
import logging
import six.moves.urllib.parse as urlparse
import datetime

from ckanext.hdx_package.helpers.constants import COD_ENHANCED, COD_STANDARD
from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
get_action = tk.get_action
config = tk.config
request = tk.request
g = tk.g
_ = tk._
abort = tk.abort


def is_indicator(pkg_dict):
    if int(pkg_dict.get('indicator', 0)) == 1:
        return 'true'
    return 'false'


def is_cod(pkg_dict):
    cod_level = pkg_dict.get('cod_level')
    if cod_level == COD_ENHANCED or cod_level == COD_STANDARD:
        return 'true'
    return 'false'


def is_archived(pkg_dict):
    if pkg_dict.get('archived'):
        return 'true'
    return 'false'


def is_private(pkg_dict):
    if pkg_dict.get('private'):
        return 'true'
    return 'false'


# def is_protected(pkg_dict):
#     if pkg_dict.get('is_requestdata_type'):
#         return 'true'
#     return 'false'


def dataset_availability(pkg_dict):
    if pkg_dict.get('is_requestdata_type'):
        level = 'metadata only'
    elif pkg_dict.get('private'):
        level = 'private'
    else:
        level = 'public'
    return level


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


def generate_analytics_data(dataset_dict):
    # in case of an edit event we populate the analytics info

    # it's going to be used mostly in JSON so using camelCase
    analytics_dict = {}
    if dataset_dict and dataset_dict.get('id'):
        analytics_dict['datasetId'] = dataset_dict['id']
        analytics_dict['datasetName'] = dataset_dict['name']
        analytics_dict['organizationName'] = dataset_dict.get('organization', {}).get('name') \
                                                if dataset_dict.get('organization') else None
        analytics_dict['organizationId'] = dataset_dict.get('organization', {}).get('name') \
                                                if dataset_dict.get('organization') else None
        analytics_dict['isCod'] = is_cod(dataset_dict)
        analytics_dict['isIndicator'] = is_indicator(dataset_dict)
        analytics_dict['isArchived'] = is_archived(dataset_dict)
        analytics_dict['groupNames'], analytics_dict['groupIds'] = extract_locations_in_json(dataset_dict)
        analytics_dict['datasetAvailability'] = dataset_availability(dataset_dict)
    else:
        analytics_dict['datasetId'] = ''
        analytics_dict['datasetName'] = ''
        analytics_dict['organizationName'] = ''
        analytics_dict['organizationId'] = ''
        analytics_dict['isCod'] = 'false'
        analytics_dict['isIndicator'] = 'false'
        analytics_dict['isArchived'] = 'false'
        analytics_dict['groupNames'] = '[]'
        analytics_dict['groupIds'] = '[]'
        analytics_dict['datasetAvailability'] = None
    return analytics_dict


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


def resource_download_with_analytics(id, resource_id, filename=None):

    send_event = True
    referer_url = request.referrer

    if referer_url:
        ckan_url = config.get('ckan.site_url', '//localhost:5000')
        ckan_parsed_url = urlparse.urlparse(ckan_url)
        referer_parsed_url = urlparse.urlparse(referer_url)

        if ckan_parsed_url.hostname == referer_parsed_url.hostname:
            send_event = False

    if send_event:
        ResourceDownloadAnalyticsSender(id, resource_id).send_to_queue()


# def wrap_resource_download_function():
#     '''
#     Changes the original resource_download function from the package controller with a version that
#     wraps the original function but also enqueues the tracking events
#     '''
#     original_resource_download = package_controller.PackageController.resource_download
#
#     def new_resource_download(self, id, resource_id, filename=None):
#
#         send_event = True
#         referer_url = request.referer
#
#         if referer_url:
#             ckan_url = config.get('ckan.site_url', '//localhost:5000')
#             ckan_parsed_url = urlparse.urlparse(ckan_url)
#             referer_parsed_url = urlparse.urlparse(referer_url)
#
#             if ckan_parsed_url.hostname == referer_parsed_url.hostname:
#                 send_event = False
#
#         if send_event:
#             ResourceDownloadAnalyticsSender(id, resource_id).send_to_queue()
#
#         return original_resource_download(self, id, resource_id, filename)
#
#     package_controller.PackageController.resource_download = new_resource_download


class ResourceDownloadAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, package_id, resource_id):
        super(ResourceDownloadAnalyticsSender, self).__init__()

        log.debug('The user IP address was {}'.format(self.user_addr))

        try:
            context = {'model': model, 'session': model.Session,
                       'user': g.user or g.author, 'auth_user_obj': g.userobj}
            dataset_dict = get_action('package_show')(context, {'id': package_id})
            resource_dict = next(r for r in dataset_dict.get('resources', {}) if r.get('id') == resource_id)
            location_names, location_ids = extract_locations(dataset_dict)

            dataset_title = dataset_dict.get('title', dataset_dict.get('name'))
            dataset_is_cod = is_cod(dataset_dict) == 'true'
            dataset_is_indicator = is_indicator(dataset_dict) == 'true'
            dataset_is_archived = is_archived(dataset_dict) == 'true'
            authenticated = True if g.userobj else False

            self.analytics_dict = {
                'event_name': 'resource download',
                'mixpanel_meta': {
                    "resource name": resource_dict.get('name'),
                    "resource id": resource_dict.get('id'),
                    "dataset name": dataset_dict.get('name'),
                    "dataset id": dataset_dict.get('id'),
                    "org name": dataset_dict.get('organization', {}).get('name'),
                    "org id": dataset_dict.get('organization', {}).get('id'),
                    "group names": location_names,
                    "group ids": location_ids,
                    "is cod": dataset_is_cod,
                    "is indicator": dataset_is_indicator,
                    "is archived": dataset_is_archived,
                    "authenticated": authenticated,
                    'event source': 'direct'
                },
                'ga_meta': {
                    'ec': 'resource',  # event category
                    'ea': 'download',  # event action
                    'el': u'{} ({})'.format(resource_dict.get('name'), dataset_title),  # event label
                    'cd1': dataset_dict.get('organization', {}).get('name'),
                    'cd2': _ga_dataset_type(dataset_is_indicator, dataset_is_cod),  # type
                    'cd3': _ga_location(location_names),  # locations

                }
            }

        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(403, _('Unauthorized to read resource %s') % id)
        except Exception as e:
            log.error('Unexpected error {}'.format(e))



def analytics_wrapper_4_package_create(original_package_action):

    def package_action(context, package_dict):

        result_dict = original_package_action(context, package_dict)

        # if the package doesn't come from the contribute flow UI form and is a normal dataset (aka not a showcase)
        # then send the even from the server side
        if not context.get('contribute_flow') and (
                package_dict.get('type') == 'dataset' or not package_dict.get('type')):
            DatasetCreatedAnalyticsSender(result_dict).send_to_queue()

        return result_dict

    return package_action


class DatasetCreatedAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, dataset_dict):
        super(DatasetCreatedAnalyticsSender, self).__init__()

        location_names, location_ids = extract_locations(dataset_dict)
        dataset_is_cod = is_cod(dataset_dict) == 'true'
        dataset_is_indicator = is_indicator(dataset_dict) == 'true'
        dataset_is_private = is_private(dataset_dict) == 'true'
        dataset_availability_level = dataset_availability(dataset_dict)



        self.analytics_dict = {
            'event_name': 'dataset create',
            'mixpanel_meta': {
                'event source': 'api',
                'group names': location_names,
                'group ids': location_ids,
                'org_name': (dataset_dict.get('organization') or {}).get('name'),
                'org_id': (dataset_dict.get('organization') or {}).get('id'),
                'is cod': dataset_is_cod,
                'is indicator': dataset_is_indicator,
                'is private': dataset_is_private,
                'dataset availability': dataset_availability_level
            },
            'ga_meta': {
                'ec': 'dataset',  # event category
                'ea': 'create',  # event action
                # There is no event label because that would correspond to the page title and this doesn't exist on the
                # server side
                'cd1': (dataset_dict.get('organization') or {}).get('name'),
                'cd2': _ga_dataset_type(dataset_is_indicator, dataset_is_cod),  # type
                'cd3': _ga_location(location_names),  # locations

            }
        }


class QACompletedAnalyticsSender(AbstractAnalyticsSender):
    def __init__(self, dataset_dict, metadata_modified, mark_as_set=True):
        '''

        :param dataset_dict:
        :type dataset_dict: dict
        :param metadata_modified:
        :type metadata_modified: datetime.datetime
        :param mark_as_set:
        :type mark_as_set: bool
        '''
        super(QACompletedAnalyticsSender, self).__init__()

        location_names, location_ids = extract_locations(dataset_dict)
        dataset_is_cod = is_cod(dataset_dict) == 'true'
        dataset_is_indicator = is_indicator(dataset_dict) == 'true'
        dataset_is_private = is_private(dataset_dict) == 'true'
        dataset_availability_level = dataset_availability(dataset_dict)

        self.analytics_dict = {
            'event_name': 'qa set complete' if mark_as_set else 'qa set incomplete',
            'mixpanel_meta': {
                "dataset name": dataset_dict.get('name'),
                "dataset id": dataset_dict.get('id'),
                'event source': 'api',
                'group names': location_names,
                'group ids': location_ids,
                'org_name': (dataset_dict.get('organization') or {}).get('name'),
                'org_id': (dataset_dict.get('organization') or {}).get('id'),
                'is cod': dataset_is_cod,
                'is private': dataset_is_private,
                'dataset availability': dataset_availability_level
            },
            'ga_meta': {
                'ec': 'dataset',  # event category
                'ea': 'qa set complete' if mark_as_set else 'qa set incomplete',  # event action
                # There is no event label because that would correspond to the page title and this doesn't exist on the
                # server side
                'cd1': (dataset_dict.get('organization') or {}).get('name'),
                'cd2': _ga_dataset_type(dataset_is_indicator, dataset_is_cod),  # type
                'cd3': _ga_location(location_names),  # locations

            }
        }

        if g.userobj.sysadmin and mark_as_set:
            self.analytics_dict['mixpanel_meta']['user id'] = g.userobj.id

            time_difference = datetime.datetime.utcnow() - metadata_modified
            self.analytics_dict['mixpanel_meta']['minutes since modified'] = int(time_difference.total_seconds()) / 60


class QAQuarantineAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, dataset_dict, resource_id, new_quarantine_value):
        super(QAQuarantineAnalyticsSender, self).__init__()

        self.old_quarantine_value = False
        self.new_quarantine_value = new_quarantine_value

        try:
            resource_dict = next(r for r in dataset_dict.get('resources', {}) if r.get('id') == resource_id)

            dataset_title = dataset_dict.get('title', dataset_dict.get('name'))
            dataset_is_archived = is_archived(dataset_dict) == 'true'
            authenticated = True if g.userobj else False

            time_difference = datetime.datetime.utcnow() - h.date_str_to_datetime(resource_dict.get('last_modified'))

            self.old_quarantine_value = resource_dict.get('in_quarantine')

            self.analytics_dict = {
                'event_name': 'qa set in quarantine' if self.new_quarantine_value else 'qa remove from quarantine',
                'mixpanel_meta': {
                    'resource name': resource_dict.get('name'),
                    'resource id': resource_dict.get('id'),
                    'dataset name': dataset_dict.get('name'),
                    'dataset id': dataset_dict.get('id'),
                    'org name': dataset_dict.get('organization', {}).get('name'),
                    'org id': dataset_dict.get('organization', {}).get('id'),
                    'is archived': dataset_is_archived,
                    'authenticated': authenticated,
                    'event source': 'api',
                },
                'ga_meta': {
                    'ec': 'resource',  # event category
                    'ea': 'added to quarantine' if self.new_quarantine_value else 'removed from quarantine',  # event action
                    'el': u'{} ({})'.format(resource_dict.get('name'), dataset_title),  # event label
                }
            }

            if self.new_quarantine_value:
                self.analytics_dict['mixpanel_meta']['minutes since modified'] = int(
                    time_difference.total_seconds()) / 60

        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(403, _('Unauthorized to read resource %s') % id)
        except Exception as e:
            log.error('Unexpected error {}'.format(e))

    def should_send_analytics_event(self):
        return self.old_quarantine_value != self.new_quarantine_value


class AbstractResourceAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, dataset_dict, resource_dict):
        super(AbstractResourceAnalyticsSender, self).__init__()

        try:
            context = {'model': model, 'session': model.Session,
                       'user': g.user or g.author, 'auth_user_obj': g.userobj}
            location_names, location_ids = extract_locations(dataset_dict)
            dataset_title = dataset_dict.get('title', dataset_dict.get('name'))
            dataset_is_cod = is_cod(dataset_dict) == 'true'
            dataset_is_indicator = is_indicator(dataset_dict) == 'true'
            dataset_is_archived = is_archived(dataset_dict) == 'true'

            self.analytics_dict = {
                # 'event_name': 'EVENT NAME', # Needs to be set in subclass
                'mixpanel_meta': {
                    'resource name': resource_dict.get('name'),
                    'resource id': resource_dict.get('id'),
                    'dataset name': dataset_dict.get('name'),
                    'dataset id': dataset_dict.get('id'),
                    'org name': dataset_dict.get('organization', {}).get('name'),
                    'org id': dataset_dict.get('organization', {}).get('id'),
                    "group names": location_names,
                    "group ids": location_ids,
                    'is archived': dataset_is_archived,
                    'event source': 'api',
                },
                'ga_meta': {
                    'ec': 'resource',  # event category
                    'el': u'{} ({})'.format(resource_dict.get('name'), dataset_title),  # event label
                    'cd1': dataset_dict.get('organization', {}).get('name'),
                    'cd2': _ga_dataset_type(dataset_is_indicator, dataset_is_cod),  # type
                    'cd3': _ga_location(location_names),  # locations

                }
            }

        except NotFound as e:
            abort(404, _('Resource not found'))
        except NotAuthorized as e:
            abort(403, _('Unauthorized to read resource %s') % id)
        except Exception as e:
            log.error('Unexpected error {}'.format(e))

    def should_send_analytics_event(self):
        raise NotImplemented('should_send_analytics_event is not implemented in {}'.format(self.__class__.__name__))


class QAPiiAnalyticsSender(AbstractResourceAnalyticsSender):

    def __init__(self, dataset_dict, resource_dict, new_pii_value):
        super(QAPiiAnalyticsSender, self).__init__(dataset_dict, resource_dict)
        self.new_pii_value = new_pii_value
        self.old_pii_value = resource_dict.get('pii_report_flag')

        if self.analytics_dict: # might not be initialized in case of tests
            self.analytics_dict['event_name'] = 'qa set pii'
            self.analytics_dict['mixpanel_meta']['flag value'] = new_pii_value
            self.analytics_dict['ga_meta']['ea value'] = 'flagging pii: {}'.format(new_pii_value),  # event action

    def should_send_analytics_event(self):
        return self.new_pii_value != self.old_pii_value


class QASdcAnalyticsSender(AbstractResourceAnalyticsSender):

    def __init__(self, dataset_dict, resource_dict, new_sdc_value):
        super(QASdcAnalyticsSender, self).__init__(dataset_dict, resource_dict)
        self.new_sdc_value = new_sdc_value
        self.old_sdc_value = resource_dict.get('sdc_report_flag')

        if self.analytics_dict:  # might not be initialized in case of tests
            self.analytics_dict['event_name'] = 'qa set sdc'
            self.analytics_dict['mixpanel_meta']['flag value'] = new_sdc_value
            self.analytics_dict['ga_meta']['ea value'] = 'flagging pii: {}'.format(new_sdc_value),  # event action

    def should_send_analytics_event(self):
        return self.new_sdc_value != self.old_sdc_value
