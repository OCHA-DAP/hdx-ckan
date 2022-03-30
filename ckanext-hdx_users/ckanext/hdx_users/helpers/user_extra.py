'''
Created on July 2nd, 2015

@author: dan
'''

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model

get_action = tk.get_action
_ = tk._
g = tk.g


def get_default_extras():
    result = []
    for us in user_model.USER_STATUSES:
        result.append({'key': us, 'value': 'False'})
    result.append({'key': user_model.HDX_FIRST_NAME, 'value': ''})
    result.append({'key': user_model.HDX_LAST_NAME, 'value': ''})
    return result


def get_initial_extras():
    result = get_default_extras()
    result = update_extras(result, {user_model.HDX_ONBOARDING_USER_REGISTERED: 'True'})
    return result


def update_extras(extras, data_dict):
    for ex in extras:
        if ex['key'] in data_dict:
            ex['value'] = data_dict[ex['key']]
    return extras


def get_user_extra(user_id=None):
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj}
    id = g.userobj.id if user_id is None else user_id

    data_dict = {'user_obj': g.userobj, 'user_id': id}
    user_extra_list = get_action('user_extra_show')(context, data_dict)
    crt_step = get_current_step(user_extra_list)
    result = {
        'data': {
            'user_id': id,
            'current_step': crt_step,
            'extra': user_extra_list,
        }
    }
    if crt_step == user_model.HDX_ONBOARDING_FIRST_LOGIN:
        data_dict['extras'] = [{'key': user_model.HDX_ONBOARDING_FIRST_LOGIN, 'new_value': 'True'}]
        get_action('user_extra_update')(context, data_dict)
    return result


def get_login(success=True, message=None):
    return get_current_step_dict(user_model.HDX_LOGIN, success, message)


def get_register(success=True, message=None):
    return get_current_step_dict(user_model.HDX_REGISTER, success, message)


def get_new_login(success=True, message=None):
    return get_current_step_dict(user_model.HDX_FIRST_LOGIN, success, message)


def get_logout(success=True, message=None):
    return get_current_step_dict(user_model.HDX_LOGOUT, success, message)


def get_current_step_dict(step, success=True, message=None):
    result = {
        'data': {
            'current_step': step,
            'success': success,
            'message': message
        }
    }
    return result


def get_current_step(extra):
    us_dict = {}
    for ex in extra:
        us_dict[ex.get('key')] = ex.get('value')
    for step in user_model.USER_STATUSES:
        if us_dict.get(step) == 'False':
            return step
    return None
