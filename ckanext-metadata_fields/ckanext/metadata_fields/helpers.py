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

import ckanext.hdx_theme.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _

log = logging.getLogger(__name__)

def hdx_user_org_num(user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
    try:
        user    = tk.get_action('organization_list_for_user')(context,{'id':user_id})
    except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to see organization member list'))    
        
    return len(user)