import json
import logging
import requests

from six.moves.urllib.parse import urlencode

import ckan.lib.munge as munge
import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)
_get_or_bust = tk.get_or_bust
get_action = tk.get_action
_check_access = tk.check_access
side_effect_free = tk.side_effect_free
config = tk.config
ValidationError = tk.ValidationError


def populate_related_items_count(context, data_dict):
    pkg_dict_list = data_dict.get('pkg_dict_list', {})
    for pkg_dict in pkg_dict_list:
        pkg = model.Package.get(pkg_dict['id'])
        _check_access('package_show', context, pkg_dict)
        # rel_items = get_action('related_list')(context, {'id': pkg_dict['id']})
        pkg_dict['related_count'] = 0
    return pkg_dict_list


def populate_showcase_items_count(context, data_dict):
    pkg_dict_list = data_dict.get('pkg_dict_list', {})
    for pkg_dict in pkg_dict_list:
        pkg = model.Package.get(pkg_dict['id'])
        # _check_access('package_show', context, pkg_dict)
        if pkg:
            try:
                # showcase_items = get_action('ckanext_package_showcase_list')(context, {'package_id': pkg_dict.get('id')})
                _check_access('package_show', context, pkg_dict)
                pkg_dict['showcase_count'] = len(
                    hdx_get_package_showcase_id_list(context, {'package_id': pkg_dict.get('id')}))
            except Exception as e:
                log.info('Package id' + pkg_dict.get('id') + ' not found')
                log.exception(e)
    return pkg_dict_list


# code adapted from ckanext-showcase.../logic/action/get.py:94
def hdx_get_package_showcase_id_list(context, data_dict):
    from ckan.lib.navl.dictization_functions import validate
    from ckanext.showcase.logic.schema import (package_showcase_list_schema)
    from ckanext.showcase.model import ShowcasePackageAssociation

    _check_access('ckanext_package_showcase_list', context, data_dict)
    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict, package_showcase_list_schema(), context)

    if errors:
        raise ValidationError(errors)

    # get a list of showcase ids associated with the package id
    showcase_id_list = ShowcasePackageAssociation.get_showcase_ids_for_package(validated_data_dict['package_id'])
    return showcase_id_list

# @tk.side_effect_free
# def hdx_search_by_object(context, data_dict):
#     _check_access('package_search', context, data_dict)
#     object_type = _get_or_bust(data_dict, 'object_type')
#     object_id = _get_or_bust(data_dict, 'object_id')
#     dataset_ids_list = None
#
#     if object_type == 'organization':
#         # Handle organization case
#         org_dict = get_action('hdx_light_group_show')(context, {'id': object_id})
#         org_name = org_dict.get('name')
#         search_data_dict = {
#             'fq_list': [f'organization:"{org_name}"', '-extras_archived:"true"', '+dataset_type:dataset'],
#             'fl':['id'],
#             'rows': 1000,
#             'start':0,
#         }
#         dataset_ids_list = get_action('package_search')(context, search_data_dict)
#     elif object_type == 'group':
#         # Handle group case
#         pass
#     elif object_type == 'crisis':
#         # Handle crisis case
#         pass
#     else:
#         raise ValueError(f'Unsupported object_type: {object_type}')
#
#     return dataset_ids_list

@tk.side_effect_free
def hdx_search_by_object(context, data_dict):
    _check_access('package_search', context, data_dict)
    object_type = _get_or_bust(data_dict, 'object_type')
    object_id = _get_or_bust(data_dict, 'object_id')
    dataset_ids_list = []

    # get by object_type
    if object_type == 'organization':
        object_dict = get_action('hdx_light_group_show')(context, {'id': object_id})
        object_name = object_dict.get('name')
        fq_filter = f'organization:"{object_name}"'
    elif object_type == 'group':
        object_dict = get_action('hdx_light_group_show')(context, {'id': object_id})
        object_name = object_dict.get('name')
        fq_filter = f'groups:"{object_name}"'
    elif object_type == 'crisis':
        pass
        # object_dict = get_action('crisis_show')(context, {'id': object_id})
        # object_name = object_dict.get('name')
        # fq_filter = f'crisis:"{object_name}"'
    else:
        raise ValueError(f'Unsupported object_type: {object_type}')

    # Loop for pagination
    start = 0
    rows = 1000

    while True:
        search_data_dict = {
            'fq_list': [fq_filter, '-extras_archived:"true"', '+dataset_type:dataset'],
            'fl': ['id'],
            'rows': rows,
            'start': start,
        }

        result = get_action('package_search')(context, search_data_dict)
        results_page = result.get('results', [])
        dataset_ids_list.extend(results_page)

        if len(results_page) < rows:
            break  # last page
        start += rows

    return dataset_ids_list
