import ckan.authz as authz
import ckan.plugins.toolkit as tk
from ckanext.hdx_users.helpers.permissions import Permissions

g = tk.g


def has_dataviz_gallery_permission(user=None):
    if not user:
        user = g.user
    if user:
        has_carousel_permission = Permissions(user).has_permission(Permissions.PERMISSION_MANAGE_CAROUSEL)
        if has_carousel_permission or authz.is_sysadmin(user):
            return True
    return False
