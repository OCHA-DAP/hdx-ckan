import ckanext.hdx_users.model as umodel
import ckan.logic as logic
NotFound = logic.NotFound

def token_update(context, user):
	session = context["session"]
	token = user.get('token')
	token_obj = umodel.ValidationToken.get_by_token(token=token)
	if token_obj is None:
		raise NotFound
	token_obj.valid=True
	session.add(token_obj)
	session.commit()
	return token_obj.as_dict()
