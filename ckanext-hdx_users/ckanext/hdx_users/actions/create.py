import ckanext.hdx_users.model as umodel
import md5

def token_create(context, user):
	model = context['model']
	token = md5.new()
	token.update(user['email']+user['name'])
	token_obj = umodel.ValidationToken(user_id=user['id'], token=token.hexdigest(), valid=False)
	model.Session.add(token_obj)
	model.Session.commit()

	return token_obj.as_dict()
