import ckanext.hdx_users.model as umodel
import ckan.logic as logic

NotFound = logic.NotFound
_check_access = logic.check_access


def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    #Logged in user should have edit access to account token belongs to
    _check_access('user_update',context, {'id':token_obj.user_id})
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()
