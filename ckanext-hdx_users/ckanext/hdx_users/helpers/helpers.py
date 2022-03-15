import json

import requests

import ckan.authz as authz
import ckan.lib.navl.dictization_functions as df
import ckan.model.user as user_model
import ckan.plugins.toolkit as tk
from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH
from ckanext.hdx_users.helpers.notification_service import get_notification_service

get_action = tk.get_action
check_access = tk.check_access
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
h = tk.h
g = tk.g
config = tk.config
_ = tk._
CaptchaNotValid = _('Captcha is not valid')
ValidationError = tk.ValidationError
Invalid = df.Invalid




def find_first_global_settings_url():
    context = {'user': g.user}
    url = None
    if authz.is_sysadmin(g.user):
        url = h.url_for('admin.index')

    if not url:
        try:
            check_access('hdx_carousel_update', context, {})
            url = h.url_for('hdx_carousel.show')
        except NotAuthorized as e:
            pass

    if not url:
        try:
            check_access('hdx_request_data_admin_list', context, {})
            url = h.url_for('requestdata_ckanadmin.requests_data')
        except NotAuthorized as e:
            pass

    if not url:
        try:
            check_access('admin_page_list', context, {})
            url = h.url_for('hdx_custom_pages.index')
        except NotAuthorized as e:
            pass

    if not url:
        try:
            check_access('hdx_quick_links_update', context, {})
            url = h.url_for('hdx_quick_links.show')
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
        if not validate_captcha(response=captcha_response):
            raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
        return True
    else:
        return None


def validate_captcha(response):
    url = config.get('hdx.captcha.url')
    secret = config.get('ckan.recaptcha.privatekey')
    params = {'secret': secret, "response": response}
    r = requests.get(url, params=params, verify=True)
    res = json.loads(r.content)
    return 'success' in res and res['success'] == True


def name_validator_with_changed_msg(val, context):
    """This is just a wrapper function around the validator.name_validator function.
        The wrapper function just changes the message in case the name_match doesn't match.
        The only purpose for still calling that function here is to keep the link visible and
        in case of a ckan upgrade to still be able to raise any new Invalid exceptions

    """
    try:
        return name_validator(val, context)
    except Invalid as invalid:
        if val in ['new', 'edit', 'search']:
            raise Invalid(_('That name cannot be used'))

        if len(val) < 2:
            raise Invalid(_('Name must be at least %s characters long') % 2)
        if len(val) > PACKAGE_NAME_MAX_LENGTH:
            raise Invalid(_('Name must be a maximum of %i characters long') % \
                          PACKAGE_NAME_MAX_LENGTH)
        if not name_match.match(val):
            raise Invalid(_('Username should be lowercase letters and/or numbers and/or these symbols: -_'))

        raise invalid
