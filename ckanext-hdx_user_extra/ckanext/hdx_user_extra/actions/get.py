'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model
import ckan.plugins.toolkit as tk

NotFound = tk.ObjectNotFound
_check_access = tk.check_access


@tk.side_effect_free
def user_extra_show(context, data_dict):
    '''
    Retrieves user extra list based on 'user_id'
    :param context:
    :param data_dict: contains the user_id
    :return: list of user extra filtered by user_id
    '''
    _check_access('user_extra_show', context, data_dict)
    user_id = data_dict.get('user_id')
    user_extra_list = ue_model.UserExtra.get_by_user(user_id=user_id)
    if user_extra_list is None:
        raise NotFound
    user_extra_dict_list = [ue.as_dict() for ue in user_extra_list]

    return user_extra_dict_list


@tk.side_effect_free
def user_extra_value_by_key_show(context, data_dict):
    '''
    Retrieves user extra based on 'user_id' and 'key'
    :param context:
    :param data_dict: contains the user_id, key
    :return: user extra key and value
    '''
    _check_access('user_extra_show', context, data_dict)
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

@tk.side_effect_free
def user_extra_value_by_keys_show(context, data_dict):
    '''
    Retrieves user extra based on 'user_id' and 'keys'
    :param context:
    :param data_dict: contains the user_id, keys
    :return: user extra list
    '''
    _check_access('user_extra_show', context, data_dict)
    user_id = data_dict.get('user_id', None)
    keys = data_dict.get('keys', None)
    if not user_id or not keys:
        return NotFound("user id or key not provided")
    user_extra_list = ue_model.UserExtra.get_by_user(user_id=user_id)
    if user_extra_list is None:
        raise NotFound('Information not found for user')
    user_extra_dict_list = [ue.as_dict() for ue in user_extra_list if ue.key in keys]
    return user_extra_dict_list
