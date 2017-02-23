'''
Created on Jun 2, 2014

@author: alexandru-m-g
'''

import logging
import ckan.plugins.toolkit as tk
import beaker.cache as bcache
import unicodedata

import ckanext.hdx_theme.helpers.country_list_hardcoded as focus_countries

log = logging.getLogger(__name__)

bcache.cache_regions.update({
    'hdx_memory_cache': {
        'expire': 86400,  # 1 days
        'type': 'file',
        'data_dir': '/tmp/hdxcache/data',
        'lock_dir': '/tmp/hdxcache/lock',
        'key_length': 250
    }
})


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


@bcache.cache_region('hdx_memory_cache', 'cached_grp_list')
def cached_group_list():
    log.info("Creating cache for group list")
    groups = tk.get_action('group_list')({'user': '127.0.0.1'}, {'all_fields': True, 'include_extras': True})
    for group in groups:
        activity_level = next(
            (extra.get('value') for extra in group.get('extras') if extra.get('key') == 'activity_level'),
            None
        )
        group['activity_level'] = activity_level
    return sorted(groups, key=lambda k: strip_accents(k['display_name']))


def invalidate_cached_group_list():
    log.info("Invalidating cache for group list")
    bcache.region_invalidate(cached_group_list, 'hdx_memory_cache', 'cached_grp_list')


def filter_focus_countries(group_package_stuff):
    focus_group_package_stuff = []
    for grp_dict in group_package_stuff:
        if grp_dict['display_name'] in focus_countries.FOCUS_COUNTRIES:
            focus_group_package_stuff.append(grp_dict)

    return focus_group_package_stuff


@bcache.cache_region('hdx_memory_cache', 'focus_countries_list')
def cached_get_group_package_stuff():
    log.info("Creating cache for focus countries")
    group_package_stuff = tk.get_action('cached_group_list')()
    focus_group_package_stuff = filter_focus_countries(group_package_stuff)

    return sorted(focus_group_package_stuff, key=lambda k: k['title'])


def invalidate_cached_get_group_package_stuff():
    log.info("Invalidating cache for focus countries")
    bcache.region_invalidate(cached_get_group_package_stuff, 'hdx_memory_cache', 'focus_countries_list')


def invalidate_group_caches():
    for invalidate_func in group_invalidation_functions:
        invalidate_func()


group_invalidation_functions = [invalidate_cached_group_list, invalidate_cached_get_group_package_stuff]
