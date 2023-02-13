import logging

import ckan.lib.plugins as lib_plugins
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import ckanext.hdx_org_group.actions.authorize as authorize
import ckanext.hdx_org_group.actions.create as create_actions
import ckanext.hdx_org_group.actions.get as get_actions
import ckanext.hdx_org_group.actions.update as update_actions
import ckanext.hdx_org_group.helpers.custom_validator as org_custom_validator
import ckanext.hdx_org_group.helpers.static_lists as static_lists
import ckanext.hdx_org_group.model as org_group_model
import ckanext.hdx_org_group.views.organization as org
import ckanext.hdx_theme.helpers.custom_validator as custom_validator
from ckanext.hdx_org_group.helpers.analytics import OrganizationCreateAnalyticsSender

log = logging.getLogger(__name__)


class HDXOrgGroupPlugin(plugins.SingletonPlugin, lib_plugins.DefaultOrganizationForm):
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer, inherit=False)
    # plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IGroupForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IOrganizationController, inherit=True)
    plugins.implements(plugins.IDomainObjectModification, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    # IConfigurable
    def configure(self, config):
        org_group_model.setup()
        org_group_model.create_table()

    def get_helpers(self):
        from ckanext.hdx_org_group.helpers import organization_helper as hdx_org_h
        return {
            'hdx_organization_type_list': hdx_org_h.hdx_organization_type_list,
            'hdx_organization_type_get_value': hdx_org_h.hdx_organization_type_get_value
        }

    def get_actions(self):
        from ckanext.hdx_org_group.helpers import organization_helper as hdx_org_actions
        return {
            'hdx_get_group_activity_list': hdx_org_actions.hdx_get_group_activity_list,
            'hdx_light_group_show': get_actions.hdx_light_group_show,
            'hdx_topline_num_for_group': get_actions.hdx_topline_num_for_group,
            'hdx_datasets_for_group': get_actions.hdx_datasets_for_group,
            'organization_update': hdx_org_actions.hdx_organization_update,
            'organization_create': hdx_org_actions.hdx_organization_create,
            'organization_delete': hdx_org_actions.hdx_organization_delete,
            'group_update': hdx_org_actions.hdx_group_update,
            'group_create': hdx_org_actions.hdx_group_create,
            'group_delete': hdx_org_actions.hdx_group_delete,
            'organization_member_delete': hdx_org_actions.organization_member_delete,
            'organization_member_create': hdx_org_actions.organization_member_create,
            'hdx_trigger_screencap': get_actions.hdx_trigger_screencap,
            'hdx_get_locations_info_from_rw': get_actions.hdx_get_locations_info_from_rw,
            'invalidate_data_completeness_for_location': update_actions.invalidate_data_completeness_for_location,
            'hdx_organization_follower_list': get_actions.hdx_organization_follower_list,
            'hdx_user_invite': create_actions.hdx_user_invite,
            'member_create':  create_actions.hdx_member_create

        }

    def get_auth_functions(self):
        return {
            'hdx_trigger_screencap': authorize.hdx_trigger_screencap,
            'member_delete': authorize.member_delete,
            'invalidate_data_completeness_for_location': authorize.invalidate_data_completeness_for_location,
            'hdx_organization_follower_list': authorize.hdx_organization_follower_list
        }

    # def get_auth_functions(self):
    #     return {
    #             'hdx_basic_user_info': helpers.auth.hdx_basic_user_info,
    #             'group_member_create': helpers.auth.group_member_create,
    #             'hdx_send_new_org_request': helpers.auth.hdx_send_new_org_request,
    #             'hdx_send_editor_request_for_org': helpers.auth.hdx_send_editor_request_for_org,
    #             'hdx_send_request_membership': helpers.auth.hdx_send_request_membership
    #             }

    # IGroupForm
    def is_fallback(self):
        return False

    # IGroupForm
    def group_types(self):
        return ['organization']

    # IGroupForm
    def setup_template_variables(self, context, data_dict):
        org.new_org_template_variables(context, data_dict)

    # IValidators
    def get_validators(self):
        org_type_keys = [t[1] for t in static_lists.ORGANIZATION_TYPE_LIST]
        return {
            'correct_hdx_org_type': custom_validator.general_value_in_list(org_type_keys, False),
            'hdx_org_keep_prev_value_if_empty_unless_sysadmin': org_custom_validator.hdx_org_keep_prev_value_if_empty_unless_sysadmin,
            'active_if_missing': org_custom_validator.active_if_missing

        }

    def _modify_group_schema(self, schema):
        schema.update({
            'description': [tk.get_validator('not_empty')],
            'org_url': [tk.get_validator('not_missing'), tk.get_converter('convert_to_extras')],
            'fts_id': [tk.get_validator('hdx_org_keep_prev_value_if_empty_unless_sysadmin'),
                       tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'user_survey_url': [tk.get_validator('hdx_org_keep_prev_value_if_empty_unless_sysadmin'),
                                tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')],
            'custom_org': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'request_membership': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'customization': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            # 'less': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'visualization_config': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'modified_at': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'hdx_org_type': [tk.get_validator('not_empty'), tk.get_validator('correct_hdx_org_type'),
                             tk.get_converter('convert_to_extras')],
            'org_acronym': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
        })
        return schema

    # IGroupForm
    def form_to_db_schema(self):
        schema = super(HDXOrgGroupPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

    #     def check_data_dict(self, data_dict):
    #         return super(HDXOrgFormPlugin, self).check_data_dict(self, data_dict)

    # def default_show_group_schema(self):
    #     schema = core_schema.default_show_group_schema()
    #     schema.update({'description': [tk.get_validator('not_empty')]})
    #     schema.update({'org_url': [tk.get_converter('convert_from_extras'), tk.get_validator('not_missing')]})
    #     schema.update({'fts_id': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     schema.update({'custom_org': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     schema.update({'customization': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     schema.update({'less': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     schema.update({'visualization_config': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     schema.update({'modified_at': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
    #     return schema

    # IGroupForm
    def db_to_form_schema(self):
        # There's a bug in dictionary validation when form isn't present
        try:
            schema = super(HDXOrgGroupPlugin, self).form_to_db_schema()
            new_org_schema = {
                'description': [tk.get_validator('not_empty')],
                'org_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'fts_id': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'user_survey_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'custom_org': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'request_membership': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'customization': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                # 'less': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'visualization_config': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'modified_at': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'hdx_org_type': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
                'org_acronym': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],

                'package_count': [],
                'packages': {'__extras': [tk.get_converter('keep_extras')]},
                'users': {'__extras': [tk.get_converter('keep_extras')]},
                'num_followers': [],
                'created': [],
                'state': [],
                'display_name': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],

            }
            schema.update(new_org_schema)
            return schema
        except TypeError as e:
            log.warn('Exception in db_to_form_schema: {}'.format(str(e)))

        return None

    # def after_map(self, map):
        # map.connect('organization_read', '/organization/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='read')
        # map.connect('organization_members', '/organization/members/{id}',
        #             controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
        #             action='members')
        # map.connect('organization_activity', '/organization/activity/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='activity_stream')
        # map.connect('organization_activity', '/organization/activity/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='activity_stream')
        # map.connect('organization_activity_offset', '/organization/activity/{id}/{offset}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='activity_stream')
        # return map

    # def before_map(self, map):
        # map.connect('organization_bulk_process',
        #             '/organization/bulk_process/{org_id}',
        #             controller='ckanext.hdx_org_group.controllers.redirect_controller:RedirectController',
        #             action='redirect_to_org_list')
        # map.connect('organization_bulk_process_no_id', '/organization/bulk_process',
        #             controller='ckanext.hdx_org_group.controllers.redirect_controller:RedirectController',
        #             action='redirect_to_org_list')
        # map.connect('organizations_index', '/organization',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='index')
        # map.connect('organization_new', '/organization/new',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='new')
        # map.connect('organization_edit', '/organization/edit/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='edit', ckan_icon='edit')
        # map.connect('request_membership', '/organization/{org_id}/request_membership',
        #             controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController', action='request_membership')
        # map.connect('request_editing_rights', '/organization/{org_id}/request_editing_rights',
        #             controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController',
        #             action='request_editor_for_org')
        # map.connect('/organization/request_new',
        #             controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController',
        #             action='request_new_organization')
        # map.connect('organization_members',
        #             '/organization/members/{id}',
        #             controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
        #             action='members')
        # map.connect(
        #     '/organization/member_new/{id}',
        #     controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
        #     action='member_new')
        # map.connect(
        #     '/organization/member_delete/{id}',
        #     controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
        #     action='member_delete')

        # map.connect('/organization/bulk_member_new/{id}',
        #             controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController',
        #             action='bulk_member_new')

        # map.connect('organization_activity', '/organization/activity/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='activity_stream'
        #             # conditions={'function': organization_controller.is_not_custom}
        #             )
        # map.connect('organization_activity_offset', '/organization/activity/{id}/{offset:([0-9]+)}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='activity_stream')
        # map.connect('custom_org_activity', '/organization/activity/{id}',
        #             controller='ckanext.hdx_org_group.controllers.custom_org_controller:CustomOrgController',
        #             action='activity_stream')

        # since the pattern of organization_read is so general it needs to be the last
        # otherwise it will override other /organization routes
        # map.connect('organization_read', '/organization/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='read')

        # map.connect('hdx_organization_stats', '/organization/stats/{id}',
        #             controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #             action='stats')

        # map.connect('browse_list', '/browse',
        #            controller='ckanext.hdx_org_group.controllers.browse_controller:BrowseController', action='index')

        # map.connect('browse_list', '/browse',
        #             controller='ckanext.hdx_org_group.controllers.redirect_controller:RedirectController',
        #             action='redirect_to_group_list')

        # map.connect('group_index', '/group',
        #             controller='ckanext.hdx_org_group.controllers.group_controller:HDXGroupController', action='index',
        #             highlight_actions='index search')
        # map.connect('group_worldmap', '/worldmap',
        #             controller='ckanext.hdx_org_group.controllers.group_controller:HDXGroupController', action='group_worldmap')
        #
        # map.connect('group_eaa_worldmap', '/eaa-worldmap',
        #             controller='ckanext.hdx_org_group.controllers.group_controller:HDXGroupController', action='group_eaa_worldmap')

        # map.connect('group_new', '/group/new', controller='group', action='new')

        # map.connect('country_read', '/group/{id}',
        #             controller='ckanext.hdx_org_group.controllers.country_controller:CountryController', action='country_read')
        #
        # map.connect('country_topline', '/country/topline/{id}',
        #             controller='ckanext.hdx_org_group.controllers.country_controller:CountryController', action='country_topline')

        # map.connect('feed_org_atom', '/feeds/organization/{id}.atom', controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
        #     action='feed_organization')

        # map.connect(
        #    'custom_org_read', '/org/{id}', controller='ckanext.hdx_org_group.controllers.custom_org_controller:CustomOrgController', action='org_read')

        # return map

    # IOrganizationController
    def create(self, org):
        OrganizationCreateAnalyticsSender(org.name,
                                          org.hdx_org_type if hasattr(org, 'hdx_org_type') else None).send_to_queue()
        from ckanext.hdx_package.helpers.caching import add_org_in_cache_organization_list
        add_org_in_cache_organization_list(org.id)

    # IOrganizationController
    def edit(self, org):
        # tk.get_action('invalidate_cache_for_organizations')({'ignore_auth': True}, {})
        from ckanext.hdx_package.helpers.caching import replace_org_in_cache_organization_list
        replace_org_in_cache_organization_list(org.id)

    # IOrganizationController
    def delete(self, org):
        tk.get_action('invalidate_cache_for_organizations')({'ignore_auth': True}, {})

    # IBlueprint
    def get_blueprint(self):
        import ckanext.hdx_org_group.views.light_organization as light_org
        import ckanext.hdx_org_group.views.redirect as redirect
        import ckanext.hdx_org_group.views.members as members
        return [
            org.hdx_org,
            light_org.hdx_light_org,
            redirect.hdx_org_group_redirect,
            members.hdx_members,
        ]


class HDXGroupPlugin(plugins.SingletonPlugin, lib_plugins.DefaultGroupForm):
    '''
    This plugin only contains the schema changes that are specific to the group entity
    '''

    plugins.implements(plugins.IGroupForm, inherit=False)
    plugins.implements(plugins.IGroupController, inherit=True)
    plugins.implements(plugins.IBlueprint)

    def group_types(self):
        return ['group']

    def is_fallback(self):
        return True

    def _modify_group_schema(self, schema):
        _clean_alert_bar_title_when_no_url = \
            tk.get_converter('hdx_clean_field_based_on_other_field_wrapper')('alert_bar_url')
        schema.update({
            'language_code': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'relief_web_url': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'hr_info_url': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'alert_bar_title': [
                _clean_alert_bar_title_when_no_url,
                tk.get_validator('ignore_empty'),
                tk.get_validator('unicode_only'),
                tk.get_validator('hdx_check_string_length_wrapper')(40),
                tk.get_converter('convert_to_extras')
            ],
            'alert_bar_url': [
                tk.get_validator('ignore_empty'),
                tk.get_validator('unicode_only'),
                tk.get_validator('hdx_is_url'),
                tk.get_converter('convert_to_extras')
            ],
            'geojson': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            # 'custom_loc': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            # 'customization': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'activity_level': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            # 'featured_section': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'key_figures': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'data_completeness': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
        })
        return schema

    # IGroupForm
    def form_to_db_schema(self):
        schema = super(HDXGroupPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

    # IGroupForm
    def db_to_form_schema(self):

        schema = super(HDXGroupPlugin, self).form_to_db_schema()
        schema.update({
            'language_code': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'relief_web_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'hr_info_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'alert_bar_title': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'alert_bar_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'geojson': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'activity_level': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
            'key_figures': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('active_if_missing')
            ],
            'data_completeness': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
            'package_count': [tk.get_validator('ignore_missing')],
            'display_name': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],

        })
        # schema.update({'custom_loc': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        # schema.update({'customization': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        # schema.update({
        #     'featured_section': [
        #         tk.get_converter('convert_from_extras'),
        #         tk.get_validator('ignore_missing')]
        # })
        return schema

    def create(self, country):
        tk.get_action('invalidate_cache_for_groups')({'ignore_auth': True}, {})

    def edit(self, country):
        # invalidate caches
        tk.get_action('invalidate_cache_for_groups')({'ignore_auth': True}, {})

        # Screenshot generation for latest COD when country is edited
        # cod_dict = country_helper.get_latest_cod_dataset(country.name)
        # shape_infos = []
        # if cod_dict:
        #     shape_infos = [r.get('shape_info') for r in cod_dict.get('resources', []) if r.get('shape_info')]
        #
        # if shape_infos and not screenshot.screenshot_exists(cod_dict):
        #     context = {'ignore_auth': True}
        #     try:
        #         tk.get_action('hdx_create_screenshot_for_cod')(context, {'id': cod_dict['id']})
        #     except Exception as ex:
        #         log.error(ex)

    # IBlueprint
    def get_blueprint(self):
        import ckanext.hdx_org_group.views.group as group
        import ckanext.hdx_org_group.views.light_group as light_group
        return [group.hdx_group, group.hdx_country_topline, light_group.hdx_light_group, light_group.hdx_group_eaa_maps]

