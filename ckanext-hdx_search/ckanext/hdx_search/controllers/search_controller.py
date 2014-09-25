
import logging, copy
from urllib import urlencode
# import datetime
# import cgi

# from ckanext.hdx_package.helpers import helpers

from pylons import config
# from genshi.template import MarkupTemplate
# from genshi.template.text import NewTextTemplate
from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.maintain as maintain
# import ckan.lib.package_saver as package_saver
# import ckan.lib.i18n as i18n
# import ckan.lib.navl.dictization_functions as dict_fns
# import ckan.lib.accept as accept
import ckan.lib.helpers as h
import ckan.model as model
# import ckan.lib.datapreview as datapreview
# import ckan.lib.plugins
# import ckan.new_authz as new_authz
import ckan.plugins as p



from ckan.common import OrderedDict, _, json, request, c, g, response
# from ckan.controllers.home import CACHE_PARAMETERS

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
# tuplize_dict = logic.tuplize_dict
# clean_dict = logic.clean_dict
# parse_params = logic.parse_params
# flatten_to_string_key = logic.flatten_to_string_key

# CONTENT_TYPES = {
#     'text': 'text/plain;charset=utf-8',
#     'html': 'text/html;charset=utf-8',
#     'json': 'application/json;charset=utf-8',
# }

# lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

from ckan.controllers.package import PackageController

def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]

def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_url(params, package_type=None):
    if not package_type or package_type == 'dataset':
        url = h.url_for(controller='package', action='search')
    else:
        url = h.url_for('{0}_search'.format(package_type))
    return url_with_params(url, params)

def count_types(context, data_dict, tab):
    search = copy.copy(data_dict)
    search['extras']['ext_indicator'] = 1
    indicators = get_action('package_search')(context, search)
    search['extras']['ext_indicator'] = 0
    datasets = get_action('package_search')(context, search)
    if tab == 'all' and len(indicators['results'])>0:
        indicator = [indicators['results'][0]]
    else:
        indicator = None
    return (datasets['count'],indicators['count'], indicator)

def isolate_tags(q, packages, tab):
    import difflib, random
    tags = list()
    features = list()
    for i in packages:
        for p in i['tags']:
            if p['name'] not in tags:
                tags.append(p['name'])
    if tab == 'all':
        if q: 
           selected = difflib.get_close_matches(q,tags,n=3)
        else:
            selected = random.sample(tags, 3)
    else:
        selected = tags
    for s in selected:
        params = [('tags', s)]
        uri = h.url_for(controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController',
                                        action='search')
        url = url_with_params(uri, params)
            
        features.append({'name':s, 'display_name':s, 'url':url})
    return features

class HDXSearchController(PackageController):

    def package_search(self):
        #Redirect to search
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
            return search_url(params, package_type)

        c.sort_by = _sort_by
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            #limit = g.datasets_per_page
            if 'ext_indicator' in search_extras:
                limit = 25
            else:
                limit = 5

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
            elif 'features' in data_dict['extras']:
                c.tab = "features"
            else:
                c.tab = "all"
                #For all tab, only paginate datasets
                data_dict['extras']['ext_indicator'] = 0
                

            query = get_action('package_search')(context, data_dict)
            if c.tab == "all":
                c.features = isolate_tags(q,query['results'], c.tab)
            c.dataset_counts, c.indicator_counts, c.indicator = count_types(context, data_dict, c.tab)
            c.sort_by_selected = query['sort']

            if c.tab == 'features':
                c.page = h.Page(
                    collection=c.features,
                    page=page,
                    url=pager_url,
                    item_count=len(c.features),
                    items_per_page=limit
                )
                c.facets = query['facets']
                c.search_facets = query['search_facets']
                c.page.items = c.features
            else:
                c.page = h.Page(
                    collection=query['results'],
                    page=page,
                    url=pager_url,
                    item_count=query['count'],
                    items_per_page=limit
                )
                c.facets = query['facets']
                c.search_facets = query['search_facets']
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
                                               g.facets_default_number))
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

        #return render(self._search_template(package_type))
        return render('search/search.html')
        
