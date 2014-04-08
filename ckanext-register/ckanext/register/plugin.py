import ckan.plugins as plugins

def user_create(context, data_dict=None):
    #Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}


class DisableUserRegistration(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthFunctions)

    def get_auth_functions(self):
        return {'user_create': user_create}
