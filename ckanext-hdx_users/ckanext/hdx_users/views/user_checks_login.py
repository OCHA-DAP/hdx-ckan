# encoding: utf-8
import logging

from flask import Blueprint

import ckan.plugins.toolkit as tk
from ckanext.hdx_users.views.user_auth_view import HDXUserAuthView

log = logging.getLogger(__name__)
_ = tk._

hdx_contribute = Blueprint(u'hdx_contribute_check', __name__, url_prefix=u'/contribute')
hdx_contact_hdx = Blueprint(u'hdx_contact_hdx_check', __name__, url_prefix=u'/contact_hdx')


def _new_login(message, page_subtitle, error=None):
    return HDXUserAuthView().new_login(info_message=message, page_subtitle=page_subtitle)


def contribute(error=None):
    """
    If the user tries to add data but isn't logged in, directs
    them to a specific contribute login page.
    """

    return _new_login(_('In order to add data, you need to login below or register on HDX'),
                           _('Login to contribute'), error=error)


def contact_hdx(error=None):
    """
    If the user tries to contact contributor but isn't logged in, directs
    them to a specific login page.
    """
    return _new_login(_('In order to contact the contributor, you need to login below or register on HDX'),
                           _('Login to contact HDX'), error=error)


hdx_contribute.add_url_rule(u'', view_func=contribute)
hdx_contact_hdx.add_url_rule(u'', view_func=contact_hdx)
