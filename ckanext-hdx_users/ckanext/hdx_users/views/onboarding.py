import logging
from typing import Any, Optional, Union, cast

from flask import Blueprint
from flask.views import MethodView
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.model as model
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.logic.schema as schema
import ckanext.hdx_users.helpers.tokens as tokens
import ckan.lib.navl.dictization_functions as dictization_functions

from ckan.common import (
    config, current_user
)
from ckan.types import Context, Schema, Response, DataDict
from ckanext.hdx_users.controller_logic.onboarding_username_confirmation_logic import send_username_confirmation_email
from ckanext.hdx_users.helpers.constants import ONBOARDING_CAME_FROM_EXTRAS_KEY, ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY, \
    ONBOARDING_MAILCHIMP_OPTIN_KEY
from ckanext.hdx_users.views.user_view_helper import CaptchaNotValid, OnbCaptchaErr, error_message

log = logging.getLogger(__name__)

# shortcuts
h = tk.h
get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
redirect = h.redirect_to
check_access = tk.check_access
abort = tk.abort
render = tk.render
g = tk.g
_ = tk._
request = tk.request

hdx_user_onboarding = Blueprint(u'hdx_user_onboarding', __name__, url_prefix=u'/signup')


def _new_form_to_db_schema() -> Schema:
    return schema.onboarding_user_new_form_schema()


def _save_user_info_in_extras(user_dict: DataDict, data_dict: DataDict) -> list[dict[str, Any]]:
    context_for_user_extra = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': user_dict.get('name'),
        u'auth_user_obj': model.User.by_name(user_dict.get('name')),
    })
    came_from = data_dict.get('came_from', None)
    extras = [
        {
            'key': ONBOARDING_CAME_FROM_EXTRAS_KEY,
            'value': came_from
        },
        {
            'key': ONBOARDING_CAME_FROM_STATE_EXTRAS_KEY,
            'value': 'active'
        },
    ]
    if 'user_info_accept_emails' in data_dict and data_dict.get('user_info_accept_emails') == 'true':
        extras.append({
            'key': ONBOARDING_MAILCHIMP_OPTIN_KEY,
            'value': data_dict.get('user_info_accept_emails', None)
        })
    else:
        extras.append({
            'key': ONBOARDING_MAILCHIMP_OPTIN_KEY,
            'value': 'false'
        })

    ue_create = get_action('user_extra_create')(context_for_user_extra,
                                                {'user_id': user_dict.get('id'), 'extras': extras})
    return ue_create


def _prepare() -> Context:
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
        u'schema': _new_form_to_db_schema(),
        u'save': u'save' in request.form
    })
    try:
        check_access(u'user_create', context)
        check_access(u'onboarding_user_can_register', context)
    except NotAuthorized:
        abort(403, _(u'Unauthorized to register as a user.'))
    return context


class UserOnboardingView(MethodView):

    def post(self) -> Union[Response, str]:
        context = _prepare()
        try:
            data_dict = logic.clean_dict(
                dictization_functions.unflatten(
                    logic.tuplize_dict(logic.parse_params(request.form))))

        except dictization_functions.DataError:
            abort(400, _(u'Integrity Error'))

        # captcha check
        try:
            is_captcha_enabled: object = config.get('hdx.captcha', 'false')
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
            return error_message('Something went wrong. Please contact support.')

        # user create
        try:
            data_dict['state'] = model.State.PENDING
            user_dict = get_action(u'user_create')(context, data_dict)
            # save came from in user extras
            _save_user_info_in_extras(user_dict, data_dict)
        except NotAuthorized:
            abort(403, _(u'Unauthorized to create user %s') % u'')
        except NotFound:
            abort(404, _(u'User not found'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(data_dict, errors, error_summary)
        except Exception as e:
            log.error(e)
            abort(404, _(u'Something went wrong. Please contact support'))

        # TODO send user validation token
        token = get_action('token_create')(context, user_dict)
        subject = h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['EMAIL_SUBJECTS']['EMAIL_CONFIRMATION']
        tokens.send_validation_email(
            user_dict,
            token,
            subject,
            'email/content/onboarding/email_confirmation.html',
            validation_link=h.url_for('hdx_user_onboarding.validate_account', token=token['token'], qualified=True)
        )

        extra_vars = {
            u'email_address': user_dict.get('email'),
        }
        return render('onboarding/signup/verify-email.html', extra_vars=extra_vars)

    def get(self,
            data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None) -> str:

        _prepare()

        extra_vars = {
            u'data': data or {},
            u'errors': errors or {},
            u'error_summary': error_summary or {}
        }
        aux = render('onboarding/signup/user-info.html', extra_vars=extra_vars)
        return aux


def value_proposition() -> str:
    _prepare()
    return render('onboarding/signup/value-proposition.html', extra_vars={})


def validate_account(token: str) -> str:
    try:
        check_access('user_can_validate', {}, {'token': token})
    except NotAuthorized as e:
        log.warning('Cannot find token: ' + e.message)
        return abort(404, 'Page not found')
    context = {'session': model.Session, 'model': model}
    user_dict = tokens.activate_user_and_disable_token(context, {'token': token})
    if not user_dict:
        log.error('Something went wrong when trying to activate user with email validation token')
        return abort(500, 'Something went wrong.')

    template_data = {
        'fullname': user_dict.get('fullname', ''),
        'url': h.url_for('hdx_user_auth.new_login')
    }
    send_username_confirmation_email(user_dict)
    return render('onboarding/signup/account-validated.html', extra_vars=template_data)


hdx_user_onboarding.add_url_rule(u'/', view_func=value_proposition, strict_slashes=False)
hdx_user_onboarding.add_url_rule(u'/user-info/', view_func=UserOnboardingView.as_view(str(u'user-info')),
                                 methods=[u'GET', u'POST'], strict_slashes=False)
hdx_user_onboarding.add_url_rule(u'/validate-account/<token>/', view_func=validate_account,
                                 methods=[u'GET'], strict_slashes=False)
