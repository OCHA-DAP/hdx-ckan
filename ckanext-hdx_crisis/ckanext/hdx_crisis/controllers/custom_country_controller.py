'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging
import math
import pylons.config as config

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.controllers.group as group
import ckanext.hdx_crisis.controllers.crisis_controller as controllers
import ckanext.hdx_crisis.dao.country_data_access as country_data_access
import ckanext.hdx_org_group.actions.get as hdx_org_get
import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.helpers.helpers as helpers

render = base.render
c = common.c
get_action = logic.get_action
json = common.json
_ = common._

log = logging.getLogger(__name__)

IndicatorAccess = indicator_access.IndicatorAccess

def is_custom(environ, result):
    try:
        group_info, custom_dict = hdx_org_get.get_group(result['id'])
        result['group_info'] = group_info
        result['group_customization'] = custom_dict
        if group_info.get('custom_loc', False):
            return True
    except Exception, e:
        log.warning("Exception while checking if page is custom")
    return False


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


    def _ckan_src_chart_config(self, chart_config, chart_type):
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
                    'source_type': 'ckan',
                    'datastore_id': resource_id,
                    # 'title': self._get_resource_name(resource_id),
                    # 'org_name': 'OCHA',
                    # 'url': None,
                    'data_link_url': resource.get('chart_data_link_url', ''),
                    'source': resource.get('chart_source', 'OCHA'),
                    'label_x': resource.get('chart_label', ''),
                    'column_x': resource.get('chart_x_column', False),
                    'column_y': resource.get('chart_y_column', False),
                }
                chart['sources'].append(source)
        return chart

    def _cps_src_chart_config(self, chart_config, chart_type, country_code):
        dataseries_code = chart_config.get('chart_dataseries_code', '')
        if '___' in dataseries_code:
            splitted_codes = dataseries_code.split('___')
            dataseries_list = [(splitted_codes[0], splitted_codes[1])]
            indicator_dao = IndicatorAccess(country_code, dataseries_list, {'sorting': 'INDICATOR_TYPE_ASC'})
            indicator_dao.fetch_indicator_data_from_cps()
            structured_cps_data = indicator_dao.get_structured_data_from_cps()
            ckan_data = indicator_dao.fetch_indicator_data_from_ckan()
            try:
                ind_code = structured_cps_data.iterkeys().next()
                ind_dict = structured_cps_data[ind_code].itervalues().next()
                chart = {
                    'title': chart_config.get('chart_title', ''),
                    'type': chart_type,
                    'dataseries_code': chart_config.get('chart_dataseries_code', ''),
                    'title_x': _('Date'),
                    'title_y': ind_dict.get('unit', ''),
                    'sources': [
                        {
                            'source_type': 'cps',
                            'source': ind_dict.get('sourceName', ''),
                            'label_x': ind_dict.get('title', ''),
                            'column_x': 'date',
                            'column_y': 'value',
                            'data': {
                                'fields': [
                                    {
                                        'id': 'date',
                                        'type': 'timestamp'
                                    },
                                    {
                                        'id': 'value',
                                        'type': 'float'
                                    }
                                ],
                                'records': ind_dict.get('data', [])
                            }
                        }
                    ]

                }
                data_link_url = ckan_data.get(ind_code, {}).get('datasetLink', '')
                if data_link_url:
                    chart['sources'][0]['data_link_url'] = data_link_url
                return chart
            except Exception, e:
                log.warning("Exception while iterating dataseries data: " + str(e))
                return {}

    def _get_charts_config(self, country_code, custom_dict, top_line_items_count, errors):
        charts = []
        for index, chart_config in enumerate(custom_dict.get('charts', [])):
            if top_line_items_count <= 4 and index == 1:
                break
            source_type = 'ckan'
            chart_type = 'area'
            if 'bar' in chart_config.get('chart_type', ''):
                chart_type = 'bar'
            if 'indicator' in chart_config.get('chart_type', ''):
                source_type = 'cps'

            if source_type == 'ckan':
                chart = self._ckan_src_chart_config(chart_config, chart_type)
                if self._show_chart(chart, errors):
                    charts.append(chart)
            else:
                chart = self._cps_src_chart_config(chart_config, chart_type, country_code)
                if self._show_chart(chart, errors):
                    charts.append(chart)

        return charts

    # def _get_resource_name(self, resource_id):
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author}
    #     try:
    #         resource_dict = get_action('resource_show')(context, {'id': resource_id})
    #
    #         return resource_dict['name']
    #     except logic.NotFound, e:
    #         return ''

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
                                            'Chart source config field "{}" is empty', ['data'],
                                            errors=errors)
        if not chart_src_check:
            return False

        return True

    def _create_sections(self, top_line_items, charts_config_data):
        sections = []
        len_charts = len(charts_config_data)
        len_toplines = len(top_line_items)
        max = len_charts if len_charts > int(math.ceil(len_toplines/4.0)) else int(math.ceil(len_toplines/4.0))

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

        charts_config_data = self._get_charts_config(group_info['name'], custom_dict, len(top_line_items), errors)

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

        is_crisis = group_info['name']=='nepal-earthquake'

        template_data['data']['is_crisis'] = is_crisis
        template_data['data']['map']['is_crisis'] = 'true' if is_crisis else 'false'
        template_data['data']['map']['basemap_url'] = 'default' if not is_crisis else config.get('hdx.crisismap.url')

        if is_crisis:
            template_data['data']['map']['circle_markers'] = config.get('hdx.nepal_earthquake.filestore.circle_markers')
            template_data['data']['map']['shakemap'] = config.get('hdx.nepal_earthquake.filestore.shakemap')

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
