import json
import logging
import requests

from six.moves.urllib.parse import urlencode

import ckan.lib.munge as munge
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_search.helpers.qa_data as qa_data

log = logging.getLogger(__name__)

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


@side_effect_free
def hdx_qa_questions_list(context, data_dict):
    return qa_data.questions_list



def _set_resource_proxy_url(context, data_dict, resource_dict, sheet=None):
    proxy_data_preview_url = config.get('hdx.hxlproxy.url') + '/api/data-preview.csv'
    url = get_action("hdx_get_s3_link_for_resource")(context, {"id": resource_dict.get("id")})
    params_dict = {'url': url.get('s3_url', resource_dict.get("download_url") or resource_dict.get("hdx_rel_url"))}
    if sheet:
        params_dict['sheet'] = sheet
    params = urlencode(params_dict)
    # {'sheet': sheet, 'url': resource_dict.get("download_url") or resource_dict.get("hdx_rel_url")})
    return proxy_data_preview_url + '?{params}'.format(params=params)


def _get_resource_s3_path(resource_dict):
    download_url = resource_dict.get("download_url") or resource_dict.get("hdx_rel_url")
    if "download/" in download_url:
        url = download_url.split("download/")[1]
    else:
        url = resource_dict.get("name")
    munged_resource_name = munge.munge_filename(url)
    return munged_resource_name

