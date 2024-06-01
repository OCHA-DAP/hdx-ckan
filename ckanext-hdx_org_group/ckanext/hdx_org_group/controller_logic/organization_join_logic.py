import logging
from typing import cast

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import current_user
from ckan.types import Context

get_action = tk.get_action
check_access = tk.check_access
config = tk.config
h = tk.h
NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)


class OrgJoinLogic(object):
    def __init__(self, context: Context):
        self.active_org_dict = {}
        self.inactive_org_dict = {}
        self.all_org_list = []
        self.context = context


    def read(self):
        self._fetch_org_list_metadata()
        return self

    def _fetch_org_list_metadata(self):
        '''
        :returns: populated self object
        :rtype:
        '''

        self.all_org_list = get_action(u'cached_organization_list')(self.context, {})

        if len(self.all_org_list) > 0:
            for o in self.all_org_list:
                if not o.get('closed_organization') and o.get('request_membership') != 'false':
                    self.active_org_dict[o.get('id')] = o.get('display_name')
                else:
                    self.inactive_org_dict[o.get('id')] = o.get('display_name')

