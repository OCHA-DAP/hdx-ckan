import hashlib
import json
import ckan.logic as logic
import ckanext.hdx_users.model as user_model

ValidationError = logic.ValidationError
_check_access = logic.check_access
NotFound = logic.NotFound
get_action = logic.get_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})


def token_create(context, user):
    _check_access('user_create', context, None)
    model = context['model']
    token = hashlib.md5()
    token.update(user['email'] + user['name'])
    token_obj = user_model.ValidationToken(user_id=user['id'], token=token.hexdigest(), valid=False)
    model.Session.add(token_obj)
    model.Session.commit()
    return token_obj.as_dict()


@logic.side_effect_free
def hdx_first_login(context, data_dict):
    _check_access('hdx_first_login', context, data_dict)
    data_dict = {'extras': [{'key': user_model.HDX_ONBOARDING_FIRST_LOGIN, 'new_value': 'True'}]}
    user = context.get('auth_user_obj', None)
    if user:
        try:
            data_dict['user_id'] = user.id
            get_action('user_extra_update')(context, data_dict)
        except NotFound, e:
            raise NotFound('User not found')
        except Exception, e:
            return error_message(str(e))
    else:
        raise NotFound('User not found')
    return True


def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})
