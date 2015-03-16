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

import ckanext.hdx_search.controllers.simple_search_controller as simple_search_controller
import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.helpers.helpers as hdx_helpers
import ckan.controllers.organization as org
import ckanext.hdx_theme.helpers.less as less

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)

suffix = '#datasets-section'

class CustomOrgController(org.OrganizationController, simple_search_controller.HDXSimpleSearchController):

    def org_read(self, id):

        org_info = self.get_org(id)

        template_data = self.generate_template_data(org_info)

        css_dest_dir = '/organization/' + org_info['name']

        template_data['style'] = {
            'css_path': less.generate_custom_css_path(css_dest_dir, id, org_info['modified_at'], True)
        }


        result = render(
            'organization/custom/custom_org.html', extra_vars=template_data)

        return result

    def assemble_viz_config(self, visualization):
        try:
            visualization = json.loads(visualization)
        except:
            return "{}"
        if visualization['datatype_1'] =='filestore':
            datatype = "filestore"
            data = h.url_for('perma_storage_file', id=visualization['dataset_id_1'], resource_id=visualization['resource_id_1'])
        else:
            datatype = "datastore"
            data = "/api/action/datastore_search?resource_id="+visualization['resource_id_1']+"&limit=10000000"
    
        if visualization['datatype_2'] =='filestore':
            geotype = "filestore"
            geo = h.url_for('perma_storage_file', id=visualization['dataset_id_2'], resource_id=visualization['resource_id_2'])
        else:
            geotype = "datastore"
            geo = "/api/action/datastore_search?resource_id="+visualization['resource_id_2']+"&limit=10000000"
    
        if visualization['visualization-select'] == '3W-dashboard':
            config = {'title':visualization['viz-title'],
            'description':visualization['viz-description'],
            'datatype': datatype,
            'data': data,
            'whoFieldName':visualization['who-column'],
            'whatFieldName':visualization['what-column'],
            'whereFieldName':visualization['where-column'],
            'geotype': geotype,
            'geo':geo,
            'joinAttribute':visualization['where-column-2'],
            'x':visualization['pos-x'],
            'y':visualization['pos-y'],
            'zoom':visualization['zoom'],
            'colors':visualization.get('colors','')
};
        return json.dumps(config)

    def generate_template_data(self, org_info):
        org_id = org_info['name']

        top_line_num_dataset = org_info.get('topline_dataset', None)
        top_line_num_resource = org_info.get('topline_resource', None)

        if top_line_num_dataset and top_line_num_resource:
            top_line_items = self.get_top_line_numbers(top_line_num_dataset, top_line_num_resource)
        else:
            top_line_items = []

        req_params = self.process_req_params(org_id, request.params)

        tab_results, all_results = self.get_dataset_search_results(
            org_id, request.params)
        tab = self.get_tab_name()
        query_placeholder = self.generate_query_placeholder(tab, c.dataset_counts, c.indicator_counts)

        facets = self.get_facet_information(
            tab_results, all_results, tab, req_params)
        if tab == 'activities':
            activities = self.get_activity_stream(org_info.get('id', org_id))
        else:
            activities = None

        allow_basic_user_info = self.check_access('hdx_basic_user_info')
        allow_req_membership = not h.user_in_org_or_group(org_info['id']) and allow_basic_user_info

        template_data = {
            'data': {
                'org_info': org_info,
                'top_line_items': top_line_items,
                'search_results': {
                    'facets': facets,
                    'activities': activities,
                    'query_placeholder': query_placeholder
                },
                'links': {
                    'edit': h.url_for('organization_edit', id=org_id),
                    'members': h.url_for('organization_members', id=org_id),
                    'request_membership': h.url_for('request_membership', org_id=org_id)
                },
                'request_params': request.params,
                'permissions': {
                    'edit': self.check_access('organization_update', {'id': org_info['id']}),
                    'view_members': allow_basic_user_info,
                    'request_membership': allow_req_membership
                },
                'visualization_config': self.assemble_viz_config(org_info['visualization_config'])
            },
            'errors': None,
            'error_summary': None,

        }

        return template_data

    def get_org(self, org_id):
        group_type = 'organization'

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True}
        data_dict = {'id': org_id}

        try:
            context['include_datasets'] = False
            result = get_action(
                'hdx_light_group_show')(context, data_dict)

            org_url = [el.get('value', None) for el in result.get('extras', []) if el.get('key', '') == 'org_url']

            json_extra = [el.get('value', None) for el in result.get('extras', []) if el.get('key', '') == 'customization']
            jsonstring = json_extra[0] if len(json_extra) == 1 else ''
            top_line_src_info = self._get_top_line_src_info(jsonstring)

            org_dict = {
                'id': result['id'],
                'display_name': result.get('display_name', ''),
                'description': result['group'].description,
                'name': result['name'],
                'link': org_url[0] if len(org_url) == 1 else None,
                'revision_id': result['group'].revision_id,
                'topline_dataset': top_line_src_info[0],
                'topline_resource': top_line_src_info[1],
                'modified_at': result.get('modified_at', ''),
                'image_url': result.get('image_url',''),
                'visualization_config': result.get('visualization_config',''),
            }

            return org_dict

        except NotFound:
            abort(404, _('Org not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read org %s') % id)

        return {}

    def _get_top_line_src_info(self, jsonstring):
        if jsonstring and jsonstring.strip():
            json_dict = json.loads(jsonstring)
            if 'topline_dataset' in json_dict and 'topline_resource' in json_dict:
                return (json_dict['topline_dataset'], json_dict['topline_resource'])

        return (None, None)

    def get_top_line_numbers(self, top_line_num_dataset, top_line_num_resource):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        top_line_src_dict = {
            'top-line-numbers': {
                'dataset': top_line_num_dataset,
                'resource_id': top_line_num_resource
            }
        }
        datastore_access = data_access.CrisisDataAccess(top_line_src_dict)
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

    def get_facet_information(self, tab_results, all_results, tab, req_params):
        search_facets = None
        result_facets = collections.OrderedDict()
        if tab == 'indicators' or tab == 'datasets':
            search_facets = tab_results['search_facets']
        else:
            search_facets = all_results['search_facets']

        self._add_facet(result_facets, search_facets, 'groups', _('Locations'))
        self._add_facet(result_facets, search_facets, 'tags', _('Tags'))
        self._add_facet(
            result_facets, search_facets, 'res_format', _('Formats'))
        self._add_facet(
            result_facets, search_facets, 'license_id', _('Licenses'))

        self._populate_facet_links(result_facets, req_params)

        return result_facets

    def _add_facet(self, facet_dict, search_facets, facet_code, facet_name):
        if facet_code in search_facets:
            facet_dict[facet_name] = {
                'value_items': search_facets.get(facet_code, {}).get('items', []),
                'code': search_facets.get(facet_code, {}).get('title', '')
            }
            facet_dict[facet_name]['count'] = len(
                facet_dict[facet_name]['value_items'])

    def _populate_facet_links(self, facets, params):
        for facet in facets.itervalues():
            params_copy = params.copy()
            code = facet['code']
            if code in params:
                facet['is_used'] = True
                params_copy.pop(code)
                facet['clear_link'] = h.url_for(
                    self._get_named_route(), **params_copy) + suffix
            else:
                facet['is_used'] = False

            for item in facet['value_items']:
                params_item_copy = params.copy()
                if code in params:
                    if item['name'] in params[code]:
                        # user already filtered by this item
                        params_item_copy[code] = [
                            el for el in params_item_copy[code] if el != item['name']]
                        item['remove_link'] = h.url_for(
                            self._get_named_route(), **params_item_copy) + suffix
                        item['is_used'] = True
                    else:
                        params_item_copy[code] = params_item_copy[
                            code] + [item['name']]
                        item['filter_link'] = h.url_for(
                            self._get_named_route(), **params_item_copy) + suffix
                        item['is_used'] = False
                else:
                    item['filter_link'] = h.url_for(
                        self._get_named_route(), **params_item_copy) + suffix
                    item['is_used'] = False

    def get_dataset_search_results(self, org_code, req_params):
        facets = ['groups', 'tags', 'res_format',
                  'license_id', 'extras_indicator']

        fq = u'organization:"{}" +dataset_type:dataset'.format(org_code)
        for (param, value) in req_params.items():
            is_fq_param = param in facets and param != 'ext_indicator'
            if is_fq_param and len(value):
                fq += u' {}:"{}"'.format(param, value)

        search_extras = {}
        ext_indicator = req_params.get('ext_indicator', None)
        if ext_indicator:
            search_extras['ext_indicator'] = ext_indicator

        ext_activities = req_params.get('ext_activities', None)
        if ext_activities:
            search_extras['ext_activities'] = ext_activities

        # limit = self._allowed_num_of_items(search_extras)
        limit = 8
        page = self._page_number()
        params_nopage = {k: v for k, v in req_params.items() if k != 'page'}

        sort_by = req_params.get('sort', None)

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            params['id'] = org_code
            return h.url_for('custom_org_read', **params) + suffix

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        is_org_member = (context.get('user', None) and
                           new_authz.has_user_permission_for_group_or_org(org_code, context.get('user'), 'read'))
        if is_org_member:
            context['ignore_capacity_check'] = True

        self._set_other_links(
            suffix=suffix, other_params_dict={'id': org_code})
        self._which_tab_is_selected(search_extras)
        (query, all_results) = self._performing_search(req_params.get('q', ''), fq, facets, limit, page, sort_by,
                                                       search_extras, pager_url, context)

        return query, all_results

    def _set_other_links(self, suffix='', other_params_dict=None):
        super(CustomOrgController, self)._set_other_links(
            suffix=suffix, other_params_dict=other_params_dict)
        c.other_links['advanced_search'] = h.url_for(
            'search', organization=other_params_dict['id'])

    def _get_named_route(self):
        return 'custom_org_read'

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

    def generate_query_placeholder(self, tab, dataset_count, indicator_count):
        static_prefix = _('Search')
        static_suffix = '...'
        body = ''

        if tab == 'all':
            body = hdx_helpers.hdx_show_singular_plural(dataset_count+indicator_count,
                                                        _('indicator / dataset'),
                                                        _('indicators & datasets'), True)
        elif tab == 'indicators':
            body = hdx_helpers.hdx_show_singular_plural(indicator_count, _('indicator'), _('indicators'), True)
        elif tab == 'datasets':
            body = hdx_helpers.hdx_show_singular_plural(dataset_count, _('dataset'), _('datasets'), True)
        else:
            return ''

        response = static_prefix + " " + body + " " + static_suffix
        return response

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

