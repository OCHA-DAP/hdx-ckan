import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import pylons.config as config

NotFound = logic.NotFound

def token_show(context, user):
    id = user.get('id')
    token_obj = umodel.ValidationToken.get(user_id=id)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def token_show_by_id(context, data_dict):
    token = data_dict.get('token', None)
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()

def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()
