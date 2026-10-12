from flask import Blueprint, redirect

import ckan.plugins.toolkit as tk

request = tk.request
g = tk.g
h = tk.h
_ = tk._

hdx_user_dashboard = Blueprint(u'hdx_user_dashboard', __name__, url_prefix=u'/dashboard')


def _moved_permanently(url):
    if request.query_string:
        url = u'{}?{}'.format(url, request.query_string.decode(u'utf-8'))
    return redirect(url, code=301)


def datasets():
    """
    Moved to the user's page (/user/<id>)
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'home.index')

    return _moved_permanently(h.url_for(u'hdx_user.read', id=g.user))


def organizations():
    """
    Moved to /user/organizations/<id>
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'user.login')

    return _moved_permanently(h.url_for(u'hdx_user.read_organizations', id=g.user))


def newsfeed():
    """
    The Newsfeed was removed: /dashboard goes to the user's page (/user/<id>),
    without the Newsfeed query string
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'user.login')

    return redirect(h.url_for(u'hdx_user.read', id=g.user), code=301)


hdx_user_dashboard.add_url_rule(u'/', view_func=newsfeed, strict_slashes=False)
hdx_user_dashboard.add_url_rule(u'/datasets', view_func=datasets)
hdx_user_dashboard.add_url_rule(u'/organizations', view_func=organizations)
