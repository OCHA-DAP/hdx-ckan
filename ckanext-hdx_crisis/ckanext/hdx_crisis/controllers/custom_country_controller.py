'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.controllers.group as group


import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_crisis.controllers.crisis_controller as controllers

render = base.render
c = common.c
get_action = logic.get_action
json = common.json

log = logging.getLogger(__name__)


def is_custom(environ, result):
    group_info, custom_dict = get_group(result['id'])
    result['group_info'] = group_info
    result['group_customization'] = custom_dict
    if group_info.get('custom_loc', False):
        return True
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

    def _get_charts_config(self, custom_dict):
        charts = []
        for chart_config in custom_dict.get('charts', []):
            chart = {
                'title': chart_config.get('chart_title', ''),
                'type': chart_config.get('chart_type', ''),
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
                        'org_name': 'OCHA',
                        'url': None,
                        'column_x': resource.get('chart_x_column', False),
                        'column_y': resource.get('chart_y_column', False),
                        }
                    chart['sources'].append(source)
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

    def generate_template_data(self, group_info, custom_dict):

        country_name = group_info['name']

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_resource_id = self._get_top_line_datastore_id(custom_dict)
        top_line_items = self.get_top_line_numbers(top_line_resource_id)

        search_params = {u'groups': country_name}

        self._generate_dataset_results(
            context, search_params, action_alias='show_custom_country', other_params_dict={'id': country_name} )

        self._generate_other_links(search_params)

        template_data = {
            'data': {
                'country_name': group_info['name'],
                'country_title': group_info.get('title', group_info['name']),
                'top_line_items': top_line_items,
                'charts': self._get_charts_config(custom_dict),
                'map': self._get_maps_config(custom_dict)
            },
            'errors': None,
            'error_summary': None,
        }

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
