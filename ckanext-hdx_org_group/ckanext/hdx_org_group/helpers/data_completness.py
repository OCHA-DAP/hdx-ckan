import logging

import requests
import yaml
from six import string_types
from six.moves import reduce

import ckan.logic as logic
from ckanext.hdx_package.helpers.freshness_calculator import OVERDUE_PROPERTY

log = logging.getLogger(__name__)

GOODNESS_PROPERTY = 'is_good'
FLAG_NOT_APPLICABLE = 'not_applicable'


class DataCompletness(object):

    basic_query_params = {
        'start': 0,
        'rows': 500,
        'fl': ['id', 'name', 'title', 'organization',
               'extras_data_update_frequency',
               'last_modified', 'review_date'],
        'ext_compute_freshness': 'for-data-completeness'
    }

    def __init__(self, location_code, config_url):
        self.location_code = location_code
        self.config_url = config_url
        self.config = {}
        self.all_orgs = logic.get_action('cached_organization_list')({}, {})
        self.__org_name_to_info_cache = {}

    def get_config(self):
        try:
            yaml_dict = self._fetch_yaml()
            self.config = yaml_dict

            context = {}
            # datasets = logic.get_action('package_search')(context, {
            #     'fq': '(res_format:"DOCX") AND -(groups:"ken")'
            # })
            self.__populate_dataseries()
        except Exception as e:
            logging.warn(str(e))
            self.config = None

        return self.config

    def _fetch_yaml(self):
        response = requests.get(self.config_url)
        response.raise_for_status()
        yaml_text = response.text
        return yaml.load(yaml_text)

    def __populate_dataseries(self):
        all_dataset_map = {}
        for category in self.config.get('categories', []):
            category_dataset_map = {}
            for ds in category.get('data_series', []):
                flags_map = self.__get_map_of_flags(ds)
                not_applicable_flag = flags_map.get(FLAG_NOT_APPLICABLE)  # type: dict
                if not not_applicable_flag:
                    overrides_map = self.__get_map_of_overrides_from_dataseries(ds)
                    include_rules = ds.get('rules', {}).get('include') or ''
                    exclude_rules = ds.get('rules', {}).get('exclude') or ''
                    if isinstance(include_rules, string_types):
                        include_rules = [include_rules]
                    if isinstance(exclude_rules, string_types):
                        exclude_rules = [exclude_rules]

                    query_string = self.__build_query(include_rules, exclude_rules)
                    if query_string:
                        query_params = {'fq': query_string}
                        query_params.update(self.basic_query_params)
                        search_result = logic.get_action('package_search')({}, query_params)
                        ds['datasets'] = search_result.get('results', [])
                        for dataset in ds['datasets']:
                            self.__replace_org_name_with_title(dataset)
                            self.__compute_goodness_flag(dataset, overrides_map)
                            self.__add_general_comments(dataset, overrides_map)
                            self.__add_dataset_to_map(category_dataset_map, dataset)
                            self.__add_dataset_to_map(all_dataset_map, dataset)

                self.__calculate_stats_for_dataseries(ds, not_applicable_flag)
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
    def __compute_goodness_flag(dataset, overrides_map):
        '''
        This needs to be called only after freshness is populated on the dataset

        :param dataset:
        :param overrides_map:
        :return:
        '''
        override = overrides_map.get(dataset['name'], overrides_map.get(dataset['id']))

        if override and override.get('display_state'):
            dataset['is_complete'] = override.get('display_state') == 'complete'
            dataset[GOODNESS_PROPERTY] = dataset.get('is_complete')
        else:
            dataset[GOODNESS_PROPERTY] = not dataset.get(OVERDUE_PROPERTY, True)

    @staticmethod
    def __add_general_comments(dataset, overrides_map):
        comments = []
        override = overrides_map.get(dataset['name'], overrides_map.get(dataset['id']))
        if override and override.get('comments'):
            comments.append(override.get('comments'))
        if not dataset.get(GOODNESS_PROPERTY) and dataset.get(OVERDUE_PROPERTY):
            comments.append('The dataset is not up-to-date.')

        dataset['general_comment'] = ' '.join(comments)

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
            key = override.get('dataset_name')
            if key:
                map[key.strip()] = override
        return map

    @staticmethod
    def __get_map_of_flags(ds):
        map = {}
        flags = ds.get('flags', [])
        for flag in flags:
            key = flag.get('key')
            if key:
                map[key.strip()] = flag
        return map

    @staticmethod
    def __calculate_stats_for_dataseries(ds, not_applicable_flag):
        if not_applicable_flag:
            ds['stats'] = {
                'total_datasets_num': 0,
                'good_datasets_num': 0,
                'state': FLAG_NOT_APPLICABLE,
                'state_comment': not_applicable_flag.get('comments') or
                                 'This subcategory is not applicable in this context.'
            }
        else:
            datasets = ds.get('datasets', [])
            total_datasets_num = len(datasets)
            good_datasets_num = reduce(lambda acc, item: acc + (1 if item.get(GOODNESS_PROPERTY) else 0),
                                        datasets, 0)
            ds['stats'] = {
                'total_datasets_num': total_datasets_num,
                'good_datasets_num': good_datasets_num,
                'state': 'empty' if total_datasets_num == 0 else 'good' if good_datasets_num > 0 else 'not_good'
            }

    @staticmethod
    def __calculate_stats_for_category(category, category_dataset_map):
        total_datasets_num = len(category_dataset_map)
        good_datasets_num = reduce(lambda acc, item: acc + (1 if item.get(GOODNESS_PROPERTY) else 0),
                                    category_dataset_map.values(), 0)

        dataset_goodness_percentage = 0 if total_datasets_num == 0 else float(good_datasets_num) / total_datasets_num

        # dataseries = category.get('data_series', [])
        dataseries = [ds for ds in category.get('data_series', [])
                      if ds.get('stats', {}).get('state') != FLAG_NOT_APPLICABLE]
        total_dataseries_num  = len(dataseries)

        good_dataseries = []
        not_good_dataseries = []
        empty_dataseries = []

        for ds in dataseries:
            state = ds.get('stats', {}).get('state')
            if state == 'empty':
                empty_dataseries.append(ds.get('title'))
            elif state == 'not_good':
                not_good_dataseries.append(ds.get('title'))
            elif state == 'good':
                good_dataseries.append(ds.get('title'))

        good_dataseries_num = len(good_dataseries)
        not_good_dataseries_num = len(not_good_dataseries)
        empty_dataseries_num = len(empty_dataseries)

        dataseries_good_percentage = 0 if total_dataseries_num == 0 else \
                        float(good_dataseries_num) / total_dataseries_num
        dataseries_not_good_percentage = 0 if total_dataseries_num == 0 else \
            float(not_good_dataseries_num) / total_dataseries_num
        dataseries_empty_percentage = 0 if total_dataseries_num == 0 else \
            float(empty_dataseries_num) / total_dataseries_num

        category['stats'] = {
            'total_datasets_num': total_datasets_num,
            'good_datasets_num': good_datasets_num,
            'dataset_goodness_percentage': dataset_goodness_percentage,
            'total_dataseries_num': total_dataseries_num,
            'good_dataseries_num': good_dataseries_num,
            'not_good_dataseries_num': not_good_dataseries_num,
            'empty_dataseries_num': empty_dataseries_num,
            'good_dataseries_text': ', '.join(good_dataseries),
            'not_good_dataseries_text': ', '.join(not_good_dataseries),
            'empty_dataseries_text': ', '.join(empty_dataseries),
            'dataseries_good_percentage': dataseries_good_percentage,
            'dataseries_not_good_percentage': dataseries_not_good_percentage,
            'dataseries_empty_percentage': dataseries_empty_percentage,
            # 'state': 'empty' if total_dataseries_num == 0 or empty_dataseries_num > 0
            #                     else 'not_good' if good_dataseries_num < total_dataseries_num else 'good',
        }

        # state = category['stats']['state']
        # category['stats']['state_flag'] = 'blue' if state == 'good' else 'red' if state == 'empty' else ''

    @staticmethod
    def __calculate_stats_general(config, all_dataset_map, org_map):
        categories = config.get('categories', [])
        total_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('total_dataseries_num', 0), categories, 0)
        good_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('good_dataseries_num', 0), categories, 0)
        not_good_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('not_good_dataseries_num', 0), categories, 0)
        empty_dataseries_num = reduce(
            lambda acc, item: acc + item.get('stats', {}).get('empty_dataseries_num', 0), categories, 0)

        dataseries_good_percentage = 0 if total_dataseries_num == 0 else \
            float(good_dataseries_num) / total_dataseries_num

        dataseries_not_good_percentage = 0 if total_dataseries_num == 0 else \
            float(not_good_dataseries_num) / total_dataseries_num

        dataseries_empty_percentage = 0 if total_dataseries_num == 0 else \
            float(empty_dataseries_num) / total_dataseries_num

        config['stats'] = {
            'total_datasets_num': len(all_dataset_map),
            'org_num': len(org_map),
            'total_dataseries_num': total_dataseries_num,
            'good_dataseries_num': good_dataseries_num,
            'not_good_dataseries_num': not_good_dataseries_num,
            'empty_dataseries_num': empty_dataseries_num,
            'dataseries_good_percentage': dataseries_good_percentage,
            'dataseries_not_good_percentage': dataseries_not_good_percentage,
            'dataseries_empty_percentage': dataseries_empty_percentage,
            'state': 'empty' if total_dataseries_num == 0 or empty_dataseries_num > 0
                                else 'not_good' if good_dataseries_num < total_dataseries_num else 'good'

        }

        # state = config['stats']['state']
        # config['stats']['state_flag'] = 'blue' if state == 'good' else 'red' if state == 'empty' else ''


