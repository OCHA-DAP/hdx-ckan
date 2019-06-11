import ckan.model.user as user_model
import ckan.plugins.toolkit as tk

from ckan.logic import NotFound

import ckanext.hdx_user_extra.model as ue_model


get_action = tk.get_action


class WrongPermissionNameException(Exception):
    def __init__(self, message, exceptions=[]):

        super(Exception, self).__init__(message)

        self.errors = exceptions


class Permissions(object):

    PERMISSION_MANAGE_CAROUSEL = 'permission_manage_carousel'
    PERMISSION_MANAGE_CAROUSEL_LABEL = 'Manage Carousel'
    PERMISSION_MANAGE_COD = 'permission_manage_cod'
    PERMISSION_MANAGE_COD_LABEL = 'Manage COD'
    PERMISSION_MANAGE_CRISIS = 'permission_manage_crisis'
    PERMISSION_MANAGE_CRISIS_LABEL = 'Manage Events/Crisis'
    PERMISSION_VIEW_REQUEST_DATA = 'permission_view_request_data'
    PERMISSION_VIEW_REQUEST_DATA_LABEL = 'View Request Data Dashboard'

    ALL_PERMISSIONS = [
        PERMISSION_MANAGE_CAROUSEL,
        PERMISSION_MANAGE_COD,
        PERMISSION_MANAGE_CRISIS,
        PERMISSION_VIEW_REQUEST_DATA
    ]

    ALL_PERMISSIONS_DICT = {
        PERMISSION_MANAGE_CAROUSEL: PERMISSION_MANAGE_CAROUSEL_LABEL,
        PERMISSION_MANAGE_COD: PERMISSION_MANAGE_COD_LABEL,
        PERMISSION_MANAGE_CRISIS: PERMISSION_MANAGE_CRISIS_LABEL,
        PERMISSION_VIEW_REQUEST_DATA: PERMISSION_VIEW_REQUEST_DATA_LABEL
    }

    USER_EXTRA_FIELD = 'hdx_permissions'

    def __init__(self, target_username_or_id):
        super(Permissions, self).__init__()
        self.target_username_or_id = target_username_or_id
        self.target_user_id = self._find_user_id()

    def set_permissions(self, context, permissions_list):
        '''
        :param context:
        :type context: dict
        :param user_name_or_id:
        :type user_name_or_id: str
        :param permissions_list:
        :type permissions_list: list of str
        '''

        for permission in permissions_list:
            self._check_existing_permission(permission)

        permission_extra_exists = self.has_permissions_property()

        value = ' '.join(permissions_list) if permissions_list else ''

        data_dict = {
            'user_id': self.target_user_id,
            'extras': [
                {
                    'key': Permissions.USER_EXTRA_FIELD,
                    'value': value,
                    'new_value': value
                }
            ]
        }
        action = 'user_extra_update' if permission_extra_exists else 'user_extra_create'
        get_action(action)(context, data_dict)

    def get_permission_list(self):
        if self.target_user_id:
            user_extra = ue_model.UserExtra.get(self.target_user_id, Permissions.USER_EXTRA_FIELD)
            if user_extra and user_extra.value:
                permission_list = user_extra.value.split(' ')
                return permission_list
        return []

    def has_permissions_property(self):
        if self.target_user_id:
            user_extra = ue_model.UserExtra.get(self.target_user_id, Permissions.USER_EXTRA_FIELD)
            if user_extra:
                return True
        return False

    def has_permission(self, permission):
        self._check_existing_permission(permission)
        permission_list = self.get_permission_list()
        return permission in permission_list

    def _find_user_id(self):
        user = user_model.User.get(self.target_username_or_id)
        if not user:
            raise NotFound()
        user_id = user.id
        return user_id

    def _check_existing_permission(self, permission):
        if permission not in Permissions.ALL_PERMISSIONS:
            raise WrongPermissionNameException('{} is not a valid permission name'.format(permission))

