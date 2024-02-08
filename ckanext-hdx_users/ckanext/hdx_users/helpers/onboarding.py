from typing import (Any, Union)
import ckan.plugins.toolkit as tk
import ckan.model as model

get_action = tk.get_action
check_access = tk.check_access
g = tk.g

HDX_ONBOARDING_CAME_FROM = 'hdx_onboarding_came_from'
HDX_ONBOARDING_CAME_FROM_STATE = 'hdx_onboarding_came_from_state'


def get_onboarding_came_from() -> Union[str, None]:
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj}

    user_id = g.userobj.id

    check_access('user_extra_show', context, {'user_id': user_id})

    ue_user = get_action('user_extra_value_by_keys_show')(context, {'user_id': user_id,
                                                                        'keys': [HDX_ONBOARDING_CAME_FROM,
                                                                                 HDX_ONBOARDING_CAME_FROM_STATE]})

    came_from, state = _get_user_extra(ue_user)
    if state == 'inactive':
        return None
    if state == 'active' and came_from:
        return came_from
    return None


def _get_user_extra(ue_user):
    state = 'inactive'
    came_from = None
    for ue_item in ue_user:
        if ue_item.get('key') == HDX_ONBOARDING_CAME_FROM_STATE:
            state = ue_item.get('value')
        if ue_item.get('key') == HDX_ONBOARDING_CAME_FROM:
            came_from = ue_item.get('value')
    return came_from, state
