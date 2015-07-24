'''
Created on Nov 18, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic
import ckanext.hdx_crisis.dao.data_access as data_access

DataAccess = data_access.DataAccess
get_action = logic.get_action
log = logging.getLogger(__name__)


class EbolaCrisisDataAccess(DataAccess):
    CUMULATIVE_CASES = 'tot_case_evd'
    CUMULATIVE_DEATHS = 'tot_death_evd'
    APPEAL_COVERAGE = 'plan_coverage'

    def __init__(self, top_line_res_id, cases_res_id, appeal_res_id):
        self.resources_dict = {
            'top-line-numbers': {
                'resource_id': top_line_res_id
            },
            EbolaCrisisDataAccess.CUMULATIVE_CASES: {
                'resource_id': cases_res_id
            },
            EbolaCrisisDataAccess.APPEAL_COVERAGE: {
                'resource_id': appeal_res_id,
                'sql': 'SELECT "Date", "Value" FROM "{}" ORDER BY "Date" desc;'.format(appeal_res_id)
            }
        }
        sql = ('SELECT "Indicator", "Date", sum(value) AS value '
               'FROM "{}" '
               'WHERE "Indicator" IN (\'Cumulative number of confirmed, probable and suspected Ebola deaths\','
               '\'Cumulative number of confirmed, probable and suspected Ebola cases\') '
               'GROUP BY "Indicator", "Date" '
               'ORDER BY "Indicator", "Date" desc ')
        self.resources_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES]['sql'] = sql.format(cases_res_id)

    def _process_appeal_coverage(self):
        if DataAccess.SPARKLINES_FIELD in self.results_dict.get(EbolaCrisisDataAccess.APPEAL_COVERAGE, {}):
            sparklines = self.results_dict[
                EbolaCrisisDataAccess.APPEAL_COVERAGE][DataAccess.SPARKLINES_FIELD]

            coverage_sparklines = [
                {'date': item['Date'], 'value': item['Value']} for item in sparklines]

            if coverage_sparklines:
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    DataAccess.SPARKLINES_FIELD] = coverage_sparklines

                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    'value'] = coverage_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    'latest_date'] = coverage_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.APPEAL_COVERAGE][
                    DataAccess.SPARKLINES_FIELD] = []
        else:
            log.error('Could not find {} field in results for {}'.format(
                DataAccess.SPARKLINES_FIELD, EbolaCrisisDataAccess.APPEAL_COVERAGE))

    def _process_cases_and_deaths(self):
        if DataAccess.SPARKLINES_FIELD in self.results_dict.get(
                EbolaCrisisDataAccess.CUMULATIVE_CASES, {}):
            sparklines = self.results_dict[
                EbolaCrisisDataAccess.CUMULATIVE_CASES][DataAccess.SPARKLINES_FIELD]

            cases_sparklines = [
                {'date': item['Date'], 'value': item['value']} for item in sparklines if
                item['Indicator'] == 'Cumulative number of confirmed, probable and suspected Ebola cases']
            deaths_sparklines = [
                {'date': item['Date'], 'value': item['value']} for item in sparklines if
                item['Indicator'] == 'Cumulative number of confirmed, probable and suspected Ebola deaths']

            if cases_sparklines:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    DataAccess.SPARKLINES_FIELD] = cases_sparklines

                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    'value'] = cases_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    'latest_date'] = cases_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_CASES][
                    DataAccess.SPARKLINES_FIELD] = []
                log.warn('There is no data in the cases_sparklines')

            if deaths_sparklines:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    DataAccess.SPARKLINES_FIELD] = deaths_sparklines

                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    'value'] = deaths_sparklines[0]['value']
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    'latest_date'] = deaths_sparklines[0]['date']
            else:
                self.results_dict[EbolaCrisisDataAccess.CUMULATIVE_DEATHS][
                    DataAccess.SPARKLINES_FIELD] = []
                log.warn('There is no data in the deaths_sparklines')
        else:
            log.error('Could not find {} field in results for {}'.format(
                DataAccess.SPARKLINES_FIELD, EbolaCrisisDataAccess.CUMULATIVE_CASES))

    def _post_process(self):
        self._process_appeal_coverage()
        self._process_cases_and_deaths()
