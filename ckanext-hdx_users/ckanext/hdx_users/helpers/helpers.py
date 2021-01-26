import requests
import json
from ckan.common import _
from ckan.common import g
from ckan.logic import NotFound
from ckan.common import config
import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
import ckan.authz as authz
import ckan.logic as logic
import ckan.model.user as user_model

from ckanext.hdx_users.helpers.notification_service import get_notification_service

get_action = toolkit.get_action
check_access = toolkit.check_access
NotAuthorized = toolkit.NotAuthorized
CaptchaNotValid = _('Captcha is not valid')
ValidationError = logic.ValidationError


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

    if not url:
        try:
            check_access('hdx_quick_links_update', context, {})
            url = h.url_for('quick_links_settings')
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


def find_user_id(username_or_id):
    user = user_model.User.get(username_or_id)
    if not user:
        raise NotFound()
    user_id = user.id
    return user_id


def is_valid_captcha(captcha_response):
    is_captcha_enabled = config.get('hdx.captcha', 'false')
    if is_captcha_enabled == 'true':
        # captcha_response = request.params.get('g-recaptcha-response')
        if not _is_valid_captcha(response=captcha_response):
            raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
        return True
    else:
        return None


def _is_valid_captcha(response):
    url = config.get('hdx.captcha.url')
    secret = config.get('ckan.recaptcha.privatekey')
    params = {'secret': secret, "response": response}
    r = requests.get(url, params=params, verify=True)
    res = json.loads(r.content)
    return 'success' in res and res['success'] == True
