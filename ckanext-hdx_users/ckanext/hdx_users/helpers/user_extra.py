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
