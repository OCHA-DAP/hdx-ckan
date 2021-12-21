"""
Requires users validate email before account is active. Has some
duplicates methods from registration_controller.py because when
enabled it will override them when enabled
"""
# import exceptions as exceptions
import json
import logging as logging
import re
import urllib2 as urllib2

import pylons.configuration as configuration
from pylons import config

import ckan.controllers.user
import ckan.controllers.user
import ckan.lib.base as base
import ckan.lib.captcha as captcha
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as df
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.tokens as tokens
import ckanext.hdx_users.helpers.user_extra as ue_helpers
import ckanext.hdx_users.model as user_model
from ckan.common import _, c, g, request, response
from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH
from ckanext.hdx_users.views.user_auth_view import HDXUserAuthView

_validate = dictization_functions.validate
log = logging.getLogger(__name__)
render = base.render
abort = base.abort
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
ValidationError = logic.ValidationError
DataError = dictization_functions.DataError
NotAuthorized = logic.NotAuthorized
unflatten = dictization_functions.unflatten

Invalid = df.Invalid
CaptchaNotValid = _('Captcha is not valid')
LoginFailed = _('Login failed. Bad username or password.')
OnbNotAuth = json.dumps({'success': False, 'error': {'message': _('Unauthorized to create user')}})
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbExistingUsername = json.dumps({'success': False, 'error': {'message': 'Username is already used'}})
OnbExistingEmail = json.dumps({'success': False, 'error': {'message': 'Email is already in use'}})
OnbTokenNotFound = json.dumps({'success': False, 'error': {'message': 'Token not found'}})
OnbIntegrityErr = json.dumps({'success': False, 'error': {'message': 'Integrity Error'}})
OnbCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})
OnbLoginErr = json.dumps({'success': False, 'error': {'message': LoginFailed}})
OnbSuccess = json.dumps({'success': True})
OnbErr = json.dumps({'success': False, 'error': {'message': _('Something went wrong. Please contact support.')}})
OnbValidationErr = json.dumps({'success': False, 'error': {'message': _('You have not yet validated your email.')}})
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})


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


class ValidationController(ckan.controllers.user.UserController):
    request_register_form = 'user/request_register.html'

    # def first_login(self, error=None):
    #     context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
    #     data_dict = {'extras': [{'key': user_model.HDX_ONBOARDING_FIRST_LOGIN, 'new_value': 'True'}]}
    #     if c.user:
    #         try:
    #             data_dict['user_id'] = c.userobj.id or c.user
    #             get_action('user_extra_update')(context, data_dict)
    #         except NotFound, e:
    #             return OnbUserNotFound
    #         except Exception, e:
    #             error_summary = str(e)
    #             return self.error_message(error_summary)
    #     else:
    #         return OnbUserNotFound
    #     return OnbSuccess

    # def login(self, error=None):
    #     '''
    #     Code copied from controllers/user.py:345
    #     :param error:
    #     :return:
    #     '''
    #     # Do any plugin login stuff
    #     for item in p.PluginImplementations(p.IAuthenticator):
    #         item.login()
    #
    #     if 'error' in request.params:
    #         h.flash_error(request.params['error'])
    #
    #     if not c.user:
    #         came_from = request.params.get('came_from')
    #         if not came_from:
    #             came_from = h.url_for('hdx_user.logged_in')
    #         c.login_handler = h.url_for(
    #             self._get_repoze_handler('login_handler_path'),
    #             came_from=came_from)
    #         if error:
    #             # vars = {'error_summary': {'': error}}
    #             template_data = ue_helpers.get_login(False, error)
    #         else:
    #             template_data = {}
    #
    #         return render('home/index.html', extra_vars=template_data)
    #         # return render('user/login.html', extra_vars=vars)
    #         # return OnbLoginErr
    #     else:
    #         return render('user/logout_first.html')


    # def _get_ue_dict_for_key_list(self, user_id, data_list):
    #     ue_dict = {'user_id': user_id}
    #     extras = []
    #     for item in data_list:
    #         extras.append({'key': item.get('key')), 'new_value': value})
    #     ue_dict['extras'] = extras
    #     return ue_dict


    # @staticmethod
    # @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    # def _validate_form(data, errors):
    #     ''' The functionality of sending emails with new user requests has been deprecated.
    #         Deprecated since 13.08.2014 - hdx 0.3.6
    #     '''
    #     if not data['fullname']:
    #         errors['fullname'] = [_(u'Fullname is required!')]
    #     if not data['email']:
    #         errors['email'] = [_(u'Email is required!')]
    #     else:
    #         if not EMAIL_REGEX.match(data['email']):
    #             errors['email'] = [_(u'Email entered is not valid!')]
    #
    #     if not data['org']:
    #         errors['org'] = [_(u'Organisation is required!')]

    # @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    # def request(self, data=None, errors=None, error_summary=None):
    #     ''' The functionality of sending emails with new user requests has been deprecated.
    #         Deprecated since hdx 0.3.5
    #     '''
    #
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user,
    #                'request': 'request' in request.params}
    #     # try:
    #     #    check_access('request_register', context)
    #     # except NotAuthorized:
    #     #    abort(401, _('Unauthorized to request new registration.'))
    #
    #     if context['request'] and not data:
    #         data = logic.clean_dict(unflatten(
    #             logic.tuplize_dict(logic.parse_params(request.params))))
    #         errors = dict()
    #         error_summary = dict()
    #
    #         self._validate_form(data, errors)
    #         try:
    #             captcha.check_recaptcha(request)
    #         except captcha.CaptchaError:
    #             error_msg = _(u'Bad Captcha. Please try again.')
    #             error_summary['captcha'] = error_msg
    #             errors['captcha'] = [error_msg]
    #
    #         if errors == {}:
    #             name = data['fullname']
    #             email = data['email']
    #             org = data['org']
    #             reason = data['reason']
    #
    #             h.log.info(
    #                 'Request access for {name} ({email}) of {org} with reason: {reason}'.format(name=name, email=email,
    #                                                                                             org=org, reason=reason))
    #             try:
    #                 # send_mail(name, email, org, reason)
    #                 h.flash_success(_('We will check your request and we will send you an email!'))
    #                 h.redirect_to('/')
    #             except mailer.MailerException, e:
    #                 error_summary['sendError'] = _('Could not send request for access: %s') % unicode(e)
    #
    #     data = data or {}
    #     errors = errors or {}
    #     error_summary = error_summary or {}
    #     vars = {'data': data,
    #             'errors': errors,
    #             'error_summary': error_summary,
    #             'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey')}
    #     c.form = render(self.request_register_form, extra_vars=vars)
    #     return base.render(self.request_register_form, cache_force=True, extra_vars=vars)

    # moved from login_controller.py
    def _new_login(self, message, page_subtitle, error=None):
        return HDXUserAuthView().new_login(info_message=message, page_subtitle=page_subtitle)

    def contribute(self, error=None):
        """
        If the user tries to add data but isn't logged in, directs
        them to a specific contribute login page.
        """

        return self._new_login(_('In order to add data, you need to login below or register on HDX'),
                               _('Login to contribute'), error=error)

    def contact_hdx(self, error=None):
        """
        If the user tries to contact contributor but isn't logged in, directs
        them to a specific login page.
        """
        return self._new_login(_('In order to contact the contributor, you need to login below or register on HDX'),
                               _('Login to contact HDX'), error=error)
