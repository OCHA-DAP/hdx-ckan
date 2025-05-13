import json
from sqlalchemy import case
import ckan.model as core_model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model
import ckan.lib.dictization.model_dictize as model_dictize
from ckanext.hdx_users.helpers.reset_password import make_key
from ckanext.hdx_users.helpers.helpers import generate_password, generate_username, NotAuthorized
from ckanext.hdx_users.logic.schema import onboarding_default_user_schema

_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
get_action = tk.get_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})

USER_STATE_SHADOW = 'shadow'

def token_create(context, user):
    _check_access('user_create', context, None)
    model = context['model']
    key = make_key()
    token_obj = user_model.ValidationToken(user_id=user['id'], token=key, valid=False)
    model.Session.add(token_obj)
    model.Session.commit()
    return token_obj.as_dict()


def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})


@tk.chained_action
def user_create(up_func, context, data_dict):
    """
    Perform user_create with a modified default schema.

    This function overrides the default schema used for creating new users with a modified schema. By default,
    it uses the schema specified by the 'onboarding_default_user_schema' function. If a schema is already provided
    in the context, it will use that instead.
    """
    context['schema'] = context.get('schema') or onboarding_default_user_schema()

    result = up_func(context, data_dict)
    return result

def hdx_shadow_user_create(context, data_dict):
    _check_access('hdx_shadow_user_create', context, None)

    email = _get_or_bust(data_dict, 'email')

    state_order = case(
        (core_model.User.state == core_model.State.ACTIVE, 1),
        (core_model.User.state == USER_STATE_SHADOW, 2),
        (core_model.User.state == core_model.State.DELETED, 3),
        (core_model.User.state == core_model.State.PENDING, 4),
        else_=5
    )

    q = core_model.Session.query(core_model.User)
    q = q.filter(core_model.User.email == email)
    q = q.order_by(state_order, core_model.User.created.desc())
    user_obj = q.first()

    user_dictize_context = context.copy()

    if user_obj:
        if user_obj.state == core_model.State.ACTIVE or user_obj.state == USER_STATE_SHADOW:
            user_dict = model_dictize.user_dictize(user_obj, user_dictize_context, include_plugin_extras=False)
            user_dict['action_performed'] = 'none'
            return user_dict
        if user_obj.state == core_model.State.PENDING:
            user_dict = get_action('user_patch')(
                context,
                {
                    'id': user_obj.id,
                    'state': USER_STATE_SHADOW,
                },
            )
            user_dict['action_performed'] = 'from-pending-to-shadow'
            return user_dict

    if not user_obj or user_obj.state == core_model.State.DELETED:
        context['schema'] = onboarding_default_user_schema()
        data_dict['state'] = USER_STATE_SHADOW
        data_dict['password'] = data_dict['password1'] = generate_password(32)
        data_dict['fullname'] = data_dict['name'] = generate_username(12, 24)
        try:
            user_dict = get_action('user_create')(context, data_dict)
            user_dict['action_performed'] = 'created-shadow-account'
        except Exception:
            raise NotAuthorized
        return user_dict

    raise NotFound
