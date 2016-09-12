'''
Created on Feb 18, 2015

@author: alexandru-m-g
'''
import logging
import collections
import json

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.lib.helpers as h
import ckan.new_authz as new_authz

import ckanext.hdx_search.controllers.search_controller as search_controller
import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.helpers.helpers as hdx_helpers
import ckan.controllers.organization as org
import ckanext.hdx_theme.helpers.less as less
from urllib import urlencode
from pylons import config
from ckan.controllers.api import CONTENT_TYPES
import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
response = common.response
_ = common._

log = logging.getLogger(__name__)

suffix = '#datasets-section'


def _get_embed_url(viz_config):
    ckan_url = config.get('ckan.site_url', '').strip()
    position = ckan_url.find('//')
    if position >= 0:
        ckan_url = ckan_url[position:]

    widget_url = ""
    if viz_config['type'] == '3W-dashboard':
        widget_url = "/widget/3W"
    if viz_config['type'] == 'WFP':
        widget_url = "/widget/WFP"

    url = ckan_url + widget_url
    return url


class CustomOrgController(org.OrganizationController, search_controller.HDXSearchController):
    def org_read(self, id, org_meta=None):
        '''

        :param id: The id of the organization
        :type id: str
        :param org_meta: Information about the organization
        :type org_meta: org_meta_dao.OrgMetaDao
        :return:
        '''

        if not org_meta:
            log.info("No org meta. Should have been created in organization_controller.py. Trying to create one now. ")
            org_meta = org_meta_dao.OrgMetaDao(id, c.user or c.author, c.userobj)
        c.org_meta = org_meta

        org_info = self.get_org(org_meta)

        if self._is_facet_only_request():
            c.full_facet_info = self.get_dataset_search_results(org_info['name'])
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            template_data = self.generate_template_data(org_info)

            result = render(
                'organization/custom/custom_org.html', extra_vars=template_data)

            return result

    def assemble_viz_config(self, vis_json_config, org_id=None):
        try:
            visualization = json.loads(vis_json_config)
        except Exception, e:
            log.warning(e)
            return "{}"

        config = {
            'title': visualization.get('viz-title', ''),
            'data_link_url': visualization.get('viz-data-link-url', '#'),
            'type': visualization.get('visualization-select', '')
        }

        if visualization.get('visualization-select', '') == 'ROEA':
            config.update({
                'data': "/api/action/datastore_search?resource_id=" + visualization.get('viz-resource-id',
                                                                                        '') + "&limit=10000000",
                'geo': h.url_for('perma_storage_file', id=visualization.get('viz-geo-dataset-id', ''),
                                 resource_id=visualization.get('viz-geo-resource-id', '')),
                'source': visualization.get('viz-data-source', '')
            })

        if visualization.get('visualization-select', '') == 'embedded' or visualization.get('visualization-select', '') == 'embedded-preview':
            config.update({
                'title': visualization.get('vis-title', ''),
                'data_link_url': visualization.get('vis-data-link-url', ''),
                'vis_url': visualization.get('vis-url', ''),
                'height': visualization.get('vis-height', '600px') if visualization.get('vis-height', '600px') != '' else '600px',
                'width': visualization.get('vis-width', '100%') if visualization.get('vis-width', '100%') != '' else '100%',
                'selector': visualization.get('vis-preview-selector', ''),
                'embedded_preview': h.url_for('image_serve', label=org_id + '_embedded_preview.png')
            })

        if visualization.get('visualization-select', '') == 'WFP':
            config.update({
                'embedded': "true",
                'datastore_id': visualization.get('viz-resource-id', '')
            })

        else:
            if visualization.get('datatype_1', '') == 'filestore':
                datatype = "filestore"
                data = h.url_for('perma_storage_file', id=visualization.get('dataset_id_1', ''),
                                 resource_id=visualization.get('resource_id_1', ''))
            else:
                datatype = "datastore"
                data = "/api/action/datastore_search?resource_id=" + visualization.get('resource_id_1',
                                                                                       '') + "&limit=10000000"

            if visualization.get('datatype_2', '') == 'filestore':
                geotype = "filestore"
                geo = h.url_for('perma_storage_file', id=visualization.get('dataset_id_2', ''),
                                resource_id=visualization.get('resource_id_2', ''))
            else:
                geotype = "datastore"
                geo = "/api/action/datastore_search?resource_id=" + visualization.get('resource_id_2',
                                                                                      '') + "&limit=10000000"

            # beware that visualisation type constants are also used
            # in the template to select different resource bundles
            if visualization.get('visualization-select', '') == '3W-dashboard':
                config.update({'datatype': datatype,
                               'data': data,
                               'whoFieldName': visualization.get('who-column', ''),
                               'whatFieldName': visualization.get('what-column', ''),
                               'whereFieldName': visualization.get('where-column', ''),
                               'startFieldName': visualization.get('start-column', ''),
                               'endFieldName': visualization.get('end-column', ''),
                               'formatFieldName': visualization.get('format-column', ''),
                               'geotype': geotype,
                               'geo': geo,
                               'joinAttribute': visualization.get('where-column-2', ''),
                               'nameAttribute': visualization.get('map_district_name_column', ''),
                               'colors': visualization.get('colors', '')
                               })

        return config

    def generate_template_data(self, org_info):
        errors = []
        org_id = org_info['name']
        top_line_num_resource = org_info.get('topline_resource', None)

        top_line_items = []
        if top_line_num_resource:
            try:
                top_line_items = self.get_top_line_numbers(top_line_num_resource)
            except Exception, e:
                log.warning(e)
                hdx_helpers.add_error('Fetching data problem', str(e), errors)

        req_params = self.process_req_params(org_id, request.params)

        activities = None
        # facets = {}
        # query_placeholder = ''
        try:
            c.full_facet_info = self.get_dataset_search_results(org_id)
            c.tab = tab = self.get_tab_name()
            # query_placeholder = self.generate_query_placeholder(tab, c.dataset_counts, c.indicator_counts)

            # facets = self.get_facet_information(
            #     tab_results, all_results, tab, req_params)
            if tab == 'activities':
                activities = self.get_activity_stream(org_info.get('id', org_id))
        except Exception, e:
            log.warning(e)
            hdx_helpers.add_error('Fetching data problem', str(e), errors)

        allow_basic_user_info = self.check_access('hdx_basic_user_info')
        allow_req_membership = not h.user_in_org_or_group(org_info['id']) and allow_basic_user_info

        allow_edit = self.check_access('organization_update', {'id': org_info['id']})
        allow_add_dataset = self.check_access('package_create',
                                              {'organization_id': org_info['id'],
                                               'owner_org': org_info['id']})

        viz_config = self.assemble_viz_config(org_info['visualization_config'], org_id)

        follower_count = get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': org_info['id']}
        )
        add_data_url = h.url_for('add dataset') + '?organization_id={}'.format(org_info['id'])
        template_data = {
            'data': {
                'org_info': org_info,
                'member_count': hdx_helpers.get_group_members(org_info['id']),
                'follower_count': follower_count,
                'top_line_items': top_line_items,
                'search_results': {
                    # 'facets': facets,
                    'activities': activities,
                    # 'query_placeholder': query_placeholder
                },
                'links': {
                    'edit': h.url_for('organization_edit', id=org_id),
                    'members': h.url_for('organization_members', id=org_id),
                    'request_membership': h.url_for('request_membership', org_id=org_id),
                    'add_data': add_data_url
                },
                'request_params': request.params,
                'permissions': {
                    'edit': allow_edit,
                    'add_dataset': allow_add_dataset,
                    'view_members': allow_basic_user_info,
                    'request_membership': allow_req_membership
                },
                'show_admin_menu': allow_add_dataset or allow_edit,
                'show_visualization': False if 'Choose Visualization Type' == viz_config['type'] else True,
                'visualization': {
                    'config': viz_config,
                    'config_type': viz_config['type'],
                    'config_url': urlencode(viz_config, True),
                    'embed_url': _get_embed_url(viz_config),
                    'basemap_url': config.get('hdx.orgmap.url')
                }

            },
            'errors': errors,
            'error_summary': '',

        }

        if template_data['data']['show_visualization']:
            template_data['data']['show_visualization'] = \
                hdx_helpers.check_all_str_fields_not_empty(template_data['data']['visualization'],
                                                       'Visualization config field "{}" is empty',
                                                       skipped_keys=['config'],
                                                       errors=errors)

        template_data['error_summary'] = \
            '; '.join([e.get('message', '') for e in template_data['errors']])
        return template_data

    def get_org(self, org_meta):
        '''

        :param org_meta: Information about the organization
        :type org_meta: org_meta_dao.OrgMetaDao
        :return: a dict containing more information specific for custom orgs
        :rtype: dict
        '''

        result = org_meta.org_dict

        org_dict = {
            'id': result['id'],
            'display_name': result.get('display_name', ''),
            'description': result['description'],
            'name': result['name'],
            'link': org_meta.org_dict.get('extras', {}).get('org_url'),
            'revision_id': result['revision_id'],
            'topline_resource': org_meta.customization.get(''),
            'modified_at': result.get('modified_at', 'topline_resource'),
            'image_sq': org_meta.customization.get('image_sq'),
            'image_rect': org_meta.customization.get('image_rect'),
            'visualization_config': result.get('visualization_config', ''),
        }

        return org_dict

    def get_top_line_numbers(self, top_line_num_resource):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        top_line_src_dict = {
            'top-line-numbers': {
                'resource_id': top_line_num_resource
            }
        }
        datastore_access = data_access.DataAccess(top_line_src_dict)
        datastore_access.fetch_data(context)
        top_line_items = datastore_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        return top_line_items

    def get_tab_name(self):
        ext_indicator = request.params.get('ext_indicator', None)
        ext_activities = request.params.get('ext_activities', None)
        if ext_indicator:
            tab = 'indicators' if ext_indicator == '1' else 'datasets'
        elif ext_activities:
            tab = 'activities'
        else:
            tab = 'all'

        return tab

    def process_req_params(self, org_id, params):
        req_params = {}
        req_params['id'] = org_id
        accepted_params = ['sort', 'q', 'organization', 'tags',
                           'vocab_Topics', 'license_id', 'groups',
                           'res_format', '_show_filters', 'ext_indicator', 'id']
        for k, v in params.items():
            if k in accepted_params:
                if k in req_params:
                    req_params[k].append(v)
                else:
                    req_params[k] = [v]
        return req_params

    # def get_facet_information(self, tab_results, all_results, tab, req_params):
    #     search_facets = None
    #     result_facets = collections.OrderedDict()
    #     if tab == 'indicators' or tab == 'datasets':
    #         search_facets = tab_results['search_facets']
    #     else:
    #         search_facets = all_results['search_facets']
    #
    #     self._add_facet(result_facets, search_facets, 'groups', _('Locations'))
    #     self._add_facet(result_facets, search_facets, 'tags', _('Tags'))
    #     self._add_facet(
    #         result_facets, search_facets, 'res_format', _('Formats'))
    #     self._add_facet(
    #         result_facets, search_facets, 'license_id', _('Licenses'))
    #
    #     # self._populate_facet_links(result_facets, req_params)
    #
    #     return result_facets
    #
    # def _add_facet(self, facet_dict, search_facets, facet_code, facet_name):
    #     if facet_code in search_facets:
    #         facet_dict[facet_name] = {
    #             'value_items': search_facets.get(facet_code, {}).get('items', []),
    #             'code': search_facets.get(facet_code, {}).get('title', '')
    #         }
    #         facet_dict[facet_name]['count'] = len(
    #             facet_dict[facet_name]['value_items'])

    # def _populate_facet_links(self, facets, params):
    #     for facet in facets.itervalues():
    #         params_copy = params.copy()
    #         code = facet['code']
    #         if code in params:
    #             facet['is_used'] = True
    #             params_copy.pop(code)
    #             facet['clear_link'] = h.url_for(
    #                 self._get_named_route(), **params_copy) + suffix
    #         else:
    #             facet['is_used'] = False
    #
    #         for item in facet['value_items']:
    #             params_item_copy = params.copy()
    #             if code in params:
    #                 if item['name'] in params[code]:
    #                     # user already filtered by this item
    #                     params_item_copy[code] = [
    #                         el for el in params_item_copy[code] if el != item['name']]
    #                     item['remove_link'] = h.url_for(
    #                         self._get_named_route(), **params_item_copy) + suffix
    #                     item['is_used'] = True
    #                 else:
    #                     params_item_copy[code] = params_item_copy[
    #                                                  code] + [item['name']]
    #                     item['filter_link'] = h.url_for(
    #                         self._get_named_route(), **params_item_copy) + suffix
    #                     item['is_used'] = False
    #             else:
    #                 params_item_copy[code] = [item['name']]
    #                 item['filter_link'] = h.url_for(
    #                     self._get_named_route(), **params_item_copy) + suffix
    #                 item['is_used'] = False

    def get_dataset_search_results(self, org_code):

        user = c.user or c.author
        ignore_capacity_check = False
        is_org_member = (user and
                         new_authz.has_user_permission_for_group_or_org(org_code, user, 'read'))
        if is_org_member:
            ignore_capacity_check = True

        package_type = 'dataset'

        suffix = '#datasets-section'

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('organization_read', id=org_code, **params) + suffix

        fq = 'organization:"{}"'.format(org_code)
        facets = {
            'vocab_Topics': _('Topics')
        }
        full_facet_info = self._search(package_type, pager_url, additional_fq=fq, additional_facets=facets,
                                       ignore_capacity_check=ignore_capacity_check)
        full_facet_info.get('facets', {}).pop('organization', {})

        c.other_links['current_page_url'] = h.url_for('organization_read', id=org_code)

        return full_facet_info

    def get_activity_stream(self, org_uuid):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'for_view': True}
        # 'group_uuid': country_uuid,
        act_data_dict = {
            'id': org_uuid, 'group_uuid': org_uuid, 'limit': 7, 'group_type': 'organization'}
        result = get_action(
            'hdx_get_group_activity_list')(context, act_data_dict)
        return result

    # def generate_query_placeholder(self, tab, dataset_count, indicator_count):
    #     static_prefix = _('Search')
    #     static_suffix = '...'
    #     body = ''
    #
    #     if tab == 'all':
    #         body = hdx_helpers.hdx_show_singular_plural(dataset_count + indicator_count,
    #                                                     _('indicator / dataset'),
    #                                                     _('indicators & datasets'), True)
    #     elif tab == 'indicators':
    #         body = hdx_helpers.hdx_show_singular_plural(indicator_count, _('indicator'), _('indicators'), True)
    #     elif tab == 'datasets':
    #         body = hdx_helpers.hdx_show_singular_plural(dataset_count, _('dataset'), _('datasets'), True)
    #     else:
    #         return ''
    #
    #     response = static_prefix + " " + body + " " + static_suffix
    #     return response

    def check_access(self, action_name, data_dict=None):
        if data_dict is None:
            data_dict = {}

        context = {'model': model,
                   'user': c.user or c.author}
        try:
            result = logic.check_access(action_name, context, data_dict)
        except logic.NotAuthorized:
            result = False

        return result

    def _activity_template(self, group_type):
        return  'organization/custom_activity_stream.html'
