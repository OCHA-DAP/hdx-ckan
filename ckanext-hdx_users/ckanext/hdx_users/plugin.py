import ckanext.hdx_users.actions.create as create
import ckanext.hdx_users.actions.get as get
import ckanext.hdx_users.actions.misc as misc
import ckanext.hdx_users.actions.update as update
import ckanext.hdx_users.actions.delete as delete
import ckanext.hdx_users.helpers.user_extra as h_user_extra
import ckanext.hdx_users.helpers.helpers as hdx_h
import ckanext.hdx_users.actions.auth as auth
import ckanext.hdx_users.logic.register_auth as authorize
import ckanext.hdx_users.logic.validators as hdx_validators
import ckanext.hdx_users.model as users_model
import ckanext.hdx_users.views.user as hdx_user
import ckanext.hdx_users.views.dashboard as dashboard
import ckanext.hdx_users.views.api as api
import ckanext.hdx_users.views.user_checks_login as ucl
import ckanext.hdx_users.views.permission as permission
import ckanext.hdx_users.views.requestdata_user_view as rduv
import ckanext.hdx_users.views.requestdata_view as rdv
import ckanext.hdx_users.views.user_register_view as urv

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def user_create(context, data_dict=None):
    # Disable registering new users
    return {'success': False, 'msg': 'Registering is disabled at the moment!'}


class HDXValidatePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=False)
    # plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def is_fallback(self):
        return False

    def get_actions(self):
        return {
            'token_create': create.token_create,
            'token_update': update.token_update,
            'onboarding_followee_list': get.onboarding_followee_list,
            'hdx_send_reset_link': update.hdx_send_reset_link,
            'hdx_send_new_org_request': misc.hdx_send_new_org_request,
            'hdx_first_login': create.hdx_first_login,
            'user_delete': delete.hdx_user_delete
        }

    def get_auth_functions(self):
        return {
            'user_can_register': authorize.user_can_register,
            'user_can_validate': authorize.user_can_validate,
            'hdx_first_login': auth.hdx_first_login,
        }

    # IConfigurable
    def configure(self, config):
        users_model.setup()

    # IBlueprint
    def get_blueprint(self):
        return [
            hdx_user.user,
            hdx_user.hdx_login_link
        ]


class HDXUsersPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IBlueprint)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {
            'get_user_extra': h_user_extra.get_user_extra,
            'get_login': h_user_extra.get_login,
            'find_first_global_settings_url': hdx_h.find_first_global_settings_url,
            'hdx_get_user_notifications': hdx_h.hdx_get_user_notifications
        }

    def is_fallback(self):
        return False

    def get_actions(self):
        return {
            'hdx_user_autocomplete': get.hdx_user_autocomplete,
            'hdx_user_fullname_show': get.hdx_user_fullname_show,
            'user_show': get.user_show,
            'notify_users_about_api_token_expiration': update.notify_users_about_api_token_expiration,
        }

    def get_auth_functions(self):
        return {
            'hdx_send_new_org_request': auth.hdx_send_new_org_request,
            'manage_permissions': auth.manage_permissions,
            'user_update': auth.user_update,
            'notify_users_about_api_token_expiration': auth.notify_users_about_api_token_expiration,
        }

    def get_validators(self):
        return {
            'user_email_validator': hdx_validators.user_email_validator,
            'user_name_validator': hdx_validators.user_name_validator
        }

    # IBlueprint
    def get_blueprint(self):
        return [
            dashboard.hdx_user_dashboard,
            api.hdx_user_autocomplete,
            ucl.hdx_contribute,
            ucl.hdx_contact_hdx,
            permission.hdx_user_permission,
            rduv.hdx_requestdata_user,
            rdv.requestdata_send_request,
            urv.user_register
        ]
