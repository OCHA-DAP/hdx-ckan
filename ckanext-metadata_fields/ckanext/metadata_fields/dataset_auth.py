import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.new_authz as new_authz
from ckan.common import _

def package_create(context, data_dict=None):
	#return {'success':False, 'msg':'Testing this shit'}

    user_name = context['user']
    #Is the user logged in?
    convert_user_name_or_id_to_id = toolkit.get_converter('convert_user_name_or_id_to_id')
    if not 'session' in context and 'model' in context:
        context['session'] = context['model'].Session

	try:
		user_id = convert_user_name_or_id_to_id(user_name, context)
	except:
		return {'success':False, 'msg':'You must be logged in to create a dataset'}

	#If we want to all org members to be able to upload
	#orgs = toolkit.get_action('organization_list_for_user')(data_dict={'permission':'member'})
	#print 'orgs ' + orgs

	data_dict = data_dict or {}
	org_id = data_dict.get('organization_id')
	if org_id and not new_authz.has_user_permission_for_group_or_org(org_id, user_id, 'create_dataset'):
		return {'success': False, 'msg': _('User %s not authorized to add dataset to this organization') % user_id}
	
	return {'success':True}

class DatasetIAuthFunctionsPlugin(plugins.SingletonPlugin):
	plugins.implements(plugins.IAuthFunctions)

	def get_auth_functions(self):
		return {'package_create':package_create}