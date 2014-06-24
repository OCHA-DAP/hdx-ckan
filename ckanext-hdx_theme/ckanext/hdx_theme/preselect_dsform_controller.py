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

c = common.c
_check_access = tk.check_access
_get_action = tk.get_action


class HDXPreselectOrgController(base.BaseController):
    def preselect(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author
                   }
        allowed_to_add_datasets = _check_access('package_create', context)
        if allowed_to_add_datasets:
            am_sysadmin = new_authz.is_sysadmin(c.user)
            c.am_sysadmin = am_sysadmin
            orgs_where_editor = []
            orgs_where_admin = []
            if not am_sysadmin:
                orgs_where_editor = self._find_org_ids_with_permission('create_dataset')
                orgs_where_admin = self._find_org_ids_with_permission('admin')
            c.organizations_available = h.organizations_available('read')
            for org in c.organizations_available:
                org['has_add_dataset_rights'] = True
                if am_sysadmin:
                    org['role'] = 'sysadmin'
                elif org['id'] in orgs_where_admin:
                    org['role'] = 'admin'
                elif org['id'] in orgs_where_editor:
                    org['role'] = 'editor'
                else:
                    org['role'] = 'member'
                    org['has_add_dataset_rights'] = False

            c.organizations_available.sort(key=lambda y:
                                        y['display_name'].lower())
            return base.render('organization/organization_preselector.html')
        else:
            return base.render('organization/request_mem_or_org.html')

    def _find_org_ids_with_permission(self, permission):
        editor_orgs = h.organizations_available(permission)
        return [org['id'] for org in editor_orgs]
