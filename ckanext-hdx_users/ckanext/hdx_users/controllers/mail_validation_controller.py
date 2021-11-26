"""
Requires users validate email before account is active. Has some
duplicates methods from registration_controller.py because when
enabled it will override them when enabled
"""
import datetime
# import exceptions as exceptions
import json
import logging as logging
import re
import urllib2 as urllib2

import dateutil
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

    def new_login(self, error=None, info_message=None, page_subtitle=None):
        template_data = {}
        if not c.user:
            template_data = ue_helpers.get_login(True, "")
        if info_message:
            if 'data' not in template_data:
                template_data['data'] = {}
            template_data['data']['info_message'] = info_message
            template_data['data']['page_subtitle'] = page_subtitle
        return render('home/index.html', extra_vars=template_data)

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

    def login(self, error=None):
        '''
        Code copied from controllers/user.py:345
        :param error:
        :return:
        '''
        # Do any plugin login stuff
        for item in p.PluginImplementations(p.IAuthenticator):
            item.login()

        if 'error' in request.params:
            h.flash_error(request.params['error'])

        if not c.user:
            came_from = request.params.get('came_from')
            if not came_from:
                came_from = h.url_for(controller='user', action='logged_in')
            c.login_handler = h.url_for(
                self._get_repoze_handler('login_handler_path'),
                came_from=came_from)
            if error:
                # vars = {'error_summary': {'': error}}
                template_data = ue_helpers.get_login(False, error)
            else:
                template_data = {}

            return render('home/index.html', extra_vars=template_data)
            # return render('user/login.html', extra_vars=vars)
            # return OnbLoginErr
        else:
            return render('user/logout_first.html')

    def logged_in(self):
        # redirect if needed
        came_from = request.params.get('came_from', '')
        if h.url_is_local(came_from):
            return h.redirect_to(str(came_from))

        if c.user:
            context = None
            data_dict = {'id': c.user}
            user_dict = get_action('user_show')(context, data_dict)

            # IAuthenticator too buggy, doing this instead
            try:
                token = tokens.token_show(context, user_dict)
            except NotFound, e:
                token = {'valid': True}  # Until we figure out what to do with existing users
            except:
                abort(500, _('Something wrong'))
            if not token['valid']:
                # force logout
                for item in p.PluginImplementations(p.IAuthenticator):
                    item.logout()
                # redirect to validation page
                h.flash_error(_('You have not yet validated your email.'))
                h.redirect_to(self._get_repoze_handler('logout_handler_path'))

            if 'created' in user_dict:
                time_passed = datetime.datetime.now() - dateutil.parser.parse(user_dict['created'])
            else:
                time_passed = None
            if 'activity' in user_dict and (not user_dict['activity']) and time_passed and time_passed.days < 3:
                # /dataset/new
                # contribute_url = h.url_for(controller='package', action='new')

                return h.redirect_to('dashboard.organizations')
            else:
                userobj = c.userobj if c.userobj else model.User.get(c.user)
                login_dict = {'display_name': userobj.display_name, 'email': userobj.email,
                              'email_hash': userobj.email_hash, 'login': userobj.name}

                max_age = int(14 * 24 * 3600)
                response.set_cookie('hdx_login', urllib2.quote(json.dumps(login_dict)), max_age=max_age)
                if not c.user:
                    h.redirect_to(locale=None, controller='user', action='login', id=None)

                # do we need this?
                # user_ref = c.userobj.get_reference_preferred_for_uri()

                _ckan_site_url = config.get('ckan.site_url', '#')
                _came_from = str(request.referrer or _ckan_site_url)

                excluded_paths = ['/user/validate/', 'user/logged_in?__logins', 'user/logged_out_redirect']
                if _ckan_site_url != _came_from and not any(path in _came_from for path in excluded_paths):
                    h.redirect_to(_came_from)

                h.flash_success(_("%s is now logged in") % user_dict['display_name'])
                h.redirect_to("user_dashboard", locale=None)
        else:
            err = _('Login failed. Bad username or password.')
            try:
                if g.openid_enabled:
                    err += _(' (Or if using OpenID, it hasn\'t been associated '
                             'with a user account.)')
            except:
                pass

            if p.toolkit.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)

            else:
                template_data = ue_helpers.get_login(False, err)
                log.error("Status code 401 : username or password incorrect")
                return render('home/index.html', extra_vars=template_data)
                # return self.login(error=err)

    def logged_out_page(self):
        template_data = ue_helpers.get_logout(True, _('User logged out with success'))
        return render('home/index.html', extra_vars=template_data)
        # return render('user/logout.html')


    def validate(self, token):
        '''
        Step 2: user click on validate link from email
        :param token:
        :return:
        '''
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        data_dict = {'token': token,
                     'extras': [{'key': user_model.HDX_ONBOARDING_USER_VALIDATED, 'new_value': 'True'}]}

        try:
            check_access('user_can_validate', context, data_dict)
        except NotAuthorized:
            return OnbNotAuth
        except ValidationError as e:
            error_summary = e.error_summary
            return self.error_message(error_summary)

        try:
            # Update token for user
            token = tokens.token_show_by_id(context, data_dict)
            data_dict['user_id'] = token['user_id']
            # removed because it is saved in next step. User is allowed to click on /validate link several times
            # get_action('user_extra_update')(context, data_dict)
        except NotFound:
            return OnbUserNotFound
        except Exception as e:
            error_summary = str(e)
            return self.error_message(error_summary)

        user = model.User.get(data_dict['user_id'])
        template_data = ue_helpers.get_user_extra(user_id=data_dict['user_id'])
        template_data['data']['current_step'] = user_model.HDX_ONBOARDING_DETAILS
        template_data['data']['email'] = user.email
        template_data['data']['name'] = user.name
        template_data['capcha_api_key'] = configuration.config.get('ckan.recaptcha.publickey')
        return render('home/index.html', extra_vars=template_data)



    # def _get_ue_dict_for_key_list(self, user_id, data_list):
    #     ue_dict = {'user_id': user_id}
    #     extras = []
    #     for item in data_list:
    #         extras.append({'key': item.get('key')), 'new_value': value})
    #     ue_dict['extras'] = extras
    #     return ue_dict


    @staticmethod
    @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    def _validate_form(data, errors):
        ''' The functionality of sending emails with new user requests has been deprecated.
            Deprecated since 13.08.2014 - hdx 0.3.6
        '''
        if not data['fullname']:
            errors['fullname'] = [_(u'Fullname is required!')]
        if not data['email']:
            errors['email'] = [_(u'Email is required!')]
        else:
            if not EMAIL_REGEX.match(data['email']):
                errors['email'] = [_(u'Email entered is not valid!')]

        if not data['org']:
            errors['org'] = [_(u'Organisation is required!')]

    @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    def request(self, data=None, errors=None, error_summary=None):
        ''' The functionality of sending emails with new user requests has been deprecated.
            Deprecated since hdx 0.3.5
        '''

        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'request': 'request' in request.params}
        # try:
        #    check_access('request_register', context)
        # except NotAuthorized:
        #    abort(401, _('Unauthorized to request new registration.'))

        if context['request'] and not data:
            data = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            errors = dict()
            error_summary = dict()

            self._validate_form(data, errors)
            try:
                captcha.check_recaptcha(request)
            except captcha.CaptchaError:
                error_msg = _(u'Bad Captcha. Please try again.')
                error_summary['captcha'] = error_msg
                errors['captcha'] = [error_msg]

            if errors == {}:
                name = data['fullname']
                email = data['email']
                org = data['org']
                reason = data['reason']

                h.log.info(
                    'Request access for {name} ({email}) of {org} with reason: {reason}'.format(name=name, email=email,
                                                                                                org=org, reason=reason))
                try:
                    # send_mail(name, email, org, reason)
                    h.flash_success(_('We will check your request and we will send you an email!'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    error_summary['sendError'] = _('Could not send request for access: %s') % unicode(e)

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data,
                'errors': errors,
                'error_summary': error_summary,
                'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey')}
        c.form = render(self.request_register_form, extra_vars=vars)
        return base.render(self.request_register_form, cache_force=True, extra_vars=vars)

    def post_register(self):
        """
            If the user has registered but not validated their email
            redirect to a special page reminding them why they can't
            login.
        """
        if not c.user:
            user = request.params.get('user')
            vars = {'user': user}
            return render('user/post_register.html', extra_vars=vars)
        else:
            return render('user/logout_first.html')

    def validation_resend(self, id):
        # Get user by id
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj}

        try:
            user = get_action('user_show')(context, data_dict)
        except NotFound, e:
            abort(404, _('User not found'))
        except:
            abort(500, _('Error'))

        # Get token for user
        try:
            token = tokens.token_show(context, data_dict)
        except NotFound, e:
            abort(404, _('User not found'))
        except:
            abort(500, _('Error'))

        # Send Validation email
        tokens.send_validation_email(user, token)

        post_register_url = h.url_for(
            controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
            action='post_register')
        redirect_url = '{0}?user={1}'
        h.redirect_to(redirect_url.format(
            post_register_url,
            user['id']))

    def error_message(self, error_summary):
        return json.dumps({'success': False, 'error': {'message': error_summary}})

    # moved from login_controller.py
    def _new_login(self, message, page_subtitle, error=None):
        # self.login(error)
        # vars = {'contribute': True}
        # tmp = hdx_mail_c.ValidationController()
        return self.new_login(info_message=message, page_subtitle=page_subtitle)

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

    # def save_mapexplorer_config(self, error=None):
    #     """
    #     If the user tries to save a map explorer configuration, we direct
    #     them to a specific login page.
    #     """
    #     return self._new_login(
    #         _('In order to save a custom map explorer view, you need to login below or register on HDX'),
    #         _('Login to save map explorer view'), error=error)
