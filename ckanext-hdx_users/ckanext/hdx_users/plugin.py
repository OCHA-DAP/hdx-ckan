import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.hdx_users.actions.create as create
import ckanext.hdx_users.actions.get as get
import ckanext.hdx_users.actions.update as update
import ckanext.hdx_users.logic.register_auth as authorize
import ckanext.hdx_users.helpers.user_extra as h_user_extra
import ckanext.hdx_users.logic.validators as hdx_validators
import ckanext.hdx_users.model as users_model


def user_create(context, data_dict=None):
    # Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}


class HDXValidatePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {}

    def is_fallback(self):
        return False

    def before_map(self, map):
        map.redirect('/user/', '/user')
        map.connect('user_generate_apikey', '/user/generate_key/{id}', action='generate_apikey', controller='user')
        map.connect('/user/register',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='register')
        map.connect('/user/register_email',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='register_email')
        map.connect('/user/request_new_organization',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='request_new_organization')
        map.connect('/user/register_details',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='register_details')
        map.connect('/user/follow_details',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='follow_details')
        map.connect('/user/request_membership',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='request_membership')
        map.connect('/user/invite_friends',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='invite_friends')
        map.connect('/user/validate/{token}',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='validate')
        map.connect('/user/post_register',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action="post_register")
        map.connect('/user/validation_resend/{id}',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action="validation_resend")
        map.connect('/user/logged_out_page',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='logged_out_page')
        # map.connect('/user/logged_out',
        #             controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
        #             action='logged_out')
        map.connect('/user/logged_out_redirect',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='logged_out_page')
        map.connect('/user/logged_in',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='logged_in')
        map.connect('/login',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='new_login')
        map.connect('/user/first_login',
                    controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
                    action='first_login')
        return map

    def after_map(self, map):
        return map

    def get_actions(self):
        return {
            'token_create': create.token_create,
            'token_update': update.token_update,
            'onboarding_followee_list': get.onboarding_followee_list,
            'hdx_send_reset_link': get.hdx_send_reset_link
        }

    def get_auth_functions(self):
        return {'user_can_register': authorize.user_can_register,
                'user_can_validate': authorize.user_can_validate}

    # IConfigurable
    def configure(self, config):
        users_model.setup()


class HDXUsersPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {'get_user_extra': h_user_extra.get_user_extra,
                'get_login': h_user_extra.get_login}

    def is_fallback(self):
        return False

    def before_map(self, map):
        map.connect('user_dashboard', '/dashboard',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard',
                    ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard_datasets',
                    ckan_icon='sitemap')
        map.connect('user_dashboard_visualizations', '/dashboard/visualizations',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard_visualizations',
                    ckan_icon='sitemap')
        map.connect('/user/register',
                    controller='ckanext.hdx_users.controllers.registration_controller:RequestController',
                    action='register')
        map.connect('/user/logged_in', controller='ckanext.hdx_users.controllers.login_controller:LoginController',
                    action='logged_in')
        map.connect('/user/reset', controller='ckanext.hdx_users.controllers.login_controller:LoginController',
                    action='request_reset')
        map.connect('/contribute', controller='ckanext.hdx_users.controllers.login_controller:LoginController',
                    action='contribute')
        map.connect('/contact_hdx', controller='ckanext.hdx_users.controllers.login_controller:LoginController',
                    action='contact_hdx')
        map.connect('/save_mapexplorer_config', controller='ckanext.hdx_users.controllers.login_controller:LoginController',
                    action='save_mapexplorer_config')
        # Included to fix fussiness when overriding user profile route
        map.connect('/user/edit', controller='user', action='edit')
        map.connect('/user/activity/{id}/{offset}', controller='user', action='activity')
        map.connect('user_activity_stream', '/user/activity/{id}',
                    controller='user', action='activity', ckan_icon='time')
        map.connect('user_follow', '/user/follow/{id}', controller='user', action='follow')
        map.connect('/user/unfollow/{id}', controller='user', action='unfollow')
        map.connect('user_followers', '/user/followers/{id:.*}',
                    controller='user', action='followers', ckan_icon='group')
        map.connect('user_edit', '/user/edit/{id:.*}', controller='user', action='edit',
                    ckan_icon='cog')
        map.connect('user_delete', '/user/delete/{id}', controller='user', action='delete')
        map.connect('register', '/user/register', controller='user', action='register')
        map.connect('login', '/user/login', controller='user', action='login')
        map.connect('/user/_logout', controller='user', action='logout')
        map.connect('/user/logged_in', controller='user', action='logged_in')
        map.connect('/user/logged_out', controller='user', action='logged_out')
        map.connect('/user/logged_out_redirect', controller='user', action='logged_out_page')
        # map.connect('/user/reset', controller='user', action='request_reset')
        map.connect('/user/me', controller='user', action='me')
        map.connect('/user/reset/{id:.*}', controller='user', action='perform_reset')
        map.connect('/user/set_lang/{lang}', controller='user', action='set_lang')

        # requestdata mapping
        user_controller = 'ckanext.requestdata.controllers.user:UserController'
        request_data_controller = 'ckanext.requestdata.controllers.request_data:RequestDataController'
        map.connect('requestdata_my_requests',
                    '/user/my_requested_data/{id}',
                    controller=user_controller,
                    action='my_requested_data', ckan_icon='list')

        map.connect('requestdata_handle_new_request_action',
                    '/user/my_requested_data/{username}/' +
                    '{request_action:reply|reject}',
                    controller='ckanext.hdx_users.controllers.requestdata_controller:HDXRequestdataController',
                    action='handle_new_request_action')

        map.connect('requestdata_handle_open_request_action',
                    '/user/my_requested_data/{username}/' +
                    '{request_action:shared|notshared}',
                    controller=user_controller,
                    action='handle_open_request_action')

        map.connect('requestdata_send_request', '/request_data',
                    controller=request_data_controller,
                    action='send_request')


        #######
        map.connect('user_datasets', '/user/{id:.*}',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='read',
                    ckan_icon='sitemap')
        map.connect('delete_page', '/dashboard/visualization/delete/{id}', controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='hdx_delete_powerview',)
        return map

    def after_map(self, map):
        map.connect('user_dashboard', '/dashboard',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard',
                    ckan_icon='list')
        map.connect('user_dashboard_datasets', '/dashboard/datasets',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard_datasets',
                    ckan_icon='sitemap')
        map.connect('user_dashboard_visualizations', '/dashboard/visualizations',
                    controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController',
                    action='dashboard_visualizations',
                    ckan_icon='sitemap')
        return map

    def get_actions(self):
        return {

        }

    def get_validators(self):
        return {
            'user_email_validator': hdx_validators.user_email_validator
        }
