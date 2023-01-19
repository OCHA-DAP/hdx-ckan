import ckan.plugins.toolkit as tk
import ckanext.hdx_user_extra.model as ue_model
from ckanext.hdx_theme.helpers.exception import BaseHdxException
from ckanext.hdx_users.helpers.helpers import find_user_id

get_action = tk.get_action


class WrongPermissionNameException(BaseHdxException):
    pass


class Permissions(object):

    PERMISSION_MANAGE_CAROUSEL = 'permission_manage_carousel'
    LABEL_PERMISSION_MANAGE_CAROUSEL = 'Manage Carousel and Dataviz Gallery'
    PERMISSION_MANAGE_COD = 'permission_manage_cod'
    LABEL_PERMISSION_MANAGE_COD = 'Manage COD'
    PERMISSION_MANAGE_CRISIS = 'permission_manage_crisis'
    LABEL_PERMISSION_MANAGE_CRISIS = 'Manage Events/Crisis'
    PERMISSION_VIEW_REQUEST_DATA = 'permission_view_request_data'
    LABEL_PERMISSION_VIEW_REQUEST_DATA = 'View Request Data Dashboard'
    PERMISSION_MANAGE_QUICK_LINKS = 'permission_manage_quick_links'
    LABEL_PERMISSION_MANAGE_QUICK_LINKS = 'Manage Quick Links'

    # These are tasks that a bot needs to trigger: HDX daily stats, api token expiry emails.
    # Note that this permission shouldn't allow for any change to be done to HDX
    PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS = 'permission_manage_basic_scheduled_tasks'
    LABEL_PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS = 'Manage Basic Scheduled Tasks'

    ALL_PERMISSIONS = [
        PERMISSION_MANAGE_CAROUSEL,
        PERMISSION_MANAGE_COD,
        PERMISSION_MANAGE_CRISIS,
        PERMISSION_VIEW_REQUEST_DATA,
        PERMISSION_MANAGE_QUICK_LINKS,
        PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS,
    ]

    ALL_PERMISSIONS_LABELS_DICT = {
        PERMISSION_MANAGE_CAROUSEL: LABEL_PERMISSION_MANAGE_CAROUSEL,
        PERMISSION_MANAGE_COD: LABEL_PERMISSION_MANAGE_COD,
        PERMISSION_MANAGE_CRISIS: LABEL_PERMISSION_MANAGE_CRISIS,
        PERMISSION_VIEW_REQUEST_DATA: LABEL_PERMISSION_VIEW_REQUEST_DATA,
        PERMISSION_MANAGE_QUICK_LINKS: LABEL_PERMISSION_MANAGE_QUICK_LINKS,
        PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS: LABEL_PERMISSION_MANAGE_BASIC_SCHEDULED_TASKS,
    }

    USER_EXTRA_FIELD = 'hdx_permissions'

    def __init__(self, target_username_or_id):
        super(Permissions, self).__init__()
        self.target_user_id = find_user_id(target_username_or_id)

    def set_permissions(self, context, permissions_list):
        '''
        :param context:
        :type context: dict
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
        return self.has_permissions([permission])

    def has_permissions(self, permissions, all=True):
        '''

        :param permissions: list of permissions to be checked
        :type permissions: list of str
        :param all: True if all permissions should be in the list, False if any permission is in the list
        :type all: bool
        :return:
        :rtype: bool
        '''
        for p in permissions:
            self._check_existing_permission(p)
        permission_set = set(permissions)

        existing_permission_list = self.get_permission_list()
        existing_permission_set = set(existing_permission_list)

        if all:
            return permission_set.issubset(existing_permission_set)

        return not permission_set.isdisjoint(existing_permission_set)

    def _check_existing_permission(self, permission):
        if permission not in Permissions.ALL_PERMISSIONS:
            raise WrongPermissionNameException('{} is not a valid permission name'.format(permission))

