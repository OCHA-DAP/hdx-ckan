import datetime
import re
import unicodedata

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckanext.hdx_search.actions.actions as actions
import ckanext.hdx_search.actions.authorize as authorize
import ckanext.hdx_search.helpers.search_history as search_history
import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper
import ckanext.hdx_search.model as search_model
from ckan.common import _
from ckan.lib.helpers import DEFAULT_FACET_NAMES
from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO
from ckanext.hdx_package.helpers.cod_filters_helper import are_new_cod_filters_enabled
from ckanext.hdx_package.helpers.date_helper import DaterangeParser
from ckanext.hdx_package.helpers.freshness_calculator import get_calculator_instance, \
    UPDATE_STATUS_URL_FILTER, UPDATE_STATUS_UNKNOWN, UPDATE_STATUS_FRESH, UPDATE_STATUS_NEEDS_UPDATE
from ckanext.hdx_package.helpers.reindex_helper import before_indexing_clean_resource_formats
from ckanext.hdx_search.helpers.constants import NEW_DATASETS_FACET_NAME, UPDATED_DATASETS_FACET_NAME, \
    DELINQUENT_DATASETS_FACET_NAME, BULK_DATASETS_FACET_NAME
from ckanext.hdx_search.helpers.solr_query_helper import generate_datetime_period_query

NotFound = tk.ObjectNotFound


def convert_country(q):
    for c in tk.get_action('group_list')({'user':'127.0.0.1'},{'all_fields': True}):
        if re.findall(c['display_name'].lower(),q.lower()):
            q += ' '+c['name']
    return q


class HDXSearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurable
    def configure(self, config):
        search_model.setup()
        search_model.create_table()

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'num_of_results_for_prev_searches': search_history.num_of_results_for_prev_searches
        }

    def before_map(self, map):
        map.connect('simple_search',
            '/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('qa_dashboard', '/qa_dashboard',
                    controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='search')
        map.connect('qa_pii_log', '/dataset/{id}/resource/{resource_id}/qa_pii_log/{file_name}',
                    controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='qa_pii_log')
        map.connect('qa_sdcmicro_log', '/dataset/{id}/resource/{resource_id}/qa_sdcmicro_log',
                    controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='qa_sdcmicro_log')
        return map

    def after_map(self, map):
        map.connect('simple_search',
            '/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('qa_dashboard', '/qa_dashboard',
                    controller='ckanext.hdx_search.controllers.qa_controller:HDXQAController', action='search')
        return map

    def before_search(self, search_params):
        #Do not allow a sort without a sort directions
        if 'sort' in search_params:
            parts = search_params['sort'].split(' ')
            try:
                parts[1]
            except:
                search_params['sort'] = parts[0]+' desc'

        def adapt_solr_fq(param_name, fq_filter_1=None, fq_filter_0=None):
            '''
            :param param_name: request param name without the "ext_" part, for example "indicator"
            :type param_name: str
            '''
            try:
                req_param = 'ext_{}'.format(param_name)
                solr_param = 'extras_{}'.format(param_name)

                if not fq_filter_1:
                    fq_filter_1 = ' +{}:1'.format(solr_param)
                if not fq_filter_0:
                    fq_filter_0 = ' -{}:1'.format(solr_param)


                if req_param in search_params['extras']:
                    if int(search_params['extras'][req_param]) == 1:
                        search_params['fq'] += fq_filter_1
                    elif int(search_params['extras'][req_param]) == 0:
                        search_params['fq'] += fq_filter_0
            except Exception, ex:
                raise NotFound('Wrong parameter value for fq')

        # If indicator flag is set, search only that type
        adapt_solr_fq('indicator')
        adapt_solr_fq('subnational')
        adapt_solr_fq('cod', ' +vocab_Topics:"common operational dataset - cod"',
                      ' -vocab_Topics:"common operational dataset - cod"')
        adapt_solr_fq('hxl', ' +vocab_Topics:hxl', ' -vocab_Topics:hxl')
        adapt_solr_fq('quickcharts', ' +has_quickcharts:true', ' -has_quickcharts:true')
        adapt_solr_fq('geodata', ' +has_geodata:true', ' -has_geodata:true')
        adapt_solr_fq('requestdata', ' +extras_is_requestdata_type:true', ' -extras_is_requestdata_type:true')
        adapt_solr_fq('showcases', ' +has_showcases:true', ' -has_showcases:true')
        adapt_solr_fq('archived', ' +extras_archived:true', ' -extras_archived:true')
        adapt_solr_fq('administrative_divisions', ' +vocab_Topics:"administrative divisions"',
                      ' -vocab_Topics:"administrative divisions"')

        adapt_solr_fq('qa_completed', ' +extras_qa_completed:true', ' -extras_qa_completed:true')
        adapt_solr_fq('broken_link', ' +res_extras_broken_link:true', ' -res_extras_broken_link:true')
        adapt_solr_fq('in_quarantine', ' +res_extras_in_quarantine:true', ' -res_extras_in_quarantine:true')
        adapt_solr_fq(NEW_DATASETS_FACET_NAME,
                      generate_datetime_period_query('metadata_created', last_x_days=7, include_leading_space=True,
                                                     include=True))
        adapt_solr_fq(UPDATED_DATASETS_FACET_NAME,
                      generate_datetime_period_query('metadata_modified', last_x_days=7, include_leading_space=True,
                                                     include=True))
        adapt_solr_fq(DELINQUENT_DATASETS_FACET_NAME,
                      generate_datetime_period_query('delinquent_date', last_x_days=None, include_leading_space=True,
                                                     include=True))
        adapt_solr_fq(BULK_DATASETS_FACET_NAME, ' +extras_updated_by_script:[* TO *]',
                      ' -extras_updated_by_script:[* TO *]')

        if 'ext_batch' in search_params['extras']:
            batch = search_params['extras']['ext_batch'].strip()
            if batch:
                search_params['fq'] += ' +batch:{}'.format(batch)
            else:
                raise Exception('wrong parameter value for ext_batch')

        if 'ext_after_metadata_modified' in search_params['extras'] or \
                'ext_before_metadata_modified' in search_params['extras']:
            start_metadata_modified = search_params['extras'].get('ext_after_metadata_modified', '*')
            end_metadata_modified = search_params['extras'].get('ext_before_metadata_modified', '*')
            search_params['fq'] += ' +metadata_modified:[{} TO {}]'.format(start_metadata_modified,
                                                                           end_metadata_modified)

        self.__process_eaa_link_params(search_params)
        self.__process_freshness_filters(search_params)

        return search_params

    def __process_eaa_link_params(self, search_params):
        for value in EAA_FACET_NAMING_TO_INFO.values():
            if value.get('url_param_name') in search_params['extras']:
                search_params['fq'] += ' ' + solr_query_helper.generate_filter_query_from_list(
                    'vocab_Topics', value.get('tag_list'), negate=value.get('negate')
                )
                search_params['fq'] += ' vocab_Topics: education'
                break

    def __process_freshness_filters(self, search_params):
        values = search_params['extras'].get(UPDATE_STATUS_URL_FILTER)

        if values:
            rules = []
            for value in values:
                now_string = datetime.datetime.utcnow().isoformat() + 'Z'
                if value == UPDATE_STATUS_NEEDS_UPDATE:
                    rules.append('due_date: [* TO {}]'.format(now_string))
                if value == UPDATE_STATUS_FRESH:
                    rules.append('due_date: [{} TO *]'.format(now_string))
                if value == UPDATE_STATUS_UNKNOWN:
                    rules.append('(*:* -due_date: [* TO *])')

            if rules:
                filter_rule = ' OR '.join(rules)
                filter_rule = '{{!tag={tag}}}{rule}'.format(tag=UPDATE_STATUS_URL_FILTER, rule=filter_rule)
                search_params['fq_list'].append(filter_rule)

    # IPackageController
    def after_search(self, search_results, search_params):
        ext_compute_freshness = search_params.get('extras', {}).get('ext_compute_freshness')
        if ext_compute_freshness in {'true', 'for-data-completeness'}:
            for dataset in search_results.get('results', []):
                get_calculator_instance(dataset, ext_compute_freshness).populate_with_freshness()
        return search_results

    def before_view(self, pkg_dict):
        return pkg_dict

    # IPackageController
    def before_index(self, pkg_dict):

        before_indexing_clean_resource_formats(pkg_dict)

        pkg_dict['title_string'] = unicodedata.normalize("NFKD", pkg_dict['title']).replace(r'\xc3', 'I')
        pkg_dict.pop('resource_grouping', None)

        self.__process_dates_in_resource_extra(pkg_dict)
        self.__process_dataset_date(pkg_dict)
        return pkg_dict

    def __process_dataset_date(self, pkg_dict):
        '''
        This is very similar to what happens in :func:`ckan.lib.search.index.index_package()`
        for '_date' fields
        :param pkg_dict:
        :type pkg_dict: dict
        '''
        key = 'extras_dataset_date'
        value = pkg_dict.get(key)
        if value:
            new_value = DaterangeParser(value).compute_daterange_string(True)
            pkg_dict[key] = new_value

    def __process_dates_in_resource_extra(self, pkg_dict):
        '''
        This is very similar to what happens in :func:`ckan.lib.search.index.index_package()`
        for '_date' fields
        :param pkg_dict:
        :type pkg_dict: dict
        '''
        new_dict = {}
        for key, values in pkg_dict.items():
            key = key.encode('ascii', 'ignore')
            if key.startswith('res_extras_daterange') and values:
                new_list = []
                for value in values:
                    try:
                        new_value = DaterangeParser(value ).compute_daterange_string(True)
                        new_list.append(new_value)
                    except:
                        continue
                new_dict[key] = new_list

        pkg_dict.update(new_dict)

    def get_actions(self):
        return {
            'populate_related_items_count': actions.populate_related_items_count,
            'populate_showcase_items_count': actions.populate_showcase_items_count,
            'qa_questions_list': actions.hdx_qa_questions_list,
            'qa_sdcmicro_run': actions.hdx_qa_sdcmicro_run,
            'qa_pii_run': actions.hdx_qa_pii_run,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):

        tagged_facets = tk.config.get(u'search.facets', DEFAULT_FACET_NAMES).split()

        # adding exclusion directive for tagged facets
        for f in tagged_facets:
            translation = facets_dict[f]
            del facets_dict[f]
            facets_dict['{{!ex={},batch}}{}'.format(f, f)] = translation

        facets_dict['{!ex=batch}indicator'] = _('Indicators')
        facets_dict['{!ex=batch}subnational'] = _('Subnational')
        facets_dict['{!ex=batch}has_quickcharts'] = _('Quick charts')
        facets_dict['{!ex=batch}has_geodata'] = _('Geodata')
        # facets_dict['{!ex=batch}administrative_divisions'] = _('Administrative Divisions')
        facets_dict['{!ex=batch}extras_is_requestdata_type'] = _('Datasets on request (HDX Connect)')
        facets_dict['{!ex=batch}has_showcases'] = _('Datasets with Showcases')

        if are_new_cod_filters_enabled():
            facets_dict['{!ex=cod_level,batch}cod_level'] = _('CODs')

        return facets_dict

    def get_auth_functions(self):
        return {
            'qa_dashboard_show': authorize.hdx_qa_dashboard_show,
            'qa_sdcmicro_run': authorize.hdx_qa_sdcmicro_run,
            'qa_pii_run': authorize.hdx_qa_pii_run
        }

    # IBlueprint
    def get_blueprint(self):
        import ckanext.hdx_package.views.light_dataset as light_dataset
        return light_dataset.hdx_light_search
