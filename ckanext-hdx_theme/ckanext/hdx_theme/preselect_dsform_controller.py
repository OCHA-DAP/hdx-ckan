'''
Created on Jun 20, 2014

@author: alexandru-m-g
'''

import ckan.lib.base as base
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h
import ckan.new_authz as new_authz

import ckanext.hdx_theme.helpers as hdx_h

c = common.c
_check_access = tk.check_access
_get_action = tk.get_action


class HDXPreselectOrgController(base.BaseController):
    def preselect(self):

#         context = {'model': model, 'session': model.Session,
#                    'user': c.user or c.author
#                    }

#         allowed_to_add_datasets = True
#         try:
#             _check_access('package_create', context)
#         except tk.NotAuthorized:
#             allowed_to_add_datasets = False
        c.am_sysadmin = new_authz.is_sysadmin(c.user)
        c.organizations_available = hdx_h.hdx_organizations_available_with_roles()
        if c.organizations_available and len(c.organizations_available) > 0:
            return base.render('organization/organization_preselector.html')
        else:
            return base.render('organization/request_mem_or_org.html')

