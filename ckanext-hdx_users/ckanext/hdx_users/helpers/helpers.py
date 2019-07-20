from ckan.common import g
from ckan.logic import NotFound

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
import ckan.authz as authz
import ckan.model.user as user_model


get_action = toolkit.get_action
check_access = toolkit.check_access
NotAuthorized = toolkit.NotAuthorized


def find_first_global_settings_url():
    context = {'user': g.user}
    url = None
    if authz.is_sysadmin(g.user):
        url = h.url_for('admin.index')

    if not url:
        try:
            check_access('hdx_carousel_update', context, {})
            url = h.url_for('carousel_settings')
        except NotAuthorized as e:
            pass

    if not url:
        try:
            check_access('hdx_request_data_admin_list', context, {})
            url = h.url_for('ckanadmin_requests_data')
        except NotAuthorized as e:
            pass

    if not url:
        try:
            check_access('admin_page_list', context, {})
            url = h.url_for('pages_show')
        except NotAuthorized as e:
            pass
    return url


def find_user_id(username_or_id):
    user = user_model.User.get(username_or_id)
    if not user:
        raise NotFound()
    user_id = user.id
    return user_id
