'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model
import ckan.plugins.toolkit as tk
_check_access = tk.check_access


def user_extra_create(context, data_dict):
    '''
    Creates an  user extra in database
    :param context:
    :param data_dict: contains 'user_id' and a list 'extras' with pairs (key,value) to be added in db
    :return: list of user_extra objects added in db
    '''
    result = []
    model = context['model']
    _check_access('user_extra_create', context, data_dict)
    for extra in data_dict['extras']:
        user_extra = ue_model.UserExtra(user_id=data_dict['user_id'], key=extra['key'], value=extra['value'])
        model.Session.add(user_extra)
        model.Session.commit()
        result.append(user_extra.as_dict())
    return result
