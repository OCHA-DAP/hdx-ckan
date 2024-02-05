'''
Created on July 2nd, 2015

@author: dan
'''
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as umodel

from ckanext.hdx_users.helpers.reset_password import ResetKeyHelper

get_action = tk.get_action

_validate = dictization_functions.validate
ValidationError = tk.ValidationError


@tk.auth_allow_anonymous_access
def user_can_register(context, data_dict=None):
    schema = context['schema'] or None
    data, errors = _validate(data_dict, schema, context)
    if errors:
        return {'success': False, 'msg': errors}

    return {'success': True}


@tk.auth_allow_anonymous_access
def user_can_validate(context, data_dict=None):
    token_str = data_dict.get('token', None)
    token_obj = umodel.ValidationToken.get_by_token(token=token_str)

    if not token_obj:
        return {'success': False, 'msg': 'User has no token'}

    # Confusingly, valid is False when the token was not used yet
    if not token_obj.valid and not ResetKeyHelper(token_obj.token).is_expired():
        return {'success': True}
    else:
        return {'success': False, 'msg': 'Token no longer usable'}
