'''
Created on Apr 10, 2014

@author:alexandru-m-g
'''
import io
import json
import logging

import ckanext.hdx_org_group.helpers.organization_helper as org_helper
import ckanext.hdx_package.actions.authorize as authorize
import ckanext.hdx_package.actions.create as hdx_create
import ckanext.hdx_package.actions.delete as hdx_delete
import ckanext.hdx_package.actions.get as hdx_get
import ckanext.hdx_package.actions.update as hdx_update
import ckanext.hdx_package.actions.patch as hdx_patch
import ckanext.hdx_package.helpers.download_wrapper as download_wrapper
import ckanext.hdx_package.helpers.custom_validator as vd
import ckanext.hdx_package.helpers.helpers as hdx_helpers
import ckanext.hdx_package.helpers.licenses as hdx_licenses
import ijson
import pylons.config as config
from routes.mapper import SubMapper

import ckan.logic as logic
import ckan.model as model
import ckan.model.license as license
import ckan.model.package as package
import ckan.authz as authz
import ckan.plugins as p
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.plugins.toolkit as toolkit
import ckanext.resourceproxy.plugin as resourceproxy_plugin
from ckan.lib import uploader
from ckan.common import c
from ckanext.hdx_package.helpers.constants import UNWANTED_DATASET_PROPERTIES, COD_VALUES_MAP

log = logging.getLogger(__name__)

ignore_empty = p.toolkit.get_validator('ignore_empty')


def run_on_startup():
    cache_on_startup = config.get('hdx.cache.onstartup', 'true')
    if 'true' == cache_on_startup:
        _generate_license_list()
        # caching.cached_get_group_package_stuff()

    compile_less_on_startup = config.get('hdx.less_compile.onstartup', 'false')
    if 'true' == compile_less_on_startup:
        org_helper.recompile_everything({'model': model, 'session': model.Session,
                                         'user': 'hdx', 'ignore_auth': True})

    # replace original get_proxified_resource_url, check hdx_get_proxified_resource_url for more info
    resourceproxy_plugin.get_proxified_resource_url = hdx_helpers.hdx_get_proxified_resource_url

    # Analytics related things that need to be run on startup are in their own plugin


