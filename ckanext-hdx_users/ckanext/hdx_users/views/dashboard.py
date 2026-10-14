from flask import Blueprint, redirect

import ckan.plugins.toolkit as tk

request = tk.request
g = tk.g
h = tk.h
_ = tk._

hdx_user_dashboard = Blueprint(u'hdx_user_dashboard', __name__, url_prefix=u'/dashboard')


def _redirect_keeping_query(url, code=302):
    if request.query_string:
        url = u'{}?{}'.format(url, request.query_string.decode(u'utf-8'))
    return redirect(url, code=code)


def datasets():
    """
    Moved to the user's page (/user/<id>)
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'home.index')

    return _redirect_keeping_query(h.url_for(u'hdx_user.read', id=g.user))


def organizations():
    """
    Moved to /user/organizations/<id>
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'user.login')

    return _redirect_keeping_query(h.url_for(u'hdx_user.read_organizations', id=g.user))


def newsfeed():
    """
    The Newsfeed was removed: /dashboard goes to the user's page (/user/<id>),
    without the Newsfeed query string
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'user.login')

    return h.redirect_to(u'hdx_user.read', id=g.user)


hdx_user_dashboard.add_url_rule(u'/', view_func=newsfeed, strict_slashes=False)
hdx_user_dashboard.add_url_rule(u'/datasets', view_func=datasets)
hdx_user_dashboard.add_url_rule(u'/organizations', view_func=organizations)
