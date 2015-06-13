import ckanext.hdx_users.model as umodel
import ckan.logic as logic
NotFound = logic.NotFound

def token_show(context, user):
	model = context['model']
	id = user.get('id')
	token_obj = umodel.ValidationToken.get(user_id=id)
	if token_obj is None:
            raise NotFound
	return token_obj.as_dict()

