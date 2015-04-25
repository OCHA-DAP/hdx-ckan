'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.controllers.group as group


import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.helpers.helpers as helpers
import ckanext.hdx_crisis.controllers.crisis_controller as controllers

render = base.render
c = common.c
get_action = logic.get_action
json = common.json

log = logging.getLogger(__name__)


def is_custom(environ, result):
    try:
        group_info, custom_dict = get_group(result['id'])
        result['group_info'] = group_info
        result['group_customization'] = custom_dict
        if group_info.get('custom_loc', False):
            return True
    except Exception, e:
        log.warning("Exception while checking if page is custom")
    return False


def get_group(id):
    context = {'model': model, 'session': model.Session,
               'include_datasets': False,
               'for_view': True}
    data_dict = {'id': id}

    group_info = get_action('hdx_light_group_show')(context, data_dict)

    extras_dict = {item['key']: item['value'] for item in group_info.get('extras', {})}
    json_string = extras_dict.get('customization', None)
    if json_string:
        custom_dict = json.loads(json_string)
    else:
        custom_dict = {}

    return group_info, custom_dict


class CustomCountryController(group.GroupController, controllers.CrisisController):

    def read(self, id,  group_info, group_customization):

        # group_info, custom_dict = get_group(id)

        template_data = self.generate_template_data(group_info, group_customization)

        return render('country/custom_country.html', extra_vars=template_data)

    # Will soon be removed
    # def show(self):
    #     return self.read(u'col')

    def _get_top_line_datastore_id(self, custom_dict):
        return custom_dict.get('topline_resource', None)

    def _get_charts_config(self, custom_dict, top_line_items_count, errors):
        charts = []
        for index, chart_config in enumerate(custom_dict.get('charts', [])):
            if top_line_items_count <= 4 and index == 1:
                break
            chart_type = 'area'
            if 'bar' in chart_config.get('chart_type', ''):
                chart_type = 'bar'
            chart = {
                'title': chart_config.get('chart_title', ''),
                'type': chart_type,
                'title_x': chart_config.get('chart_x_label', ''),
                'title_y': chart_config.get('chart_y_label', ''),
                'sources': []
            }

            for resource in chart_config.get('resources', []):
                resource_id = resource.get('chart_resource_id', False)
                if resource_id:
                    source = {
                        'datastore_id': resource_id,
                        'title': self._get_resource_name(resource_id),
                        #'org_name': 'OCHA',
                        # 'url': None,
                        'data_link_url': resource.get('chart_data_link_url', ''),
                        'source': resource.get('chart_source', 'OCHA'),
                        'label_x': resource.get('chart_label', ''),
                        'column_x': resource.get('chart_x_column', False),
                        'column_y': resource.get('chart_y_column', False),
                        }
                    chart['sources'].append(source)
            if self._show_chart(chart, errors):
                charts.append(chart)

        return charts

    def _get_resource_name(self, resource_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        try:
            resource_dict = get_action('resource_show')(context, {'id': resource_id})

            return resource_dict['name']
        except logic.NotFound, e:
            return ''

    def _get_maps_config(self, custom_dict):
        return custom_dict.get('map', {})

    def _show_map(self, map_dict, errors):
        return helpers.check_all_str_fields_not_empty(map_dict, 'Map config field "{}" is empty', errors=errors)

    def _show_chart(self, chart_dict, errors):
        chart_main_check = \
            helpers.check_all_str_fields_not_empty(chart_dict,
                                            'Chart config field "{}" is empty', ['sources'], errors=errors)
        if not chart_main_check:
            return False
        if len(chart_dict.get('sources', [])) == 0:
            return False

        chart_src_check = \
            helpers.check_all_str_fields_not_empty(chart_dict['sources'][0],
                                            'Chart source config field "{}" is empty', errors=errors)
        if not chart_src_check:
            return False

        return True

    def _create_sections(self, top_line_items, charts_config_data):
        sections = []
        len_charts = len(charts_config_data)
        len_toplines = len(top_line_items)
        max = len_charts if len_charts > len_toplines/4 else len_toplines/4

        for i in range(0, max):
            section = {
                'top_line_items': top_line_items[i*4:(i+1)*4],
                'chart': charts_config_data[i] if i < len_charts else None
            }
            sections.append(section)
        return sections

    def generate_template_data(self, group_info, custom_dict):

        errors = []

        country_name = group_info['name']

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_items = []
        try:
            top_line_resource_id = self._get_top_line_datastore_id(custom_dict)
            top_line_items = self.get_top_line_numbers(top_line_resource_id)
        except Exception, e:
            log.warning(e)
            helpers.add_error('Fetching data problem', str(e), errors)

        search_params = {u'groups': country_name}

        self._generate_dataset_results(
            context, search_params, action_alias='show_custom_country', other_params_dict={'id': country_name})

        self._generate_other_links(search_params)

        charts_config_data = self._get_charts_config(custom_dict, len(top_line_items), errors)

        template_data = {
            'data': {
                'country_name': group_info['name'],
                'country_title': group_info.get('title', group_info['name']),
                # 'top_line_items': top_line_items,
                # 'charts': charts_config_data,
                'topline_chart_sections': self._create_sections(top_line_items, charts_config_data),
                'show_map': True,
                'map': self._get_maps_config(custom_dict)
            },
            'errors': errors,
            'error_summary': '',
        }

        template_data['data']['show_map'] = self._show_map(template_data['data']['map'], errors)

        template_data['error_summary'] = \
            '; '.join([e.get('message', '') for e in template_data['errors']])
        return template_data

    def get_top_line_numbers(self, top_line_resource_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        crisis_data_access = country_data_access.ColombiaCrisisDataAccess(top_line_resource_id)
        crisis_data_access.fetch_data(context)
        top_line_items = crisis_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        return top_line_items
