import json
import hashlib
import ckan.logic as logic
import ckan.model as model
import logging as logging
from ckan.common import _, request, config, c
import ckan.lib.navl.dictization_functions as dictization_functions
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.logic.schema as user_reg_schema
from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH
from ckanext.hdx_users.controllers.mail_validation_controller import name_validator_with_changed_msg
import ckanext.hdx_users.helpers.user_extra as ue_helpers
import ckanext.hdx_users.helpers.tokens as tokens
from mailchimp3 import MailChimp

log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound
DataError = dictization_functions.DataError
CaptchaNotValid = _('Captcha is not valid')
OnbCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})
OnbNotAuth = json.dumps({'success': False, 'error': {'message': _('Unauthorized to create user')}})
OnbTokenNotFound = json.dumps({'success': False, 'error': {'message': 'Token not found'}})
OnbIntegrityErr = json.dumps({'success': False, 'error': {'message': 'Integrity Error'}})
OnbSuccess = json.dumps({'success': True})

class HDXRegisterView:
    def __init__(self):
        pass

    def register_email(self, data=None, errors=None, error_summary=None):

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
            return self.error_message(error_summary)
        except Exception as e:
            log.error(e)
            # error_summary = e.error_summary
            return self.error_message('Something went wrong. Please contact support.')

        """
        STEP 1: user register the email
        """
        temp_schema = user_reg_schema.register_user_schema()
        if 'name' in temp_schema:
            temp_schema['name'] = [name_validator_with_changed_msg if var == name_validator else var for var in
                                   temp_schema['name']]
        context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj,
                   'schema': temp_schema, 'save': 'save' in request.params}

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
                # return self.error_message(['The email address is already registered on HDX. Please use the sign in screen below.'])
                return self.error_message(self._get_exc_msg_by_key(e, 'email'))
            return OnbNotAuth
        except ValidationError as e:
            # errors = e.error_dict
            if e and e.error_summmary:
                error_summary = e.error_summary
            else:
                error_summary = ['Email address is not valid. Please contact our team.']
            return self.error_message(error_summary)

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
        except NotFound as e:
            return OnbTokenNotFound
            # abort(404, _('User not found'))
        except DataError:
            return OnbIntegrityErr
            # abort(400, _(u'Integrity Error'))
        except ValidationError as e:
            # errors = e.error_dict
            error_summary = e.error_summary
            return self.error_message(error_summary)
        except Exception as e:
            error_summary = str(e)
            return self.error_message(error_summary)

        if not c.user:
            # Send validation email
            tokens.send_validation_email(user, token)

        c.user = save_user
        return OnbSuccess

    def error_message(self, error_summary):
        return json.dumps({'success': False, 'error': {'message': error_summary}})

    def _signup_newsletter(self, data):
        if 'signup' in data:
            signup = data['signup']
            if signup == "true":
                log.info("Will signup to newsletter: " + signup)
                m = self._get_mailchimp_api()
                try:
                    m.ping.get()
                    list_id = config.get('hdx.mailchimp.list.newsletter')
                    if (list_id):
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

