'''
Created on April 24, 2015

@author: alexandru-m-g
'''
import json
import logging

import ckan.lib.dictization as d
import ckan.lib.helpers as helpers
import ckan.lib.navl.dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_org_group.dao.widget_data_service as widget_data_service
import ckanext.hdx_org_group.helpers.organization_helper as org_helper
from ckan.common import c
from ckanext.hdx_theme.helpers.caching import cached_make_rest_api_request as cached_make_rest_api_request

_validate = ckan.lib.navl.dictization_functions.validate

log = logging.getLogger(__name__)

config = tk.config
get_action = tk.get_action
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
side_effect_free = tk.side_effect_free

IndicatorAccess = indicator_access.IndicatorAccess


@side_effect_free
def hdx_datasets_for_group(context, data_dict):
    '''
    Returns a paginated list of datasets for a group with 25 items per page.
    Options for sorting are: metadata_modified desc, title_case_insensitive desc, title_case_insensitive asc,
    views_recent desc, score desc ( only useful if query string is specified, should be combined
    with metadata_modified desc )
    :param id: the id of the group for which datasets are requested
    :type id: string
    :param page: page number starting from 1
    :type page: int
    :param sort: the field by which the datasets should be sorted. Defaults to 'metadata_modified desc'
    :type sort: string
    :param q: query string
    :type q: string
    :param type: 'all', 'indicators', 'datasets'. Defaults to 'all'
    :type q: string
    :return:
    '''

    skipped_keys = ['q', 'id', 'sort', 'type', 'page']

    id = _get_or_bust(data_dict, "id")

    limit = 25

    sort_option = data_dict.get('sort', 'metadata_modified desc')

    page = int(data_dict.get('page', 1))
    new_data_dict = {'sort': sort_option,
                     'rows': limit,
                     'start': (page - 1) * limit,
                     }
    type = data_dict.get('type', None)
    if type == 'indicators':
        new_data_dict['ext_indicator'] = u'1'
    elif type == 'datasets':
        new_data_dict['ext_indicator'] = u'0'

    search_param_list = [
        key + ":" + value for key, value in data_dict.iteritems() if key not in skipped_keys]
    search_param_list.append(u'groups:{}'.format(id))

    if search_param_list != None:
        new_data_dict['fq'] = " ".join(
            search_param_list) + ' +dataset_type:dataset'

    if data_dict.get('q', None):
        new_data_dict['q'] = data_dict['q']

    query = get_action("package_search")(context, new_data_dict)

    return query


@side_effect_free
def hdx_topline_num_for_group(context, data_dict):
    '''
    :param id: the id of the group for which top line numbers are requested
    :type id: string
    :return: a dict of top line numbers. Please note that depending on the selected group the source
    of the data ( either the datastore or CPS/indicators ) might be different. The data will have some fields
     that are specific to the source.
    '''
    id = _get_or_bust(data_dict, "id")
    grp_result = get_group(id)
    group_info = grp_result.get('group_info')
    # custom_dict = grp_result.get('custom_dict')

    # datastore_id = custom_dict.get('topline_resource', None)

    common_format = data_dict.get('common_format', True) not in ['false', '0']  # type: bool

    # if group_info.get('custom_loc', False) and datastore_id:
    #     # source is datastore
    #     crisis_data_access = location_data_access.LocationDataAccess(datastore_id)
    #     crisis_data_access.fetch_data(context)
    #     top_line_items = crisis_data_access.get_top_line_items()
    #     for item in top_line_items:
    #         item['source_system'] = 'datastore'
    #         del item['units']
    if group_info.get('activity_level') == 'active':
        top_line_items = __get_toplines_for_active_country(group_info, common_format)
    else:
        top_line_items = __get_toplines_for_standard_country(group_info, common_format)

    return top_line_items


def __get_toplines_for_active_country(group_info, common_format):
    '''
    :param group_info:
    :type group_info: dict
    :param common_format:
    :type common_format: bool
    :return:
    :rtype: list
    '''

    # source is rw
    top_line_data_list = widget_data_service.build_widget_data_access(group_info).get_dataset_results()
    if common_format:
        def _parse_integer_value(item):
            try:
                value = float(item.get('value', ''))
            except:
                value = None
            return value

        top_line_items = [
            {
                'source_system': 'reliefweb crisis app',
                'code': item.get('indicatorTypeCode', ''),
                'title': item.get('indicatorTypeName', ''),
                'source_link': item.get('datasetLink', ''),
                'source': item.get('sourceName', ''),
                'value': _parse_integer_value(item),
                'latest_date': item.get('time', ''),
                'units': item.get('units', )
            }
            for item in top_line_data_list
        ]
    else:
        top_line_items = top_line_data_list
    return top_line_items


