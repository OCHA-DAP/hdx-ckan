'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_users.model as user_model
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, c

get_action = logic.get_action


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


def get_user_extra(user_id=None):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}
    id = c.userobj.id if user_id is None else user_id

    data_dict = {'user_obj': c.userobj, 'user_id': id,
                 'extras': {'key': user_model.HDX_ONBOARDING_USER_VALIDATED, 'value': 'True'}}
    result = {
        'data': {
            'user_id': id,
            'extra': get_action('user_extra_show')(context, data_dict),
        }
    }
    return result
