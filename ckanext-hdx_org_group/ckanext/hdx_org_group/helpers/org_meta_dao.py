
import ckan.logic as logic
import ckan.model as model
import ckan.new_authz as new_authz
import ckan.lib.base as base
from ckan.common import c, request, _

import ckanext.hdx_theme.helpers.less as less
import ckanext.hdx_theme.helpers.helpers as helpers
import ckanext.hdx_search.controllers.search_controller as search_controller

abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized


class OrgMetaDao(search_controller.HDXSearchController):
    def __init__(self, org_id):
        self.id = org_id
        self.datasets_num = 0
        self.org_dict = None
        self.followers_num = 0
        self.members_num = 0
        self.members = None
        self.is_custom = False
        self.custom_css_path = None

    def fetch_all(self):
        self.fetch_org_dict()
        self.fetch_dataset_info()
        self.fetch_followers()
        self.fetch_members()

    def fetch_dataset_info(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
        }

        user = c.user or c.author
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
            'extras': {}
        }

        query = logic.get_action('package_search')(context, data_dict)

        self.datasets_num = query['count']

    def fetch_org_dict(self):
        try:
            context = {
                'model': model,
                'session': model.Session,
                'user': c.user or c.author,
                'include_datasets': False,
                'for_view': True
            }
            self.org_dict = logic.get_action('hdx_light_group_show')(context, {'id': self.id})

            self.__process_custom()
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

    def fetch_followers(self):
        self.followers_num = helpers.get_group_followers(self.id)

    def fetch_members(self):
        self.members = logic.get_action('member_list')(
            {'model': model, 'session': model.Session},
            {'id': self.id, 'object_type': 'user'}
        )
        self.members_num = len(self.members)

    def __process_custom(self):
        org_extras = self.org_dict.get('extras')
        if [o.get('value') for o in org_extras if o.get('key', '') == 'custom_org' and o.get('value')]:
            self.is_custom = True

        if self.is_custom:
            css_dest_dir = '/organization/' + self.org_dict['name']

            self.custom_css_path = less.generate_custom_css_path(css_dest_dir, self.org_dict['name'], self.org_dict.get('modified_at'), True)

    def as_dict(self):
        return self.__dict__