import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

import ckanext.hdx_org_group.helpers


class HDXOrgGroupPlugin(plugins.SingletonPlugin, lib_plugins.DefaultOrganizationForm):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IGroupForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IActions)

    num_times_new_template_called = 0
    num_times_read_template_called = 0
    num_times_edit_template_called = 0
    num_times_search_template_called = 0
    num_times_history_template_called = 0
    num_times_package_form_called = 0
    num_times_check_data_dict_called = 0
    num_times_setup_template_variables_called = 0

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def get_helpers(self):
        return {}

    def get_actions(self):
        from ckanext.hdx_org_group.helpers import organization_helper as hdx_org_actions
        return {
            'hdx_get_group_activity_list': hdx_org_actions.hdx_get_group_activity_list,
            'hdx_light_group_show': hdx_org_actions.hdx_light_group_show,
            'organization_update': hdx_org_actions.hdx_organization_update
        }

    # def get_auth_functions(self):
    #     return {
    #             'hdx_basic_user_info': helpers.auth.hdx_basic_user_info,
    #             'group_member_create': helpers.auth.group_member_create,
    #             'hdx_send_new_org_request': helpers.auth.hdx_send_new_org_request,
    #             'hdx_send_editor_request_for_org': helpers.auth.hdx_send_editor_request_for_org,
    #             'hdx_send_request_membership': helpers.auth.hdx_send_request_membership
    #             }

    def is_fallback(self):
        return False

    def group_types(self):
        return ['organization']

    def _modify_group_schema(self, schema):
        schema.update({
            'description': [tk.get_validator('not_empty')],
            'org_url': [tk.get_validator('not_missing'), tk.get_converter('convert_to_extras')],
            'fts_id': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'custom_org': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'customization': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'less': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'visualization_config':[tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'modified_at': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
        })
        return schema

    def form_to_db_schema(self):
        schema = super(HDXOrgGroupPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

#     def check_data_dict(self, data_dict):
#         return super(HDXOrgFormPlugin, self).check_data_dict(self, data_dict)

    def db_to_form_schema(self):
        # There's a bug in dictionary validation when form isn't present
        if tk.request.urlvars['action'] == 'index' or tk.request.urlvars['action'] == 'edit' or tk.request.urlvars['action'] == 'new':
            schema = super(HDXOrgGroupPlugin, self).form_to_db_schema()
            schema.update({'description': [tk.get_validator('not_empty')]})
            schema.update(
                {'org_url': [tk.get_validator('not_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'fts_id': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'custom_org': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'customization': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'less': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'visualization_config': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'modified_at': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            return schema
        else:
            return None

    def before_map(self, map):
        map.connect('organization_bulk_process',
                    '/organization/bulk_process/{org_id}', controller='ckanext.hdx_org_group.controllers.redirect_controller:RedirectController', action='redirect_to_org_list')
        map.connect('organization_bulk_process_no_id', '/organization/bulk_process',
                    controller='ckanext.hdx_org_group.controllers.redirect_controller:RedirectController', action='redirect_to_org_list')
        map.connect('organizations_index', '/organization',
                    controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController', action='index')
        map.connect('organization_new', '/organization/new',
                    controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController', action='new')
        map.connect('organization_edit', '/organization/edit/{id}', controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController',
                  action='edit', ckan_icon='edit')
        map.connect('request_membership', '/organization/{org_id}/request_membership',
                    controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController', action='request_membership')
        map.connect('request_editing_rights', '/organization/{org_id}/request_editing_rights',
                    controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController', action='request_editor_for_org')
        map.connect('/organization/request_new',
                    controller='ckanext.hdx_org_group.controllers.request_controller:HDXReqsOrgController', action='request_new_organization')
        map.connect(
            '/organization/members/{id}', controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController', action='members')
        map.connect(
            '/organization/member_new/{id}', controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController', action='member_new')
        map.connect(
            '/organization/member_delete/{id}', controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController', action='member_delete')
        map.connect(
            '/organization/member_delete/{id}', controller='ckanext.hdx_org_group.controllers.member_controller:HDXOrgMemberController', action='member_delete')

        # since the pattern of organization_read is so general it needs to be the last
        # otherwise it will override other /organization routes
        map.connect('organization_read', '/organization/{id}',
                    controller='ckanext.hdx_org_group.controllers.organization_controller:HDXOrganizationController', action='read')

        map.connect('browse_list', '/browse',
                    controller='ckanext.hdx_org_group.controllers.browse_controller:BrowseController', action='index')
        map.connect('group_new', '/group/new', controller='group', action='new')
        map.connect(
            'country_read', '/group/{id}', controller='ckanext.hdx_org_group.controllers.country_controller:CountryController', action='country_read')

        map.connect(
            'wfp_read', '/alpha/wfp', controller='ckanext.hdx_org_group.controllers.wfp_controller:WfpController', action='org_read')
        
        map.connect(
            'image_serve', '/image/{label}', controller='ckanext.hdx_org_group.controllers.image_upload_controller:ImageController', action='file')
        

        #map.connect(
        #    'custom_org_read', '/org/{id}', controller='ckanext.hdx_org_group.controllers.custom_org_controller:CustomOrgController', action='org_read')

        return map


class HDXGroupPlugin(plugins.SingletonPlugin, lib_plugins.DefaultGroupForm):
    plugins.implements(plugins.IGroupForm, inherit=False)

    def group_types(self):
        return ['']

    def is_fallback(self):
        return True

    def _modify_group_schema(self, schema):
        schema.update({'language_code': [
                      tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')], })
        schema.update({'relief_web_url': [
                      tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]})
        schema.update({'hr_info_url': [
                      tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]})
        schema.update({'geojson': [tk.get_validator(
            'ignore_missing'), tk.get_converter('convert_to_extras')],
        'custom_loc': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            'customization': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
            })
        return schema

    def form_to_db_schema(self):
        schema = super(HDXGroupPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

    def db_to_form_schema(self):
        # There's a bug in dictionary validation when form isn't present
        if tk.request.urlvars['action'] == 'index' or tk.request.urlvars['action'] == 'edit' or tk.request.urlvars['action'] == 'new':
            schema = super(HDXGroupPlugin, self).form_to_db_schema()
            schema.update({'language_code': [
                          tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
            schema.update({'relief_web_url': [
                          tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
            schema.update({'hr_info_url': [
                          tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
            schema.update({'geojson': [tk.get_converter(
                'convert_from_extras'), tk.get_validator('ignore_missing')]})
            schema.update({'custom_loc': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            schema.update({'customization': [tk.get_validator(
                'ignore_missing'), tk.get_converter('convert_to_extras')]})
            return schema
        else:
            return None
