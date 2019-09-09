
from ckan.common import g
import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
import ckan.authz as authz

from ckanext.hdx_users.helpers.notification_service import get_notification_service

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


def hdx_get_user_notifications():
    # return get_notification_service().get_notifications()
    try:
        if not g.hdx_user_notifications:
            # this part is for pylons, flask gives an exception (see below)
            g.hdx_user_notifications = get_notification_service().get_notifications()
    except AttributeError as e:
        # if we are in flask we get an AttributeError before setting the property in g the first time
        g.hdx_user_notifications = get_notification_service().get_notifications()

    return g.hdx_user_notifications
