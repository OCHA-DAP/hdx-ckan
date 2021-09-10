import six
import ckan.authz as authz
import ckan.plugins.toolkit as tk

if not six.PY3:
    from ckanext.hdx_users.helpers.permissions import Permissions
else:
    Permissions = None

g = tk.g


def has_dataviz_gallery_permission(user=None):
    if not user:
        user = g.user
    if user:
        if Permissions:
            has_carousel_permission = Permissions(user).has_permission(Permissions.PERMISSION_MANAGE_CAROUSEL)
        else:
            has_carousel_permission = False
        if has_carousel_permission or authz.is_sysadmin(user):
            return True
    return False
