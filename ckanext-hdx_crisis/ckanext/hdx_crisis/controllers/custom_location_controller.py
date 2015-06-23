'''
Created on Dec 2, 2014

@author: alexandru-m-g
updated by dan on Jun 22, 2015
'''

import logging
import math

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.controllers.group as group
import ckanext.hdx_crisis.dao.location_data_access as location_data_access
import ckanext.hdx_org_group.actions.get as hdx_org_get
import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.helpers.helpers as helpers
import ckanext.hdx_crisis.dao.crisis_config as crisis_config
import ckan.lib.helpers as h

render = base.render
c = common.c
get_action = logic.get_action
json = common.json
_ = common._
request = common.request
LocationDataAccess = location_data_access.LocationDataAccess
log = logging.getLogger(__name__)

IndicatorAccess = indicator_access.IndicatorAccess


def is_custom(environ, result):
    '''
    check if location is a custom one and/or contains visual customizations
    :param environ:
    :param result:
    :return:
    '''
    try:
        group_info, custom_dict = hdx_org_get.get_group(result['id'])
        result['group_info'] = group_info
        result['group_customization'] = custom_dict
        if group_info.get('custom_loc', False):
            return True
    except Exception, e:
        log.warning("Exception while checking if page is custom")
    return False


class CustomLocationController(group.GroupController, base.BaseController):
    '''
    Extends Group and Base Controller and is used by custom locations to populate
    and compute the data to be displayed
    Crisis Controller is deprecated and removed.
    '''

    def read(self, id, group_info, group_customization):

        template_data = self.generate_template_data(group_info, group_customization)
        return render('country/custom_country.html', extra_vars=template_data)

    def generate_template_data(self, group_info, custom_dict):
        '''
        Compute all data for current custom location/crisis
        :param group_info: information about group (location)
        :param custom_dict: information about map
        :return: return the template (dictionary) containing data
        '''
        errors = []

        country_name = group_info['name']

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        top_line_items = []
        try:
            top_line_resource_id = self._get_top_line_datastore_id(custom_dict)
            top_line_items = self.get_topline_numbers(top_line_resource_id)
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
                'topline_chart_sections': self._create_sections(top_line_items, charts_config_data),
                'show_map': True,
                'map': self._get_maps_config(custom_dict),
                'is_crisis': False

            },
            'errors': errors,
            'error_summary': '',
        }
        template_data['data']['map']['basemap_url'] = 'default'
        template_data['data']['map']['is_crisis'] = 'false'

        is_crisis = self.is_crisis(group_info['name'])
        if is_crisis:
            crisis = crisis_config.CrisisConfig.get_crises(group_info['name'])
            crisis.process_config(template_data['data'])

        template_data['data']['show_map'] = self._show_map(template_data['data']['map'], errors)

        template_data['error_summary'] = \
            '; '.join([e.get('message', '') for e in template_data['errors']])
        return template_data

    def _get_top_line_datastore_id(self, custom_dict):
        return custom_dict.get('topline_resource', None)

    def get_topline_numbers(self, top_line_resource_id):
        '''
        Compute topline numbers items
        :param top_line_resource_id:
        :return:
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        loc_data_access = LocationDataAccess(top_line_resource_id)
        loc_data_access.fetch_data(context)
        top_line_items = loc_data_access.get_top_line_items()

        formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
        formatter.format_results()

        return top_line_items

    def _ckan_src_chart_config(self, chart_config, chart_type):
        '''
        Used in _get_charts_config method. Return information stored in CKAN to be used in a chart
        :param chart_config:
        :param chart_type:
        :return: chart dictionary metadata and data
        '''
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
                    'data_link_url': resource.get('chart_data_link_url', ''),
                    'source': resource.get('chart_source', 'OCHA'),
                    'label_x': resource.get('chart_label', ''),
                    'column_x': resource.get('chart_x_column', False),
                    'column_y': resource.get('chart_y_column', False),
                }
                chart['sources'].append(source)
        return chart

    def _cps_src_chart_config(self, chart_config, chart_type, country_code):
        '''
        Used in _get_charts_config method. Return information stored in CPS to be used in a chart
        :param chart_config:
        :param chart_type:
        :param country_code:
        :return: chart dictionary metadata and data
        '''
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
        '''
        Used in generate_template_data to provide information about chart configurations (data stored in CPS or CKAN)
        :param country_code:
        :param custom_dict:
        :param top_line_items_count:
        :param errors:
        :return: list of charts
        '''
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

    def _get_maps_config(self, custom_dict):
        '''
        Retrieve the map field from custom_dict
        :param custom_dict: dictionary containing a map field
        :return: map field from custom dict
        '''
        return custom_dict.get('map', {})

    def _show_map(self, map_dict, errors):
        '''
        Validates if map's fields contains data (configs)
        :param map_dict:
        :param errors:
        :return: true if fields are not empty
        '''
        return helpers.check_all_str_fields_not_empty(map_dict, 'Map config field "{}" is empty', errors=errors)

    def _show_chart(self, chart_dict, errors):
        '''
        Validates if chart's fields contains data (configs)
        :param chart_dict:
        :param errors:
        :return: true if fields are not empty
        '''
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
        '''
        Creates the sections based on number of topline items and charts. Basically for 4 topline items there is
        displayed a chart.
        :param top_line_items:
        :param charts_config_data:
        :return: sections ready to be displayed
        '''
        sections = []
        len_charts = len(charts_config_data)
        len_toplines = len(top_line_items)
        max = len_charts if len_charts > int(math.ceil(len_toplines / 4.0)) else int(math.ceil(len_toplines / 4.0))

        for i in range(0, max):
            section = {
                'top_line_items': top_line_items[i * 4:(i + 1) * 4],
                'chart': charts_config_data[i] if i < len_charts else None
            }
            sections.append(section)
        return sections

    def is_crisis(self, label):
        '''
        check if label (group name) is one of our crises
        :param label:
        :return:
        '''
        return True if label in crisis_config.CRISES else False

    def _generate_dataset_results(self, context, search_params,
                                  action_alias='show_crisis', other_params_dict={}):
        '''
        Perform a search of datasets. Moved from crisis_controller.py
        :param context:
        :param search_params:
        :param action_alias:
        :param other_params_dict:
        :return:
        '''
        limit = 25

        sort_option = request.params.get('sort', None)

        page = int(request.params.get('page', 1))
        data_dict = {'sort': sort_option if sort_option else u'metadata_modified desc',
                     'rows': limit,
                     'start': (page - 1) * limit,
                     'ext_indicator': u'0'
                     }

        search_param_list = [
            key + ":" + value for key, value in search_params.iteritems() if key != 'q']
        if 'q' in search_params:
            data_dict['q'] = search_params['q']
            c.q = search_params['q']
        if search_param_list != None:
            data_dict['fq'] = " ".join(
                search_param_list) + ' +dataset_type:dataset'

        query = get_action("package_search")(context, data_dict)

        def pager_url(q=None, page=None):
            if sort_option:
                url = h.url_for(
                    action_alias, page=page, sort=sort_option, **other_params_dict) + '#datasets-section'
            else:
                url = h.url_for(action_alias, page=page, **other_params_dict) + '#datasets-section'
            return url

        get_action('populate_related_items_count')(context, {'pkg_dict_list': query['results']})

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )
        c.items = query['results']
        c.item_count = query['count']

    def _generate_other_links(self, search_params):
        '''
        Show all search results based on sort options and search params. Moved from crisis_controller.py
        :param search_params: some extra search parameters
        :return:
        '''
        c.other_links = {}
        sort_option = request.params.get('sort', None)

        show_more_params = {'sort': sort_option if sort_option else u'metadata_modified desc',
                            'ext_indicator': '0'}
        show_more_params.update(search_params)
        c.other_links['show_more'] = h.url_for(
            "search", **show_more_params)
