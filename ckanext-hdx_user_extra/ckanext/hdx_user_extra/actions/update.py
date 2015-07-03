'''
Created on July 2nd, 2015

@author: dan
'''

import ckanext.hdx_user_extra.model as ue_model
import ckan.logic as logic

NotFound = logic.NotFound


def user_extra_update(context, data_dict):
    '''
    Updates an user_extra record in database
    :param context:
    :param data_dict: contains 'extras' which is a list of dictionaries. An extras contains 'user_id', 'key',
    and 'new_value'
    :return: list of extras updated
    '''
    session = context['session']
    result = []
    for ue in data_dict.get('extras'):
        user_extra = ue_model.UserExtra.get(user_id=ue['user_id'], key=ue['key'])
        if user_extra is None:
            raise NotFound
        user_extra.value = ue['new_value']
        session.add(user_extra)
        session.commit()
        result.append(user_extra)
    return result
