import logging
import datetime
import sqlalchemy
from urllib import urlencode

from pylons import config
from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as p

from ckan.common import OrderedDict, _, json, request, c, g, response

from ckan.controllers.package import PackageController
from ckan.controllers.api import CONTENT_TYPES

from ckanext.hdx_package.controllers.dataset_controller import find_approx_download
from ckanext.hdx_package.helpers.analytics import generate_analytics_data

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
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action

NUM_OF_ITEMS = 25


def get_default_facet_titles():
    return {
        'organization': _('Organizations'),
        'groups': _('Groups'),
        'tags': _('Tags'),
        'res_format': _('Formats'),
        'license_id': _('Licenses'),
    }


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)
#
#
# def search_for_all(context, data_dict):
#     '''This search is independent of the tab in which the user
#        currently is.
#        The result is used for finding counts for datasets, indicators and totals
#     '''
#     facet_fields = data_dict.get('facet.field', [])
#     facet_fields.append('extras_indicator')
#     sort = data_dict.get('sort', None)
#     if not sort:
#         sort = 'score desc'
#
#     q = data_dict.get('q', None)
#     search = {
#         'q': data_dict.get('q', None),
#         'fq': data_dict.get('fq', None),
#         'facet.field': facet_fields,
#         'facet.limit': 1000,
#         'rows': 1,  # since this is just for facets,counts and one indicator, 1 should be enough
#         'sort': 'extras_indicator desc, ' + sort,
#     }
#     #     if tab == 'indicators':
#     #         search['extras'] = {'ext_indicator': 1}
#     #     elif tab == 'datasets':
#     #         search['extras'] = {'ext_indicator': 0}
#     result = get_action('package_search')(context, search)
#     return result
#
#
# def extract_counts(result):
#     ''' Extracts the counts from a search_for_all() result '''
#
#     total = result['count']
#     if '1' in result['facets']['extras_indicator']:
#         indicator_no = result['facets']['extras_indicator']['1']
#     else:
#         indicator_no = 0
#     # dataset_no = total  - this is a wrong fix
#     dataset_no = total - indicator_no
#     return (dataset_no, indicator_no)
#
#
# def extract_one_indicator(result):
#     ''' Extracts the first indicator from a search_for_all() result '''
#
#     if len(result['results']) > 0 \
#             and result['results'][0] \
#             and 'indicator' in result['results'][0] \
#             and result['results'][0]['indicator'] == '1':
#         indicator = [result['results'][0]]
#     else:
#         indicator = None
#     return indicator

#
# def sort_features(features):
#     return sorted(features, key=lambda x: x['count'], reverse=True)
#
#
# @maintain.deprecated('Showing features in search results has been deprecated')
# def isolate_features(context, facets, q, tab, skip=0, limit=25):
#     ''' Showing features in search results has been deprecated.
#         Deprecated since 25.01.2015 - hdx 0.6.5
#     '''
#     import difflib
#     import random
#
#     try:
#         all_topics = get_action('tag_list')(
#             context, {'vocabulary_id': 'Topics'})
#     except NotFound, e:
#         all_topics = []
#         log.error('ERROR getting vocabulary named Topics: %r' %
#                   str(e.extra_msg))
#
#     extract = dict()
#     tags = list()
#     features = list()
#     for o in facets['organization']['items']:
#         tags.append(o['name'])
#         extract[o['name']] = {'name': o['name'], 'display_name': o['display_name'],
#                               'url': h.url_for(controller='organization', action='read', id=o['name']),
#                               'description': o['description'], 'feature_type': 'organization', 'count': o['count']}
#
#     for p in facets['vocab_Topics']['items']:
#         tags.append(p['name'])
#         extract[p['name']] = {'name': p['name'], 'display_name': p['name'],
#                               'url': h.url_for(
#                                   controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController',
#                                   action='search', vocab_Topics=p['name']), 'description': '', 'last_update': '',
#                               'feature_type': 'topic', 'count': p['count']}
#
#     for g in facets['groups']['items']:
#         tags.append(g['name'])
#         extract[g['name']] = {'name': g['name'], 'display_name': g['display_name'],
#                               'url': h.url_for(controller='group', action='read', id=g['name']),
#                               'description': g['description'], 'feature_type': 'country', 'count': g['count']}
#
#     if tab == 'all' and len(tags) > 3:
#         if q:
#             selected = difflib.get_close_matches(q, tags, cutoff=0.1, n=3)
#         else:
#             selected = random.sample(tags, 3)
#     else:
#         selected = tags
#     for s in selected:
#         features.append(extract[s])
#     if tab == 'features':
#         feature_list = sort_features(features)
#         return (feature_list[skip:skip + limit], len(features))
#     return features


