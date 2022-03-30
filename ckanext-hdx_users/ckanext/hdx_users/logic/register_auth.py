'''
Created on July 2nd, 2015

@author: dan
'''
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.tokens as tokens

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
    token = tokens.token_show_by_id(context, data_dict)

    if not token:
        return {'success': False, 'msg': 'User has no token'}

    if not token['valid']:
        return {'success': True}
    else:
        return {'success': False, 'msg': 'User already validated'}
