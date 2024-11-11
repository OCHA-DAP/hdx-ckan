'''
Created on Jun 2, 2014

@author: alexandru-m-g
'''
import csv
import logging
import unicodedata
from typing import Set

import requests
from dogpile.cache import make_region

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.country_list_hardcoded as focus_countries
from ckanext.hdx_theme.helpers.caching import dogpile_standard_config, dogpile_config_filter, dogpile_requests_region, \
    HDXRedisInvalidationStrategy

log = logging.getLogger(__name__)
config = tk.config

dogpile_org_group_config = {
    'cache.redis.expiration_time': 60 * 60 * 24,
}
dogpile_org_group_config.update(dogpile_standard_config)

dogpile_org_group_lists_region = make_region(key_mangler=lambda key: 'org_group-' + key)
dogpile_org_group_lists_region.configure_from_config(dogpile_org_group_config, dogpile_config_filter)

if dogpile_config_filter == 'cache.redis.':
    dogpile_org_group_lists_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_org_group_lists_region)

# API HIGHWAYS cache config
dogpile_external_config = {
    'cache.redis.expiration_time': 60 * 60 * 24 * 3,
}
dogpile_external_config.update(dogpile_standard_config)
dogpile_pkg_external_region = make_region(key_mangler=lambda key: 'pkg_external-' + key)
dogpile_pkg_external_region.configure_from_config(dogpile_external_config, dogpile_config_filter)

if dogpile_config_filter == 'cache.redis.':
    dogpile_pkg_external_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_pkg_external_region)


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


@dogpile_org_group_lists_region.cache_on_arguments()
def cached_group_iso_to_title():
    log.info("Creating cache for group iso to title mapping")
    groups = cached_group_list()

    result = {g.get('name'): g.get('title') for g in groups}

    return result


@dogpile_org_group_lists_region.cache_on_arguments()
def cached_group_list():
    log.info("Creating cache for group list ")
    groups = tk.get_action('group_list')({'user': '127.0.0.1'},
                                         {
                                             'all_fields': True,
                                             'include_extras': True,
                                             'package_count': True
                                         })
    # for group in groups:
    #     activity_level = next(
    #         (extra.get('value') for extra in group.get('extras', []) if extra.get('key') == 'activity_level'),
    #         None
    #     )
    #     group['activity_level'] = activity_level
    return sorted(groups, key=lambda k: strip_accents(k['display_name']))


def invalidate_cached_group_list():
    log.info("Invalidating cache for group list")
    # bcache.region_invalidate(cached_group_list, 'hdx_memory_cache', 'cached_grp_list')
    # bcache.region_invalidate(cached_group_iso_to_title, 'hdx_memory_cache', 'cached_grp_iso_to_title')
    cached_group_list.invalidate()
    cached_group_iso_to_title.invalidate()


def filter_focus_countries(group_package_stuff):
    focus_group_package_stuff = []
    for grp_dict in group_package_stuff:
        if grp_dict['display_name'] in focus_countries.FOCUS_COUNTRIES:
            focus_group_package_stuff.append(grp_dict)

    return focus_group_package_stuff


# @dogpile_org_group_lists_region.cache_on_arguments()
# def cached_get_group_package_stuff():
#     log.info("Creating cache for focus countries")
#     group_package_stuff = tk.get_action('cached_group_list')()
#     focus_group_package_stuff = filter_focus_countries(group_package_stuff)
#
#     return sorted(focus_group_package_stuff, key=lambda k: k['title'])
#
#
# def invalidate_cached_get_group_package_stuff():
#     log.info("Invalidating cache for focus countries")
#     bcache.region_invalidate(cached_get_group_package_stuff, 'hdx_memory_cache', 'focus_countries_list')


def invalidate_group_caches():
    for invalidate_func in group_invalidation_functions:
        invalidate_func()


group_invalidation_functions = [invalidate_cached_group_list]


@dogpile_org_group_lists_region.cache_on_arguments()
def cached_organization_list():
    log.info("Creating cache for organization list")
    orgs = tk.get_action('organization_list')({'user': '127.0.0.1'},
                                              {
                                                  'all_fields': True,
                                                  'include_extras': True
                                              })

    return _sort_orgs_by_display_name(orgs)


def _sort_orgs_by_display_name(orgs):
    return sorted(orgs, key=lambda k: strip_accents(k['display_name']))


def invalidate_cached_organization_list():
    log.info("Invalidating cache for org list")
    # bcache.region_invalidate(cached_organization_list, 'hdx_memory_cache', 'cached_organization_list')
    cached_organization_list.invalidate()


def replace_org_in_cache_organization_list(org_id):
    modified_org = tk.get_action('organization_show')(
        {},{
            'id': org_id,
            'include_extras': True,
            'include_tags': False,
            'include_users': False,
            'include_groups': False,
            'include_followers': False
        })
    orgs = cached_organization_list()
    index = next((i for i, o in enumerate(orgs) if o['id'] == modified_org['id']), -1)
    if index >= 0:
        orgs[index] = modified_org
    else:
        orgs.append(modified_org)

        orgs = _sort_orgs_by_display_name(orgs)

    cached_organization_list.set(orgs)


def add_org_in_cache_organization_list(org_id):
    modified_org = tk.get_action('organization_show')(
        {},{
            'id': org_id,
            'include_extras': True,
            'include_tags': False,
            'include_users': False,
            'include_groups': False,
            'include_followers': False
        })
    orgs = cached_organization_list()
    orgs.append(modified_org)
    orgs = _sort_orgs_by_display_name(orgs)
    cached_organization_list.set(orgs)


@dogpile_pkg_external_region.cache_on_arguments()
def cached_resource_id_apihighways():
    log.info("Creating cache for HDX resource_id to apihighways dataset_id mapping")

    result = {}
    # if config.get('hdx.apihighways.enabled') == 'true':
    #     try:
    #         response = requests.get(config.get('hdx.apihighways.url'))
    #         response.raise_for_status()
    #         result = response.json()
    #     except Exception as ex:
    #         log.error(ex)
    return result


def invalidate_cached_resource_id_apihighways():
    log.info("Invalidating cache for apihighways")
    cached_resource_id_apihighways.invalidate()


@dogpile_requests_region.cache_on_arguments()
def cached_approved_tags_list():
    log.info('Creating cache for approved tags list')
    tags = tk.get_action('hdx_retrieve_approved_tags')({'user': '127.0.0.1'}, {})
    return tags


def invalidate_cached_approved_tags():
    log.info('Invalidating cache for approved tags list')
    cached_approved_tags_list.invalidate()

@dogpile_requests_region.cache_on_arguments()
def cached_datasets_with_notifications() -> Set[str]:
    log.info('Creating cache list of datasets with notifications')
    return hdx_retrieve_datasets_with_notifications(None, None)

def hdx_retrieve_datasets_with_notifications(context, data_dict) -> Set[str]:
    url = config.get('hdx.notifications.enabled_datasets_csv')
    if url:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            log.error(f"An error occurred: {error_msg}")
            raise Exception(f'Couldn\'t fetch datasets with notifications from Google Spreadsheets: {error_msg}')

        csv_data = response.text
        csv_reader = csv.reader(csv_data.splitlines())

        datasets = {row[0] for row in csv_reader}
        return datasets
    else:
        log.error('No URL for notification-enabled datasets found in config')
        return set()
