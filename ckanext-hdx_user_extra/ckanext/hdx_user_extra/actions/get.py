'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model
import ckan.plugins.toolkit as tk

NotFound = tk.ObjectNotFound


@tk.side_effect_free
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
    user_extra_dict_list = [ue.as_dict() for ue in user_extra_list]

    return user_extra_dict_list


@tk.side_effect_free
def user_extra_value_by_key_show(context, data_dict):
    '''
    Retrieves user extra list based on 'user_id'
    :param context:
    :param data_dict: contains the user_id
    :return: list of user extra filtered by user_id
    '''
    user_id = data_dict.get('user_id')
    key = data_dict.get('key')
    if not user_id or not key:
        return NotFound("user id or key not provided")
    user_extra_obj = ue_model.UserExtra.get(user_id=user_id, key=key)
    if user_extra_obj is None:
        raise NotFound('Pair user id and key not found')
    # user_extra_dict_list = [ue.as_dict() for ue in user_extra_list]
    return {
      user_extra_obj.key: user_extra_obj.value
    }
