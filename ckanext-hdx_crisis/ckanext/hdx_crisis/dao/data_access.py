'''
Created on Nov 18, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic

get_action = logic.get_action

log = logging.getLogger(__name__)

# ebola_sample_resources_dict = {
#     'top-line-numbers': {
#         'dataset': 'ds_name',
#         'resource': 'resource_name'
#     },
#     'Cumulative Cases of Ebola': {
#         'dataset': 'ds_name',
#         'resource': 'resource_name',
#         'sql': "SQL QUERY"
#     }
#
# }


class CrisisDataAccess():

    UNIQUE_ID_COL = 'code'
    SPARKLINES_FIELD = 'sparklines'
    SORT_FIELD = '_id'

    def __init__(self, resources_dict):
        self.resources_dict = resources_dict

    def get_top_line_items(self):
        return self.results

    def _find_datastore_resource_id(self, context, dataset_id, resource_id):
        try:
            modified_context = dict(context)
            modified_context['ignore_auth'] = True
            dataset = get_action('package_show')(
                modified_context,
                {'id': dataset_id})

            if 'resources' in dataset:
                for r in dataset['resources']:
                    if r['name'] == resource_id:
                        return r['id']
            return None
        except:
            log.warning(
                'No dataset with id ' +
                dataset_id)
            return None

        return None

    def _fetch_items_from_datastore(self, context, datastore_resource_id,
                                    ignore_auth=False, sql=None, sort=None):
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
        else:
            log.error(
                'Resource id is None ')
        return []

    def _post_process(self):
        pass

    def fetch_data(self, context):
        top_line_info = self.resources_dict['top-line-numbers']
        datastore_resource_id = top_line_info['resource']
        
        #datastore_resource_id = self._find_datastore_resource_id(
        #    context, top_line_info['dataset'], top_line_info['resource'])
        self.results = self._fetch_items_from_datastore(
            context, datastore_resource_id, True,
            top_line_info.get('sql', None), CrisisDataAccess.SORT_FIELD)
        self.results_dict = {
            item[CrisisDataAccess.UNIQUE_ID_COL]: item for item in self.results
            if CrisisDataAccess.UNIQUE_ID_COL in item}

        for it in self.results:
            if 'source_link' in it and it['source_link']:
                it['source_link'] = it['source_link'].strip()

        for code, res_dict in self.resources_dict.iteritems():
            if code != 'top-line-numbers':
                log.info("Fetching data for dataset:{} and resource: {} ".format(
                    res_dict['dataset'], res_dict['resource']))
                res_id = self._find_datastore_resource_id(
                    context, res_dict['dataset'], res_dict['resource'])
                if not res_id:
                    log.error(
                        'Problem with resource (maybe it does not exist): ' +
                        res_dict['dataset'] + " and " + res_dict['resource'])
                sparkline_items = self._fetch_items_from_datastore(
                    context, res_id, True, res_dict.get('sql', None))
                if code in self.results_dict:
                    self.results_dict[code][
                        CrisisDataAccess.SPARKLINES_FIELD] = sparkline_items
                else:
                    log.error(
                        "{} is not in the results dict".format(code))

        self._post_process()


class EbolaCrisisDataAccess(CrisisDataAccess):

    CUMULATIVE_CASES = 'tot_case_evd'
    CUMULATIVE_DEATHS = 'tot_death_evd'
    APPEAL_COVERAGE = 'plan_coverage'

    def __init__(self):
        self.resources_dict = {
            'top-line-numbers': {
                'dataset': 'topline-ebola-outbreak-figures',
                'resource': 'topline-ebola-outbreak-figures.csv'
            },
            EbolaCrisisDataAccess.CUMULATIVE_CASES: {
                'dataset': 'ebola-cases-2014',
                'resource': 'ebola-data-db-format.csv',
            },
            EbolaCrisisDataAccess.APPEAL_COVERAGE: {
                'dataset': 'fts-ebola-coverage',
                'resource': 'fts-ebola-coverage.csv',
                'sql': 'SELECT "Date", "Value" FROM "93b92803-f9fa-45f4-bf72-73a8ab1d8922" ORDER BY "Date" desc;'
            }
        }
        self.resources_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES]['sql'] = ('SELECT "Indicator", "Date", sum(value) AS value '
                                                                              'FROM "f48a3cf9-110e-4892-bedf-d4c1d725a7d1" '
                                                                              'WHERE "Indicator" IN (\'Cumulative number of confirmed, probable and suspected Ebola deaths\','
                                                                              '\'Cumulative number of confirmed, probable and suspected Ebola cases\') '
                                                                              'GROUP BY "Indicator", "Date" '
                                                                              'ORDER BY "Indicator", "Date" desc ')

    def _process_appeal_coverage(self):
        if CrisisDataAccess.SPARKLINES_FIELD in self.results_dict.get(EbolaCrisisDataAccess.APPEAL_COVERAGE, {}):
            sparklines = self.results_dict[
                EbolaCrisisDataAccess.APPEAL_COVERAGE][CrisisDataAccess.SPARKLINES_FIELD]

            coverage_sparklines = [
                {'date': item['Date'], 'value': item['Value']} for item in sparklines]

            if coverage_sparklines:
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    CrisisDataAccess.SPARKLINES_FIELD] = coverage_sparklines

                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    'value'] = coverage_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    'latest_date'] = coverage_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    CrisisDataAccess.SPARKLINES_FIELD] = []
        else:
            log.error('Could not find {} field in results for {}'.format(
                CrisisDataAccess.SPARKLINES_FIELD, EbolaCrisisDataAccess.APPEAL_COVERAGE))

    def _process_cases_and_deaths(self):
        if CrisisDataAccess.SPARKLINES_FIELD in self.results_dict.get(
                EbolaCrisisDataAccess.CUMULATIVE_CASES, {}):
            sparklines = self.results_dict[
                EbolaCrisisDataAccess.CUMULATIVE_CASES][CrisisDataAccess.SPARKLINES_FIELD]

            cases_sparklines = [
                {'date': item['Date'], 'value': item['value']} for item in sparklines if item['Indicator'] == 'Cumulative number of confirmed, probable and suspected Ebola cases']
            deaths_sparklines = [
                {'date': item['Date'], 'value': item['value']} for item in sparklines if item['Indicator'] == 'Cumulative number of confirmed, probable and suspected Ebola deaths']

            if cases_sparklines:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    CrisisDataAccess.SPARKLINES_FIELD] = cases_sparklines

                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    'value'] = cases_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    'latest_date'] = cases_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    CrisisDataAccess.SPARKLINES_FIELD] = []
                log.warn('There is no data in the cases_sparklines')

            if deaths_sparklines:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    CrisisDataAccess.SPARKLINES_FIELD] = deaths_sparklines

                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    'value'] = deaths_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    'latest_date'] = deaths_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    CrisisDataAccess.SPARKLINES_FIELD] = []
                log.warn('There is no data in the deaths_sparklines')
        else:
            log.error('Could not find {} field in results for {}'.format(
                CrisisDataAccess.SPARKLINES_FIELD, EbolaCrisisDataAccess.CUMULATIVE_CASES))

    def _post_process(self):
        self._process_appeal_coverage()
        self._process_cases_and_deaths()
