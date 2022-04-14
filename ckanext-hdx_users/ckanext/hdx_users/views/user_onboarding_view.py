import logging as logging
import ckan.logic as logic
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.model as user_model
from ckan import model
from six import text_type
from ckan.plugins import toolkit as tk
from ckanext.hdx_users.views.user_view_helper import *

abort = tk.abort
g = tk.g
_ = tk._
request = tk.request
h = tk.h
_check_access = tk.check_access
_get_action = tk.get_action
config = tk.config
render = tk.render
_get_validator = tk.get_validator
log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
_validate = dictization_functions.validate

NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError


class HDXUserOnboardingView:
    def __init__(self):
        pass

    def follow_details(self):
        """
        Step 4: user follows key entities
        :return:
        """
        data_dict = logic.clean_dict(unflatten(logic.tuplize_dict(logic.parse_params(request.form))))
        name = g.user or data_dict['id']
        user_obj = model.User.get(name)
        user_id = user_obj.id
        context = {'model': model, 'session': model.Session, 'user': user_obj.name, 'auth_user_obj': g.userobj}
        try:
            ue_dict = self._get_ue_dict(user_id, user_model.HDX_ONBOARDING_FOLLOWS)
            _get_action('user_extra_update')(context, ue_dict)
        except NotAuthorized:
            return OnbNotAuth
        except NotFound as e:
            return OnbUserNotFound
        except DataError:
            return OnbIntegrityErr
        except ValidationError as e:
            error_summary = e.error_summary
            return error_message(error_summary)
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)
        return OnbSuccess

    def request_new_organization(self):
        '''
        Step 5a: user can request to create a new organization
        :return:
        '''
        context = {'model': model, 'session': model.Session, 'auth_user_obj': g.userobj,
                   'user': g.user}
        try:
            _check_access('hdx_send_new_org_request', context)
        except NotAuthorized:
            return OnbNotAuth

        try:
            user = model.User.get(context['user'])
            data = self._process_new_org_request(user)
            self._validate_new_org_request_field(data, context)

            _get_action('hdx_send_new_org_request')(context, data)

            if data.get('user_extra'):
                ue_dict = self._get_ue_dict(user.id, user_model.HDX_ONBOARDING_ORG)
                _get_action('user_extra_update')(context, ue_dict)

        except hdx_mail.NoRecipientException as e:
            error_summary = str(e)
            return error_message(error_summary)
        except ValidationError as e:
            error_summary = e.error_summary.get('Message') if 'Message' in e.error_summary else e.error_summary
            return error_message(error_summary)
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)
        return OnbSuccess

    def request_membership(self):
        '''
        Step 5b: user can request membership to an existing organization
        :return:
        '''

        context = {'model': model, 'session': model.Session,
                   'user': g.user, 'auth_user_obj': g.userobj}
        try:
            _check_access('hdx_send_new_org_request', context)
        except NotAuthorized:
            return OnbNotAuth

        try:
            org_id = request.form.get('org_id', '')
            msg = request.form.get('message', 'please add me to this organization')

            data_dict = {
                'organization': org_id,
                'message': msg,
                'save': u'save',
                'role': u'member',
                'group': org_id
            }
            member = _get_action('member_request_create')(context, data_dict)

            ue_dict = self._get_ue_dict(g.userobj.id, user_model.HDX_ONBOARDING_ORG)
            _get_action('user_extra_update')(context, ue_dict)

        except hdx_mail.NoRecipientException as e:
            return error_message(_(str(e)))
        except ValidationError as e:
            log.error(str(e))
            if isinstance(e.error_summary, dict):
                error_summary = ' '.join(e.error_summary.values())
            else:
                error_summary = json.dumps(e.error_summary)
            return error_message(error_summary)
        except Exception as e:
            log.error(str(e))
            return error_message(_('Request can not be sent. Contact an administrator.'))
        return OnbSuccess

    def invite_friends(self):
        '''
        Step 6: user can invite friends by email to access HDX
        :return:
        '''

        context = {'model': model, 'session': model.Session, 'auth_user_obj': g.userobj,
                   'user': g.user}
        try:
            _check_access('hdx_basic_user_info', context)
        except NotAuthorized:
            return OnbNotAuth
        try:
            if not g.user:
                return OnbNotAuth
            # usr = g.userobj.display_name or g.user
            user_id = g.userobj.id or g.user
            ue_dict = self._get_ue_dict(user_id, user_model.HDX_ONBOARDING_FRIENDS)
            _get_action('user_extra_update')(context, ue_dict)

            subject = u'Invitation to join the Humanitarian Data Exchange (HDX)'
            email_data = {
                'user_fullname': g.userobj.fullname,
                'user_email': g.userobj.email,
            }
            cc_recipients_list = [{'display_name': g.userobj.fullname, 'email': g.userobj.email}]
            friends = [request.form.get('email1'), request.form.get('email2'), request.form.get('email3')]
            for f in friends:
                if f and config.get('hdx.onboarding.send_confirmation_email', 'false') == 'true':
                    hdx_mailer.mail_recipient([{'display_name': f, 'email': f}], subject, email_data,
                                              cc_recipients_list=cc_recipients_list,
                                              snippet='email/content/onboarding_invite_others.html')
        except Exception as e:
            error_summary = str(e)
            return error_message(error_summary)
        return OnbSuccess

    def _get_ue_dict(self, user_id, key, value='True'):
        ue_dict = self._build_extras_dict(key, value)
        ue_dict['user_id'] = user_id
        return ue_dict

    def _build_extras_dict(self, key, value='True'):
        return {'extras': [{'key': key, 'new_value': value}]}

    def _process_new_org_request(self, user):
        data = {'name': request.form.get('name', ''),
                # 'title': request.form.get('name', ''),
                'description': request.form.get('description', ''),
                'description_data': request.form.get('description_data', ''),
                'work_email': request.form.get('work_email', ''),
                'org_url': request.form.get('url', ''),
                'acronym': request.form.get('acronym', ''),
                'org_type': request.form.get('org_type') if request.form.get('org_type') != '-1' else '',
                'your_email': request.form.get('your_email') or user.email,
                'your_name': request.form.get('your_name') or user.fullname or user.name,
                'user_extra': request.form.get('user_extra') if request.form.get('user_extra') == 'True' else None
                }
        return data

    def _validate_new_org_request_field(self, data, context):
        errors = {}
        for field in ['name', 'description', 'description_data', 'work_email', 'your_name', 'your_email']:
            if data[field] is None or data[field].strip() == '':
                errors[field] = [_('should not be empty')]

        if len(errors) > 0:
            raise ValidationError(errors)

        user_email_validator = _get_validator('email_validator')
        schema = {'work_email': [user_email_validator, text_type]}
        data_dict, _errors = _validate(data, schema, context)

        if _errors:
            raise ValidationError(_errors.get('work_email'))
