
import logging
import copy
from urllib import urlencode

from pylons import config
from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.search as search
import sqlalchemy
import ckan.plugins as p
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

from ckan.common import OrderedDict, _, json, request, c, g, response
from pydoc_data.topics import topics

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

from ckan.controllers.package import PackageController


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)



def count_types(context, data_dict, tab):
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
    if tab == 'indicators':
        search['extras'] = {'ext_indicator': 1}
    elif tab == 'datasets':
        search['extras'] = {'ext_indicator': 0}
    result = get_action('package_search')(context, search)
    total = result['count']
    if '1' in result['facets']['extras_indicator']:
        indicator_no = result['facets']['extras_indicator']['1']
    else:
        indicator_no = 0
    dataset_no = total - indicator_no
    if tab == 'all' and len(result['results']) > 0 \
        and result['results'][0] \
        and 'indicator' in result['results'][0] \
        and result['results'][0]['indicator'] == '1':
        indicator = [result['results'][0]]
    else:
        indicator = None
        
    facets = result['facets']
    search_facets = result['search_facets']  
    return (dataset_no, indicator_no, indicator, facets, search_facets)



def package_search(context, data_dict):
    '''
    EDITTED VERSION GETS MORE INFO FROM FACETS
    '''
    # sometimes context['schema'] is None
    schema = (context.get('schema') or
              logic.schema.default_package_search_schema())
    data_dict, errors = _validate(data_dict, schema, context)
    # put the extras back into the data_dict so that the search can
    # report needless parameters
    data_dict.update(data_dict.get('__extras', {}))
    data_dict.pop('__extras', None)
    if errors:
        raise ValidationError(errors)

    model = context['model']
    session = context['session']

    _check_access('package_search', context, data_dict)

    # Move ext_ params to extras and remove them from the root of the search
    # params, so they don't cause and error
    data_dict['extras'] = data_dict.get('extras', {})
    for key in [key for key in data_dict.keys() if key.startswith('ext_')]:
        data_dict['extras'][key] = data_dict.pop(key)

    # check if some extension needs to modify the search params
    for item in p.PluginImplementations(p.IPackageController):
        data_dict = item.before_search(data_dict)

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = 'score desc, metadata_modified desc'

    results = []
    if not abort:
        data_source = 'data_dict' if data_dict.get('use_default_schema',
                                                   False) else 'validated_data_dict'
        # return a list of package ids
        data_dict['fl'] = 'id {0}'.format(data_source)

        # If this query hasn't come from a controller that has set this flag
        # then we should remove any mention of capacity from the fq and
        # instead set it to only retrieve public datasets
        fq = data_dict.get('fq', '')
        if not context.get('ignore_capacity_check', False):
            fq = ' '.join(p for p in fq.split(' ')
                          if not 'capacity:' in p)
            data_dict['fq'] = fq + ' capacity:"public"'

        # Pop these ones as Solr does not need them
        extras = data_dict.pop('extras', None)

        query = search.query_for(model.Package)
        query.run(data_dict)

        # Add them back so extensions can use them on after_search
        data_dict['extras'] = extras

        for package in query.results:
            # get the package object
            package, package_dict = package['id'], package.get(data_source)
            pkg_query = session.query(model.PackageRevision)\
                .filter(model.PackageRevision.id == package)\
                .filter(_and_(
                    model.PackageRevision.state == u'active',
                    model.PackageRevision.current == True
                ))
            pkg = pkg_query.first()

            # if the index has got a package that is not in ckan then
            # ignore it.
            if not pkg:
                log.warning(
                    'package %s in index but not in database' % package)
                continue
            # use data in search index if there
            if package_dict:
                # the package_dict still needs translating when being viewed
                package_dict = json.loads(package_dict)
                if context.get('for_view'):
                    for item in p.PluginImplementations(p.IPackageController):
                        package_dict = item.before_view(package_dict)
                results.append(package_dict)
            else:
                results.append(model_dictize.package_dictize(pkg, context))

        count = query.count
        facets = query.facets
    else:
        count = 0
        facets = {}
        results = []

    search_results = {
        'count': count,
        'facets': facets,
        'results': results,
        'sort': data_dict['sort']
    }

    # Transform facets into a more useful data structure.
    restructured_facets = {}
    for key, value in facets.items():
        restructured_facets[key] = {
            'title': key,
            'items': []
        }
        for key_, value_ in value.items():
            new_facet_dict = {}
            new_facet_dict['name'] = key_
            if key in ('groups', 'organization'):
                group = model.Group.get(key_)
                if group:
                    new_facet_dict['display_name'] = group.display_name
                    new_facet_dict['description'] = group.description
                else:
                    new_facet_dict['display_name'] = key_
                    new_facet_dict['description'] = ''
            elif key == 'license_id':
                license = model.Package.get_license_register().get(key_)
                if license:
                    new_facet_dict['display_name'] = license.title
                else:
                    new_facet_dict['display_name'] = key_
            else:
                new_facet_dict['display_name'] = key_
            new_facet_dict['count'] = value_
            restructured_facets[key]['items'].append(new_facet_dict)
    search_results['search_facets'] = restructured_facets

    # check if some extension needs to modify the search results
    for item in p.PluginImplementations(p.IPackageController):
        search_results = item.after_search(search_results, data_dict)

    # After extensions have had a chance to modify the facets, sort them by
    # display name.
    for facet in search_results['search_facets']:
        search_results['search_facets'][facet]['items'] = sorted(
            search_results['search_facets'][facet]['items'],
            key=lambda facet: facet['display_name'], reverse=True)

    return search_results


