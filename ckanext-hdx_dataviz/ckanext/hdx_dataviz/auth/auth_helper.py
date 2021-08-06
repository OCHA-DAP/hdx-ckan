import ckan.plugins.toolkit as tk

import ckanext.hdx_dataviz.helpers.helpers as h

h = tk.h


def _is_editor():
    '''
    Check if the current user is at least editor in some organization
    :return: True if user is at least editor in some org
    :rtype: bool
    '''
    organizations = h.organizations_available('create_dataset')
    if not organizations:
        organizations = h.organizations_available('admin')

    if organizations:
        return True
    return False


# showcase
def showcase_create(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_update(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_delete(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_package_association_create(context, data_dict):
    return {'success': _is_editor()}


# showcase
def showcase_package_association_delete(context, data_dict):
    return {'success': _is_editor()}


