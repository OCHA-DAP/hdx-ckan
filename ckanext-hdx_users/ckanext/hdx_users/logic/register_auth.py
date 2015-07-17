'''
Created on July 2nd, 2015

@author: dan
'''
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dictization_functions

get_action = logic.get_action

_validate = dictization_functions.validate
ValidationError = logic.ValidationError


@logic.auth_allow_anonymous_access
def user_can_register(context, data_dict=None):
    schema = context['schema'] or None
    data, errors = _validate(data_dict, schema, context)
    if errors:
        return {'success': False, 'msg': errors}

    return {'success': True}


@logic.auth_allow_anonymous_access
def user_can_validate(context, data_dict=None):
    token = get_action('token_show_by_id')(context, data_dict)

    if not token:
        return {'success': False, 'msg': 'User has no token'}

    if not token['valid']:
        return {'success': True}
    else:
        return {'success': False, 'msg': 'User already validated'}
