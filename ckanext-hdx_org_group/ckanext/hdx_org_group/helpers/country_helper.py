import ckan
import logging
import ckan.model as model
import ckan.lib.base as base
import ckan.plugins.toolkit as tk
import ckanext.hdx_org_group.helpers.caching as caching
# import ckanext.hdx_package.helpers.screenshot as screenshot

from ckanext.hdx_org_group.controller_logic.group_search_logic import GroupSearchLogic
import ckan.lib.helpers as h
from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING
from ckan.common import config

c = tk.c
render = tk.render
abort = tk.abort
NotFound = NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
get_action = tk.get_action
request = tk.request
_ = tk._
log = logging.getLogger(__name__)

lookup_group_plugin = ckan.lib.plugins.lookup_group_plugin
GROUP_TYPES = ['group']

# def get_latest_cod_dataset(country_name):
#     context = {'model': model, 'session': model.Session,
#                'user': c.user or c.author, 'for_view': True,
#                'auth_user_obj': c.userobj}
#
#     search = search_controller.HDXSearchController()
#
#     fq = 'groups:"{}" tags:cod +dataset_type:dataset'.format(country_name)
#     query_result = search._performing_search(u'', fq, ['organization', 'tags'], 1, 1, DEFAULT_SORTING, None,
#                                              None, context)
#
#     return next(iter(query_result.get('results', [])), None)


def _sort_datasets_by_is_good(data_completeness):
    categories = data_completeness.get("categories")
    for cat in categories:
        if cat.get("data_series"):
            for ds in cat.get("data_series"):
                datasets_list = ds.get("datasets")
                if datasets_list:
                    datasets_sorted_list = sorted(datasets_list, key=lambda item: item['is_good'] == False)
                    ds['datasets'] = datasets_sorted_list

    return data_completeness


def country_topline(id):
    log.info("The id of the page is: " + id)

    country_dict = get_country(id)
    top_line_data_list = caching.cached_topline_numbers(id)
    template_data = {
        'data': {
            'country_dict': country_dict,
            'widgets': {
                'top_line_data_list': top_line_data_list
            }
        }
    }
    return base.render('country/country_topline.html', extra_vars=template_data)

    # return country_read(id=id, get_only_toplines=True)


def get_template_data(country_dict, not_filtered_facet_info):

    # latest_cod_dataset = get_latest_cod_dataset(country_dict.get('name'))

    follower_count = get_action('group_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': country_dict['id']}
    )

    top_line_data_list = caching.cached_topline_numbers(country_dict['id'], country_dict.get('activity_level'))

    organization_list = _get_org_list_for_menu_from_facets(not_filtered_facet_info)
    # f_event_list = _get_event_list_for_featured(country_dict['id'])
    # f_thumbnail_list = _get_thumbnail_list_for_featured(country_dict, f_event_list,
    #                                                     not_filtered_facet_info.get('results'),
    #                                                     latest_cod_dataset)
    # f_organization_list = _get_org_list_for_featured_from_facets(not_filtered_facet_info)
    # f_tag_list = _get_tag_list_for_featured_from_facets(not_filtered_facet_info)

    data_completness = _get_data_completeness(country_dict.get('name')) \
        if country_dict.get('data_completeness') == 'active' else None

    if data_completness:
        data_completness = _sort_datasets_by_is_good(data_completness)

    template_data = {
        'data': {
            'country_dict': country_dict,
            'stats_section': {
                'organization_list': organization_list,
                'num_of_organizations':
                    len(not_filtered_facet_info.get('facets', {}).get('organization', {}).get('items', [])),
                'num_of_cods': not_filtered_facet_info.get('num_of_cods', 0),
                'num_of_datasets': not_filtered_facet_info.get('num_of_total_items'),
                'num_of_followers': follower_count
            },
            'widgets': {
                'top_line_data_list': top_line_data_list,
                # 'chart_data_list': chart_data_list,
                'show': len(top_line_data_list) > 0  # or len(chart_data_list) > 0
            },
            # 'featured_section': {
            #     'thumbnail_list': f_thumbnail_list,
            #     'event_list': f_event_list,
            #     'organization_list': f_organization_list[:5],
            #     'tag_list': f_tag_list[:10],
            #     'show': len(f_organization_list) > 0 or len(f_tag_list) > 0
            # },
            'data_completness': data_completness,

        },
        'errors': None,
        'error_summary': '',
    }

    return template_data


def _get_org_list_for_menu_from_facets(full_facet_info):
    org_list = [
        {
            'display_name': org.get('display_name'),
            'name': org.get('name'),
            'url': h.url_for('organization_read', id=org.get('name'))
        }
        for org in full_facet_info.get('facets', {}).get('organization', {}).get('items', [])
    ]
    return org_list


# def _get_org_list_for_featured_from_facets(full_facet_info):
#     org_list = [
#         {
#             'display_name': org.get('display_name'),
#             'name': org.get('name'),
#             'count': org.get('count'),
#             'url': h.url_for('organization_read', id=org.get('name'))
#         }
#         for org in full_facet_info.get('facets', {}).get('organization', {}).get('items', []) if
#         org.get('name') != 'hdx'
#     ]
#     result = sorted(org_list, key=itemgetter('count'), reverse=True)
#     return result


