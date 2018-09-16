import yaml
import requests
import ckan.logic as logic

from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator, FRESHNESS_PROPERTY


class DataCompletness(object):

    def __init__(self, location_code):
        self.location_code = location_code
        self.config = {}
        self.all_orgs = logic.get_action('cached_organization_list')({}, {})
        self.__org_name_to_title_cache = {}

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
        all_dataset_map = {}
        for category in self.config.get('categories', []):
            category_dataset_map = {}
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
                        'fl': ['id', 'name', 'title', 'organization',
                               'metadata_modified', 'extras_data_update_frequency'],
                        'fq': query_string
                    })
                    ds['datasets'] = search_result.get('results', [])
                    for dataset in ds['datasets']:
                        FreshnessCalculator(dataset).populate_with_freshness()
                        self.__replace_org_name_with_title(dataset)
                        self.__add_dataset_to_map(category_dataset_map, dataset)
                        self.__add_dataset_to_map(all_dataset_map, dataset)


                    self.__calculate_stats_for_dataseries(ds)
            self.__calculate_stats_for_category(category, category_dataset_map)
        self.__calculate_stats_general(self.config, all_dataset_map, self.__org_name_to_title_cache)

    def __build_query(self, include_rule, exclude_rule):
        query_string = ''
        if include_rule:
            query_string += self.__add_paranthesis_if_missing(include_rule)
            if exclude_rule:  # you can't just have exclude rules
                query_string += ' AND -{}'.format(self.__add_paranthesis_if_missing(exclude_rule))

        return query_string

    def __add_paranthesis_if_missing(self, rule):
        return '({})'.format(rule) if not rule.startswith('(') else rule

    def __replace_org_name_with_title(self, dataset):
        org_name = dataset.get('organization')
        title = self.__org_name_to_title_cache.get(org_name)
        if not title:
            for org in self.all_orgs:
                if org.get('name') == org_name:
                    title = org.get('title')
                    self.__org_name_to_title_cache[org_name] = title
                    break
        dataset['organization_title'] = title


    @staticmethod
    def __add_dataset_to_map(map, dataset):
        name = dataset.get('name')
        if name not in map:
            map[name] = dataset

    @staticmethod
    def __calculate_stats_for_dataseries(ds):
        datasets = ds.get('datasets', [])
        total_datasets_num = len(datasets)
        fresh_datasets_num = reduce(lambda acc, item: acc + (1 if item.get(FRESHNESS_PROPERTY) else 0),
                                    datasets, 0)
        ds['stats'] = {
            'total_datasets_num': total_datasets_num,
            'fresh_datasets_num': fresh_datasets_num,
            'state': 'empty' if total_datasets_num == 0
                                else 'not_fresh' if fresh_datasets_num < total_datasets_num else 'fresh'
        }

    @staticmethod
    def __calculate_stats_for_category(category, category_dataset_map):
        total_datasets_num = len(category_dataset_map)
        fresh_datasets_num = reduce(lambda acc, item: acc + (1 if item.get(FRESHNESS_PROPERTY) else 0),
                                    category_dataset_map.values(), 0)

        freshness_percentage = 0 if total_datasets_num == 0 else float(fresh_datasets_num) / total_datasets_num

        dataseries = category.get('data_series', [])
        total_dataseries_num  = len(dataseries)
        fresh_dataseries_num = 0
        not_fresh_dataseries_num = 0
        empty_dataseries_num = 0

        for ds in dataseries:
            state = ds.get('stats', {}).get('state')
            if state == 'empty':
                empty_dataseries_num += 1
            elif state == 'not_fresh':
                not_fresh_dataseries_num += 1
            elif state == 'fresh':
                fresh_dataseries_num += 1



        category['stats'] = {
            'total_datasets_num': total_datasets_num,
            'fresh_datasets_num': fresh_datasets_num,
            'dataset_freshness_percentage': freshness_percentage,
            'total_dataseries_num': total_dataseries_num,
            'fresh_dataseries_num': fresh_dataseries_num,
            'not_fresh_dataseries_num': not_fresh_dataseries_num,
            'empty_dataseries_num': empty_dataseries_num,
            'state': 'empty' if total_datasets_num == 0
                                else 'not-fresh' if fresh_datasets_num < total_datasets_num else 'fresh'
        }

    @staticmethod
    def __calculate_stats_general(config, all_dataset_map, org_map):
        categories = config.get('categories', [])
        total_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('total_dataseries_num', 0), categories, 0)
        fresh_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('fresh_dataseries_num', 0), categories, 0)
        not_fresh_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('not_fresh_dataseries_num', 0), categories, 0)
        empty_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('empty_dataseries_num', 0), categories, 0)

        dataseries_freshness_percentage = 0 if total_dataseries_num == 0 else \
            float(fresh_dataseries_num) / total_dataseries_num

        dataseries_not_freshness_percentage = 0 if total_dataseries_num == 0 else \
            float(not_fresh_dataseries_num) / total_dataseries_num

        dataseries_empty_percentage = 0 if total_dataseries_num == 0 else \
            float(empty_dataseries_num) / total_dataseries_num

        config['stats'] = {
            'total_datasets_num': len(all_dataset_map),
            'org_num': len(org_map),
            'total_dataseries_num': total_dataseries_num,
            'fresh_dataseries_num': fresh_dataseries_num,
            'not_fresh_dataseries_num': not_fresh_dataseries_num,
            'empty_dataseries_num': empty_dataseries_num,
            'dataseries_freshness_percentage': dataseries_freshness_percentage,
            'dataseries_not_freshness_percentage': dataseries_not_freshness_percentage,
            'dataseries_empty_percentage': dataseries_empty_percentage,

        }


