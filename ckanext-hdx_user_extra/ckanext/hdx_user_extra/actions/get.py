'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model
import ckan.logic as logic

NotFound = logic.NotFound


def user_extra_show(context, data_dict):
    '''
    Retrieves user extra list based on 'user_id'
    :param context:
    :param data_dict: contains the user_id
    :return: list of user extra filtered by user_id
    '''
    user_id = data_dict.get('user_id')
    user_extra_list = ue_model.UserExtra.get_by_user(user_id=user_id)
    if user_extra_list is None:
        raise NotFound
    return user_extra_list
