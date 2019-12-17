import logging, re
import datetime
import unicodedata
import ckan.logic
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import _
from ckan.lib.helpers import DEFAULT_FACET_NAMES

import ckanext.hdx_search.actions.actions as actions
import ckanext.hdx_search.model as search_model
import ckanext.hdx_search.helpers.search_history as search_history
import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper
import ckanext.hdx_package.helpers.helpers as hdx_package_helper

from ckanext.hdx_package.helpers.freshness_calculator import get_calculator_instance,\
    UPDATE_STATUS_URL_FILTER, UPDATE_STATUS_UNKNOWN, UPDATE_STATUS_FRESH, UPDATE_STATUS_NEEDS_UPDATE
from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO

import ckanext.hdx_search.actions.authorize as authorize
from ckanext.hdx_search.helpers.constants import NEW_DATASETS_FACET_NAME

NotFound = ckan.logic.NotFound

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

        now_string = datetime.datetime.utcnow().isoformat() + 'Z'
        adapt_solr_fq(NEW_DATASETS_FACET_NAME, ' +metadata_created:[{}-7DAYS TO {}]'.format(now_string, now_string))

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

    def before_index(self, pkg_dict):
        if pkg_dict.get('res_format'):
            new_formats = []
            for format in pkg_dict['res_format']:
                new_format = hdx_package_helper.hdx_unified_resource_format(format)
                new_formats.append(new_format)
            pkg_dict['res_format'] = new_formats
        pkg_dict['title_string'] = unicodedata.normalize("NFKD", pkg_dict['title']).replace(r'\xc3', 'I')
        return pkg_dict

    def get_actions(self):
        return {
            'populate_related_items_count': actions.populate_related_items_count,
            'populate_showcase_items_count': actions.populate_showcase_items_count,
            'qa_questions_list': actions.hdx_qa_questions_list
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

        return facets_dict

    def get_auth_functions(self):
        return {'qa_dashboard_show': authorize.qa_dashboard_show
                }
