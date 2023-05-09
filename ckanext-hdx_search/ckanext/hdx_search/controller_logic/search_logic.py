import logging
import re
import datetime
import json
from six import string_types, text_type
from six.moves.urllib.parse import urlencode
from collections import OrderedDict

from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as p
import ckan.plugins.toolkit as tk


from ckanext.hdx_search.helpers.constants import \
    DEFAULT_SORTING, DEFAULT_NUMBER_OF_ITEMS_PER_PAGE, \
    HXLATED_DATASETS_FACET_NAME, HXLATED_DATASETS_FACET_QUERY, SADD_DATASETS_FACET_NAME, SADD_DATASETS_FACET_QUERY, \
    ADMIN_DIVISIONS_DATASETS_FACET_NAME, ADMIN_DIVISIONS_DATASETS_FACET_QUERY, \
    COD_DATASETS_FACET_NAME, COD_DATASETS_FACET_QUERY, \
    SUBNATIONAL_DATASETS_FACET_NAME, QUICKCHARTS_DATASETS_FACET_NAME, GEODATA_DATASETS_FACET_NAME, \
    REQUESTDATA_DATASETS_FACET_NAME, SHOWCASE_DATASETS_FACET_NAME, ARCHIVED_DATASETS_FACET_NAME
from ckanext.hdx_package.helpers.util import find_approx_download
from ckanext.hdx_package.helpers.analytics import generate_analytics_data
from ckanext.hdx_package.helpers.cod_filters_helper import are_new_cod_filters_enabled
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER
from ckanext.hdx_package.helpers.constants import COD_VALUES_MAP, COD_GROUP_EXPLANATION_LINK


FEATURED_FACETS = [
    COD_DATASETS_FACET_NAME, SUBNATIONAL_DATASETS_FACET_NAME, QUICKCHARTS_DATASETS_FACET_NAME,
    GEODATA_DATASETS_FACET_NAME, REQUESTDATA_DATASETS_FACET_NAME, HXLATED_DATASETS_FACET_NAME,
    SHOWCASE_DATASETS_FACET_NAME, ARCHIVED_DATASETS_FACET_NAME, ADMIN_DIVISIONS_DATASETS_FACET_NAME,
    SADD_DATASETS_FACET_NAME
]
FEATURED_FACET_PARAMS = ['ext_' + item for item in FEATURED_FACETS]

_validate = dict_fns.validate
_check_access = logic.check_access

log = logging.getLogger(__name__)

g = tk.g
_ = tk._
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to

NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action

config = tk.config