class HDXSearchController(PackageController):
    def search(self):
        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        package_type = self._guess_package_type()

        if package_type == 'search':
            package_type = 'dataset'

        params_nopage = self._params_nopage()
        c.search_url_params = urlencode(_encode_params(params_nopage))

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return self._search_url(params, package_type)

        c.full_facet_info = self._search(package_type, pager_url, default_sort_by='pageviews_last_14_days desc')

        c.cps_off = config.get('hdx.cps.off', 'false')

        # If we're only interested in the facet numbers a json will be returned with the numbers
        if self._is_facet_only_request():
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            self._setup_template_variables(context, {},
                                           package_type=package_type)
            return self._search_template()

    def _search(self, package_type, pager_url,
                additional_fq='', additional_facets=None,
                default_sort_by=None, num_of_items=NUM_OF_ITEMS,
                ignore_capacity_check=False):
        from ckan.lib.search import SearchError

        # unicode format (decoded from utf8)
        q = c.q = request.params.get('q', u'')
        c.query_error = False

        page = self._page_number()

        # Commenting below parts as it doesn't seem to be used
        # def drill_down_url(alternative_url=None, **by):
        #     return h.add_url_param(alternative_url=alternative_url,
        #                            controller='package', action='search',
        #                            new_params=by)
        #
        # c.drill_down_url = drill_down_url

        # self._set_remove_field_function()
        req_sort_by = request.params.get('sort', None)
        sort_by = req_sort_by if req_sort_by else default_sort_by
        # params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        # The sort_by function seems to not be used anymore

        #  def _sort_by(fields):
        #     """
        #     Sort by the given list of fields.
        #
        #     Each entry in the list is a 2-tuple: (fieldname, sort_order)
        #
        #     eg - [('metadata_modified', 'desc'), ('name', 'asc')]
        #
        #     If fields is empty, then the default ordering is used.
        #     """
        #     params = params_nosort[:]
        #
        #     if fields:
        #         sort_string = ', '.join('%s %s' % f for f in fields)
        #         params.append(('sort', sort_string))
        #     return self._search_url(params, package_type)
        #
        # c.sort_by = _sort_by

        if not sort_by:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        self._set_other_links()

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            # limit = g.datasets_per_page

            fq = additional_fq
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s:"%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            self._set_filters_are_selected_flag()

            try:
                limit = 1 if self._is_facet_only_request() else int(request.params.get('ext_page_size', num_of_items))
            except:
                limit = num_of_items

            c.ext_page_size = limit

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True,
                       'auth_user_obj': c.userobj}

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

            facets = OrderedDict()

            default_facet_titles = get_default_facet_titles()

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            if additional_facets:
                facets.update(additional_facets)

            c.facet_titles = facets

            # TODO Line below to be removed after refactoring
            c.tab = 'all'
            if request.params.get('ext_cod', '0') == '1':
                fq += ' tags:cod'
            self._performing_search(q, fq, facets.keys(), limit, page, sort_by,
                                    search_extras, pager_url, context)

        except SearchError, se:
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.search_facets = {}
            c.page = h.Page(collection=[])
        c.search_facets_limits = {}
        for facet in c.search_facets.keys():
            limit = 1000
            try:
                limit = int(request.params.get('_%s_limit' % facet,
                                               1000))
            except ValueError:
                abort(400, _('Parameter "{parameter_name}" is not '
                             'an integer').format(
                    parameter_name='_%s_limit' % facet
                ))
            c.search_facets_limits[facet] = limit

        maintain.deprecate_context_item(
            'facets',
            'Use `c.search_facets` instead.')

        # return render(self._search_template(package_type))
        full_facet_info = self._prepare_facets_info(c.search_facets, c.fields_grouped, search_extras, c.facet_titles,
                                                    c.count, c.q)
        return full_facet_info

    def _is_facet_only_request(self):
        return request.params.get('ext_only_facets') == 'true'

    def _performing_search(self, q, fq, facet_keys, limit, page, sort_by,
                           search_extras, pager_url, context):
        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': facet_keys,
            # added for https://github.com/OCHA-DAP/hdx-ckan/issues/3340
            'facet.limit': 2000,
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras
        }

        include_private = context.pop('ignore_capacity_check', None)
        if include_private:
            data_dict['include_private'] = include_private

        query = get_action('package_search')(context, data_dict)

        if not query.get('results', None):
            log.warn('No query results found for data_dict: {}. Query dict is: {}. Query time {}'.format(
                str(data_dict), str(query), datetime.datetime.now()))

        c.facets = query['facets']
        c.search_facets = query['search_facets']

        # get_action('populate_related_items_count')(
        #     context, {'pkg_dict_list': query['results']})

        get_action('populate_showcase_items_count')(context, {'pkg_dict_list': query['results']})

        c.page = h.Page(
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

        for dataset in query['results']:
            dataset['hdx_analytics'] = json.dumps(generate_analytics_data(dataset))

        c.page.items = query['results']
        c.sort_by_selected = query['sort']

        c.count = c.item_count = query['count']

        return query

    def _search_template(self):
        return render('search/search.html')

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
        if len(c.fields_grouped) > 0 \
                and ('_show_filters' not in request.params or request.params['_show_filters'] != 'false'):
            c.filters_are_selected = True
        else:
            c.filters_are_selected = False

    # def _set_remove_field_function(self):
    #     '''
    #     Defines the method that is used to generate the URL for a search result
    #     with the specific key(s) removed. For example the function will be used
    #     to generate the link when clicking on a remove filter link.
    #     '''
    #
    #     def remove_field(key, value=None, replace=None):
    #         return h.remove_url_param(key, value=value, replace=replace,
    #                                   controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController',
    #                                   action='search')
    #
    #     c.remove_field = remove_field

    # def _get_named_route(self):
    #     return 'search'

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

        # c.other_links['all'] = h.url_for(named_route, **params) + suffix
        # params_copy = params.copy()
        # params_copy['ext_indicator'] = 1
        # c.other_links['indicators'] = h.url_for(
        #     named_route, **params_copy) + suffix
        # params_copy['ext_indicator'] = 0
        # c.other_links['datasets'] = h.url_for(
        #     named_route, **params_copy) + suffix
        #
        # params_copy = params.copy()
        # params_copy['ext_feature'] = 1
        # c.other_links['features'] = h.url_for(
        #     named_route, **params_copy) + suffix
        #
        # params_copy = params.copy()
        # params_copy['ext_activities'] = 1
        # c.other_links['activities'] = h.url_for(
        #     named_route, **params_copy) + suffix

        #         c.other_links['params'] = params
        c.other_links = {}
        c.other_links['params_noq'] = {k: v for k, v in params.items()
                                       if k not in ['q', '_show_filters', 'id']}
        c.other_links['params_nosort_noq'] = {k: v for k, v in params.items()
                                              if k not in ['sort', 'q', 'id']}
        c.other_links['current_page_url'] = self._current_url()

    def _current_url(self):
        url = h.url_for('search')
        return url

    def _prepare_facets_info(self, existing_facets, selected_facets, search_extras, title_translations, total_count, query):
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

        checkboxes = ['ext_cod', 'ext_indicator', 'ext_subnational']

        for param in checkboxes:
            if param in search_extras:
                result['filters_selected'] = True

        num_of_indicators = 0
        num_of_cods = 0
        num_of_subnational = 0
        for category_key, category_title in title_translations.items():
            item_list = existing_facets.get(category_key, {}).get('items', [])

            # We're only interested in the number of items of the "indicator" facet
            if category_key == 'indicator':
                num_of_indicators = next((item.get('count', 0) for item in item_list if item.get('name', '') == '1'), 0)
            elif category_key == 'subnational':
                num_of_subnational = next((item.get('count', 0) for item in item_list if item.get('name', '') == '1'), 0)
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
                            'name': item_name,
                            'display_name': item.get('display_name', ''),
                            'selected': selected
                        }
                        sorted_item_list.append(new_item)
                        if category_key == 'tags' and new_item['name'] == 'cod':
                            num_of_cods = new_item['count']

                sorted_item_list.sort(key=lambda x: x.get('display_name'))

                result['facets'][category_key] = {
                    'name': category_key,
                    'display_name': category_title,
                    'items': sorted_item_list
                }

        result['num_of_indicators'] = num_of_indicators
        result['num_of_cods'] = num_of_cods
        result['num_of_subnational'] = num_of_subnational
        result['num_of_total_items'] = total_count

        result['query_selected'] = True if query and query.strip() else False

        return result