def __get_toplines_for_standard_country(group_info, common_format):
    '''
    :param group_info:
    :type group_info: dict
    :param common_format:
    :type common_format: bool
    :return:
    :rtype: list
    '''
    # source is configured in 'hdx.locations.toplines_url'
    # ckan_site_url = config.get('ckan.site_url')
    raw_top_line_items = widget_data_service.build_widget_data_access(group_info).get_dataset_results()
    # ckan_data = indicator_dao.fetch_indicator_data_from_ckan()
    top_line_items = []
    if common_format:
        for item in raw_top_line_items:
            code = item.get('indicatorTypeCode', '')
            title = item.get('indicatorTypeName', '')
            new_item = {
                'source_system': 'cps',
                'code': code or title,
                'title': title or code,
                # 'source_link': ckan_site_url + ckan_data.get(code, {}).get('datasetLink', ''),
                'source': item.get('sourceName', ''),
                'value': item.get('value', ''),
                'latest_date': item.get('time', ''),
                'units': item.get('unitName', )
            }
            top_line_items.append(new_item)
    else:
        top_line_items = raw_top_line_items
    return top_line_items


@side_effect_free
def hdx_light_group_show(context, data_dict):
    '''
    Return a lightweight ( less resource intensive,faster but without datasets ) version of the group details
    :param id: the id of the group for which top line numbers are requested
    :type id: string
    '''

    id = _get_or_bust(data_dict, "id")
    group_dict = {}
    group = model.Group.get(id)
    if not group:
        raise NotFound
    if group.state == 'deleted' and (not c.userobj or not c.userobj.sysadmin):
        raise NotFound
    # group_dict['group'] = group
    group_dict['id'] = group.id
    group_dict['name'] = group.name
    group_dict['image_url'] = group.image_url
    group_dict['display_name'] = group_dict['title'] = group.title
    group_dict['description'] = group.description
    # group_dict['revision_id'] = group.revision_id
    group_dict['state'] = group.state
    group_dict['created'] = group.created
    group_dict['type'] = group.type

    result_list = []
    for name, extra in group._extras.items():
        dictized = d.table_dictize(extra, context)
        if not extra.state == 'active':
            continue
        value = dictized["value"]
        result_list.append(dictized)

        # Keeping the above for backwards compatibility
        group_dict[name] = dictized["value"]

    group_dict['extras'] = sorted(result_list, key=lambda x: x["key"])
    return group_dict


def get_group(id):
    context = {'model': model, 'session': model.Session,
               'include_datasets': False,
               'for_view': True}
    data_dict = {'id': id}

    group_info = get_action('hdx_light_group_show')(context, data_dict)

    extras_dict = {item['key']: item['value'] for item in group_info.get('extras', {})}
    json_string = extras_dict.get('customization', None)
    if json_string:
        custom_dict = json.loads(json_string)
    else:
        custom_dict = {}

    return {'group_info': group_info, 'custom_dict': custom_dict}


@side_effect_free
def hdx_trigger_screencap(context, data_dict):
    cfg = context['cfg']
    file_path = context['file_path']
    # checking if user is sysadmin
    sysadmin = False
    if data_dict.get('reset_thumbnails', 'false') == 'true':
        try:
            _check_access('hdx_trigger_screencap', context, data_dict)
            sysadmin = True
        except:
            return False
    if not sysadmin and not context.get('reset', False):
        return False
    if not cfg['screen_cap_asset_selector']:  # If there's no selector set just don't bother
        return False

    return org_helper.hdx_capturejs(config['ckan.site_url'] + helpers.url_for('organization_read', id=cfg['org_name']),
                                    file_path, cfg['screen_cap_asset_selector'])


@side_effect_free
def hdx_get_locations_info_from_rw(context, data_dict):
    try:
        url = data_dict.get('rw_url')
        if url:
            return cached_make_rest_api_request(url)
        return None
    except:
        log.error("RW file was not found or can not be accessed")
        return None


@side_effect_free
def hdx_organization_follower_list(context, data_dict):
    '''Return the list of users that are following the given organization.

    :param id: the id or name of the organization
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('hdx_organization_follower_list', context, data_dict)
    context['keep_email'] = True
    return _follower_list(
        context, data_dict,
        ckan.logic.schema.default_follow_group_schema(),
        context['model'].UserFollowingGroup)


def _follower_list(context, data_dict, default_schema, FollowerClass):
    schema = context.get('schema', default_schema)
    data_dict, errors = _validate(data_dict, schema, context)
    if errors:
        raise ValidationError(errors)

    # Get the list of Follower objects.
    model = context['model']
    object_id = data_dict.get('id')
    followers = FollowerClass.follower_list(object_id)

    # Convert the list of Follower objects to a list of User objects.
    users = [model.User.get(follower.follower_id) for follower in followers]
    users = [user for user in users if user is not None]

    # Dictize the list of User objects.
    return _user_list_dictize(users, context)


def _user_list_dictize(obj_list, context,
                       sort_key=lambda x: x['name'], reverse=False):
    import ckan.lib.dictization.model_dictize as model_dictize
    result_list = []

    for obj in obj_list:
        user_dict = model_dictize.user_dictize(obj, context)
        user_dict.pop('reset_key', None)
        user_dict.pop('apikey', None)
        # user_dict.pop('email', None)
        result_list.append(user_dict)
    return sorted(result_list, key=sort_key, reverse=reverse)
