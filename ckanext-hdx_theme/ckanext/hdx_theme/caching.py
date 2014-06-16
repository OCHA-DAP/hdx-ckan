'''
Created on Jun 2, 2014

@author: alexandru-m-g
'''

import ckan.plugins.toolkit as tk
import beaker.cache as bcache

## Quick patch to fix CKAN 2.2 errors
import logging
log = logging.getLogger('ckan.logic')
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.logic.action.get as ckan_get
## end patch imports

import ckanext.hdx_theme.country_list_hardcoded as focus_countries


bcache.cache_regions.update({
        'hdx_memory_cache':{
            'expire': 172800, # 2 days
            'type':'memory',
            'key_length': 250
        }
    })


@bcache.cache_region('hdx_memory_cache', 'cached_group_list')
def cached_group_list(context):
    groups  = group_list(context, data_dict={'all_fields': True})
    return groups


def invalidate_cached_group_list():
        bcache.region_invalidate(cached_group_list, 'hdx_memory_cache', 'cached_group_list')
        


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

## Quick patch to fix CKAN 2.2 errors
def group_list(context, data_dict):
    '''Return a list of the names of the site's groups.

    :param order_by: the field to sort the list by, must be ``'name'`` or
      ``'packages'`` (optional, default: ``'name'``) Deprecated use sort.
    :type order_by: string
    :param sort: sorting of the search results.  Optional.  Default:
        "name asc" string of field name and sort-order. The allowed fields are
        'name' and 'packages'
    :type sort: string
    :param groups: a list of names of the groups to return, if given only
        groups whose names are in this list will be returned (optional)
    :type groups: list of strings
    :param all_fields: return full group dictionaries instead of  just names
        (optional, default: ``False``)
    :type all_fields: boolean

    :rtype: list of strings

    '''
    #_check_access('group_list', context, data_dict)
    data_dict['type'] = 'group'
    return _group_or_org_list(context, data_dict)


def _group_or_org_list(context, data_dict, is_org=False):

    model = context['model']
    #user = context['user'] <--- This is the problem right here, which is stupid since this function never even uses this
    api = context.get('api_version')
    groups = data_dict.get('groups')
    ref_group_by = 'id' if api == 2 else 'name'

    sort = data_dict.get('sort', 'name')
    q = data_dict.get('q')

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by
    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() == 'packages':
        sort = 'packages desc'

    sort_info = ckan_get._unpick_search(sort,
                               allowed_fields=['name', 'packages'],
                               total=1)

    all_fields = data_dict.get('all_fields', None)


    query = model.Session.query(model.Group).join(model.GroupRevision)
    query = query.filter(model.GroupRevision.state=='active')
    query = query.filter(model.GroupRevision.current==True)
    if groups:
        query = query.filter(model.GroupRevision.name.in_(groups))
    if q:
        q = u'%{0}%'.format(q)
        query = query.filter(_or_(
            model.GroupRevision.name.ilike(q),
            model.GroupRevision.title.ilike(q),
            model.GroupRevision.description.ilike(q),
        ))


    query = query.filter(model.GroupRevision.is_organization==is_org)

    groups = query.all()
    group_list = model_dictize.group_list_dictize(groups, context,
                                                  lambda x:x[sort_info[0][0]],
                                                  sort_info[0][1] == 'desc')

    if not all_fields:
        group_list = [group[ref_group_by] for group in group_list]

    return group_list
## End patch functions