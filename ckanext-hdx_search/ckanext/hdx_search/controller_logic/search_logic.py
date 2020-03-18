import logging
import re
import datetime
import sqlalchemy
import json
from urllib import urlencode
from collections import OrderedDict

from pylons import config
from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as p

import ckanext.hdx_search.helpers.search_history as search_history

from ckan.common import _, request, g


from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING, DEFAULT_NUMBER_OF_ITEMS_PER_PAGE
from ckanext.hdx_package.controllers.dataset_controller import find_approx_download
from ckanext.hdx_package.helpers.analytics import generate_analytics_data
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER,\
    UPDATE_STATUS_UNKNOWN, UPDATE_STATUS_FRESH, UPDATE_STATUS_NEEDS_UPDATE

_validate = dict_fns.validate
_check_access = logic.check_access

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = h.redirect_to

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action

def get_default_facet_titles():
    return {
        'organization': _('Organizations'),
        'groups': _('Groups'),
        # 'tags': _('Tags'),
        'vocab_Topics': _('Tags'),
        'res_format': _('Formats'),
        'license_id': _('Licenses'),
    }


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


class SearchLogic(object):

    def __init__(self):
        super(SearchLogic, self).__init__()
        self.package_type = 'dataset'
        self.template_data = DictProxy()

    def _search(self, package_type, additional_fq='', additional_facets=None,
                default_sort_by=DEFAULT_SORTING, num_of_items=DEFAULT_NUMBER_OF_ITEMS_PER_PAGE,
                ignore_capacity_check=False, use_solr_collapse=False):

        from ckan.lib.search import SearchError

        # unicode format (decoded from utf8)
        q = self.template_data.q = request.params.get('q', u'')
        self.template_data.query_error = False

        page = self._page_number()
        package_type = self.package_type

        def pager_url(q=None, page=None):
            params = list(self._params_nopage())
            params.append(('page', page))
            return self._search_url(params, package_type)


        req_sort_by = request.params.get('sort', None)
        if not req_sort_by and q:
            req_sort_by = 'score desc, ' + DEFAULT_SORTING

        if req_sort_by:
            sort_by = req_sort_by
            self.template_data.used_default_sort_by = False
        else:
            sort_by = default_sort_by
            self.template_data.used_default_sort_by = True

        if not sort_by:
            self.template_data.sort_by_fields = []
        else:
            self.template_data.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        self._set_other_links()

        search_extras = {}
        try:
            self.template_data.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            self.template_data.fields_grouped = {}
            # limit = g.datasets_per_page

            fq = additional_fq
            tagged_fq_dict = {}
            featured_filters_set = False

            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort', 'force_layout'] \
                        and len(value) and not param.startswith('_'):
                    if param == 'fq':
                        fq += ' %s' % (value,)
                    elif not param.startswith('ext_'):
                        self.template_data.fields.append((param, value))
                        # fq += ' {!tag=%s}%s:"%s"' % (param, param, value)
                        if param not in tagged_fq_dict:
                            tagged_fq_dict[param] = []
                        tagged_fq_dict[param].append(u'{}:"{}"'.format(param, value))
                        self.append_selected_facet_to_group(self.template_data.fields_grouped, param, value)
                    elif param == UPDATE_STATUS_URL_FILTER:
                        self.append_selected_facet_to_group(self.template_data.fields_grouped, param, value)
                    else:
                        if param in ['ext_cod', 'ext_subnational', 'ext_quickcharts', 'ext_geodata', 'ext_requestdata',
                                     'ext_hxl', 'ext_showcases', 'ext_archived', 'ext_administrative_divisions']:
                            featured_filters_set = True
                        search_extras[param] = value


            if self.template_data.fields_grouped.get(UPDATE_STATUS_URL_FILTER):
                search_extras[UPDATE_STATUS_URL_FILTER] = self.template_data.fields_grouped[UPDATE_STATUS_URL_FILTER]

            self._set_filters_are_selected_flag()

            fq_list = [u'{{!tag={tag}}}{value}'.format(tag=key, category=key, value=' OR '.join(value_list))
                       for key, value_list in tagged_fq_dict.items()]

            # if the search is not filtered by query or facet group datasets
            solr_expand = 'false'
            if use_solr_collapse and not fq_list and not q and not featured_filters_set:
                fq_list = ['{!tag=batch}{!collapse field=batch nullPolicy=expand} ']
                solr_expand = 'true'

            try:
                limit = 1 if self._is_facet_only_request() else int(request.params.get('ext_page_size', num_of_items))
            except:
                limit = num_of_items

            self.template_data.ext_page_size = limit

            context = {'model': model, 'session': model.Session,
                       'user': g.user, 'for_view': True,
                       'auth_user_obj': g.userobj}

            if ignore_capacity_check:
                context['ignore_capacity_check'] = ignore_capacity_check

            if package_type and package_type != 'dataset':
                # Only show datasets of this particular type
                fq += ' +dataset_type:{type}'.format(type=package_type)
            else:
                # Unless changed via config options, don't show non standard
                # dataset types on the default search page
                if not asbool(config.get('ckan.search.show_all_types', 'False')):
                    fq += ' +dataset_type:dataset'

            facets = self._generate_facet_name_to_title_map(package_type)
            #adding site_id to facets to facilitate totals counts in case of batch/collapse
            facet_keys = ['{!ex=batch}site_id'] + facets.keys()
            self._performing_search(q, fq, facet_keys, limit, page, sort_by, search_extras, pager_url, context,
                                    fq_list=fq_list, expand=solr_expand)

        except SearchError, se:
            log.error('Dataset search error: %r', se.args)
            facets = {}
            self.template_data.query_error = True
            self.template_data.search_facets = {}
            self.template_data.page = h.Page(collection=[])
        self.template_data.search_facets_limits = {}
        for facet in self.template_data.search_facets.keys():
            limit = 1000
            try:
                limit = int(request.params.get('_%s_limit' % facet,
                                               1000))
            except ValueError:
                abort(400, _('Parameter "{parameter_name}" is not '
                             'an integer').format(
                    parameter_name='_%s_limit' % facet
                ))
            self.template_data.search_facets_limits[facet] = limit

        # return render(self._search_template(package_type))
        full_facet_info = self._prepare_facets_info(self.template_data.search_facets, self.template_data.fields_grouped, search_extras, facets,
                                                    self.template_data.batch_total_items, self.template_data.q)
        self.template_data['full_facet_info'] = full_facet_info

    def append_selected_facet_to_group(self, group, param, value):
        if param not in group:
            group[param] = [value]
        else:
            group[param].append(value)

    def _is_facet_only_request(self):
        return request.params.get('ext_only_facets') == 'true'

    def _performing_search(self, q, fq, facet_keys, limit, page, sort_by,
                           search_extras, pager_url, context, fq_list=None, expand='false',
                           enable_update_status_facet=False):
        data_dict = {
            'q': q,
            'fq_list': fq_list if fq_list else [],
            'expand': expand,
            'expand.rows': 1,  # we anyway don't show the expanded datasets, but doesn't work with 0
            'fq': fq.strip(),
            'facet.field': facet_keys,
            # added for https://github.com/OCHA-DAP/hdx-ckan/issues/3340
            'facet.limit': 2000,
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras,
            'ext_compute_freshness': 'true'
        }

        self._add_additional_faceting_queries(data_dict)

        include_private = context.pop('ignore_capacity_check', None)
        if include_private:
            data_dict['include_private'] = include_private

        query = get_action('package_search')(context, data_dict)

        if not query.get('results', None):
            log.warn('No query results found for data_dict: {}. Query dict is: {}. Query time {}'.format(
                str(data_dict), str(query), datetime.datetime.now()))

        self._process_found_package_list(query['results'])

        self.template_data.facets = query['facets']
        self.template_data.search_facets = query['search_facets']

        # if we're using collapse/expand/batch then take total count from facet site_id
        if expand:
            site_id_items = query['search_facets'].get('site_id', {}).get('items', [])
            self.template_data.batch_total_items = sum((item.get('count', 0) for item in site_id_items))

        # get_action('populate_related_items_count')(
        #     context, {'pkg_dict_list': query['results']})

        get_action('populate_showcase_items_count')(context, {'pkg_dict_list': query['results']})

        self.template_data.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )

        for dataset in query['results']:
            downloads_list = (res['tracking_summary']['total'] for res in dataset.get('resources', []) if
                              res.get('tracking_summary', {}).get('total'))
            download_sum = sum(downloads_list)

            dataset['approx_total_downloads'] = find_approx_download(dataset.get('total_res_downloads', 0))

            dataset['batch_length'] = query['expanded'].get(dataset.get('batch',''), {}).get('numFound', 0)
            if dataset.get('organization'):
                dataset['batch_url'] = h.url_for(
                    'hdx_light_dataset.search', organization=dataset['organization'].get('name'),
                    ext_batch=dataset.get('batch'))

        for dataset in query['results']:
            dataset['hdx_analytics'] = json.dumps(generate_analytics_data(dataset))

        self.template_data.page.items = query['results']
        self.template_data.sort_by_selected = query['sort']

        self.template_data.count = self.template_data.item_count = query['count']

        return query

    def _add_additional_faceting_queries(self, search_data_dict):
        # to be overridden in sub classes that need to add more complex faceting queries
        pass

    def _search_url(self, params, package_type=None):
        '''
        Returns the url of the current search type
        :param params: the parameters that will be added to the search url
        :type params: list of key-value tuples
        :param package_type: for now this is always 'dataset'
        :type package_type: string

        :rtype: string
        '''
        if not package_type or package_type == 'dataset':
            url = h.url_for('search')
        else:
            url = h.url_for('{0}_search'.format(package_type))
        return url_with_params(url, params)

    def _set_filters_are_selected_flag(self):
        if len(self.template_data.fields_grouped) > 0 \
                and ('_show_filters' not in request.params or request.params['_show_filters'] != 'false'):
            self.template_data.filters_are_selected = True
        else:
            self.template_data.filters_are_selected = False

    def _page_number(self):
        try:
            return int(request.params.get('page', 1))
        except ValueError, e:
            abort(400, ('"page" parameter must be an integer'))

    def _params_nopage(self):
        params_to_skip = ['_show_filters']
        # most search operations should reset the page counter:
        return [(k, v) for k, v in request.params.items()
                if k != 'page' and k not in params_to_skip]

    def _set_search_url_params(self):
        params_nopage = self._params_nopage()
        self.template_data['search_url_params'] = urlencode(_encode_params(params_nopage))

    def _set_other_links(self, suffix='', other_params_dict=None):
        url_param_list = ['sort', 'q', 'organization', 'tags',
                          'vocab_Topics', 'license_id', 'groups', 'res_format', '_show_filters']
        # named_route = self._get_named_route()
        params = {}

        for k, v in request.params.items():
            if k in url_param_list:
                if k in params:
                    params[k].append(v)
                else:
                    params[k] = [v]

        if other_params_dict:
            params.update(other_params_dict)

        self.template_data.other_links = {}
        self.template_data.other_links['params_noq'] = {k: v for k, v in params.items()
                                       if k not in ['q', '_show_filters', 'id']}
        self.template_data.other_links['params_nosort_noq'] = {k: v for k, v in params.items()
                                              if k not in ['sort', 'q', 'id']}
        self.template_data.other_links['current_page_url'] = self._current_url()

    def _current_url(self):
        url = h.url_for('hdx_light_dataset.search')
        return url

    def _prepare_facets_info(self, existing_facets, selected_facets, search_extras, title_translations, total_count,
                             query):
        '''
        Sample return
        {
          'facets':
          {
              'tags':
              {
                'display_name': u'Tags',
                'name': 'tags',
                'items': [
                  {
                    'count': 1,
                    'selected': True,
                    'display_name': 'africa',
                    'name': 'africa'
                  },
                  {
                    'count': 1,
                    'selected': False,
                    'display_name': 'environment',
                    'name': 'environment'
                  },
                ]
              }
              .................
          },
          'num_of_indicators': 10,
          'num_of_cods': 0,
          'num_of_total_items': 1000,
          'query_selected': False #if there was any query in this request
          'filters_selected': True #if there was any filter in this request
        }
        :param existing_facets: possible facets for this search
        :type existing_facets: dict
        :param selected_facets: facets that have been selected
        :type selected_facets: dict
        :param search_extras: extra search parameters given on the search page: "ext_"
        :type search_extras: dict
        :param title_translations: translation of the facet categories
        :type title_translations: dict
        :return: facet information
        :rtype: OrderedDict
        '''

        result = OrderedDict()
        result['facets'] = OrderedDict()
        result['filters_selected'] = False

        checkboxes = ['ext_cod', 'ext_indicator', 'ext_subnational', 'ext_quickcharts',
                      'ext_geodata', 'ext_hxl', 'ext_requestdata', 'ext_showcases', 'ext_archive',
                      'ext_administrative_divisions']

        for param in checkboxes:
            if param in search_extras:
                result['filters_selected'] = True

        num_of_indicators = 0
        num_of_cods = 0
        num_of_subnational = 0
        num_of_quickcharts = 0
        num_of_geodata = 0
        num_of_hxl = 0
        num_of_requestdata = 0
        num_of_showcases = 0
        num_of_administrative_divisions = 0

        featured_facet_items = []
        result['facets']['featured'] = {
            'name': 'featured',
            'display_name': 'Featured',
            'items': featured_facet_items,
            'show_everything': True
        }

        self._process_complex_facet_data(existing_facets, title_translations, result['facets'], search_extras)

        for solr_category_key, category_title in title_translations.items():
            regex = r'\{[\s\S]*\}'
            category_key = re.sub(regex, '', solr_category_key)

            item_list = existing_facets.get(category_key, {}).get('items', [])

            # We're only interested in the number of items of the "indicator" facet
            if category_key == 'indicator':
                num_of_indicators = next((item.get('count', 0) for item in item_list if item.get('name', '') == '1'), 0)
            elif category_key == 'subnational':
                num_of_subnational = next((item.get('count', 0) for item in item_list if item.get('name', '') == '1'),
                                          0)
            elif category_key == 'has_quickcharts':
                # has_quickcharts is a solr boolean that is transformed to the string 'true'
                num_of_quickcharts = next(
                    (item.get('count', 0) for item in item_list if item.get('name', '') == 'true'), 0)
            elif category_key == 'has_geodata':
                # has_geodata is a solr boolean that is transformed to the string 'true'
                num_of_geodata = next((item.get('count', 0) for item in item_list if item.get('name', '') == 'true'), 0)
            elif category_key == 'extras_is_requestdata_type':
                # extras_is_requestdata_type is a solr boolean that is transformed to the string 'true'
                num_of_requestdata = next(
                    (item.get('count', 0) for item in item_list if item.get('name', '') == 'true'), 0)
            elif category_key == 'has_showcases':
                # has_showcases is a solr boolean that is transformed to the string 'true'
                num_of_showcases = next((item.get('count', 0) for item in item_list if item.get('name', '') == 'true'),
                                        0)
            else:
                sorted_item_list = []
                for item in item_list:
                    item_name = item.get('name', '')
                    if item_name and item_name.strip():
                        selected = item_name in selected_facets.get(category_key, [])
                        if selected and not result['filters_selected']:
                            result['filters_selected'] = selected
                        new_item = {
                            'count': item.get('count', 0),
                            'category_key': category_key,
                            'name': item_name,
                            'display_name': item.get('display_name', ''),
                            'selected': selected,
                        }
                        sorted_item_list.append(new_item)
                        if category_key == 'vocab_Topics' and new_item['name'] == 'common operational dataset - cod':
                            num_of_cods = new_item['count']
                        if category_key == 'vocab_Topics' and new_item['name'] == 'hxl':
                            num_of_hxl = new_item['count']
                        if category_key == 'vocab_Topics' and new_item['name'] == 'administrative divisions':
                            num_of_administrative_divisions = new_item['count']

                sorted_item_list.sort(key=lambda x: x.get('display_name'))

                result['facets'][category_key] = {
                    'name': category_key,
                    'display_name': category_title,
                    'items': sorted_item_list,
                    'show_everything': len(sorted_item_list) < 5
                }

        self._add_item_to_featured_facets(featured_facet_items, 'ext_cod', 'CODs', num_of_cods, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_subnational', 'Sub-national',
                                          num_of_subnational, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_geodata', 'Geodata', num_of_geodata, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_administrative_divisions', 'Administrative Divisions',
                                          num_of_administrative_divisions, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_requestdata', 'Datasets on request (HDX Connect)',
                                          num_of_requestdata, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_quickcharts', 'Datasets with Quick Charts',
                                          num_of_quickcharts, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_showcases', 'Datasets with Showcase',
                                          num_of_showcases, search_extras)
        self._add_item_to_featured_facets(featured_facet_items, 'ext_hxl', 'Datasets with HXL tags',
                                          num_of_hxl, search_extras)

        result['num_of_indicators'] = num_of_indicators
        result['num_of_cods'] = num_of_cods
        result['num_of_subnational'] = num_of_subnational
        result['num_of_quickcharts'] = num_of_quickcharts
        result['num_of_geodata'] = num_of_geodata
        result['num_of_hxl'] = num_of_hxl
        result['num_of_requestdata'] = num_of_requestdata
        result['num_of_showcases'] = num_of_showcases
        result['num_of_administrative_divisions'] = num_of_administrative_divisions
        result['num_of_total_items'] = total_count

        result['query_selected'] = True if query and query.strip() else False

        return result

    def _generate_facet_name_to_title_map(self, package_type):
        facets = OrderedDict()
        default_facet_titles = get_default_facet_titles()

        for facet in h.facets():
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        for plugin in p.PluginImplementations(p.IFacets):
            facets = plugin.dataset_facets(facets, package_type)

        return facets

    def _add_item_to_featured_facets(self, featured_facet_items, key, display_name, num_of_cods, search_extras):
        featured_facet_items.append({
            'count': num_of_cods,
            'category_key': key,
            'name': '1',
            'display_name': display_name,
            'selected': search_extras.get(key),
        })

    def _process_complex_facet_data(self, existing_facets, title_translations, result_facets, search_extras):
        # to be overridden in sub-classes that need to process the results of the solr query in order to
        # do more complex preparation of the data that needs to be shown in the filter/facets
        pass

    def _process_found_package_list(self, package_list):
        # to be overridden in sub-classes that need to process the results of the solr query in order to
        # change the data in the package or its resources
        pass


class DictProxy(dict):

    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        self[name] = value

