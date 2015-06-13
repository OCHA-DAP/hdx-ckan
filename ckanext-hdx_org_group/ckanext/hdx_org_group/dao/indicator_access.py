'''
Created on April 20, 2015

@author: alexandru-m-g
'''


import logging
import datetime as dt

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.search as search
import ckan.common as common
import ckan.lib.helpers as h


abort = base.abort
get_action = logic.get_action
_ = common._

class IndicatorAccess(object):

    def __init__(self, country_code, dataseries_list, additional_cps_params_dict={}):
        self.__cps_params_dict = {
            'l': country_code.upper(),
            'ds': [el[0] + '___' + el[1] for el in dataseries_list]
        }
        self.__cps_params_dict.update(additional_cps_params_dict)

        self.__dataseries_list = dataseries_list

    def fetch_indicator_data_from_cps(self):
        try:
            self.__cps_data = get_action('hdx_get_indicator_values')({}, self.__cps_params_dict)
        except:
            return {}
        return self.__cps_data

    def get_structured_data_from_cps(self):
        '''

        :return: A dict structure as in the sample below
            {
                INDICATOR_CODE: {
                    SOURCE_CODE: {
                        'title': INDICATOR_TYPE_NAME,
                        'sourceName': SOURCE_NAME,
                        'sourceCode': SOURCE_CODE,
                        'lastDate': LAST_DATE,
                        'lastValue': LAST_VALUE,
                        'unit': UNIT_NAME,
                        'code': INDICATOR_TYPE_CODE,
                        'data': [{'date': DATE, 'value': VALUE},..]
                    }
                }
            }
        '''
        structured_cps_data = {}
        for el in self.__cps_data.get('results', []):
            ind_type = el.get('indicatorTypeCode', None)
            src = el.get('sourceCode', None)
            if ind_type and src:
                # d = dt.datetime.strptime(el.get('time', ''), '%Y-%m-%d')
                el_time = el.get('time')
                el_value = el.get('value')
                val = {
                    'date': el_time,
                    'value': el_value
                }

                if ind_type in structured_cps_data and src in structured_cps_data[ind_type]:
                    data_dict = structured_cps_data[ind_type][src]
                    data_dict['data'].append(val)

                    last_date = dt.datetime.strptime(
                        data_dict['lastDate'], '%Y-%m-%d')
                    curr_date = dt.datetime.strptime(el_time, '%Y-%m-%d')

                    if last_date < curr_date:
                        data_dict['lastDate'] = el_time
                        data_dict['lastValue'] = el_value

                else:
                    if ind_type not in structured_cps_data:
                        structured_cps_data[ind_type] = {}
                    newel = {
                        'title': el.get('indicatorTypeName'),
                        'sourceName': el.get('sourceName'),
                        'sourceCode': src,
                        'lastDate': el_time,
                        'lastValue': el_value,
                        'unit': el.get('unitName'),
                        'code': ind_type,
                        'data': [val]
                    }
                    structured_cps_data[ind_type][src] = newel

        return structured_cps_data

    def fetch_indicator_data_from_ckan(self):
        indic_code_list = [el[0] for el in self.__dataseries_list]
        self.__ckan_data = {}
        fq = '+extras_indicator_type_code:('
        fq += ' OR '.join(['"{}"'.format(code) for code in indic_code_list])
        fq += ')'
        data_dict = {
            'rows': 25,
            'start': 0,
            'ext_indicator': u'1',
            'fq': fq + ' +dataset_type:dataset'
        }
        try:
            query = get_action("package_search")({}, data_dict)
        except search.SearchError as se:
            query = {}
        except Exception as e:
            abort(404, _('Query produced some error'))
        if 'results' in query:
            for dataset in query['results']:
                date_parts = dataset.get('metadata_modified', '').split('T')
                if date_parts:
                    self.__ckan_data[dataset['indicator_type_code']] = {
                        'datasetUpdateDate': dt.datetime.strptime(date_parts[0], '%Y-%m-%d').strftime('%b %d, %Y'),
                        'datasetLink': h.url_for(controller='package', action='read', id=dataset['name'])
                    }
        return self.__ckan_data