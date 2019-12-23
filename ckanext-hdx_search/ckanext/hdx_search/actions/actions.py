import logging

import ckan.logic as logic
import ckan.model as model
import ckanext.hdx_search.helpers.qa_data as qa_data


log = logging.getLogger(__name__)

get_action = logic.get_action
_check_access = logic.check_access


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
            except Exception, e:
                log.info('Package id' + pkg_dict.get('id') + ' not found')
                log.exception(e)
    return pkg_dict_list


# code adapted from ckanext-showcase.../logic/action/get.py:94
def hdx_get_package_showcase_id_list(context, data_dict):
    import ckan.plugins.toolkit as toolkit
    from ckan.lib.navl.dictization_functions import validate
    from ckanext.showcase.logic.schema import (package_showcase_list_schema)
    from ckanext.showcase.model import ShowcasePackageAssociation

    toolkit.check_access('ckanext_package_showcase_list', context, data_dict)
    # validate the incoming data_dict
    validated_data_dict, errors = validate(data_dict, package_showcase_list_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    # get a list of showcase ids associated with the package id
    showcase_id_list = ShowcasePackageAssociation.get_showcase_ids_for_package(validated_data_dict['package_id'])
    return showcase_id_list

@logic.side_effect_free
def hdx_qa_questions_list(context, data_dict):
    return qa_data.questions_list

@logic.side_effect_free
def hdx_qa_sdcmicro_run(context, data_dict):
    '''
    Add sdc micro flag "running" to resource
    Post to aws endpoint to start the sdc micro check
    :param data_dict: dictionary containg parameters
    :type data_dict: dict
    Parameters from data_dict
    :param dataset_id: the id or name of the dataset
    :type dataset_id: str
    :param resource_id: the id or name of the resource
    :type resource_id: str
    :param data_columns_list: list with data columns
    :param weight_column: the weight column
    :param columns_type_list: list with types for each column - text, double, numeric, date
    :param sheet: in case of excel/xlsx/xls we need the sheet id (0-n)
    :param skip_rows: how many rows to skip until data
    :return: True or False or data_dict
    :rtype: bool
    '''
    # resource_patch to mark sdc micro flag in "running" mode
    # post to aws endpoint to start the sdc micro (sdc micro will have to mark the flag and upload the result)
    _check_access('hdx_qa_sdcmicro_run', context, {})
    return data_dict

@logic.side_effect_free
def hdx_qa_pii_run(context, data_dict):
    '''
    Add sdc micro flag "running" to resource
    Post to aws endpoint to start the sdc micro check
    :param data_dict: dictionary containg parameters
    :type data_dict: dict
    Parameters from data_dict
    :param dataset_id: the id or name of the dataset
    :type dataset_id: str
    :param resource_id: the id or name of the resource
    :type resource_id: str
    :return: True or False or data_dict
    :rtype: bool
    '''
    # resource_patch to mark sdc micro flag in "running" mode
    # post to aws endpoint to start the sdc micro (sdc micro will have to mark the flag and upload the result)
    _check_access('hdx_qa_pii_run', context, {})
    return data_dict
