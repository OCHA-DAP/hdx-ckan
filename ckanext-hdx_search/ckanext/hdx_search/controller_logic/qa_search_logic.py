import ckan.plugins.toolkit as tk

import ckanext.hdx_search.controller_logic.search_logic as sl

from ckanext.hdx_search.helpers.constants import NEW_DATASETS_FACET_NAME, UPDATED_DATASETS_FACET_NAME, \
    DELINQUENT_DATASETS_FACET_NAME, BULK_DATASETS_FACET_NAME, STATUS_PRIORITIES
from ckanext.hdx_search.helpers.qa_data import questions_list as qa_data_questions_list
from ckanext.hdx_search.helpers.solr_query_helper import generate_datetime_period_query


from ckanext.hdx_theme.helpers.json_transformer import get_obj_from_json_in_dict

h = tk.h
config = tk.config
_ = tk._


class QASearchLogic(sl.SearchLogic):

    def __init__(self, package_type='dataset'):
        super(QASearchLogic, self).__init__(package_type)
        self.flask_route_name = 'hdx_qa.dashboard'

    def search(self):
        self._search()
        return self

    def _search_url(self, params, package_type=None):
        url = self._current_url()
        return sl.url_with_params(url, params)

    def _current_url(self):
        url = h.url_for(self.flask_route_name)
        return url

    def _add_additional_faceting_queries(self, search_data_dict):
        super(QASearchLogic, self)._add_additional_faceting_queries(search_data_dict)
        new_datasets_query = generate_datetime_period_query('metadata_created', last_x_days=7)
        updated_datasets_query = generate_datetime_period_query('metadata_modified', last_x_days=7)
        delinquent_datasets_query = generate_datetime_period_query('delinquent_date')
        updated_by_script_query = 'extras_updated_by_script:[* TO *]'

        facet_queries = search_data_dict.get('facet.query') or []
        facet_queries.append('{{!key={} ex=batch}} {}'.format(NEW_DATASETS_FACET_NAME, new_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(UPDATED_DATASETS_FACET_NAME, updated_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(DELINQUENT_DATASETS_FACET_NAME,
                                                              delinquent_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(BULK_DATASETS_FACET_NAME, updated_by_script_query))
        search_data_dict['facet.query'] = facet_queries

        search_data_dict['facet.field'].append('{!ex=methodology,batch}methodology')
        search_data_dict['facet.field'].append('res_extras_broken_link')
        search_data_dict['facet.field'].append('res_extras_in_quarantine')
        search_data_dict['facet.field'].append('{!ex=batch}extras_qa_completed')
        search_data_dict['f.extras_qa_completed.facet.missing'] = 'true'
        search_data_dict['facet.field'].append('{!ex=batch}res_extras_pii_is_sensitive')
        search_data_dict['f.res_extras_pii_is_sensitive.facet.missing'] = 'true'

    def _process_found_package_list(self, package_list):
        super(QASearchLogic, self)._process_found_package_list(package_list)
        self.__process_checklist_data(package_list)
        self.__process_script_check_data(package_list, 'pii_report_flag', 'pii_timestamp')
        self.__process_script_check_data(package_list, 'sdc_report_flag', 'sdc_timestamp')

    def __process_checklist_data(self, package_list):

        if package_list:
            num_of_resource_questions = len(qa_data_questions_list['resources_checklist'])
            num_of_package_questions = len(qa_data_questions_list['data_protection_checklist']) + \
                                       len(qa_data_questions_list['metadata_checklist'])

            for package_dict in package_list:
                resource_list = package_dict.get('resources', [])
                checklist = get_obj_from_json_in_dict(package_dict, 'qa_checklist')
                package_dict['qa_checklist'] = checklist
                package_dict['qa_checklist_num'] = len(checklist.get('dataProtection', [])) + \
                                                   len(checklist.get('metadata', []))
                package_dict['qa_checklist_total_num'] = num_of_package_questions + \
                                                         num_of_resource_questions * len(resource_list)

                for r in resource_list:
                    r['qa_checklist_total_num'] = num_of_resource_questions
                    if package_dict.get('qa_checklist_completed'):
                        r['qa_checklist'] = None
                        r['qa_checklist_num'] = 0
                        r['qa_check_list_status'] = 'OK'
                    else:
                        r['qa_checklist'] = get_obj_from_json_in_dict(r, 'qa_checklist')
                        r['qa_checklist_num'] = len(r['qa_checklist'])
                        package_dict['qa_checklist_num'] += r['qa_checklist_num']
                        r['qa_check_list_status'] = 'ERROR' if r['qa_checklist_num'] > 0 else None

                # This needs to be set AFTER we've aggregated the statuses of the resources
                package_dict['qa_check_list_status'] = \
                    'OK' if package_dict.get('qa_checklist_completed') \
                        else 'ERROR' if package_dict['qa_checklist_num'] > 0 \
                        else None

    def __process_script_check_data(self, package_list, report_flag_field, timestamp_field):

        if package_list:
            for package_dict in package_list:
                resource_list = package_dict.get('resources', [])
                package_dict[report_flag_field] = ''
                package_dict[timestamp_field] = ''
                package_pii_priority = 0
                for r in resource_list:
                    res_pii_priority = STATUS_PRIORITIES.get(r.get(report_flag_field, ''), 0)
                    if res_pii_priority > package_pii_priority:
                        package_pii_priority = res_pii_priority
                        package_dict[report_flag_field] = r.get(report_flag_field, '')
                        package_dict[timestamp_field] = r.get(timestamp_field, '')

    def _process_complex_facet_data(self, existing_facets, title_translations, result_facets, search_extras):
        super(QASearchLogic, self)._process_complex_facet_data(existing_facets, title_translations, result_facets,
                                                                 search_extras)

        if existing_facets:
            item_list = []
            result_facets['qa_only'] = {
                'name': 'qa_only',
                'display_name': _('QA only'),
                'items': item_list,
                'show_everything': True
            }

            self._add_facet_query_item_to_list(NEW_DATASETS_FACET_NAME, _('New datasets'), existing_facets,
                                               item_list, search_extras)
            self._add_facet_query_item_to_list(UPDATED_DATASETS_FACET_NAME, _('Updated datasets'), existing_facets,
                                               item_list, search_extras)
            self._add_facet_query_item_to_list(DELINQUENT_DATASETS_FACET_NAME, _('Delinquent datasets'), existing_facets,
                                               item_list, search_extras)
            self.__process_bulk_dataset_facet(existing_facets, item_list, search_extras)

            self.__process_qa_completed_facet(existing_facets, title_translations, search_extras, item_list)

            self.__process_broken_link_facet(existing_facets, title_translations, search_extras, item_list)

            self.__process_in_quarantine_facet(existing_facets, title_translations, search_extras, item_list)

            self.__process_methodology(title_translations)

            self.__process_pii_is_sensitive_facet(existing_facets, title_translations, search_extras, item_list)

    def __process_bulk_dataset_facet(self, existing_facets, qa_only_item_list, search_extras):
        bulk_facet_item = self._add_facet_query_item_to_list(BULK_DATASETS_FACET_NAME, _('Bulk upload'),
                                                             existing_facets, qa_only_item_list, search_extras)

        non_bulk_facet_item = dict(bulk_facet_item)
        non_bulk_facet_item['display_name'] = _('Non-bulk upload')
        non_bulk_facet_item['name'] = '0'
        non_bulk_facet_item['count'] = self.template_data.batch_total_items - bulk_facet_item.get('count', 0)
        non_bulk_facet_item['selected'] = search_extras.get('ext_' + BULK_DATASETS_FACET_NAME) == '0'
        qa_only_item_list.append(non_bulk_facet_item)

    def __process_qa_completed_facet(self, existing_facets, title_translations, search_extras, qa_only_item_list):
        title_translations.pop('qa_completed', None)

        facet_data = existing_facets.pop('extras_qa_completed', {})
        qa_completed_item = dict(next(
            (i for i in facet_data.get('items', []) if i.get('name') == 'true'),
            {}
        ))

        qa_category_key = 'ext_qa_completed'
        qa_completed_item['category_key'] = qa_category_key
        qa_completed_item['display_name'] = 'QA Completed'
        qa_completed_item['name'] = '1'
        qa_completed_item['count'] = qa_completed_item.get('count', 0)
        qa_completed_item['selected'] = search_extras.get(qa_category_key) == '1'

        qa_only_item_list.append(qa_completed_item)

        qa_not_completed_count = sum(
            (i.get('count', 0) for i in facet_data.get('items', []) if i.get('name') != 'true')
        )
        qa_not_completed_item = {}
        qa_not_completed_item['category_key'] = qa_category_key
        qa_not_completed_item['display_name'] = 'QA Not Completed'
        qa_not_completed_item['name'] = '0'
        qa_not_completed_item['count'] = qa_not_completed_count
        qa_not_completed_item['selected'] = search_extras.get(qa_category_key) == '0'
        qa_only_item_list.append(qa_not_completed_item)

    def __process_broken_link_facet(self, existing_facets, title_translations, search_extras, qa_only_item_list):
        title_translations.pop('res_extras_broken_link', None)

        facet_data = existing_facets.pop('res_extras_broken_link', {})
        item = next(
            (i for i in facet_data.get('items', []) if i.get('name') == 'true'),
            {}
        )

        qa_category_key = 'ext_broken_link'
        item['category_key'] = qa_category_key
        item['display_name'] = 'Broken links'
        item['name'] = '1'
        item['count'] = item.get('count', 0)
        item['selected'] = search_extras.get(qa_category_key)

        qa_only_item_list.append(item)

    def __process_pii_is_sensitive_facet(self, existing_facets, title_translations, search_extras, qa_only_item_list):
        title_translations.pop('res_extras_pii_is_sensitive', None)

        facet_data = existing_facets.pop('res_extras_pii_is_sensitive', {})
        item = next(
            (i for i in facet_data.get('items', []) if i.get('name') is None),
            {}
        )

        qa_category_key = 'ext_pii_is_sensitive'
        item['category_key'] = qa_category_key
        item['display_name'] = 'Unconfirmed Sensitivity Classification'
        item['name'] = '1'
        item['count'] = item.get('count', 0)
        item['selected'] = search_extras.get(qa_category_key)

        qa_only_item_list.append(item)

    def __process_in_quarantine_facet(self, existing_facets, title_translations, search_extras, qa_only_item_list):
        title_translations.pop('res_extras_in_quarantine', None)

        facet_data = existing_facets.pop('res_extras_in_quarantine', {})
        item = next(
            (i for i in facet_data.get('items', []) if i.get('name') == 'true'),
            {}
        )

        qa_category_key = 'ext_in_quarantine'
        item['category_key'] = qa_category_key
        item['display_name'] = 'Under review'
        item['name'] = '1'
        item['count'] = item.get('count', 0)
        item['selected'] = search_extras.get(qa_category_key)

        qa_only_item_list.append(item)

    def __process_methodology(self, title_translations):
        '''
        :param title_translations:
        :type title_translations: collections.OrderedDict
        :return:
        '''
        cloned_dict = title_translations.copy()
        title_translations.clear()
        title_translations['{!ex=methodology,batch}methodology'] = _('Methodology')
        title_translations.update(cloned_dict)
