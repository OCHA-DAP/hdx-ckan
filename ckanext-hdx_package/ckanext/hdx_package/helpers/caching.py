'''
Created on Jun 2, 2014

@author: alexandru-m-g
'''

import ckan.plugins.toolkit as tk
import ckan.model as model
import beaker.cache as bcache
import unicodedata

import ckanext.hdx_theme.helpers.country_list_hardcoded as focus_countries


bcache.cache_regions.update({
        'hdx_memory_cache':{
            'expire': 86400, # 1 days
            'type':'memory',
            'key_length': 250
        }
    })

bcache.cache_regions.update({
        'group_names_memory_cache':{
            'expire': 600, # 10 mins
            'type':'memory',
            'key_length': 250
        }
    })


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

@bcache.cache_region('hdx_memory_cache', 'cached_grp_list')
def cached_group_list():
    groups  = tk.get_action('group_list')({'user':'127.0.0.1'},{'all_fields': True})
    return sorted(groups, key=lambda k: strip_accents(k['display_name']))


def invalidate_cached_group_list():
        bcache.region_invalidate(cached_group_list, 'hdx_memory_cache', 'cached_grp_list')
        


def filter_focus_countries(group_package_stuff):
    focus_group_package_stuff = []
    for grp_dict in group_package_stuff:
        if grp_dict['display_name'] in focus_countries.FOCUS_COUNTRIES:
            focus_group_package_stuff.append(grp_dict)

    return focus_group_package_stuff
        
@bcache.cache_region('hdx_memory_cache', 'focus_countries_list')
def cached_get_group_package_stuff():
    group_package_stuff = tk.get_action('cached_group_list')()
    focus_group_package_stuff = filter_focus_countries(group_package_stuff)
    
    return sorted(focus_group_package_stuff, key=lambda k: k['title'])


def invalidate_cached_get_group_package_stuff():
    bcache.region_invalidate(cached_get_group_package_stuff, 'hdx_memory_cache', 'focus_countries_list')    


def invalidate_group_caches():
    for invalidate_func in group_invalidation_functions:
        invalidate_func()
        
group_invalidation_functions = [invalidate_cached_group_list, invalidate_cached_get_group_package_stuff]


@bcache.cache_region('group_names_memory_cache', 'find_display_name_for_group')
def find_display_name_for_group(name):
    '''
    This is used in package_search() to speed up the display name
    :param name: name of the org or group
    :type name: str
    :return: The display_name of the org or group
    :rtype: str
    '''
    group = model.Group.get(name)
    if group:
       return group.display_name
    else:
        return name
