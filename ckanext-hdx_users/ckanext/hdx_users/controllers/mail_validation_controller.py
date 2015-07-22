"""
Requires users validate email before account is active. Has some
duplicates methods from registration_controller.py because when
enabled it will override them when enabled
"""
import datetime
import dateutil
import hashlib
import requests

from pylons import config

# import ckan.lib.base as base
import ckan.controllers.user
from ckan.common import _, c, g, request, response
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.lib.base as base
import ckan.controllers.user
import ckan.model as model
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.captcha as captcha
import ckan.new_authz as new_authz
import pylons.configuration as configuration
import re
import json
import ckan.lib.navl.dictization_functions as df
import ckan.lib.maintain as maintain
# from urllib import quote
import ckan.plugins as p
import exceptions as exceptions

import ckanext.hdx_users.helpers.user_extra as ue_helpers
import ckanext.hdx_users.logic.schema as user_reg_schema
import ckanext.hdx_users.model as user_model
# import ckan.lib.dictization.model_dictize as model_dictize
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_theme.helpers.helpers as hdx_h
import logging as logging
import urllib2 as urllib2
from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH
from sqlalchemy.exc import IntegrityError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ckanext.hdx_users.controllers.mailer as hdx_mailer

log = logging.getLogger(__name__)
render = base.render
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
abort = base.abort
check_access = logic.check_access
get_action = logic.get_action
render = base.render
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

    def new_login(self, error=None):
        template_data = {}
        if not c.user:
            template_data = ue_helpers.get_login(True, "")
        return render('home/index.html', extra_vars=template_data)

    def first_login(self, error=None):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        data_dict = {'extras': [{'key': user_model.HDX_ONBOARDING_FIRST_LOGIN, 'new_value': 'True'}]}
        if c.user:
            try:
                data_dict['user_id'] = c.userobj.id or c.user
                get_action('user_extra_update')(context, data_dict)
            except NotFound, e:
                return OnbUserNotFound
            except exceptions.Exception, e:
                error_summary = str(e)
                return self.error_message(error_summary)
        else:
            return OnbUserNotFound
        return OnbSuccess

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
                came_from = h.url_for(controller='user', action='logged_in',
                                      __ckan_no_root=True)
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
                token = get_action('token_show')(context, user_dict)
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
                contribute_url = h.url_for(controller='package', action='new')
                # message = ''' Now that you've registered an account , you can <a href="%s">start adding datasets</a>.
                #    If you want to associate this dataset with an organization, either click on "My Organizations" below
                #    to create a new organization or ask the admin of an existing organization to add you as a member.''' % contribute_url
                # h.flash_success(_(message), True)
                return h.redirect_to(controller='user', action='dashboard_organizations')
            else:
                userobj = c.userobj if c.userobj else model.User.get(c.user)
                login_dict = {'display_name': userobj.display_name, 'email': userobj.email,
                              'email_hash': userobj.email_hash, 'login': userobj.name}
                h.flash_success(_("%s is now logged in") % user_dict['display_name'])
                max_age = int(14 * 24 * 3600)
                response.set_cookie('hdx_login', urllib2.quote(json.dumps(login_dict)), max_age=max_age)
                return self.me()
        else:
            err = _('Login failed. Bad username or password.')
            try:
                if g.openid_enabled:
                    err += _(' (Or if using OpenID, it hasn\'t been associated '
                             'with a user account.)')
            except:
                pass

            if h.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def logged_out_page(self):
        template_data = ue_helpers.get_logout(True, _('User logged out with success'))
        return render('home/index.html', extra_vars=template_data)
        # return render('user/logout.html')

    def register_email(self, data=None, errors=None, error_summary=None):
        """
        STEP 1: user register the email
        """
        temp_schema = user_reg_schema.register_user_schema()
        if 'name' in temp_schema:
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]
        context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj,
                   'schema': temp_schema, 'save': 'save' in request.params}
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.params))))
        if 'email' in data_dict:
            md5 = hashlib.md5()
            md5.update(data_dict['email'])
            data_dict['name'] = md5.hexdigest()
        context['message'] = data_dict.get('log_message', '')

        try:
            check_access('user_create', context, data_dict)
            check_access('user_can_register', context, data_dict)
        except NotAuthorized, e:
            if e.message and e.message.get('email'):
                return self.error_message(e.message.get('email')[0])
            return OnbNotAuth
        except ValidationError, e:
            # errors = e.error_dict
            error_summary = e.error_summary
            return self.error_message(error_summary)

        # hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        try:

            user = get_action('user_create')(context, data_dict)
            token = get_action('token_create')(context, user)
            user_extra = get_action('user_extra_create')(context, {'user_id': user['id'],
                                                                   'extras': ue_helpers.get_initial_extras()})

        except NotAuthorized:
            return OnbNotAuth
            # abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            return OnbTokenNotFound
            # abort(404, _('User not found'))
        except DataError:
            return OnbIntegrityErr
            # abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            # errors = e.error_dict
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)

        if not c.user:
            # Send validation email
            self.send_validation_email(user, token)

        c.user = save_user
        return OnbSuccess

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
        except ValidationError, e:
            error_summary = e.error_summary
            return self.error_message(error_summary)

        try:
            # Update token for user
            token = get_action('token_show_by_id')(context, data_dict)
            data_dict['user_id'] = token['user_id']
            get_action('user_extra_update')(context, data_dict)
        except NotFound, e:
            return OnbUserNotFound
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)

        user = model.User.get(data_dict['user_id'])
        template_data = ue_helpers.get_user_extra(user_id=data_dict['user_id'])
        # template_data['data']['current_step'] = user_model.HDX_ONBOARDING_DETAILS
        template_data['data']['email'] = user.email
        template_data['data']['name'] = user.name
        return render('home/index.html', extra_vars=template_data)

    def register_details(self, data=None, errors=None, error_summary=None):
        '''
        Step 3: user enters details for registration (username, password, firstname, lastname and captcha
        :param data:
        :param errors:
        :param error_summary:
        :return:
        '''
        temp_schema = user_reg_schema.register_details_user_schema()
        if 'name' in temp_schema:
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.params))))
        user_obj = model.User.get(data_dict['id'])
        context = {'model': model, 'session': model.Session, 'user': user_obj.name,
                   'schema': temp_schema}
        # data_dict['name'] = data_dict['email']
        data_dict['fullname'] = data_dict['first-name'] + ' ' + data_dict['last-name']
        try:
            captcha_response = data_dict.get('g-recaptcha-response', None)
            if not self.is_valid_captcha(response=captcha_response):
                raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            return OnbNotAuth
        except ValidationError, e:
            error_summary = e.error_summary
            if error_summary == CaptchaNotValid:
                return OnbCaptchaErr
            return self.error_message(error_summary)

        # hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        try:
            token_dict = get_action('token_show')(context, data_dict)
            data_dict['token'] = token_dict['token']
            get_action('token_update')(context, data_dict)
            get_action('user_update')(context, data_dict)

            ue_dict = self._get_ue_dict(data_dict['id'], user_model.HDX_ONBOARDING_DETAILS)
            get_action('user_extra_update')(context, ue_dict)

            if configuration.config.get('hdx.onboarding.send_confirmation_email') == 'true':
                subject = 'Thank you for registering on HDX!'
                link = config['ckan.site_url'] + '/login'
                tour_link = '<a href="https://www.youtube.com/watch?v=hCVyiZhYb4M">tour</a>'
                html = """\
                <html>
                  <head></head>
                  <body>
                    <p>You have successfully registered your account on HDX.</p>
                    <p>Username: {username}</p>
                    <p>Password: {password}</p>
                    <p><a href="{link}">Login</a></p>
                    <p>You can learn more about HDX by taking this quick {tour_link} or by reading our FAQ.</p>
                  </body>
                </html>
                """.format(username=data_dict.get('name'), password=data_dict.get('password'), link=link,
                           tour_link=tour_link)
                hdx_mailer.mail_recipient(data_dict.get('fullname'), data_dict.get('email'), subject, html)

        except NotAuthorized:
            return OnbNotAuth
        except NotFound, e:
            return OnbUserNotFound
        except DataError:
            return OnbIntegrityErr
        except ValidationError, e:
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except IntegrityError:
            return OnbExistingUsername
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)
        # if not c.user:
        #     pass
        c.user = save_user
        return OnbSuccess

    def follow_details(self, data=None, errors=None, error_summary=None):
        '''
        Step 4: user follows key entities
        :param data:
        :param errors:
        :param error_summary:
        :return:
        '''
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.params))))
        name = c.user or data_dict['id']
        user_obj = model.User.get(name)
        user_id = user_obj.id
        context = {'model': model, 'session': model.Session, 'user': user_obj.name}
        try:
            ue_dict = self._get_ue_dict(user_id, user_model.HDX_ONBOARDING_FOLLOWS)
            get_action('user_extra_update')(context, ue_dict)
        except NotAuthorized:
            return OnbNotAuth
            # abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            return OnbUserNotFound
            # abort(404, _('User not found'))
        except DataError:
            return OnbIntegrityErr
            # abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            # errors = e.error_dict
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)
        return OnbSuccess

    def request_new_organization(self):
        '''
        Step 5a: user can request to create a new organization
        :return:
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        try:
            check_access('hdx_send_new_org_request', context)
        except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to send a new org request'))

        try:
            user = model.User.get(context['user'])
            data = self._process_new_org_request(user)
            self._validate_new_org_request_field(data)

            get_action('hdx_send_new_org_request')(context, data)

            ue_dict = self._get_ue_dict(user.id, user_model.HDX_ONBOARDING_ORG)
            get_action('user_extra_update')(context, ue_dict)

        except hdx_mail.NoRecipientException, e:
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except logic.ValidationError, e:
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)
        return OnbSuccess

    def request_membership(self):
        '''
        Step 5b: user can request membership to an existing organization
        :return:
        '''
        try:
            org_id = request.params.get('org_id', '')
            msg = request.params.get('message', 'New Onboarding module: create a new organization')
            user = hdx_h.hdx_get_user_info(c.user)
            context = {'model': model, 'session': model.Session,
                       'user': c.user}
            org_admins = get_action('member_list')(context, {'id': org_id, 'capacity': 'admin', 'object_type': 'user'})
            admins = []
            for admin_tuple in org_admins:
                admin_id = admin_tuple[0]
                admins.append(hdx_h.hdx_get_user_info(admin_id))
            admins_with_email = [admin for admin in admins if admin['email']]

            data_dict = {'display_name': user['display_name'], 'name': user['name'],
                         'email': user['email'], 'organization': org_id,
                         'message': msg, 'admins': admins_with_email}
            get_action('hdx_send_request_membership')(context, data_dict)

            ue_dict = self._get_ue_dict(user['id'], user_model.HDX_ONBOARDING_ORG)
            get_action('user_extra_update')(context, ue_dict)

        except hdx_mail.NoRecipientException, e:
            return self.error_message(_(str(e)))
        except exceptions.Exception, e:
            log.error(str(e))
            return self.error_message(_('Request can not be sent. Contact an administrator.'))
        return OnbSuccess

    def invite_friends(self):
        '''
        Step 6: user can invite friends by email to access HDX
        :return:
        '''
        if not c.user:
            return OnbNotAuth
        try:
            context = {'model': model, 'session': model.Session,
                       'user': c.user}
            usr = c.userobj.display_name or c.user
            user_id = c.userobj.id or c.user
            ue_dict = self._get_ue_dict(user_id, user_model.HDX_ONBOARDING_FRIENDS)
            get_action('user_extra_update')(context, ue_dict)

            subject = '{fullname} invited you to join HDX!'.format(fullname=usr)
            link = config['ckan.site_url'] + '/login'
            hdx_link = '<a href="{link}">tour</a>'.format(link=link)
            tour_link = '<a href="https://www.youtube.com/watch?v=hCVyiZhYb4M">tour</a>'
            html = """\
                <html>
                  <head></head>
                  <body>
                    <p>{fullname} invited you to join the <a href="https://hdx.rwlabs.org">Humanitarian Data Exchange (HDX)</a>, an open platform for sharing humanitarian data. Anyone can access the data on HDX but registered users are able to share data and be part of the HDX community.</p>
                    <p>You can learn more about HDX by taking this quick {tour_link}</p>
                    <p>Join {hdx_link}</p>
                  </body>
                </html>
            """.format(fullname=usr, tour_link=tour_link, hdx_link=hdx_link)

            friends = [request.params.get('email1'), request.params.get('email2'), request.params.get('email3')]
            for f in friends:
                if f:
                    hdx_mailer.mail_recipient(f, f, subject, html)

        except exceptions.Exception, e:
            error_summary = str(e)
            return self.error_message(error_summary)
        return OnbSuccess

    def _get_ue_dict(self, user_id, key, value='True'):
        ue_dict = self._build_extras_dict(key, value)
        ue_dict['user_id'] = user_id
        return ue_dict

    def _build_extras_dict(self, key, value='True'):
        return {'extras': [{'key': key, 'new_value': value}]}

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

    def register(self, data=None, errors=None, error_summary=None):
        """
        Creates a new user, but allows logged in users to create
        additional accounts as per HDX requirements at the time.
        """
        context = {'model': model, 'session': model.Session, 'user': c.user}
        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to register as a user.'))
        # hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        result = self.new(data, errors, error_summary)
        c.user = save_user

        return result

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

    def new(self, data=None, errors=None, error_summary=None):
        '''GET to display a form for registering a new user.
           or POST the form data to actually do the user registration.
        '''

        temp_schema = self._new_form_to_db_schema()
        if temp_schema.has_key('name'):
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'auth_user_obj': c.userobj,
                   'schema': temp_schema,
                   'save': 'save' in request.params}

        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a user'))

        if context['save'] and not data:
            return self._save_new(context)

        if c.user and not data:
            # #1799 Don't offer the registration form if already logged in
            return render('user/logout_first.html')

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary,
                'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey')}

        c.is_sysadmin = new_authz.is_sysadmin(c.user)
        c.form = render(self.new_user_form, extra_vars=vars)
        return render('user/new.html')

    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            captcha.check_recaptcha(request)
            user = get_action('user_create')(context, data_dict)
            token = get_action('token_create')(context, user)
            user_extra = get_action('user_extra_create')(context, {'user_id': user['id'],
                                                                   'extras': ue_helpers.get_default_extras()})
            # print user_extra

        except NotAuthorized:
            abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.new(data_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        if not c.user:
            # Send validation email
            self.send_validation_email(user, token)

            # Redirect to a URL picked up by repoze.who which performs the
            # login
            # login_url = self._get_repoze_handler('login_handler_path')

            post_register_url = h.url_for(
                controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                action='post_register')

            # We need to pass the logged in URL as came_from parameter
            # otherwise we lose the language setting
            came_from = h.url_for(controller='user', action='logged_in',
                                  __ckan_no_root=True)
            redirect_url = '{0}?came_from={1}&user={2}'
            h.redirect_to(redirect_url.format(
                post_register_url,
                came_from, user['id']))
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            h.flash_success(_('User "%s" is now registered but you are still '
                              'logged in as "%s" from before') %
                            (data_dict['name'], c.user))
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
            token = get_action('token_show')(context, data_dict)
        except NotFound, e:
            abort(404, _('User not found'))
        except:
            abort(500, _('Error'))

        # Send Validation email
        self.send_validation_email(user, token)

        post_register_url = h.url_for(
            controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
            action='post_register')
        redirect_url = '{0}?user={1}'
        h.redirect_to(redirect_url.format(
            post_register_url,
            user['id']))

    def send_validation_email(self, user, token):
        validate_link = h.url_for(
            controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
            action='validate',
            token=token['token'])
        link = '{0}{1}'
        subject = "Please verify your email address"
        print 'Validate link: ' + validate_link
        html = """\
        <html>
          <head></head>
          <body>
            <p>Thank you for your interest in HDX. In order to continue registering your account, please verify your email address by simply clicking below.</p>
            <p><a href="{link}">Verify Email</a></p>
          </body>
        </html>
        """.format(link=link.format(config['ckan.site_url'], validate_link))

        try:
            # mailer.mail_recipient(user['name'], user['email'], subject, body)
            hdx_mailer.mail_recipient('User', user['email'], subject, html)
            return True
        except:
            return False

    def error_message(self, error_summary):
        return json.dumps({'success': False, 'error': {'message': error_summary}})

    def _validate_new_org_request_field(self, data):
        errors = {}
        for field in ['title', 'description', 'your_email', 'your_name']:
            if data[field].strip() == '':
                errors[field] = [_('should not be empty')]

        if len(errors) > 0:
            raise logic.ValidationError(errors)

    def _process_new_org_request(self, user):
        data = {'name': request.params.get('name', ''),
                'title': request.params.get('name', ''),
                'org_url': request.params.get('url', ''),
                'description': request.params.get('description', ''),
                'your_email': user.email,
                'your_name': user.fullname,
                }
        return data

    def is_valid_captcha(self, response):
        url = configuration.config.get('hdx.captcha.url')
        secret = configuration.config.get('ckan.recaptcha.privatekey')
        params = {'secret': secret, "response": response}
        r = requests.get(url, params=params, verify=True)
        res = json.loads(r.content)
        return 'success' in res and res['success'] == True
