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
import ckanext.hdx_search.actions.actions as hdx_actions

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

SMALL_NUM_OF_ITEMS = 5
LARGE_NUM_OF_ITEMS = 25


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_for_all(context, data_dict):
    '''This search is independent of the tab in which the user
       currently is.
       The result is used for finding counts for datasets, indicators and totals
    '''
    facet_fields = data_dict.get('facet.field', [])
    facet_fields.append('extras_indicator')
    sort = data_dict.get('sort', None)
    if not sort:
        sort = 'score desc'
    search = {
        'q': data_dict.get('q', None),
        'fq': data_dict.get('fq', None),
        'facet.field': facet_fields,
        'facet.limit': 1000,
        'rows': 10,
        'sort': 'extras_indicator desc, ' + sort,
    }
#     if tab == 'indicators':
#         search['extras'] = {'ext_indicator': 1}
#     elif tab == 'datasets':
#         search['extras'] = {'ext_indicator': 0}
    result = get_action('package_search')(context, search)
    return result


def extract_counts(result):
    ''' Extracts the counts from a search_for_all() result '''

    total = result['count']
    if '1' in result['facets']['extras_indicator']:
        indicator_no = result['facets']['extras_indicator']['1']
    else:
        indicator_no = 0
    dataset_no = total - indicator_no
    return (dataset_no, indicator_no)


def extract_one_indicator(result):
    ''' Extracts the first indicator from a search_for_all() result '''

    if len(result['results']) > 0 \
            and result['results'][0] \
            and 'indicator' in result['results'][0] \
            and result['results'][0]['indicator'] == '1':
        indicator = [result['results'][0]]
    else:
        indicator = None
    return indicator


def sort_features(features):
    return sorted(features, key=lambda x: x['count'], reverse=True)


@maintain.deprecated('Showing features in search results has been deprecated')
def isolate_features(context, facets, q, tab, skip=0, limit=25):
    ''' Showing features in search results has been deprecated.
        Deprecated since 25.01.2015 - hdx 0.6.5
    '''
    import difflib
    import random

    try:
        all_topics = get_action('tag_list')(
            context, {'vocabulary_id': 'Topics'})
    except NotFound, e:
        all_topics = []
        log.error('ERROR getting vocabulary named Topics: %r' %
                  str(e.extra_msg))

    extract = dict()
    tags = list()
    features = list()
    for o in facets['organization']['items']:
        tags.append(o['name'])
        extract[o['name']] = {'name': o['name'], 'display_name': o['display_name'],
                              'url': h.url_for(controller='organization', action='read', id=o['name']), 'description': o['description'], 'feature_type': 'organization', 'count': o['count']}

    for p in facets['vocab_Topics']['items']:
        tags.append(p['name'])
        extract[p['name']] = {'name': p['name'], 'display_name': p['name'],
                              'url': h.url_for(controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search', vocab_Topics=p['name']), 'description': '', 'last_update': '', 'feature_type': 'topic', 'count': p['count']}

    for g in facets['groups']['items']:
        tags.append(g['name'])
        extract[g['name']] = {'name': g['name'], 'display_name': g['display_name'],
                              'url': h.url_for(controller='group', action='read', id=g['name']), 'description': g['description'], 'feature_type': 'country', 'count': g['count']}

    if tab == 'all' and len(tags) > 3:
        if q:
            selected = difflib.get_close_matches(q, tags, cutoff=0.1, n=3)
        else:
            selected = random.sample(tags, 3)
    else:
        selected = tags
    for s in selected:
        features.append(extract[s])
    if tab == 'features':
        feature_list = sort_features(features)
        return (feature_list[skip:skip + limit], len(features))
    return features


class HDXSearchController(PackageController):

    def search(self):
        from ckan.lib.search import SearchError

        package_type = self._guess_package_type()

        if package_type == 'search':
            package_type = 'dataset'

        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # unicode format (decoded from utf8)
        q = c.q = request.params.get('q', u'')
        c.query_error = False

        page = self._page_number()

        params_nopage = self._params_nopage()

        # Commenting below parts as it doesn't seem to be used
        # def drill_down_url(alternative_url=None, **by):
        #     return h.add_url_param(alternative_url=alternative_url,
        #                            controller='package', action='search',
        #                            new_params=by)
        #
        # c.drill_down_url = drill_down_url

        self._set_remove_field_function()

        sort_by = request.params.get('sort', None)
        params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        def _sort_by(fields):
            """
            Sort by the given list of fields.

            Each entry in the list is a 2-tuple: (fieldname, sort_order)

            eg - [('metadata_modified', 'desc'), ('name', 'asc')]

            If fields is empty, then the default ordering is used.
            """
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join('%s %s' % f for f in fields)
                params.append(('sort', sort_string))
            return self._search_url(params, package_type)

        c.sort_by = _sort_by
        if not sort_by:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return self._search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))
        self._set_other_links()

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            #limit = g.datasets_per_page

            fq = ''
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

            limit = self._allowed_num_of_items(search_extras)

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True,
                       'auth_user_obj': c.userobj}

            if package_type and package_type != 'dataset':
                # Only show datasets of this particular type
                fq += ' +dataset_type:{type}'.format(type=package_type)
            else:
                # Unless changed via config options, don't show non standard
                # dataset types on the default search page
                if not asbool(config.get('ckan.search.show_all_types', 'False')):
                    fq += ' +dataset_type:dataset'

            facets = OrderedDict()

            default_facet_titles = {
                'organization': _('Organizations'),
                'groups': _('Groups'),
                'tags': _('Tags'),
                'res_format': _('Formats'),
                'license_id': _('Licenses'),
            }

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            c.facet_titles = facets

            self._which_tab_is_selected(search_extras)
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

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        # return render(self._search_template(package_type))
        return self._search_template()

    def _which_tab_is_selected(self, search_extras):
        c.tab = 'all'
        if 'ext_indicator' in search_extras:
            if int(search_extras['ext_indicator']) == 1:
                c.tab = 'indicators'
            elif int(search_extras['ext_indicator']) == 0:
                c.tab = 'datasets'
        elif 'ext_feature' in search_extras:
            c.tab = 'features'
        elif 'ext_activities' in search_extras:
            c.tab = 'activities'

    def _performing_search(self, q, fq, facet_keys, limit, page, sort_by,
                           search_extras, pager_url, context):
        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': facet_keys,
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras
        }

        self._decide_adding_dataset_criteria(data_dict)

        query = hdx_actions.package_search(context, data_dict)

        if not query.get('results', None):
            log.warn('No query results found for data_dict: {}. Query dict is: {}. Query time {}'.format(
                str(data_dict), str(query), datetime.datetime.now()))

        all_result = search_for_all(context, data_dict)
        c.dataset_counts, c.indicator_counts = extract_counts(all_result)

        c.count = c.dataset_counts + c.indicator_counts
        if not c.count:
            log.warn('Dataset counts are zero for data_dict: {}. all_results dict is: {}. Query time {}'.format(
                str(data_dict), str(query), datetime.datetime.now()))

        if c.tab == "all":
            # c.features = isolate_features(
            #     context, query['search_facets'], q, c.tab)
            c.indicator = extract_one_indicator(all_result)
            if c.indicator:
                get_action('populate_related_items_count')(
                    context, {'pkg_dict_list': c.indicator})
            c.facets = all_result['facets']
            c.search_facets = all_result['search_facets']
        else:
            c.facets = query['facets']
            c.search_facets = query['search_facets']