def _generate_license_list():
    package.Package._license_register = license.LicenseRegister()
    package.Package._license_register.licenses = [
        license.License(
            hdx_licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        license.License(hdx_licenses.LicenseHDXCreativeCommonsAttributionInternational()),
        license.License(license.LicenseCreativeCommonsAttributionShareAlike()),
        license.License(hdx_licenses.LicenseHdxOpenDatabaseLicense()),
        license.License(
            hdx_licenses.LicenseHdxOpenDataCommonsAttributionLicense()),
        license.License(
            hdx_licenses.LicenseHdxOpenDataCommonsPublicdomainDedicationAndLicense()),
        license.License(hdx_licenses.LicenseOtherPublicDomainNoRestrictions()),
        license.License(hdx_licenses.LicenseHdxMultiple()),
        license.License(hdx_licenses.LicenseHdxOther())
    ]


def cached_group_list():
    return tk.get_action('cached_group_list')()


class HDXPackagePlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IValidators, inherit=True)
    plugins.implements(plugins.IBlueprint)

    __startup_tasks_done = False

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    def after_map(self, map):
        map.connect('dataset_edit', '/dataset/edit/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='show_notification_page')
        return map

    # def before_delete(context, data_dict, resource, resources):
    #     try:
    #         if resource.get('id'):
    #             file_remove(resource.get('id'))
    #     except Exception, ex:
    #         log.error(ex)

    def before_map(self, map):
        # map.connect('storage_file', '/storage/f/{label:.*}',
        #             controller='ckanext.hdx_package.controllers.storage_controller:FileDownloadController',
        #             action='file')
        # map.connect('perma_storage_file', '/dataset/{id}/resource_download/{resource_id}',
        #             controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
        #             action='resource_download')
        map.connect('dataset_preselect', '/dataset/preselect',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='preselect')
        # map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
        #             controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='resource_edit', ckan_icon='edit')
        map.connect('resource_read', '/dataset/{id}/resource/{resource_id}',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='resource_read')
        map.connect('shorten_url', '/package/tools/shorten',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='shorten')
        map.connect('resource_datapreview', '/dataset/{id}/resource/{resource_id}/preview',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='resource_datapreview')
        map.connect('related_edit', '/dataset/{id}/related/edit/{related_id}',
                    controller='ckanext.hdx_package.controllers.related_controller:RelatedController',
                    action='edit')

        map.connect('add dataset', '/dataset/new',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='new_notification_page')
        map.connect('dataset_edit', '/dataset/edit/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='edit_notification_page')
        map.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resource_edit_notification_page', ckan_icon='edit')
        map.connect('new_resource', '/dataset/new_resource/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resource_new_notification_page')
        map.connect('dataset_resources', '/dataset/resources/{id}',
                    controller='ckanext.hdx_package.controllers.dataset_old_links_controller:DatasetOldLinks',
                    action='resources_notification_page')
        map.connect('/membership/contact_contributor',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='contact_contributor')
        map.connect('/membership/contact_members',
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController',
                    action='contact_members')

        with SubMapper(map, controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController') as m:
            # m.connect('add dataset', '/dataset/new', action='new')
            m.connect('/dataset/{id}/resource_delete/{resource_id}', action='resource_delete')
            m.connect('/dataset/{id}.{format}', action='read')
            m.connect('dataset_read', '/dataset/{id}', action='read',
                      ckan_icon='sitemap')
            m.connect('/dataset/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'new_metadata',
                          # 'new_resource',
                          'visibility',
                          'delete',
                          # 'edit',
                      ])))

        map.connect(
            '/indicator/{id}', controller='ckanext.hdx_package.controllers.indicator:IndicatorController',
            action='read')

        # map.connect('/api/action/package_create', controller='ckanext.hdx_package.controllers.dataset_controller:HDXApiController', action='package_create', conditions=dict(method=['POST']))
        map.connect('/contribute/new',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='new')
        map.connect('/contribute/edit/{id}',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='edit')
        map.connect('/contribute/validate',
                    controller='ckanext.hdx_package.controllers.contribute_flow_controller:ContributeFlowController',
                    action='validate')

        return map

    def is_fallback(self):
        return True

    def package_types(self):
        # default - no specific package type
        return []

    def _remove_package_fields_from_schema(self, schema):
        for property_name in UNWANTED_DATASET_PROPERTIES:
            schema.pop(property_name, None)

    def _modify_package_schema(self, schema):

        self._remove_package_fields_from_schema(schema)

        schema.update({
            # Notes == description. Makes description required
            'notes': [vd.not_empty_ignore_ws],
            'package_creator': [tk.get_validator('find_package_creator'),
                                tk.get_validator('not_empty'),
                                tk.get_converter('convert_to_extras')],
            'groups_list': [vd.groups_not_empty],
            'is_requestdata_type': [tk.get_validator('hdx_boolean_string_converter'), tk.get_converter('convert_to_extras')],
            'indicator': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'last_data_update_date': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'last_metadata_update_date': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'dataset_source_short_name': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'indicator_type': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'indicator_type_code': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'dataset_summary': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'more_info': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'terms_of_use': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'source_code': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'caveats': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'dataset_source': [tk.get_validator('not_empty'), tk.get_converter('convert_to_extras')],
            'dataset_date': [tk.get_validator('hdx_daterange_possible_infinite_end'), tk.get_validator('not_empty'),
                             tk.get_converter('convert_to_extras')],
            'methodology': [tk.get_validator('not_empty'), tk.get_converter('convert_to_extras')],
            'methodology_other': [tk.get_validator('not_empty_if_methodology_other'),
                                  tk.get_converter('convert_to_extras')],
            'license_id': [tk.get_validator('not_empty'), unicode],
            'license_other': [tk.get_validator('not_empty_if_license_other'), tk.get_converter('convert_to_extras')],
            'solr_additions': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'subnational': [tk.get_validator('hdx_show_subnational'), tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
            'quality': [tk.get_validator('ignore_not_sysadmin'), tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')],
            'data_update_frequency': [tk.get_validator('not_empty'), tk.get_converter('convert_to_extras')],
            'batch': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'maintainer': [tk.get_validator('hdx_find_package_maintainer'), tk.get_validator('not_empty')],
            'dataset_preview': [tk.get_validator('hdx_dataset_preview_validator'), tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
            'author_email': [tk.get_validator('ignore_missing'), unicode],
            'customviz': {
                'url': [tk.get_validator('hdx_is_url'), tk.get_validator('hdx_convert_list_item_to_extras')],
            },
            'archived': [tk.get_validator('hdx_boolean_string_converter'), tk.get_converter('convert_to_extras')],
            'review_date': [tk.get_validator('ignore_missing'),
                            tk.get_validator('isodate'),
                            tk.get_validator('hdx_isodate_to_string_converter'),
                            tk.get_converter('convert_to_extras')],
            'qa_completed': [tk.get_validator('hdx_reset_unless_allow_qa_completed'),
                             # tk.get_validator('ignore_missing'),
                             tk.get_validator('hdx_boolean_string_converter'),
                             tk.get_converter('convert_to_extras')],
            'qa_checklist_completed': [tk.get_validator('hdx_reset_unless_allow_qa_checklist_completed'),
                             tk.get_validator('ignore_missing'),
                             tk.get_validator('hdx_boolean_string_converter'),
                             tk.get_converter('convert_to_extras')],
            'qa_checklist': [tk.get_validator('hdx_keep_unless_allow_qa_checklist_field'),
                            tk.get_converter('convert_to_extras')],
            'updated_by_script': [tk.get_validator('hdx_keep_prev_value_if_empty'),
                             tk.get_converter('convert_to_extras')],
            'cod_level': [
                tk.get_validator('hdx_delete_unless_authorized_to_update_cod'),
                tk.get_validator('hdx_keep_prev_value_if_empty'),
                tk.get_validator('hdx_in_cod_values'),
                tk.get_converter('convert_to_extras')
            ],
            'resource_grouping': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('hdx_convert_to_json_string'),
                tk.get_converter('convert_to_extras')
            ]
        })

        schema['resources'].update(
            {
                'name': [tk.get_validator('not_empty'), unicode, tk.get_validator('remove_whitespace')],
                'format': [
                    tk.get_validator('hdx_detect_format'),
                    tk.get_validator('not_empty'),
                    tk.get_validator('hdx_to_lower'),
                    tk.get_validator('clean_format'),
                    unicode
                ],
                'url': [tk.get_validator('not_empty'), unicode, tk.get_validator('remove_whitespace')],
                'in_quarantine': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('boolean_validator'),
                    tk.get_validator('hdx_reset_on_file_upload')
                ],
                'pii_timestamp': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('isodate'),
                    tk.get_validator('hdx_isodate_to_string_converter'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'pii_report_flag': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'pii_report_id': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'sdc_timestamp': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('isodate'),
                    tk.get_validator('hdx_isodate_to_string_converter'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'sdc_report_flag': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'sdc_report_id': [
                    tk.get_validator('hdx_keep_unless_allow_resource_qa_script_field'),
                    tk.get_validator('hdx_reset_on_file_upload'),
                    tk.get_validator('ignore_missing')  # if None, don't save 'None' string
                ],
                'dataset_preview_enabled': [
                    tk.get_validator('hdx_convert_values_to_boolean_for_dataset_preview'),
                    tk.get_validator('ignore_missing')
                ],
                'broken_link': [
                    tk.get_validator('hdx_delete_unless_allow_broken_link'),
                    tk.get_validator('ignore_missing'),
                    tk.get_validator('hdx_boolean_string_converter')
                ],
                'daterange_for_data': [
                    tk.get_validator('ignore_missing'),
                    tk.get_validator('hdx_daterange_possible_infinite_end')
                ],
                'grouping': [
                    tk.get_validator('ignore_missing')
                ]
            }
        )

        return schema

    def create_package_schema(self):
        schema = super(HDXPackagePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(HDXPackagePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(HDXPackagePlugin, self).show_package_schema()

        self._remove_package_fields_from_schema(schema)

        schema['resources'].update(
            {
                'format': [
                    tk.get_validator('hdx_to_lower'),
                    tk.get_validator('clean_format'),
                ],
                'in_quarantine': [
                    tk.get_validator('ignore_missing'),
                    tk.get_validator('boolean_validator')
                ],
                'broken_link': [
                    tk.get_validator('ignore_missing'),
                    tk.get_validator('boolean_validator')
                ],
                'daterange_for_data': [
                    tk.get_validator('ignore_missing'),
                ]
            }
        )
        schema.update({
            # Notes == description. Makes description required
            'notes': [vd.not_empty_ignore_ws],
            'package_creator': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'is_requestdata_type': [tk.get_converter('convert_from_extras'), tk.get_validator('boolean_validator')],
            'indicator': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'last_data_update_date': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'last_metadata_update_date': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'dataset_source_short_name': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'indicator_type': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'indicator_type_code': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'dataset_summary': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'more_info': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'terms_of_use': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'source_code': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'caveats': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'dataset_source': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'dataset_date': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'methodology': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'methodology_other': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'license_other': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'solr_additions': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'subnational': [tk.get_converter('convert_from_extras'), tk.get_validator('hdx_show_subnational')],
            'quality': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'data_update_frequency': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'pageviews_last_14_days': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'total_res_downloads': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'has_quickcharts': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'has_geodata': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'batch': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'dataset_preview': [tk.get_converter('convert_from_extras'), tk.get_validator('hdx_dataset_preview_validator')],
            'customviz__url': [tk.get_converter('hdx_convert_from_extras_to_list_item'), tk.get_validator('ignore_missing')],
            'archived': [tk.get_converter('convert_from_extras'), tk.get_validator('boolean_validator')],
            'review_date': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'has_showcases': [tk.get_validator('ignore_missing')],
            'last_modified': [tk.get_validator('ignore_missing')],
            # 'due_daterange': [tk.get_validator('ignore_missing')],
            # 'overdue_daterange': [tk.get_validator('ignore_missing')],
            'due_date': [tk.get_validator('ignore_missing')],
            'overdue_date': [tk.get_validator('ignore_missing')],
            'qa_completed': [
                tk.get_converter('convert_from_extras'),
                tk.get_converter('hdx_assume_missing_is_true'),
                tk.get_validator('boolean_validator')
            ],
            'qa_checklist_completed': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing'),
                tk.get_validator('boolean_validator')
            ],
            'qa_checklist': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'updated_by_script': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'cod_level': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')],
            'resource_grouping': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing'),
                tk.get_converter('hdx_convert_from_json_string'),
            ],

        })

        return schema

    def get_helpers(self):
        return {
            'list_of_all_groups': cached_group_list,
            'hdx_find_license_name': hdx_helpers.hdx_find_license_name,
            'filesize_format': hdx_helpers.filesize_format,
            'generate_mandatory_fields': hdx_helpers.generate_mandatory_fields,
            'hdx_check_add_data': hdx_helpers.hdx_check_add_data,
            'hdx_get_due_overdue_date': hdx_helpers.hdx_get_due_overdue_date,
            'hdx_get_last_modification_date': hdx_helpers.hdx_get_last_modification_date,
            'hdx_render_resource_updated_date': hdx_helpers.hdx_render_resource_updated_date,
        }

    def get_actions(self):
        from ckanext.hdx_package.helpers import helpers as hdx_actions
        return {
            'package_update': hdx_update.package_update,
            'package_patch': hdx_patch.package_patch,
            'package_resource_reorder': hdx_update.package_resource_reorder,
            'dataset_purge': hdx_delete.dataset_purge,
            'hdx_dataset_purge': hdx_delete.hdx_dataset_purge,
            'hdx_get_activity_list': hdx_actions.hdx_get_activity_list,
            'hdx_package_update_metadata': hdx_update.hdx_package_update_metadata,
            'hdx_resource_update_metadata': hdx_update.hdx_resource_update_metadata,
            'hdx_resource_delete_metadata': hdx_update.hdx_resource_delete_metadata,
            'resource_view_update': hdx_update.resource_view_update,
            'resource_view_create': hdx_create.resource_view_create,
            'resource_view_delete': hdx_delete.resource_view_delete,
            'hdx_resource_id_list': hdx_get.hdx_resource_id_list,
            'tag_autocomplete': hdx_actions.hdx_tag_autocomplete_list,
            'format_autocomplete': hdx_get.hdx_format_autocomplete,
            'hdx_guess_format_from_extension': hdx_get.hdx_guess_format_from_extension,
            'package_create': hdx_create.package_create,
            'resource_create': hdx_create.resource_create,
            'resource_update': hdx_update.resource_update,
            'resource_patch': hdx_patch.resource_patch,
            'resource_show': hdx_get.resource_show,
            'resource_delete': hdx_delete.resource_delete,
            'package_search': hdx_get.package_search,
            'package_show': hdx_get.package_show,
            'package_show_edit': hdx_get.package_show_edit,
            'package_validate': hdx_get.package_validate,
            'shape_info_show': hdx_get.shape_info_show,
            'hdx_member_list': hdx_get.hdx_member_list,
            'hdx_send_mail_contributor': hdx_get.hdx_send_mail_contributor,
            'hdx_send_mail_members': hdx_get.hdx_send_mail_members,
            'hdx_create_screenshot_for_cod': hdx_create.hdx_create_screenshot_for_cod,
            'recently_changed_packages_activity_list': hdx_get.recently_changed_packages_activity_list,
            # 'hdx_test_recommend_tags': hdx_get.hdx_test_recommend_tags,
            'hdx_recommend_tags': hdx_get.hdx_recommend_tags,
            'hdx_package_qa_checklist_update': hdx_update.package_qa_checklist_update,
            'hdx_package_qa_checklist_show': hdx_get.package_qa_checklist_show,
            'hdx_get_s3_link_for_resource': hdx_get.hdx_get_s3_link_for_resource,
            'hdx_mark_broken_link_in_resource': hdx_patch.hdx_mark_broken_link_in_resource,
            'hdx_mark_qa_completed': hdx_patch.hdx_mark_qa_completed,
            'hdx_qa_resource_patch': hdx_patch.hdx_qa_resource_patch,

        }

    # IValidators
    def get_validators(self):
        return {
            'hdx_detect_format': vd.detect_format,
            'hdx_to_lower': vd.to_lower,
            'find_package_creator': vd.find_package_creator,
            'not_empty_if_methodology_other': vd.general_not_empty_if_other_selected('methodology', 'Other'),
            'not_empty_if_license_other': vd.general_not_empty_if_other_selected('license_id', 'hdx-other'),
            'hdx_show_subnational': vd.hdx_show_subnational,
            'hdx_find_package_maintainer': vd.hdx_find_package_maintainer,
            'hdx_dataset_preview_validator': vd.hdx_dataset_preview_validator,
            'hdx_convert_values_to_boolean_for_dataset_preview': vd.hdx_convert_values_to_boolean_for_dataset_preview,
            'hdx_convert_list_item_to_extras': vd.hdx_convert_list_item_to_extras,
            'hdx_convert_from_extras_to_list_item': vd.hdx_convert_from_extras_to_list_item,
            'hdx_is_url':  vd.hdx_is_url,
            'hdx_boolean_string_converter': vd.hdx_boolean_string_converter,
            'hdx_assume_missing_is_true': vd.hdx_assume_missing_is_true,
            'hdx_isodate_to_string_converter': vd.hdx_isodate_to_string_converter,
            'hdx_resource_keep_prev_value_unless_sysadmin': vd.hdx_resource_keep_prev_value_unless_sysadmin,
            'hdx_reset_on_file_upload': vd.reset_on_file_upload,
            'hdx_keep_prev_value_if_empty': vd.hdx_keep_prev_value_if_empty,
            'hdx_delete_unless_allow_broken_link': vd.hdx_delete_unless_field_in_context('allow_broken_link_field'),
            'hdx_reset_unless_allow_qa_completed': vd.hdx_delete_unless_field_in_context('allow_qa_completed_field'),
            'hdx_reset_unless_allow_qa_checklist_completed':
                vd.hdx_delete_unless_field_in_context('allow_qa_checklist_completed_field'),
            'hdx_keep_unless_allow_qa_checklist_field':
                vd.hdx_package_keep_prev_value_unless_field_in_context_wrapper('allow_qa_checklist_field'),
            'hdx_keep_unless_allow_resource_qa_script_field':
                vd.hdx_package_keep_prev_value_unless_field_in_context_wrapper('allow_resource_qa_script_field',
                                                                               resource_level=True),
            'hdx_delete_unless_authorized_to_update_cod':
                vd.hdx_delete_unless_authorized_wrapper('hdx_cod_update'),
            'hdx_in_cod_values':
                vd.hdx_value_in_list_wrapper(COD_VALUES_MAP.keys(), False),
            'hdx_daterange_possible_infinite_end': vd.hdx_daterange_possible_infinite_end,
            'hdx_convert_to_json_string': vd.hdx_convert_to_json_string,
            'hdx_convert_from_json_string': vd.hdx_convert_from_json_string,
        }

    def get_auth_functions(self):
        return {'package_create': authorize.package_create,
                'package_update': authorize.package_update,
                'hdx_resource_id_list': authorize.hdx_resource_id_list,
                'hdx_send_mail_contributor': authorize.hdx_send_mail_contributor,
                'hdx_send_mail_members': authorize.hdx_send_mail_members,
                'hdx_create_screenshot_for_cod': authorize.hdx_create_screenshot_for_cod,
                'hdx_resource_download': authorize.hdx_resource_download,
                'hdx_mark_qa_completed': authorize.hdx_mark_qa_completed,
                'hdx_package_qa_checklist_update': authorize.package_qa_checklist_update,
                'hdx_qa_resource_patch': authorize.hdx_qa_resource_patch,
                'hdx_cod_update': authorize.hdx_cod_update
                }

    def make_middleware(self, app, config):
        if not HDXPackagePlugin.__startup_tasks_done:
            run_on_startup()
            HDXPackagePlugin.__startup_tasks_done = True
        return app

    def validate(self, context, data_dict, schema, action):
        '''
            We're using a different validation schema if the dataset is private !
        '''
        is_requestdata_type = self._is_requestdata_type(data_dict)

        if action in ['package_create', 'package_update']:
            private = False if str(data_dict.get('private', '')).lower() == 'false' else True

            if private:
                self._update_with_private_modify_package_schema(schema)

            if is_requestdata_type:
                self._update_with_requestdata_modify_package_schema(schema)

            fields_to_skip = config.get('hdx.validation.allow_skip_for_sysadmin', '').split(',')
            if len(fields_to_skip) > 0 and fields_to_skip[0] and \
                    authz.is_sysadmin(c.user) and context.get(hdx_update.SKIP_VALIDATION):
                self._update_with_skip_validation(schema, fields_to_skip)

        if action == 'package_show':
            if is_requestdata_type:
                self._update_with_requestdata_show_package_schema(schema)

        return toolkit.navl_validate(data_dict, schema, context)

    def _is_requestdata_type(self, data_dict):
        is_requestdata_type_show = False
        is_requestdata_type_modify = str(data_dict.get('is_requestdata_type', '')).lower() == 'true'

        if not is_requestdata_type_modify:
            is_requestdata_type_show = next(
                (extra.get('value') for extra in data_dict.get('extras', [])
                 if extra.get('state') == 'active' and extra.get('key') == 'is_requestdata_type'),
                'false') == 'true'

        return is_requestdata_type_modify or is_requestdata_type_show

    def _update_with_skip_validation(self, schema, fields_to_skip):
        for field in fields_to_skip:
            field = field.strip()
            if field in ['notes', 'maintainer']:
                schema[field] = [tk.get_validator('ignore_missing')]
            elif field.startswith('resources/'):
                resources_field = field.split('/')[1]
                schema['resources'][resources_field] = [tk.get_validator('ignore_missing')]
            else:
                schema[field] = [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]

    def _update_with_private_modify_package_schema(self, schema):
        log.debug('Update with private modifiy package schema')
        schema['notes'] = [tk.get_validator('ignore_missing'), unicode]
        schema['methodology'] = [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
        schema['dataset_date'] = [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
        schema['data_update_frequency'] = [tk.get_validator('ignore_missing'),
                                           tk.get_converter('convert_to_extras')]

        if 'groups_list' in schema:
            del schema['groups_list']

    def _update_with_requestdata_modify_package_schema(self, schema):
        log.debug('Update with requestdata modifiy package schema')
        for plugin in plugins.PluginImplementations(plugins.IDatasetForm):
            if plugin.name == 'requestdata':
                if type == 'create':
                    requestdata_schema = plugin.create_package_schema()
                    schema.update(requestdata_schema)
                elif type == 'update':
                    requestdata_schema = plugin.update_package_schema()
                    schema.update(requestdata_schema)

        schema.update({
            'field_names': [tk.get_validator('not_empty'), tk.get_converter('convert_to_extras')],
            'file_types': [tk.get_validator('not_empty'), tk.get_converter('convert_to_extras')],
            'num_of_rows': [tk.get_validator('ignore_missing'), tk.get_validator('is_positive_integer'),
                            tk.get_converter('convert_to_extras')],
            'data_update_frequency': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'methodology': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
        })

        schema.pop('license_id')
        schema.pop('license_other')

    def _update_with_requestdata_show_package_schema(self, schema):
        log.debug('Update with requestdata show package schema')

        # Adding requestdata related schema
        for plugin in plugins.PluginImplementations(plugins.IDatasetForm):
            if plugin.name == 'requestdata':
                requestdata_schema = plugin.show_package_schema()
                schema.update(requestdata_schema)

        # Adding hdx specific request data schema
        schema.update({
            'field_names': [tk.get_converter('convert_from_extras'), tk.get_validator('not_empty')],
            'file_types': [tk.get_converter('convert_from_extras'), tk.get_validator('not_empty')],
            'num_of_rows': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing'),
                            tk.get_validator('is_positive_integer')],
            'data_update_frequency': [tk.get_validator('convert_from_extras'), tk.get_converter('ignore_missing')],
            'methodology': [tk.get_validator('convert_from_extras'), tk.get_converter('ignore_missing')]
        })

    def get_blueprint(self):
        import ckanext.hdx_package.views.light_dataset as light_dataset
        return light_dataset.hdx_light_dataset

class HDXAnalyticsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    __startup_tasks_done = False

    def run_on_startup(self):
        # wrap resource download function so that we can track download events
        download_wrapper.wrap_resource_download_function()

    def make_middleware(self, app, config):
        if not HDXAnalyticsPlugin.__startup_tasks_done:
            self.run_on_startup()
            HDXAnalyticsPlugin.__startup_tasks_done = True

        return app

    # def after_create(self, context, data_dict):
    #     if not context.get('contribute_flow'):
    #         analytics.DatasetCreatedAnalyticsSender(data_dict).send_to_queue()


class HDXChartViewsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        schema = {
            'chart_type': [],
            'x_axis_label': [ignore_empty],
            'y_axis_label': [],
            'x_column': [],
            'y_column': [],
            'chart_data_source': [],
            'data_link_url': [],
            'data_label': []
        }
        return {
            'name': 'hdx_chart_view',
            'title': 'Line / Bar Chart',
            'filterable': False,
            'preview_enabled': True,
            'icon': 'bar-chart',
            'requires_datastore': True,
            'iframed': True,
            'schema': schema,
            'default_title': p.toolkit._('HDX New Chart')
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                resource.get('url') == '_datastore_only_resource')

    def setup_template_variables(self, context, data_dict):
        return {
            'datastore_columns': self._datastore_cols(data_dict['resource']),
            'chart_type': [
                {
                    'value': 'bar',
                    'text': p.toolkit._('Bar Chart')
                },
                {
                    'value': 'area',
                    'text': p.toolkit._('Line Area Chart')
                },
                {
                    'value': 'line',
                    'text': p.toolkit._('Line Chart')
                },
            ],
            'chart_info': self._format_settings_for_chart(data_dict['resource'], data_dict['resource_view'])
        }

    def view_template(self, context, data_dict):
        return 'new_views/chart_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/chart_view_form.html'

    def _format_settings_for_chart(self, resource_dict, resource_view_dict):
        result = {
            'title': resource_view_dict.get('title'),
            'title_x': resource_view_dict.get('x_axis_label'),
            'title_y': resource_view_dict.get('y_axis_label'),
            'type': resource_view_dict.get('chart_type'),
            'sources': [
                {
                    'label_x': resource_view_dict.get('data_label'),
                    'column_x': resource_view_dict.get('x_column'),
                    'column_y': resource_view_dict.get('y_column'),
                    'data_link_url': resource_view_dict.get('data_link_url'),
                    'source': resource_view_dict.get('chart_data_source'),
                    'datastore_id': resource_dict.get('id'),
                    'source_type': 'ckan'
                }
            ]
        }
        return result

    def _datastore_cols(self, resource):
        '''
        Returns a list of columns found in this resource's datastore
        '''
        data = {'resource_id': resource['id'], 'limit': 0}
        fields = toolkit.get_action('datastore_search')({}, data)['fields']
        return [{'value': col['id'], 'text': col['id']} for col in fields if col != '_id']


class HDXGeopreviewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        return {
            'name': 'hdx_geopreview_view',
            'title': 'Geopreview',
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': False,
            'iframed': True,
            'default_title': p.toolkit._('Geopreview')
        }

    def can_view(self, data_dict):
        from ckanext.hdx_package.helpers.geopreview import GIS_FORMATS

        resource = data_dict.get('resource', {})
        format = resource.get('format')
        format = format.lower() if format else ''
        return format in GIS_FORMATS

    def setup_template_variables(self, context, data_dict):
        from ckanext.hdx_package.controllers.dataset_controller import DatasetController

        shape_info = DatasetController.process_shapes([data_dict['resource']])

        return {
            'shape_info': json.dumps(shape_info)
        }

    def view_template(self, context, data_dict):
        return 'new_views/geopreview_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/geopreview_view_form.html'


class HDXKeyFiguresPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        return {
            'name': 'hdx_key_figures_view',
            'title': 'Key Figures',
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': True,
            'iframed': True,
            'default_title': p.toolkit._('Key Figures')
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                resource.get('url') == '_datastore_only_resource')

    def setup_template_variables(self, context, data_dict):
        import ckanext.hdx_crisis.dao.location_data_access as location_data_access
        id = data_dict['resource']['id']
        key_figures = location_data_access.get_formatted_topline_numbers(id)

        return {
            'key_figures': key_figures
        }

    def view_template(self, context, data_dict):
        return 'new_views/key_figures_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/key_figures_view_form.html'


class HDXChoroplethMapPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceView, inherit=True)

    def info(self):
        schema = {
            'map_name': [],
            'district_name_column': [],
            'values_resource_id': [],
            'values_column_name': [],
            'values_description_column': [],
            'map_join_column': [],
            'values_join_column': [],
            'threshold': [],
            'max_zoom': [],
            'show_legend': []
        }
        return {
            'name': 'hdx_choropleth_map_view',
            'title': 'Choropleth Map',
            'schema': schema,
            'filterable': False,
            'preview_enabled': True,
            'requires_datastore': False,
            'iframed': True,
            'default_title': p.toolkit._('Choropleth Map')
        }

    def can_view(self, data_dict):
        resource = data_dict.get('resource', {})
        format = resource.get('format')
        format = format.lower() if format else ''

        return format == 'geojson'

    def _detect_fields_in_geojson(self, resource_dict):
        geo_columns_dict = {}
        try:
            upload = uploader.ResourceUpload(resource_dict)
            with io.open(upload.get_path(resource_dict['id']), 'rb') as f, io.TextIOWrapper(f,
                                                                                            encoding='utf-8-sig') as tf:
                parser = ijson.parse(tf)

                geo_columns = set()
                i = 0
                for prefix, event, value in parser:
                    if prefix == u'features.item.properties' and event == u'map_key':
                        geo_columns.add(value)
                        i += 1

                    if i > 10:
                        break
                    pass
                geo_columns_dict = [{'value': item, 'text': item} for item in sorted(geo_columns)]
        except Exception as e:
            log.warn(u'Error accessing resource size for resource {}: {}'.format(resource_dict.get('name', ''),
                                                                                 str(e)))
            geo_columns_dict = {}
        return geo_columns_dict

    def setup_template_variables(self, context, data_dict):

        max_zoom_values = [{'value': str(item), 'text': str(item)} for item in range(1, 16)]
        max_zoom_values.insert(0, {'value': 'default', 'text': p.toolkit._('Default')})

        show_legend_values = [
            {
                'value': 'true',
                'text': p.toolkit._('Yes')
            },
            {
                'value': 'false',
                'text': p.toolkit._('No')
            }
        ]

        geo_columns_dict = self._detect_fields_in_geojson(data_dict['resource'])

        resource_view_dict = data_dict['resource_view']

        values_resource_id = resource_view_dict.get('values_resource_id')
        if values_resource_id:

            values_res_dict = logic.get_action('resource_show')(context, {'id': values_resource_id})

            return {
                'map': {
                    'map_datatype_2': 'filestore',
                    'map_district_name_column': resource_view_dict.get('district_name_column'),
                    'map_datatype_1': 'datastore',
                    'map_dataset_id_1': values_res_dict.get('package_id'),
                    'map_dataset_id_2': data_dict['resource'].get('package_id'),
                    'map_resource_id_2': data_dict['resource'].get('id'),
                    'map_resource_id_1': values_resource_id,
                    'map_title': resource_view_dict.get('map_name'),
                    'map_values': resource_view_dict.get('values_column_name'),
                    'map_column_2': resource_view_dict.get('map_join_column'),
                    'map_column_1': resource_view_dict.get('values_join_column'),
                    'map_description_column': resource_view_dict.get('values_description_column'),
                    'is_crisis': 'false',
                    'basemap_url': 'default',
                    'map_threshold': resource_view_dict.get('threshold'),
                    'max_zoom': resource_view_dict.get('max_zoom'),
                    'show_legend': resource_view_dict.get('show_legend'),
                },
                'formdata': {
                    'map_columns': geo_columns_dict,
                    'max_zoom_values': max_zoom_values,
                    'show_legend_values': show_legend_values
                }

            }
        else:
            return {
                'formdata': {
                    'map_columns': geo_columns_dict,
                    'max_zoom_values': max_zoom_values,
                    'show_legend_values': show_legend_values
                }
            }

    def view_template(self, context, data_dict):
        return 'new_views/choropleth_map_view.html'

    def form_template(self, context, data_dict):
        return 'new_views/choropleth_map_view_form.html'
