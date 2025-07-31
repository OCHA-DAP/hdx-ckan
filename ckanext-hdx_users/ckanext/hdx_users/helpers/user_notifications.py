import ckan.model as core_model
from ckanext.hdx_users.actions.create import USER_STATE_SHADOW


def get_shadow_user_obj_by_email(email):
    if not email:
        return None
    email = email.lower()
    q = core_model.Session.query(core_model.User)
    q = q.filter(core_model.User.email == email)
    q = q.filter(core_model.User.state == USER_STATE_SHADOW)
    user_obj = q.first()
    if user_obj:
        return user_obj
    return None
