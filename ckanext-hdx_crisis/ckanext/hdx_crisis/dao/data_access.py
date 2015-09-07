'''
Created on Nov 18, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic

get_action = logic.get_action

log = logging.getLogger(__name__)


class DataAccess:
    UNIQUE_ID_COL = 'code'
    SPARKLINES_FIELD = 'sparklines'
    SORT_FIELD = '_id'

    def __init__(self, resources_dict):
        self.resources_dict = resources_dict

    def get_top_line_items(self):
        return self.results

    def _fetch_items_from_datastore(self, context, datastore_resource_id,
                                    ignore_auth=False, sql=None, sort=None):
        '''
        Retrieve and fetch records from datastore
        :param context:
        :param datastore_resource_id:
        :param ignore_auth:
        :param sql:
        :param sort:
        :return: Founded records in database or empty list
        '''
        modified_context = context
        if ignore_auth:
            modified_context = dict(context)
            modified_context['ignore_auth'] = True

        data_dict = {'resource_id': datastore_resource_id}
        if sql:
            data_dict['sql'] = sql
        if sort:
            data_dict['sort'] = sort
        action_name = 'datastore_search_sql' if sql else 'datastore_search'

        if datastore_resource_id:
            try:
                result = get_action(action_name)(
                    modified_context, data_dict)
                if 'records' in result:
                    return result['records']
            except logic.NotFound, e:
                log.error(str(e))
            except logic.ValidationError, e:
                log.error('Validation error: ' + str(e))
        else:
            log.error(
                'Resource id is None ')
        return []

    def _post_process(self):
        pass

    def fetch_data_generic(self, context):
        '''
        fetch_data but not specific to topline numbers
        :param context:
        :return:
        '''
        datastore_config = self.resources_dict['datastore_config']
        datastore_resource_id = datastore_config['resource_id']

        self.results = self._fetch_items_from_datastore(
            context, datastore_resource_id, True,
            datastore_config.get('sql', None), DataAccess.SORT_FIELD)
        self.results_dict = {
            item[DataAccess.UNIQUE_ID_COL]: item for item in self.results
            if DataAccess.UNIQUE_ID_COL in item
            }


    def fetch_data(self, context):
        '''
        Getting data and fetching setting "results" and "results_dict" with data
        :param context:
        :return:
        '''
        top_line_info = self.resources_dict['top-line-numbers']
        datastore_resource_id = top_line_info['resource_id']

        self.results = self._fetch_items_from_datastore(
            context, datastore_resource_id, True,
            top_line_info.get('sql', None), DataAccess.SORT_FIELD)
        self.results_dict = {
            item[DataAccess.UNIQUE_ID_COL]: item for item in self.results
            if DataAccess.UNIQUE_ID_COL in item
            }

        for it in self.results:
            if 'source_link' in it and it['source_link']:
                it['source_link'] = it['source_link'].strip()

        for code, res_dict in self.resources_dict.iteritems():
            if code != 'top-line-numbers':
                log.info("Fetching data for datastore: {} ".format(
                    res_dict['resource_id']))
                res_id = res_dict['resource_id']
                if not res_id:
                    log.error(
                        'A resource id for a datastore was not specified ')
                sparkline_items = self._fetch_items_from_datastore(
                    context, res_id, True, res_dict.get('sql', None))
                if code in self.results_dict:
                    self.results_dict[code][
                        DataAccess.SPARKLINES_FIELD] = sparkline_items
                else:
                    log.error(
                        "{} is not in the results dict".format(code))

        self._post_process()