def get_default_facet_titles():
    return {
        'dataseries_name': _('Data series'),
        'organization': _('Organizations'),
        'groups': _('Groups'),
        # 'tags': _('Tags'),
        'vocab_Topics': _('Tags'),
        'res_format': _('Formats'),
        'license_id': _('Licenses'),
    }


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, string_types) else text_type(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def get_url_param_iterator():
    keys = set(request.args.keys())

    def list_of_values(key):
        return request.args.getlist(key) if hasattr(request.args, 'getlist') else request.args.getall(key)

    param_values = ((param, value) for param in keys for value in list_of_values(param))
    return param_values


class SearchLogic(object):

    def __init__(self, package_type='dataset'):
        super(SearchLogic, self).__init__()
        self.package_type = package_type
        self.template_data = DictProxy()

    def add_archived_url_helper(self):
        full_facet_info = self.template_data.get('full_facet_info', {})
        base_url = self.template_data['other_links']['current_page_url']
        archived_url_helper = ArchivedUrlHelper(full_facet_info.get('num_of_unarchived'),
                                                full_facet_info.get('num_of_archived'),
                                                base_url, self._params_nopage())
        self.template_data['full_facet_info']['archived_url_helper'] = archived_url_helper
        return archived_url_helper

    def init_archived_url_helper(self):
        self.add_archived_url_helper()
        return self

    def redirect_if_needed(self):
        return self.archived_url_helper.redirect_if_needed()

    @property
    def archived_url_helper(self):
        '''
        :return:
        :rtype: ArchivedUrlHelper
        '''
        try:
            return self.template_data['full_facet_info']['archived_url_helper']
        except KeyError as ke:
            log.error('archived_url_helper object is only available after calling _search() '
                      'and add_archived_url_helper()')

    def _search(self, additional_fq='', additional_facets=None,
                default_sort_by=DEFAULT_SORTING, num_of_items=DEFAULT_NUMBER_OF_ITEMS_PER_PAGE,
                ignore_capacity_check=False, use_solr_collapse=False, hide_archived=True):

        from ckan.lib.search import SearchError

        # unicode format (decoded from utf8)
        q = self.template_data.q = request.args.get('q', u'')
        self.template_data.query_error = False

        page = self._page_number()
        package_type = self.package_type

        req_sort_by = request.args.get('sort', None)
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

            for (param, value) in get_url_param_iterator():
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
                        self._append_selected_facet_to_group(self.template_data.fields_grouped, param, value)
                    elif param == UPDATE_STATUS_URL_FILTER:
                        self._append_selected_facet_to_group(self.template_data.fields_grouped, param, value)
                    else:
                        if param in FEATURED_FACET_PARAMS:
                            featured_filters_set = True
                        if param == 'ext_archived' and value == '1':
                            hide_archived = False
                        search_extras[param] = value

            if self.template_data.fields_grouped.get(UPDATE_STATUS_URL_FILTER):
                search_extras[UPDATE_STATUS_URL_FILTER] = self.template_data.fields_grouped[UPDATE_STATUS_URL_FILTER]

            self._set_filters_are_selected_flag()

            fq_list = [self._create_filter_query(key, ' OR '.join(value_list))
                       for key, value_list in tagged_fq_dict.items()]

            # if the search is not filtered by query or facet group datasets
            solr_expand = 'false'
            if use_solr_collapse and not fq_list and not q and not featured_filters_set:
                fq_list = [
                    '{{!tag=batch q.op=OR}}{{!collapse field=batch nullPolicy=expand sort="{sort}"}} '
                        .format(sort=sort_by)
                ]
                solr_expand = 'true'

            # filtering archived datasets should happen after we decide whether to collapse/batch results
            fq_list.append(self._create_filter_query(
                ARCHIVED_DATASETS_FACET_NAME, '-extras_archived:"true"' if hide_archived else 'extras_archived:"true"'))

            try:
                limit = 1 if self._is_facet_only_request() else int(request.args.get('ext_page_size', num_of_items))
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
            facet_keys = ['{!ex=batch}site_id'] + list(facets)
            self._performing_search(q, fq, facet_keys, limit, page, sort_by, search_extras,
                                    self._get_pager_function(package_type), context,
                                    fq_list=fq_list, expand=solr_expand)

        except SearchError as se:
            log.error('Dataset search error: %r', se.args)
            facets = {}
            self.template_data.query_error = True
            self.template_data.search_facets = {}
            self.template_data.page = h.Page(collection=[])
        self.template_data.search_facets_limits = {}
        for facet in self.template_data.search_facets.keys():
            limit = 1000
            try:
                limit = int(request.args.get('_%s_limit' % facet,
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
        full_facet_info['results'] = self.template_data.get('page').collection if 'page' in self.template_data else []
        self.template_data['full_facet_info'] = full_facet_info


    def _get_pager_function(self, package_type):
        def pager_url(q=None, page=None):
            params = list(self._params_nopage())
            params.append(('page', page))
            return self._search_url(params, package_type)
        return pager_url

    def _append_selected_facet_to_group(self, group, param, value):
        if param not in group:
            group[param] = [value]
        else:
            group[param].append(value)

    def _create_filter_query(self, tag, value):
        query_string = u'{{!tag={tag}}}{value}'.format(tag=tag, value=value)
        return query_string

    def _is_facet_only_request(self):
        return request.args.get('ext_only_facets') == 'true'

    def _performing_search(self, q, fq, facet_keys, limit, page, sort_by,
                           search_extras, pager_url, context, fq_list=None, expand='false',
                           enable_update_status_facet=False):
        data_dict = {
            'q': q,
            'fq_list': fq_list if fq_list else [],
            'expand': expand,
            'expand.rows': 1,  # we anyway don't show the expanded datasets, but doesn't work with 0
            'fq': fq.strip(),
            'f.extras_archived.facet.missing': 'true',
            'facet.field': facet_keys,
            'facet.query': [
                '{{!key={} ex=batch}} {}'.format(HXLATED_DATASETS_FACET_NAME, HXLATED_DATASETS_FACET_QUERY),
                '{{!key={} ex=batch}} {}'.format(SADD_DATASETS_FACET_NAME, SADD_DATASETS_FACET_QUERY),
                '{{!key={} ex=batch}} {}'.format(ADMIN_DIVISIONS_DATASETS_FACET_NAME,
                                                 ADMIN_DIVISIONS_DATASETS_FACET_QUERY),
                '{{!key={} ex=batch}} {}'.format(COD_DATASETS_FACET_NAME, COD_DATASETS_FACET_QUERY),
            ],
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

        if self.package_type == 'dataset':
            get_action('populate_showcase_items_count')(context, {'pkg_dict_list': query['results']})

        self.template_data.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )

        for dataset in query['results']:
            if self.package_type == 'dataset':
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
                and ('_show_filters' not in request.args or request.args['_show_filters'] != 'false'):
            self.template_data.filters_are_selected = True
        else:
            self.template_data.filters_are_selected = False

    def _page_number(self):
        try:
            return int(request.args.get('page', 1))
        except ValueError as e:
            abort(400, ('"page" parameter must be an integer'))

    def _params_nopage(self):
        params_to_skip = ['_show_filters']
        # most search operations should reset the page counter:
        return [(k, v) for k, v in request.args.items()
                if k != 'page' and k not in params_to_skip]

    def _set_search_url_params(self):
        params_nopage = self._params_nopage()
        self.template_data['search_url_params'] = urlencode(_encode_params(params_nopage))

    def _set_other_links(self, suffix='', other_params_dict=None):
        url_param_list = ['sort', 'q', 'organization', 'tags',
                          'vocab_Topics', 'license_id', 'groups', 'res_format', '_show_filters']
        # named_route = self._get_named_route()
        params = {}

        for k, v in request.args.items():
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

        for param in FEATURED_FACET_PARAMS:
            if param in search_extras:
                result['filters_selected'] = True

        # num_of_indicators = 0
        # num_of_cods = 0
        num_of_subnational = 0
        num_of_quickcharts = 0
        num_of_geodata = 0
        # num_of_hxl = 0
        # num_of_sadd = 0
        num_of_requestdata = 0
        num_of_showcases = 0
        # num_of_administrative_divisions = 0
        num_of_archived = 0
        num_of_unarchived = 0

        new_cod_filters_enabled = are_new_cod_filters_enabled()

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
            category_tooltip = None
            item_list = existing_facets.get(category_key, {}).get('items', [])

            # We're only interested in the number of items of the "indicator" facet
            # if category_key == 'indicator':
            #     num_of_indicators = next((item.get('count', 0) for item in item_list if item.get('name', '') == '1'), 0)
            if category_key == SUBNATIONAL_DATASETS_FACET_NAME:
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
            elif category_key == 'extras_archived':
                # extras_archived is a solr boolean that is transformed to the string 'true'
                num_of_archived = next(
                    (item.get('count', 0) for item in item_list if item.get('name', '') == 'true'), 0)
                num_of_unarchived = sum(
                    (item.get('count', 0) for item in item_list if item.get('name', '') != 'true'), 0)
            else:
                if category_key == 'dataseries_name':
                    category_tooltip = 'Data series is a collection of datasets that has a shared topic usually ' \
                                       'provided by a single organisation '

                standard_facet_category, anything_selected = \
                    self._create_standard_facet_category(category_key, category_title, category_tooltip, item_list,
                                                         selected_facets)

                result['facets'][category_key] = standard_facet_category
                result['filters_selected'] = result['filters_selected'] or anything_selected

        if new_cod_filters_enabled:
            cod_category = result['facets'].pop('cod_level', None)
            if cod_category:
                modified_cod_category = self.__create_featured_cod_facet_category(cod_category)
                featured_facet_items.append(modified_cod_category)

        if not new_cod_filters_enabled:
            # self._add_item_to_featured_facets(featured_facet_items, 'ext_cod', 'CODs', num_of_cods, search_extras)
            self._add_facet_query_item_to_list(featured_facet_items, COD_DATASETS_FACET_NAME, _('CODs'),
                                               existing_facets, search_extras)

        self._add_facet_item_to_list(featured_facet_items, SUBNATIONAL_DATASETS_FACET_NAME, 'Sub-national',
                                     num_of_subnational, search_extras)
        self._add_facet_item_to_list(featured_facet_items, GEODATA_DATASETS_FACET_NAME, 'Geodata',
                                     num_of_geodata, search_extras)
        # self._add_item_to_featured_facets(featured_facet_items, 'ext_administrative_divisions', 'Administrative Divisions',
        #                                   num_of_administrative_divisions, search_extras)
        self._add_facet_query_item_to_list(featured_facet_items, ADMIN_DIVISIONS_DATASETS_FACET_NAME,
                                           _('Administrative Divisions'), existing_facets, search_extras)
        self._add_facet_item_to_list(featured_facet_items, REQUESTDATA_DATASETS_FACET_NAME,
                                     'Datasets on request (HDX Connect)', num_of_requestdata, search_extras)
        self._add_facet_item_to_list(featured_facet_items, QUICKCHARTS_DATASETS_FACET_NAME,
                                     'Datasets with Quick Charts', num_of_quickcharts, search_extras)
        self._add_facet_item_to_list(featured_facet_items, SHOWCASE_DATASETS_FACET_NAME, 'Datasets with Showcase',
                                     num_of_showcases, search_extras)
        # self._add_item_to_featured_facets(featured_facet_items, 'ext_hxl', 'Datasets with HXL tags',
        #                                   num_of_hxl, search_extras)
        self._add_facet_query_item_to_list(featured_facet_items, HXLATED_DATASETS_FACET_NAME,
                                           _('Datasets with HXL tags'), existing_facets, search_extras)
        # self._add_item_to_featured_facets(featured_facet_items, 'ext_sadd', 'Datasets with SADD tags',
        #                                   num_of_sadd, search_extras)
        self._add_facet_query_item_to_list(featured_facet_items, SADD_DATASETS_FACET_NAME, _('Datasets with SADD tags'),
                                           existing_facets, search_extras)

        # archived_explanation = _('A dataset is archived when it is no longer being actively updated, '
        #                          'but remains available primarily for historical purposes')
        # self._add_item_to_featured_facets(featured_facet_items, 'ext_archived', 'Archived datasets',
        #                                   num_of_archived, search_extras, explanation=archived_explanation)

        # result['num_of_indicators'] = num_of_indicators
        # result['num_of_cods'] = num_of_cods
        result['num_of_subnational'] = num_of_subnational
        result['num_of_quickcharts'] = num_of_quickcharts
        result['num_of_geodata'] = num_of_geodata
        # result['num_of_hxl'] = num_of_hxl
        # result['num_of_sadd'] = num_of_sadd
        result['num_of_requestdata'] = num_of_requestdata
        result['num_of_showcases'] = num_of_showcases
        # result['num_of_administrative_divisions'] = num_of_administrative_divisions
        result['num_of_selected_filters'] = sum(
            map(
                lambda facet_group: sum((1 if i.get('selected') else 0 for i in facet_group.get('items', []))),
                result.get('facets', {}).values()
            )
        )
        result['num_of_total_items'] = total_count
        result['num_of_archived'] = num_of_archived
        result['num_of_unarchived'] = num_of_unarchived

        # result['archived_explanation'] = archived_explanation

        result['query_selected'] = True if query and query.strip() else False

        return result

    def _get_facet_item_count_from_list(self, item_list, facet_item_name):
        count = 0
        for item in item_list:
            item_name = item.get('name', '')
            if item_name == facet_item_name:
                count = item.get('count', 0)
        return count

    def _create_standard_facet_category(self, category_key, category_title, category_tooltip, item_list,
                                        selected_facets):
        sorted_item_list = []
        anything_selected = False
        for item in item_list:
            item_name = item.get('name', '')
            if item_name and item_name.strip():
                selected = item_name in selected_facets.get(category_key, [])
                anything_selected = anything_selected or selected
                new_item = {
                    'count': item.get('count', 0),
                    'category_key': category_key,
                    'name': item_name,
                    'display_name': item.get('display_name', ''),
                    'selected': selected,
                }
                sorted_item_list.append(new_item)

        sorted_item_list.sort(key=lambda x: ('a' if x.get('selected') else 'b', x.get('display_name')))
        standard_facet_category = {
            'name': category_key,
            'display_name': category_title,
            'items': sorted_item_list,
            'tooltip': category_tooltip,
            'show_everything': len(sorted_item_list) < 5
        }
        return standard_facet_category, anything_selected

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

    def _add_facet_item_to_list(self, item_list, item_name, item_display_name, count, search_extras,
                                explanation=None):
        new_facet_item = self._create_facet_item(item_name, item_display_name, count, search_extras=search_extras,
                                                 explanation=explanation)
        item_list.append(new_facet_item)

    def _add_facet_query_item_to_list(self, item_list, item_name, item_display_name, existing_facets, search_extras):
        '''
        :param item_list: the list where the new facet item should be added
        :type item_list: list
        :param item_name: the facet key, the name that appears in existing_facets->queries list
        :type item_name: string
        :param item_display_name: facet display name
        :type item_display_name: string
        :param existing_facets: dictionary containing facet numbers
        :type existing_facets: dict
        :param search_extras: dictionary containing currently selected facets
        :type search_extras: dict
        :returns: the item that was added to the list
        :rtype: dict
        '''

        item = next(
            (i for i in existing_facets.get('queries', []) if i.get('name') == item_name), None)
        if item:
            new_facet_item = self._create_facet_item(item_name, item_display_name, item['count'],
                                                     search_extras=search_extras)
            item_list.append(new_facet_item)
            return new_facet_item
        return {}

    def _create_facet_item(self, item_name, display_name, count, search_extras=None,
                           search_extras_value=None, force_selected=None, explanation=None, value=None):
        key = 'ext_' + item_name
        value = '1' if value is None else value
        selected = force_selected
        if selected is None:
            selected_value = '1' if search_extras_value is None else search_extras_value
            selected = search_extras.get(key) == selected_value
        return {
            'count': count,
            'category_key': key,
            'name': value,  # this gets displayed as value in HTML <input>
            'display_name': display_name,
            'selected': selected,
            'explanation': explanation
        }

    def _process_complex_facet_data(self, existing_facets, title_translations, result_facets, search_extras):
        # to be overridden in sub-classes that need to process the results of the solr query in order to
        # do more complex preparation of the data that needs to be shown in the filter/facets
        pass

    def _process_found_package_list(self, package_list):
        # to be overridden in sub-classes that need to process the results of the solr query in order to
        # change the data in the package or its resources
        pass

    def __create_featured_cod_facet_category(self, cod_category):
        real_cod_items = [
            item for item in cod_category.get('items') if COD_VALUES_MAP.get(item.get('name'), {}).get('is_cod')
        ]
        for item in real_cod_items:
            cod_information = COD_VALUES_MAP.get(item.get('name'), {})
            item['display_name'] = cod_information.get('title')
            item['explanation'] = cod_information.get('explanation')
        total_count = sum((item.get('count', 0) for item in real_cod_items))
        real_cod_items.sort(key=lambda item: COD_VALUES_MAP.get(item.get('name'), {}).get('index', -1))
        cod_category['items'] = real_cod_items
        cod_category['category_key'] = cod_category['name']
        cod_category['name'] = 'ALL'
        cod_category['count'] = total_count
        cod_category['selected'] = all((item.get('selected') for item in real_cod_items)) if real_cod_items else False
        cod_category['explanation_link'] = COD_GROUP_EXPLANATION_LINK
        return cod_category


class DictProxy(dict):

    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        self[name] = value


class ArchivedUrlHelper(object):

    archived_explanation = _('A dataset is archived when it is no longer being actively updated, '
                             'but remains available primarily for historical purposes')

    def __init__(self, num_of_unarchived, num_of_archived, base_search_url, params_no_page):
        super(ArchivedUrlHelper, self).__init__()
        self.num_of_unarchived = num_of_unarchived
        self.num_of_archived = num_of_archived
        self.url_for_search = base_search_url
        self.on_archived_page = next((True for tpl in params_no_page if tpl[0] == 'ext_archived'), False)
        self.params = (tpl for tpl in params_no_page if tpl[0] != 'ext_archived')

    @property
    def archived_url(self):
        if self.num_of_archived > 0:
            params = [('ext_archived', '1')]
            params.extend(self.params)
            url = url_with_params(self.url_for_search, params)
            return url
        return None

    @property
    def show_archived_link(self):
        if self.on_archived_page or self.num_of_archived == 0:
            return False
        return True

    @property
    def unarchived_url(self):
        if self.num_of_unarchived > 0:
            url = url_with_params(self.url_for_search, self.params)
            return url
        return None

    @property
    def show_unarchived_link(self):
        if not self.on_archived_page or self.num_of_unarchived == 0:
            return False
        return True

    @property
    def archived_disabled(self):
        if self.num_of_archived > 0:
            return False
        return True

    @property
    def unarchived_disabled(self):
        if self.num_of_unarchived > 0:
            return False
        return True

    def redirect_if_needed(self):
        if not self.on_archived_page and self.num_of_unarchived == 0 and self.num_of_archived > 0:
            result = redirect(self.archived_url)
            return result
        return None
