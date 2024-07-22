import json

import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model

from ckanext.hdx_users.helpers.reset_password import make_key
from ckanext.hdx_users.logic.schema import onboarding_default_user_schema

ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
get_action = tk.get_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})


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
