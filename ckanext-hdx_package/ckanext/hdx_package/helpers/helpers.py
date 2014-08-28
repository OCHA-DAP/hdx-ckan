import ckan.lib.helpers as h
from ckan.common import (
     c, request
)
import sqlalchemy
import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import datetime
import json
import logging
import ckan.plugins.toolkit as tk
import re
import ckan.new_authz as new_authz

import ckanext.hdx_theme.helpers.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _

log = logging.getLogger(__name__)

def hdx_user_org_num(user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
    try:
        user    = tk.get_action('organization_list_for_user')(context,{'id':user_id, 'permission': 'create_dataset'})
    except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to see organization member list'))    
        
    return user

def hdx_organizations_available_with_roles():
    organizations_available = h.organizations_available('read')
    if organizations_available and len(organizations_available) > 0:
        orgs_where_editor = []
        orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set([org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id'] for org in h.organizations_available('admin')])

    for org in organizations_available:
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

    organizations_available.sort(key=lambda y:
                                y['display_name'].lower())
    return organizations_available