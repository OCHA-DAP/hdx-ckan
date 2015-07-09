'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_users.model as user_model


def get_default_extras():
    result = []
    for us in user_model.USER_STATUSES:
        result.append({'key': us, 'value': 'False'})
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