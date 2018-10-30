import yaml
import requests
import ckan.logic as logic

from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator, FRESHNESS_PROPERTY


class DataCompletness(object):

    basic_query_params = {
        'start': 0,
        'rows': 500,
        'fl': ['id', 'name', 'title', 'organization',
               'metadata_modified', 'extras_data_update_frequency']
    }

    def __init__(self, location_code, config_url):
        self.location_code = location_code
        self.config_url = config_url
        self.config = {}
        self.all_orgs = logic.get_action('cached_organization_list')({}, {})
        self.__org_name_to_info_cache = {}

    def get_config(self):
        response = requests.get(self.config_url)
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
                overrides_map = self.__get_map_of_overrides_from_dataseries(ds)
                include_rules = ds.get('rules', {}).get('include') or ''
                exclude_rules = ds.get('rules', {}).get('exclude') or ''
                if isinstance(include_rules, basestring):
                    include_rules = [include_rules]
                if isinstance(exclude_rules, basestring):
                    exclude_rules = [exclude_rules]

                query_string = self.__build_query(include_rules, exclude_rules)
                if query_string:
                    query_params = {'fq': query_string}
                    query_params.update(self.basic_query_params)
                    search_result = logic.get_action('package_search')({},query_params)
                    ds['datasets'] = search_result.get('results', [])
                    for dataset in ds['datasets']:
                        FreshnessCalculator(dataset).populate_with_freshness()
                        self.__replace_org_name_with_title(dataset)
                        self.__add_metadata_overrides(dataset, overrides_map)
                        self.__add_dataset_to_map(category_dataset_map, dataset)
                        self.__add_dataset_to_map(all_dataset_map, dataset)


                    self.__calculate_stats_for_dataseries(ds)
            self.__calculate_stats_for_category(category, category_dataset_map)
        self.__calculate_stats_general(self.config, all_dataset_map, self.__org_name_to_info_cache)
        pass

    def __build_query(self, include_rules, exclude_rules):
        query_string = ''
        if include_rules:
            include_query = self.__generate_query_from_rules(include_rules)
            query_string += include_query
            query_string += ' AND (groups:{})'.format(self.location_code)
            if exclude_rules:  # you can't just have exclude rules without any include rules
                exclude_query = self.__generate_query_from_rules(exclude_rules)
                if exclude_query:
                    query_string += ' AND -{}'.format(exclude_query)

        return query_string

    def __generate_query_from_rules(self, include_rules):
        query = ''
        processed_include_rules = [self.__add_paranthesis_if_missing(r) for r in include_rules if r and r.strip()]
        if processed_include_rules:
            query = '(' + ' OR '.join(processed_include_rules) + ')'
        return query

    def __add_paranthesis_if_missing(self, rule):
        return '({})'.format(rule) if not rule.startswith('(') else rule

    def __replace_org_name_with_title(self, dataset):
        org_name = dataset.get('organization')
        org_info = self.__org_name_to_info_cache.get(org_name)
        if not org_info:
            for org in self.all_orgs:
                if org.get('name') == org_name:
                    org_info = {
                        'title': org.get('title'),
                        'org_acronym': org.get('org_acronym', org_name)
                    }
                    self.__org_name_to_info_cache[org_name] = org_info
                    break
        dataset['organization_title'] = org_info.get('title')
        dataset['organization_acronym'] = org_info.get('org_acronym')

    @staticmethod
    def __add_metadata_overrides(dataset, overrides_map):
        override = overrides_map.get(dataset['name'])

        if override:
            dataset['completeness'] = override.get('display_state') == 'complete'
            dataset['completeness_comment'] = override.get('comments')

    @staticmethod
    def __add_dataset_to_map(map, dataset):
        name = dataset.get('name')
        if name not in map:
            map[name] = dataset

    @staticmethod
    def __get_map_of_overrides_from_dataseries(ds):
        map = {}
        overrides = ds.get('metadata_overrides', [])
        for override in overrides:
            map[override.get('dataset_name')] = override
        return map

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

        dataset_freshness_percentage = 0 if total_datasets_num == 0 else float(fresh_datasets_num) / total_datasets_num

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

        dataseries_fresh_percentage = 0 if total_dataseries_num == 0 else \
                        float(fresh_dataseries_num) / total_dataseries_num
        dataseries_not_fresh_percentage = 0 if total_dataseries_num == 0 else \
            float(not_fresh_dataseries_num) / total_dataseries_num
        dataseries_empty_percentage = 0 if total_dataseries_num == 0 else \
            float(empty_dataseries_num) / total_dataseries_num

        category['stats'] = {
            'total_datasets_num': total_datasets_num,
            'fresh_datasets_num': fresh_datasets_num,
            'dataset_freshness_percentage': dataset_freshness_percentage,
            'total_dataseries_num': total_dataseries_num,
            'fresh_dataseries_num': fresh_dataseries_num,
            'not_fresh_dataseries_num': not_fresh_dataseries_num,
            'empty_dataseries_num': empty_dataseries_num,
            'dataseries_fresh_percentage': dataseries_fresh_percentage,
            'dataseries_not_fresh_percentage': dataseries_not_fresh_percentage,
            'dataseries_empty_percentage': dataseries_empty_percentage,
            'state': 'empty' if total_dataseries_num == 0 or empty_dataseries_num > 0
                                else 'not_fresh' if fresh_dataseries_num < total_dataseries_num else 'fresh',
        }

        state = category['stats']['state']
        category['stats']['state_flag'] = 'blue' if state == 'fresh' else 'red' if state == 'empty' else ''

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

        dataseries_fresh_percentage = 0 if total_dataseries_num == 0 else \
            float(fresh_dataseries_num) / total_dataseries_num

        dataseries_not_fresh_percentage = 0 if total_dataseries_num == 0 else \
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
            'dataseries_fresh_percentage': dataseries_fresh_percentage,
            'dataseries_not_fresh_percentage': dataseries_not_fresh_percentage,
            'dataseries_empty_percentage': dataseries_empty_percentage,
            'state': 'empty' if total_dataseries_num == 0 or empty_dataseries_num > 0
                                else 'not_fresh' if fresh_dataseries_num < total_dataseries_num else 'fresh'

        }

        state = config['stats']['state']
        config['stats']['state_flag'] = 'blue' if state == 'fresh' else 'red' if state == 'empty' else ''


