import ckanext.hdx_users.actions.create as create
import ckanext.hdx_users.actions.get as get
import ckanext.hdx_users.actions.misc as misc
import ckanext.hdx_users.actions.update as update
import ckanext.hdx_users.actions.delete as delete
import ckanext.hdx_users.helpers.helpers as hdx_h
import ckanext.hdx_users.actions.auth as auth
import ckanext.hdx_users.logic.register_auth as authorize
import ckanext.hdx_users.logic.validators as hdx_validators
import ckanext.hdx_users.model as users_model
import ckanext.hdx_users.views.user as hdx_user
# import ckanext.hdx_users.views.user_auth_view as user_auth_view
import ckanext.hdx_users.views.dashboard as dashboard
import ckanext.hdx_users.views.api as api
# import ckanext.hdx_users.views.user_checks_login as ucl
import ckanext.hdx_users.views.permission as permission
import ckanext.hdx_users.views.requestdata_user_view as rduv
import ckanext.hdx_users.views.onboarding as onboarding
import ckanext.hdx_users.views.signin as signin
import ckanext.hdx_users.views.notification_platform as notification_platform

import ckanext.security.validators as security_validators

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
            'hdx_send_reset_link': update.hdx_send_reset_link,
            'hdx_send_new_org_request': misc.hdx_send_new_org_request,
            'hdx_send_request_data_auto_approval': misc.hdx_send_request_data_auto_approval,
            'user_delete': delete.hdx_user_delete,
            'user_update': update.user_update,
            'user_create': create.user_create,
        }

    def get_auth_functions(self):
        return {
            'user_can_register': authorize.user_can_register,
            'user_can_validate': authorize.user_can_validate,
            'onboarding_user_can_register': authorize.onboarding_user_can_register,
        }

    # IConfigurable
    def configure(self, config):
        users_model.setup()

    # IBlueprint
    def get_blueprint(self):
        return [
            hdx_user.user,
            # user_auth_view.hdx_user_auth
        ]

@toolkit.blanket.config_declarations
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
            'find_first_global_settings_url': hdx_h.find_first_global_settings_url,
            'hdx_get_user_notifications': hdx_h.hdx_get_user_notifications
        }

    def is_fallback(self):
        return False

    def get_actions(self):
        return {
            'hdx_user_autocomplete': get.hdx_user_autocomplete,
            'notify_users_about_api_token_expiration': update.notify_users_about_api_token_expiration,
            'hdx_add_notification_subscription': update.hdx_add_notification_subscription,
            'hdx_delete_notification_subscription': delete.hdx_delete_notification_subscription,
        }

    def get_auth_functions(self):
        return {
            'hdx_send_new_org_request': auth.hdx_send_new_org_request,
            'manage_permissions': auth.manage_permissions,
            'user_update': auth.user_update,
            'notify_users_about_api_token_expiration': auth.notify_users_about_api_token_expiration,
            'hdx_send_request_data_auto_approval': auth.hdx_send_request_data_auto_approval,
            'hdx_add_notification_subscription': auth.hdx_add_notification_subscription,
            'hdx_delete_notification_subscription': auth.hdx_delete_notification_subscription,
        }

    def get_validators(self):
        return {
            'user_email_validator': hdx_validators.user_email_validator,
            'user_password_validator': security_validators.user_password_validator,
            # 'user_name_validator': hdx_validators.user_name_validator,
            'user_emails_match': hdx_validators.user_emails_match,
        }

    # IBlueprint
    def get_blueprint(self):
        return [
            dashboard.hdx_user_dashboard,
            api.hdx_user_autocomplete,
            # ucl.hdx_contribute,
            # ucl.hdx_contact_hdx,
            permission.hdx_user_permission,
            rduv.hdx_requestdata_user,
            onboarding.hdx_user_onboarding,
            signin.hdx_signin,
            notification_platform.hdx_notifications,
        ]
