import yaml
import requests
import ckan.logic as logic

from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator, FRESHNESS_PROPERTY


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
                        'fl': ['id', 'name', 'title', 'metadata_modified', 'extras_data_update_frequency'],
                        'fq': query_string
                    })
                    ds['datasets'] = search_result.get('results', [])
                    for dataset in ds['datasets']:
                        FreshnessCalculator(dataset).populate_with_freshness()

                    self.__calculate_stats(ds, 'datasets', False)
            self.__calculate_stats(category, 'data_series', True)

    def __build_query(self, include_rule, exclude_rule):
        query_string = ''
        if include_rule:
            query_string += self.__add_paranthesis_if_missing(include_rule)
            if exclude_rule:  # you can't just have exclude rules
                query_string += ' AND -{}'.format(self.__add_paranthesis_if_missing(exclude_rule))

        return query_string

    def __add_paranthesis_if_missing(self, rule):
        return '({})'.format(rule) if not rule.startswith('(') else rule

    @staticmethod
    def __calculate_stats(entity, list_property, do_sum_of_children):
        '''
        Populates a property 'stats' inside entity
        :param entity: a dict whose stats we should compute
        :type entity: dict
        :param list_property: the name of the property that contains the children
        :type list_property: str
        :param do_sum_of_children: False on first level (just count children), True otherwise (to sum up)
        :type do_sum_of_children: bool
        '''

        children = entity.get(list_property, [])
        is_fresh = True
        total_num = 0

        for child in children:
            freshness = child.get(FRESHNESS_PROPERTY)
            if not freshness:
                is_fresh = False
                break

        if do_sum_of_children:
            for child in children:
                total_num += child['stats']['datasets_num']

        entity['stats'] = {
            'datasets_num': total_num if do_sum_of_children else len(children),
            FRESHNESS_PROPERTY: is_fresh
        }