#             if c.tab == 'features':
#                 c.features, c.count = isolate_features(
# context, query['search_facets'], q, c.tab, ((page - 1) * limit), limit)


#             if c.tab == 'features':
#                 c.page = h.Page(
#                     collection=c.features,
#                     page=page,
#                     url=pager_url,
#                     item_count=c.count,
#                     items_per_page=limit
#                 )
# c.facets = query['facets']
# c.search_facets = query['search_facets']
#                 c.page.items = c.features
#             else:
#                 c.page = h.Page(
#                     collection=query['results'],
#                     page=page,
#                     url=pager_url,
#                     item_count=query['count'],
#                     items_per_page=limit
#                 )
# c.facets = query['facets']
# c.search_facets = query['search_facets']
#                 c.page.items = query['results']

        get_action('populate_related_items_count')(
            context, {'pkg_dict_list': query['results']})

        c.page = h.Page(
            collection=query['results'],
            page=page,
            url=pager_url,
            item_count=query['count'],
            items_per_page=limit
        )
        c.page.items = query['results']
        c.sort_by_selected = query['sort']

        return query, all_result

    def _decide_adding_dataset_criteria(self, data_dict):
        # For all tab, only paginate datasets
        if c.tab == "all":
            data_dict['extras']['ext_indicator'] = 0

    def _allowed_num_of_items(self, search_extras):
        if 'ext_indicator' in search_extras or 'ext_feature' in search_extras:
            return LARGE_NUM_OF_ITEMS
        else:
            return SMALL_NUM_OF_ITEMS

    def _search_template(self):
        return render('search/search.html')

    def _search_url(self, params, package_type=None):
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

    def _set_remove_field_function(self):
        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')

        c.remove_field = remove_field

    def _get_named_route(self):
        return 'search'

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
                           'vocab_Topics', 'license_id', 'groups', 'res_format', '_show_filters'];
        named_route = self._get_named_route()
        params = {}

        for k, v in request.params.items():
            if k in url_param_list:
                if k in params:
                    params[k].append(v)
                else:
                    params[k] = [v]

        if other_params_dict:
            params.update(other_params_dict)

        c.other_links = {}
        c.other_links['all'] = h.url_for(named_route, **params) + suffix
        params_copy = params.copy()
        params_copy['ext_indicator'] = 1
        c.other_links['indicators'] = h.url_for(
            named_route, **params_copy) + suffix
        params_copy['ext_indicator'] = 0
        c.other_links['datasets'] = h.url_for(
            named_route, **params_copy) + suffix

        params_copy = params.copy()
        params_copy['ext_feature'] = 1
        c.other_links['features'] = h.url_for(
            named_route, **params_copy) + suffix

        params_copy = params.copy()
        params_copy['ext_activities'] = 1
        c.other_links['activities'] = h.url_for(
            named_route, **params_copy) + suffix

#         c.other_links['params'] = params
        c.other_links['params_noq'] = {k: v for k, v in params.items()
                                       if k not in ['q', '_show_filters', 'id']}
        c.other_links['params_nosort_noq'] = {k: v for k, v in params.items()
                                              if k not in ['sort', 'q', 'id']}