# def _get_tag_list_for_featured_from_facets(full_facet_info):
#     tag_list = [
#         {
#             'display_name': tag.get('display_name'),
#             'count': tag.get('count'),
#             'name': tag.get('name'),
#             'url': '?tags=' + tag.get('name') + '#dataset-filter-start'
#         }
#         for tag in full_facet_info.get('facets', {}).get('vocab_Topics', {}).get('items', [])
#     ]
#     tag_list_by_count = sorted(tag_list, key=itemgetter('count'), reverse=True)
#     return tag_list_by_count


# def _get_thumbnail_list_for_featured(country_dict, event_list, latest_datasets, latest_cod_dataset):
#     '''
#     :param country_dict:
#     :type country_dict: dict
#     :param event_list: if this was already fetched in the controller we can reuse it
#     :type event_list: list
#     :param latest_datasets: a list of the latest updated datasets for the country
#     :type latest_datasets: list
#     :return: list of dicts containing display_name, type and url for the featured thumbnails
#     :rtype: list
#     '''
#
#     cloned_latest_datasets = latest_datasets[:]
#     default_thumbnail_url = '/images/featured_locs_placeholder1.png'
#     thumbnail_list = [None, None]
#     if event_list:
#         thumbnail_list[0] = __event_as_thumbnail_dict(event_list[0], default_thumbnail_url)
#     elif cloned_latest_datasets:
#         thumbnail_list[0] = __dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
#         del cloned_latest_datasets[0]
#     if latest_cod_dataset:
#         cod_thumbnail_url = screenshot.create_download_link(latest_cod_dataset, default_thumbnail_url)
#         thumbnail_list[1] = __dataset_as_thumbnail_dict(latest_cod_dataset, cod_thumbnail_url, True)
#     elif cloned_latest_datasets:
#         thumbnail_list[1] = __dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
#         del cloned_latest_datasets[0]
#
#     if thumbnail_list[0] and thumbnail_list[1] \
#         and thumbnail_list[0].get('url') == thumbnail_list[1].get('url') and cloned_latest_datasets:
#         thumbnail_list[0] = __dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
#         del cloned_latest_datasets[0]
#
#     # thumbnail_list[0]['thumbnail_url'] = '/images/featured_locs_placeholder1.png'
#     # thumbnail_list[1]['thumbnail_url'] = '/images/featured_locs_placeholder2.png'
#     return thumbnail_list


# def __dataset_as_thumbnail_dict(dataset_dict, thumbnail_url, is_cod=False):
#     return {
#         'display_name': dataset_dict.get('title'),
#         'type': 'COD' if is_cod else 'Dataset',
#         'url': h.url_for('dataset_read', id=dataset_dict.get('name')),
#         'thumbnail_url': thumbnail_url
#     }


# def __event_as_thumbnail_dict(event_dict, thumbnail_url, is_cod=False):
#     return {
#         'display_name': event_dict.get('title'),
#         'type': 'Event',
#         'url': h.url_for('read_event', id=event_dict.get('name')),
#         'thumbnail_url': thumbnail_url
#     }


# def _get_event_list_for_featured(group_id):
#     context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
#     pages_list = get_action('group_page_list')(context, {'id': group_id})
#     return pages_list


def get_country(id):
    context = {'model': model, 'session': model.Session,
               'user': c.user,
               'schema': _db_to_form_schema(group_type='group'),
               'for_view': True}
    try:
        context['include_datasets'] = False
        group_dict = get_action('hdx_light_group_show')(context, {'id': id})
        if group_dict.get('type') not in GROUP_TYPES:
            abort(404, _('Incorrect group type'))
        return group_dict

    except NotFound:
        abort(404, _('Group not found'))
    except NotAuthorized:
        abort(403, _('Unauthorized to read group %s') % id)


def _db_to_form_schema(group_type=None):
    '''This is an interface to manipulate data from the database
    into a format suitable for the form (optional)'''
    return lookup_group_plugin(group_type).db_to_form_schema()


def _get_data_completeness(location_code):
    cached = config.get('hdx.datagrid.prod') == 'true'
    data = None
    if cached:
        data = caching.cached_data_completeness(location_code)
    else:
        data = caching.cached_data_completeness.original(location_code)
    return data


def get_not_filtered_facet_info(country_dict):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'for_view': True,
               'auth_user_obj': c.userobj}

    fq = 'groups:"{}" +dataset_type:dataset'.format(country_dict.get('name'))

    # The facet titles are not really needed in this case but we need to follow the process
    facets = {'vocab_Topics': 'tags', 'organization': 'organization'}
    search_logic = GroupSearchLogic(country_dict.get('name'), None)
    query_result = search_logic._performing_search(u'', fq, list(facets.keys()), 2, 1, DEFAULT_SORTING, None,
                                                   None, context)
    non_filtered_facet_info = search_logic._prepare_facets_info(query_result.get('search_facets'), {}, {},
                                                                facets, query_result.get('count'), u'')

    non_filtered_facet_info['results'] = query_result.get('results', [])

    return non_filtered_facet_info
