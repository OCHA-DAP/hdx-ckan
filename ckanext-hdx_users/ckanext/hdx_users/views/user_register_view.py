import hashlib
import logging as logging

from mailchimp3 import MailChimp
from sqlalchemy.exc import IntegrityError
import ckan.lib.base as base
import ckan.model as model
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.tokens as tokens
import ckanext.hdx_users.helpers.user_extra as ue_helpers
import ckanext.hdx_users.logic.schema as user_reg_schema
import ckanext.hdx_users.model as user_model
from ckan.common import request, config, c
from ckan.logic.validators import name_validator
from ckanext.hdx_users.controllers.mail_validation_controller import name_validator_with_changed_msg
from ckanext.hdx_users.views.user_view_helper import *

log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
render = base.render
abort = base.abort


class HDXRegisterView:
    def __init__(self):
        pass

    def register_email(self):
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.form))))

        try:
            is_captcha_enabled = config.get('hdx.captcha', 'false')
            if is_captcha_enabled == 'true':
                captcha_response = data_dict.get('g-recaptcha-response', None)
                if not usr_h.is_valid_captcha(captcha_response=captcha_response):
                    raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
        except ValidationError as e:
            error_summary = e.error_summary
            if error_summary == CaptchaNotValid:
                return OnbCaptchaErr
            return error_message(error_summary)
        except Exception as e:
            log.error(e)
            # error_summary = e.error_summary
            return error_message('Something went wrong. Please contact support.')

        """
        STEP 1: user register the email
        """
        temp_schema = user_reg_schema.register_user_schema()
        if 'name' in temp_schema:
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]
        context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj,
                   'schema': temp_schema, 'save': 'save' in request.form}

        if 'email' in data_dict:
            md5 = hashlib.md5()
            md5.update(data_dict['email'])
            data_dict['name'] = md5.hexdigest()
        context['message'] = data_dict.get('log_message', '')

        try:
            check_access('user_create', context, data_dict)
            check_access('user_can_register', context, data_dict)
        except NotAuthorized as e:
            if e.args and len(e.args):
                # return error_message(['The email address is already registered on HDX. Please use the sign in screen below.'])
                return error_message(self._get_exc_msg_by_key(e, 'email'))
            return OnbNotAuth
        except ValidationError as e:
            # errors = e.error_dict
            if e and e.error_summmary:
                error_summary = e.error_summary
            else:
                error_summary = ['Email address is not valid. Please contact our team.']
            return error_message(error_summary)

        # hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        try:

            user = get_action('user_create')(context, data_dict)
            token = get_action('token_create')(context, user)
            context['auth_user_obj'] = context['user_obj']
            user_extra = get_action('user_extra_create')(context, {'user_id': user['id'],
                                                                   'extras': ue_helpers.get_initial_extras()})
            is_mailchimp_enabled = config.get('hdx.mailchimp', 'false')
            if 'email' in data_dict and 'nosetest' not in data_dict and is_mailchimp_enabled == 'true':
                self._signup_newsletter(data_dict)
                self._signup_newsuser(data_dict)
        except NotAuthorized:
            return OnbNotAuth
            # abort(401, _('Unauthorized to create user %s') % '')
        except NotFound:
            return OnbTokenNotFound
            # abort(404, _('User not found'))
        except DataError:
            return OnbIntegrityErr
            # abort(400, _(u'Integrity Error'))
        except ValidationError as e:
            # errors = e.error_dict
            error_summary = e.error_summary
            return error_message(error_summary)
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)

        if not c.user:
            # Send validation email
            tokens.send_validation_email(user, token)

        c.user = save_user
        return OnbSuccess

    def register_details(self):
        """
        Step 3: user enters details for registration (username, password, firstname, lastname and captcha
        :return:
        """
        temp_schema = user_reg_schema.register_details_user_schema()
        if 'name' in temp_schema:
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.form))))
        user_obj = model.User.get(data_dict['id'])
        context = {'model': model, 'session': model.Session, 'user': user_obj.name,
                   'schema': temp_schema}
        # data_dict['name'] = data_dict['email']
        first_name = data_dict['first-name']
        last_name = data_dict['last-name']
        data_dict['fullname'] = first_name + ' ' + last_name
        try:
            # is_captcha_enabled = configuration.config.get('hdx.captcha', 'false')
            # if is_captcha_enabled == 'true':
            #     captcha_response = data_dict.get('g-recaptcha-response', None)
            #     if not self.is_valid_captcha(response=captcha_response):
            #         raise ValidationError(CaptchaNotValid, error_summary=CaptchaNotValid)
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            return OnbNotAuth
        # except ValidationError, e:
        #     error_summary = e.error_summary
        #     if error_summary == CaptchaNotValid:
        #         return OnbCaptchaErr
        #     return error_message(error_summary)
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)
        # hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        try:
            token_dict = tokens.token_show(context, data_dict)
            data_dict['token'] = token_dict['token']
            get_action('user_update')(context, data_dict)
            tokens.token_update(context, data_dict)

            # ue_dict = self._get_ue_dict(data_dict['id'], user_model.HDX_ONBOARDING_USER_VALIDATED)
            # get_action('user_extra_update')(context, ue_dict)
            #
            # ue_dict = self._get_ue_dict(data_dict['id'], user_model.HDX_ONBOARDING_DETAILS)
            # get_action('user_extra_update')(context, ue_dict)

            ue_data_dict = {'user_id': data_dict.get('id'), 'extras': [
                {'key': user_model.HDX_ONBOARDING_USER_VALIDATED, 'new_value': 'True'},
                {'key': user_model.HDX_ONBOARDING_DETAILS, 'new_value': 'True'},
                {'key': user_model.HDX_FIRST_NAME, 'new_value': first_name},
                {'key': user_model.HDX_LAST_NAME, 'new_value': last_name},
            ]}
            get_action('user_extra_update')(context, ue_data_dict)

            if config.get('hdx.onboarding.send_confirmation_email') == 'true':
                link = config['ckan.site_url'] + '/login'
                full_name = data_dict.get('fullname')
                subject = u'Thank you for joining the HDX community!'
                email_data = {
                    'user_first_name': first_name,
                    'username': data_dict.get('name'),
                }
                hdx_mailer.mail_recipient([{'display_name': full_name, 'email': data_dict.get('email')}], subject,
                                          email_data, footer=data_dict.get('email'),
                                          snippet='email/content/onboarding_confirmation_of_registration.html')

        except NotAuthorized:
            return OnbNotAuth
        except NotFound:
            return OnbUserNotFound
        except DataError:
            return OnbIntegrityErr
        except ValidationError as e:
            error_summary = ''
            if 'Name' in e.error_summary:
                error_summary += str(e.error_summary.get('Name'))
            if 'Password' in e.error_summary:
                error_summary += str(e.error_summary.get('Password'))
            return error_message(error_summary or e.error_summary)
        except IntegrityError:
            return OnbExistingUsername
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)
        c.user = save_user
        return OnbSuccess

    def register(self):
        """
        Creates a new user, but allows logged in users to create
        additional accounts as per HDX requirements at the time.
        """
        context = {'model': model, 'session': model.Session, 'user': c.user}
        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(403, _('Unauthorized to register as a user.'))
        if c.user:
            # #1799 Don't offer the registration form if already logged in
            return render('user/logout_first.html')
        template_data = {}
        if not c.user:
            template_data = ue_helpers.get_register(True, "")
        return render('home/index.html', extra_vars=template_data)

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
            return error_message(error_summary)

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
            return error_message(error_summary)

        user = model.User.get(data_dict['user_id'])
        template_data = ue_helpers.get_user_extra(user_id=data_dict['user_id'])
        template_data['data']['current_step'] = user_model.HDX_ONBOARDING_DETAILS
        template_data['data']['email'] = user.email
        template_data['data']['name'] = user.name
        template_data['capcha_api_key'] = config.get('ckan.recaptcha.publickey')
        return render('home/index.html', extra_vars=template_data)

    def _signup_newsletter(self, data):
        if 'signup' in data:
            signup = data['signup']
            if signup == "true":
                log.info("Will signup to newsletter: " + signup)
                m = self._get_mailchimp_api()
                try:
                    m.ping.get()
                    list_id = config.get('hdx.mailchimp.list.newsletter')
                    if list_id:
                        m.lists.members.create(list_id, {
                            'email_address': data['email'],
                            'status': 'subscribed'
                        })
                except Exception as ex:
                    log.error(ex)
                signup = signup
        return None

    def _signup_newsuser(self, data):
        m = self._get_mailchimp_api()
        try:
            m.ping.get()
            list_id = config.get('hdx.mailchimp.list.newuser')
            if list_id:
                m.lists.members.create(list_id, {
                    'email_address': data['email'],
                    'status': 'subscribed'
                })
        except Exception as ex:
            log.error(ex)

        return None

    def _get_mailchimp_api(self):
        return MailChimp(config.get('hdx.mailchimp.api.key'))

    def _get_exc_msg_by_key(self, e, key):
        if e and e.args:
            for arg in e.args:
                if key in arg:
                    return arg[key]
        return None
