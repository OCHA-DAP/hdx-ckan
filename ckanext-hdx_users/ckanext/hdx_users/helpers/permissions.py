import ckan.model.user as user_model
import ckan.plugins.toolkit as tk

from ckan.logic import NotFound

import ckanext.hdx_user_extra.model as ue_model

MANAGE_CAROUSEL_PERMISSION = 'manage_carousel_permission'
MANAGE_COD_PERMISSION = 'manage_cod_permission'
MANAGE_CRISIS_PERMISSION = 'manage_crisis_permission'
VIEW_REQUEST_DATA_PERMISSION = 'view_request_data_permission'

ALL_PERMISSIONS = [
    MANAGE_CAROUSEL_PERMISSION,
    MANAGE_COD_PERMISSION,
    MANAGE_CRISIS_PERMISSION,
    VIEW_REQUEST_DATA_PERMISSION
]

USER_EXTRA_FIELD = 'hdx_permissions'


get_action = tk.get_action


class WrongPermissionNameException(Exception):
    def __init__(self, message, exceptions=[]):

        super(Exception, self).__init__(message)

        self.errors = exceptions


def set_permissions(context, user_name_or_id, permissions_list):
    '''
    :param context:
    :type context: dict
    :param user_name_or_id:
    :type user_name_or_id: str
    :param permissions_list:
    :type permissions_list: list of str
    '''

    for permission in permissions_list:
        if permission not in ALL_PERMISSIONS:
            raise WrongPermissionNameException('{} is not a valid permission name'.format(permission))

    user_id = find_user_id(user_name_or_id)

    permission_extra_exists = has_permissions_property(user_id)

    value = ' '.join(permissions_list) if permissions_list else ''

    data_dict = {
        'user_id': user_id,
        'extras': [
            {
                'key': USER_EXTRA_FIELD,
                'value': value,
                'new_value': value
            }
        ]
    }
    action = 'user_extra_update' if permission_extra_exists else 'user_extra_create'
    get_action(action)(context, data_dict)


def get_permission_list(user_name_or_id):
    if user_name_or_id:
        user_id = find_user_id(user_name_or_id)
        user_extra = ue_model.UserExtra.get(user_id, USER_EXTRA_FIELD)
        if user_extra.value:
            permission_list = user_extra.value.split(' ')
            return permission_list
    return []


def has_permissions_property(user_name_or_id):
    if user_name_or_id:
        user_id = find_user_id(user_name_or_id)
        user_extra = ue_model.UserExtra.get(user_id, USER_EXTRA_FIELD)
        if user_extra:
            return True
    return False


def find_user_id(user_name_or_id):
    user = user_model.User.get(user_name_or_id)
    if not user:
        raise NotFound()
    user_id = user.id
    return user_id