def sort_features(features):
    return sorted(features, key=lambda x: x['count'], reverse=True)


def isolate_features(context, facets, q, tab, skip=0, limit=25):
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

    def package_search(self):
        # Redirect to search
        params = request.params.items()
        uri = h.url_for(controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController',
                        action='search')
        url = url_with_params(uri, params)
        redirect(url)

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
        try:
            page = int(request.params.get('page', 1))
        except ValueError, e:
            abort(400, ('"page" parameter must be an integer'))

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']

        def drill_down_url(alternative_url=None, **by):
            return h.add_url_param(alternative_url=alternative_url,
                                   controller='package', action='search',
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='package', action='search')

        c.remove_field = remove_field

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
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return self._search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))

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

            data_dict = {
                'q': q,
                'fq': fq.strip(),
                'facet.field': facets.keys(),
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras
            }

            c.tab = "all"
            if 'ext_indicator' in data_dict['extras']:
                if int(data_dict['extras']['ext_indicator']) == 1:
                    c.tab = "indicators"
                elif int(data_dict['extras']['ext_indicator']) == 0:
                    c.tab = "datasets"
            elif 'ext_feature' in data_dict['extras']:
                c.tab = "features"
            
            self._decide_adding_dataset_criteria(data_dict)

            query = package_search(context, data_dict)
            c.dataset_counts, c.indicator_counts, c.indicator, c.facets, c.search_facets = \
                count_types( context, data_dict, c.tab)
            c.count = c.dataset_counts + c.indicator_counts
            if c.tab == "all":
                c.features = isolate_features(
                    context, query['search_facets'], q, c.tab)

            if c.tab == 'features':
                c.features, c.count = isolate_features(
                    context, query['search_facets'], q, c.tab, ((page - 1) * limit), limit)

            c.sort_by_selected = query['sort']

            if c.tab == 'features':
                c.page = h.Page(
                    collection=c.features,
                    page=page,
                    url=pager_url,
                    item_count=c.count,
                    items_per_page=limit
                )
#                 c.facets = query['facets']
#                 c.search_facets = query['search_facets']
                c.page.items = c.features
            else:
                c.page = h.Page(
                    collection=query['results'],
                    page=page,
                    url=pager_url,
                    item_count=query['count'],
                    items_per_page=limit
                )
#                 c.facets = query['facets']
#                 c.search_facets = query['search_facets']
                c.page.items = query['results']
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
