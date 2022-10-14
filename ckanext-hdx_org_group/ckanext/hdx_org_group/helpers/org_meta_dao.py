import json

import ckan.model as model
import ckan.authz as new_authz
import ckan.lib.helpers as ckan_helpers
import ckan.plugins.toolkit as tk


import ckanext.hdx_theme.helpers.helpers as helpers
import ckanext.hdx_org_group.helpers.organization_helper as org_helpers
import ckanext.hdx_package.helpers.membership_data as membership_data

_ = tk._
abort = tk.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
_get_action = tk.get_action
_check_access = tk.check_access


class OrgMetaDao(object):
    def __init__(self, org_id, username, userobj):
        self.id = org_id
        self._username = username
        self._userobj = userobj

        self.datasets_num = 0
        self.org_dict = None
        self.followers_num = 0
        self.members_num = 0
        self.members = None
        self.is_custom = False
        self.customization = None
        self.custom_rect_logo_url = None
        self.custom_sq_logo_url = None
        self.group_message_info = {}

        self.allow_basic_user_info = False
        self.allow_req_membership = False
        self.allow_edit = False
        self.allow_add_dataset = False

        self._fetched_org_dict = False
        self._fetched_dataset_info = False
        self._fetched_followers = False
        self._fetched_members = False
        self._fetched_permissions = False
        self._fetched_group_message_topics = False

    def fetch_all(self):
        if not self._fetched_org_dict:
            self.fetch_org_dict()

        if not self._fetched_dataset_info:
            self.fetch_dataset_info()

        if not self._fetched_followers:
            self.fetch_followers()

        if not self._fetched_members:
            self.fetch_members()

        if not self._fetched_permissions:
            self.fetch_permissions()

        if not self._fetched_group_message_topics:
            self.fetch_group_message_topics()

    def fetch_dataset_info(self):
        self._fetched_dataset_info = True

        context = {
            'model': model,
            'session': model.Session,
            'user': self._username,
        }

        user = self._username
        ignore_capacity_check = False
        is_org_member = (user and
                         new_authz.has_user_permission_for_group_or_org(self.id, user, 'read'))
        if is_org_member:
            ignore_capacity_check = True

        context['ignore_capacity_check'] = ignore_capacity_check

        data_dict = {
            'q': '',
            'fq': 'organization:"{}" +dataset_type:dataset'.format(self.org_dict.get('name')),
            'rows': 1,
            'start': 0,
            'include_private': True if ignore_capacity_check else False,
            'extras': {}
        }

        query = _get_action('package_search')(context, data_dict)

        self.datasets_num = query['count']

    def fetch_org_dict(self):
        self._fetched_org_dict = True

        try:
            context = {
                'model': model,
                'session': model.Session,
                # 'user': c.user or c.author,
                'include_datasets': False,
                'for_view': True
            }
            self.org_dict = _get_action('hdx_light_group_show')(context, {'id': self.id})

            self.__process_custom()
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(403, _('Unauthorized to read group %s') % self.id)

    def fetch_permissions(self):
        self._fetched_permissions = True
        self.allow_basic_user_info = self.__check_access('hdx_basic_user_info')
        self.allow_req_membership = not org_helpers.hdx_user_in_org_or_group(self.org_dict['id'],
                                                                             True) and self.allow_basic_user_info

        self.allow_edit = self.__check_access('organization_update', {'id': self.id})
        self.allow_add_dataset = self.__check_access('package_create',
                                                     {'organization_id': self.id,
                                                      'owner_org': self.id})

    def fetch_followers(self):
        self._fetched_followers = True
        self.followers_num = helpers.get_group_followers(self.id)

    def fetch_members(self):
        self._fetched_members = True
        self.members = _get_action('member_list')(
            {'model': model, 'session': model.Session},
            {'id': self.id, 'object_type': 'user'}
        )
        self.members_num = len(self.members)

    def fetch_group_message_topics(self):
        group_message_topics = membership_data.get_message_groups(self._username, self.id)
        self.group_message_info = {
            'display_group_message': bool(group_message_topics),
            'data': {
                'group_topics': group_message_topics,
                'fullname': self._userobj.display_name if self._userobj else '',
                'email': self._userobj.email if self._userobj else ''

            }
        }

        # small hack because many templates are looking for 'group_message_topics' inside the org_dict
        if self.org_dict:
            self.org_dict['group_message_info'] = self.group_message_info

    def __process_custom(self):
        org_extras = {item.get('key'): item.get('value') for item in self.org_dict.get('extras', []) if item.get('key')}
        self.org_dict['extras'] = org_extras

        self.is_custom = True if org_extras.get('custom_org') else False

        if self.is_custom:
            # Transform the json string representing the customizations to dict
            self.customization = org_extras['customization'] = json.loads(org_extras.get('customization', '').strip())

            self.custom_sq_logo_url = ckan_helpers.url_for('hdx_local_image_server.org_file',
                                                           filename=self.customization.get('image_sq'))
            self.custom_rect_logo_url = ckan_helpers.url_for('hdx_local_image_server.org_file',
                                                             filename=self.customization.get('image_rect'))

    def __check_access(self, action_name, data_dict=None):
        if data_dict is None:
            data_dict = {}

        context = {
            'model': model,
            'user': self._username
        }
        try:
            result = _check_access(action_name, context, data_dict)
        except NotAuthorized:
            result = False

        return result

    def as_dict(self):
        return self.__dict__
