import logging, re
import unicodedata
import ckan.logic
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import _

import ckanext.hdx_search.actions.actions as actions
import ckanext.hdx_search.model as search_model
import ckanext.hdx_search.helpers.search_history as search_history
import ckanext.hdx_package.helpers.helpers as hdx_package_helper

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
        return map

    def after_map(self, map):
        map.connect('simple_search',
            '/dataset', controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        map.connect('search', '/search',
                    controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        return map

    def before_search(self, search_params):
        #Do not allow a sort without a sort directions
        if 'sort' in search_params:
            parts = search_params['sort'].split(' ')
            try:
                parts[1]
            except:
                search_params['sort'] = parts[0]+' desc'

        #search_params['q'] = convert_country(search_params['q'])
        if 'facet.field' in search_params and 'vocab_Topics' not in search_params['facet.field']:
            search_params['facet.field'].append('vocab_Topics')

        def adapt_solr_fq(param_name, fq_filter_1=None, fq_filter_0=None):
            '''
            :param param_name: request param name without the "ext_" part, for example "indicator"
            :type str:
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
        adapt_solr_fq('cod', ' +tags:cod', ' -tags:cod')
        adapt_solr_fq('hxl', ' +tags:hxl', ' -tags:hxl')
        adapt_solr_fq('quickcharts', ' +has_quickcharts:true', ' -has_quickcharts:true')
        adapt_solr_fq('geodata', ' +has_geodata:true', ' -has_geodata:true')
        adapt_solr_fq('requestdata', ' +extras_is_requestdata_type:true', ' -extras_is_requestdata_type:true')
        adapt_solr_fq('showcases', ' +has_showcases:true', ' -has_showcases:true')

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

        return search_params

    def after_search(self, search_results, search_params):
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
            'populate_showcase_items_count': actions.populate_showcase_items_count
        }

    def dataset_facets(self, facets_dict, package_type):

        tagged_facets = ['groups', 'res_format', 'organization', 'tags', 'license_id']

        # adding exclusion directive for tagged facets
        for f in tagged_facets:
            translation = facets_dict[f]
            del facets_dict[f]
            facets_dict['{{!ex={},batch}}{}'.format(f, f)] = translation

        facets_dict['{!ex=batch}indicator'] = _('Indicators')
        facets_dict['{!ex=batch}subnational'] = _('Subnational')
        facets_dict['{!ex=batch}has_quickcharts'] = _('Quick charts')
        facets_dict['{!ex=batch}has_geodata'] = _('Geodata')
        facets_dict['{!ex=batch}extras_is_requestdata_type'] = _('Datasets on request')
        facets_dict['{!ex=batch}has_showcases'] = _('Datasets with Showcases')

        return facets_dict
