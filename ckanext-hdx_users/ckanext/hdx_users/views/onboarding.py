import logging
from typing import Any, Optional, Union, cast

from flask import Blueprint
from flask.views import MethodView

import ckan.logic as logic
import ckan.model as model
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.logic.schema as schema
import ckanext.hdx_users.helpers.tokens as tokens

from ckan.common import (
    config, current_user
)
from ckan.types import Context, Schema, Response, DataDict
from ckanext.hdx_users.helpers.onboarding import HDX_ONBOARDING_CAME_FROM, HDX_ONBOARDING_CAME_FROM_STATE
from ckanext.hdx_users.views.user_view_helper import *

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


def _save_came_from_in_user_extras(data_dict: DataDict,
                                   user_dict: DataDict) -> list[dict[str, Any]]:
    came_from = data_dict.get('came_from', None)
    context_for_user_extra = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': user_dict.get('name'),
        u'auth_user_obj': model.User.by_name(user_dict.get('name')),
        u'schema': _new_form_to_db_schema(),
        u'save': u'save' in request.form
    })
    extras = [
        {
            'key': HDX_ONBOARDING_CAME_FROM,
            'value': came_from
        },
        {
            'key': HDX_ONBOARDING_CAME_FROM_STATE,
            'value': 'active'
        }
    ]
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
            user_extra = _save_came_from_in_user_extras(data_dict, user_dict)
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
            'email/content/onboarding_email_validation.html'
        )

        # TODO render&redirect the verify your email address page
        extra_vars = {
            # TODO add relevant data
        }
        return self.get(data_dict, {}, {})

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


def value_proposition():
    _prepare()
    return render('onboarding/signup/value-proposition.html', extra_vars={})


hdx_user_onboarding.add_url_rule(u'/', view_func=value_proposition, strict_slashes=False)
hdx_user_onboarding.add_url_rule(u'/user-info', view_func=UserOnboardingView.as_view(str(u'user-info')),
                                 methods=[u'GET', u'POST'])