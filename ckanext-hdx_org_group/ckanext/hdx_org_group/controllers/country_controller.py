'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''
import json

import logging
import datetime as dt

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.controllers.group as group

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)

group_type = 'group'

indicators_4_charts = ['PVH140', 'PVN010', 'PVW010', 'PVF020',
                       'PSE160', 'PCX051', 'PVE130', 'PCX060',
                       'RW002', 'PVE110', 'PVN050', 'PVN070',
                       'PVW040']
# http://localhost:8080/public/api2/values?it=PSP120&it=PSP090&l=CHN&sorting=INDICATOR_TYPE_ASC

indicators_4_top_line = ['PSP120', 'PSP090', 'PSE220', 'PSE030',
                         'CG300']
# http://localhost:8080/public/api2/values?it=PSP120&l=CHN&periodType=LATEST_YEAR


class CountryController(group.GroupController):

    def read(self, id):
        self.get_country(id)
        self.get_dataset_results(c.group_dict.get('name', id))

        # activity stream
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'for_view': True}
        country_uuid = c.group_dict.get('id', id)
        self.get_activity_stream(context, country_uuid)

        return render('country/country.html')

    def get_country(self, id):
        if group_type != self.group_type:
            abort(404, _('Incorrect group type'))

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True}
        data_dict = {'id': id}

        try:
            context['include_datasets'] = False
            c.group_dict = self._action('group_show')(context, data_dict)
            c.group = context['group']
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)


    def get_dataset_results(self, country_id):
        upper_case_id = country_id.upper()
        top_line_results = self._get_top_line_num(upper_case_id)
        top_line_data = top_line_results.get('results', [])

        if not top_line_data:
            log.warn(
                'No top line numbers found for country: {}'.format(country_id))
        # [ {el['indicatorTypeCode']:el} for el in top_line_data ]
        top_line_data_dict = top_line_data
        c.top_line_data_dict = top_line_data_dict

        chart_results = self._get_chart_data(upper_case_id)
        chart_data = chart_results.get('results', [])
        if not chart_data:
            log.warn('No chart data found for country: {}'.format(country_id))
        chart_data_dict = {}

        # for el in chart_data:
        #     ind_type = el.get('indicatorTypeCode', None)
        #     if ind_type:
        #         d = dt.datetime.strptime(el.get('time', ''), '%Y-%m-%d')
        #         el['datetime'] = d
        #         if ind_type in chart_data_dict:
        #             chart_data_dict[ind_type].append(el)
        #         else:
        #             chart_data_dict[ind_type] = [el]

        for el in chart_data:
            ind_type = el.get('indicatorTypeCode', None)
            if ind_type:
                # d = dt.datetime.strptime(el.get('time', ''), '%Y-%m-%d')
                val = {
                    'date': el.get('time'),
                    'value': el.get('value')
                }

                if ind_type in chart_data_dict:
                    chart_data_dict[ind_type]['data'].append(val);
                else:
                    newel = {
                        'title': el.get('unitName'),
                        'data': [val]
                    }
                    chart_data_dict[ind_type] = newel

        # for code in chart_data_dict.keys():
        #     chart_data_dict[code] = sorted(chart_data_dict[code], key=lambda x: x.get('datetime', None))

        for code in chart_data_dict.keys():
            chart_data_dict[code]['data'] = json.dumps(chart_data_dict[code]['data'])

        c.chart_data_dict = chart_data_dict

    def _get_chart_data(self, country_id):
        data_dict = {
            'sorting': 'INDICATOR_TYPE_ASC',
            'l': country_id,
            'it': indicators_4_charts
        }
        result = get_action('hdx_get_indicator_values')({}, data_dict)
        return result

    def _get_top_line_num(self, country_id):
        data_dict = {
            'periodType': 'LATEST_YEAR',
            'l': country_id,
            'it': indicators_4_top_line
        }
        result = get_action('hdx_get_indicator_values')({}, data_dict)
        return result

    def get_activity_stream(self, context, country_id):
        act_data_dict = {'id': country_id, 'limit': 7}
        c.hdx_group_activities = get_action(
            'hdx_get_group_activity_list')(context, act_data_dict)
