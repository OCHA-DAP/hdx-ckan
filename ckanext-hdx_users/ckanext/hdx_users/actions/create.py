import ckanext.hdx_users.model as umodel
import hashlib
import ckan.logic as logic

ValidationError = logic.ValidationError
_check_access = logic.check_access


def token_create(context, user):
    _check_access('user_create',context, None)
    model = context['model']
    token = hashlib.md5()
    token.update(user['email'] + user['name'])
    token_obj = umodel.ValidationToken(user_id=user['id'], token=token.hexdigest(), valid=False)
    model.Session.add(token_obj)
    model.Session.commit()

    return token_obj.as_dict()
