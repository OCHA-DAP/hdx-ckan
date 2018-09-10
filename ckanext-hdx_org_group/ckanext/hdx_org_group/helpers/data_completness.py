import yaml
import requests
import ckan.logic as logic

from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator


class DataCompletness(object):

    def __init__(self, location_code):
        self.location_code = location_code
        self.config = {}

    def get_config(self):
        url = 'https://raw.githubusercontent.com/OCHA-DAP/data-grid-recipes/master/data%20grid%20recipe%20-%20default.yml'
        response = requests.get(url)
        yaml_text = response.text
        self.config = yaml.load(yaml_text)

        context = {}
        # datasets = logic.get_action('package_search')(context, {
        #     'fq': '(res_format:"DOCX") AND -(groups:"ken")'
        # })
        self.__populate_dataseries()
        return self.config

    def __populate_dataseries(self):
        for category in self.config.get('categories', []):
            for ds in category.get('data_series', []):
                include_rule = ds.get('rules', {}).get('include') or ''
                exclude_rule = ds.get('rules', {}).get('exclude') or ''
                if isinstance(include_rule, list):
                    include_rule = include_rule[0]
                if isinstance(exclude_rule, list):
                    exclude_rule = exclude_rule[0]

                query_string = self.__build_query(include_rule.strip(), exclude_rule.strip())
                if query_string:
                    search_result = logic.get_action('package_search')({}, {
                        'start': 0,
                        'rows': 500,
                        'fl': ['id','name','title','metadata_modified','extras_data_update_frequency'],
                        'fq': query_string
                    })
                    ds['datasets'] = search_result.get('results', [])
                    for dataset in ds['datasets']:
                        FreshnessCalculator(dataset).populate_with_freshness()
                    pass

    def __build_query(self, include_rule, exclude_rule):
        query_string = ''
        if include_rule:
            query_string += self.__add_paranthesis_if_missing(include_rule)
            if exclude_rule: # you can't just have exclude rules
                query_string += ' AND -{}'.format(self.__add_paranthesis_if_missing(exclude_rule))

        return query_string

    def __add_paranthesis_if_missing(self, rule):
        return '({})'.format(rule) if not rule.startswith('(') else rule

