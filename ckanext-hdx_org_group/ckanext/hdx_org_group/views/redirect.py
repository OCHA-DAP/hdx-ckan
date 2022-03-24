import logging

from flask import Blueprint

import ckan.plugins.toolkit as tk

h = tk.h

log = logging.getLogger(__name__)

hdx_org_group_redirect = Blueprint(u'hdx_org_group_redirect', __name__, url_prefix=u'/organization/bulk_process')


def redirect_to_org_list(id=None):
    return h.redirect_to('organization.index')

def redirect_to_org_list2():
    return h.redirect_to('organization.index')


hdx_org_group_redirect.add_url_rule(u'', view_func=redirect_to_org_list2,
                                    defaults={
                                        'id': ''
                                    })
hdx_org_group_redirect.add_url_rule(u'/<id>', view_func=redirect_to_org_list)
