import ckan.plugins as plugins
import ckan.logic.auth.create as create
import ckan.logic.auth.update as update
import logging

log = logging.getLogger(__name__)
# def package_create(context, data_dict=None):
#     #return {'success':False, 'msg':'Testing this shit'}
# 
#     user_name = context['user']
#     #Is the user logged in?
#     convert_user_name_or_id_to_id = toolkit.get_converter('convert_user_name_or_id_to_id')
#     if not 'session' in context and 'model' in context:
#         context['session'] = context['model'].Session
# 
#     try:
#         user_id = convert_user_name_or_id_to_id(user_name, context)
#     except:
#         return {'success':False, 'msg':'You must be logged in to create a dataset'}
# 
#     #If we want to all org members to be able to upload
#     #orgs = toolkit.get_action('organization_list_for_user')(data_dict={'permission':'member'})
#     #print 'orgs ' + orgs
# 
#     data_dict = data_dict or {}
#     org_id = data_dict.get('organization_id')
#     if org_id and not new_authz.has_user_permission_for_group_or_org(org_id, user_id, 'create_dataset'):
#         return {'success': False, 'msg': _('User %s not authorized to add dataset to this organization') % user_id}
#     
#     return {'success':True}


def package_create(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth 
        log.info('Removed groups from data_dict: ' + str(data_dict))
        retvalue = create.package_create(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = create.package_create(context, data_dict)

    return retvalue


def package_update(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth 
        log.info('Removed groups from data_dict: ' + str(data_dict))
        retvalue = update.package_update(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = update.package_update(context, data_dict)

    return retvalue


class DatasetIAuthFunctionsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthFunctions)

    def get_auth_functions(self):
        return {'package_create': package_create,
                'package_update': package_update}
