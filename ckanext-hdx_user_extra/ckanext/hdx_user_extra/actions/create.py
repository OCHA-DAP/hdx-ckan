'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model


def user_extra_create(context, data_dict):
    '''
    Creates an  user extra in database
    :param context:
    :param data_dict: contains 'user_id' and a dictionary 'extras' with pairs (key,value) to be added in db
    :return: list of user_extra objects added in db
    '''
    result = []
    model = context['model']
    for extras in data_dict['extras']:
        user_extra = ue_model.UserExtra(user_id=data_dict['user_id'], key=extras['key'], value=extras['value'])
        model.Session.add(user_extra)
        model.Session.commit()
        result.append(user_extra)
    return result
