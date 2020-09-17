import ckan.model as model
import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import ckanext.hdx_users.model as user_model

NotFound = logic.NotFound
_check_access = logic.check_access
get_action = logic.get_action


def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    # Logged in user should have edit access to account token belongs to
    _check_access('user_update', context, {'id': token_obj.user_id})
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()


def user_fullname_update(context, data_dict):
    # Logged in user should have edit access to account token belongs to
    _check_access('user_update', context, {'id': data_dict.get('id')})
    first_name = data_dict.get('first_name')
    last_name = data_dict.get('last_name')
    fullname = first_name + ' ' + last_name
    user_obj = model.User.get(data_dict.get('id'))
    if not user_obj:
        raise NotFound('User id not found')
    ue_data_dict = {'user_id': user_obj.id, 'extras': [
        {'key': user_model.HDX_FIRST_NAME, 'new_value': first_name},
        {'key': user_model.HDX_LAST_NAME, 'new_value': last_name},
    ]}
    ue_result = get_action('user_extra_update')(context, ue_data_dict)
    return ue_result
