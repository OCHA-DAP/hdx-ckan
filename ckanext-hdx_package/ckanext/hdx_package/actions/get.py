'''
Created on Sep 02, 2015

@author: alexandru-m-g
'''

import json
import logging
import os

import dateutil.parser
import sqlalchemy
from botocore.exceptions import ClientError
from paste.deploy.converters import asbool
from pylons import config

import ckan.authz as authz
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions
import ckan.lib.plugins as lib_plugins
import ckan.lib.search as search
import ckan.logic as logic
import ckan.logic.action.get as logic_get
import ckan.logic.schema
import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckanext.hdx_package.helpers.caching as pkg_caching
import ckanext.hdx_package.helpers.freshness_calculator as freshness
import ckanext.hdx_package.helpers.helpers as helpers
import ckanext.hdx_theme.util.jql as jql
import ckanext.hdx_users.controllers.mailer as hdx_mailer

from ckan.common import _, c
from ckan.lib import uploader
from ckanext.hdx_package.helpers.extras import get_extra_from_dataset
from ckanext.hdx_package.helpers.geopreview import GIS_FORMATS
from ckanext.hdx_package.helpers.resource_format import resource_format_autocomplete, guess_format_from_extension
from ckanext.hdx_package.helpers.resource_grouping import ResourceGrouping
from ckanext.hdx_package.helpers.tag_recommender import TagRecommender, TagRecommenderTest
from ckanext.hdx_search.actions.actions import hdx_get_package_showcase_id_list
from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING
from ckanext.hdx_theme.helpers.json_transformer import get_obj_from_json_in_dict
from ckanext.s3filestore.helpers import generate_temporary_link

_validate = ckan.lib.navl.dictization_functions.validate
ValidationError = logic.ValidationError
NotFound = ckan.logic.NotFound
NotAuthorized = ckan.logic.NotAuthorized
_check_access = logic.check_access
log = logging.getLogger(__name__)
get_action = logic.get_action
base_abort = base.abort
get_or_bust = logic.get_or_bust

# _FOOTER_CONTACT_CONTRIBUTOR = hdx_mailer.FOOTER #+ '<small><p>Note: <a href="mailto:hdx@un.org">hdx@un.org</a> is blind copied on this message so that we are aware of the initial correspondence related to datasets on the HDX site. Please contact us directly should you need further support.</p></small>'
# _FOOTER_GROUP_MESSAGE = hdx_mailer.FOOTER

GEODATA_FORMATS = GIS_FORMATS + ['shapefile', 'shapefiles', 'dem', 'feature server', 'feature service', 'file geodatabase',
                   'garmin img', 'gdb', 'geodatabase', 'geonode', 'geotiff', 'map server', 'map service', 'obf',
                   'topojson', 'wkt', 'zipped gdb', 'zipped geodatabase', 'zipped geopackage', 'zipped geotiff',
                   'zipped grd', 'zipped img', 'zipped kml', 'zipped raster', 'zipped shapefiles']


@logic.side_effect_free
def hdx_resource_id_list(context, data_dict):
    logic.check_access('hdx_resource_id_list', context, data_dict)

    q = sqlalchemy.text("SELECT id FROM resource where state='active' ORDER BY id;")
    result = model.Session.connection().execute(q, entity_id=id)
    ids = [row[0] for row in result]
    return ids


@logic.side_effect_free
def package_search(context, data_dict):
    '''
    THIS IS A COPY OF THE package_search() ACTION FROM CORE CKAN.

    IT'S CHANGED TO:

    *  RETURN MORE DATA FROM THE SOLR QUERY (collapse/expand)
    *  HAVE A DIFFERENT DEFAULT SORTING
    *  TO SET DIFFERENT DEFAULT SOLR QUERY PARAMS

    Searches for packages satisfying a given search criteria.

    This action accepts solr search query parameters (details below), and
    returns a dictionary of results, including dictized datasets that match
    the search criteria, a search count and also facet information.

    **Solr Parameters:**

    For more in depth treatment of each paramter, please read the `Solr
    Documentation <http://wiki.apache.org/solr/CommonQueryParameters>`_.

    This action accepts a *subset* of solr's search query parameters:


    :param q: the solr query.  Optional.  Default: ``"*:*"``
    :type q: string
    :param fq: any filter queries to apply.  Note: ``+site_id:{ckan_site_id}``
        is added to this string prior to the query being executed.
    :type fq: string
    :param sort: sorting of the search results.  Optional.  Default:
        ``'relevance asc, metadata_modified desc'``.  As per the solr
        documentation, this is a comma-separated string of field names and
        sort-orderings.
    :type sort: string
    :param rows: the number of matching rows to return. There is a hard limit
        of 1000 datasets per query.
    :type rows: int
    :param start: the offset in the complete result for where the set of
        returned datasets should begin.
    :type start: int
    :param facet: whether to enable faceted results.  Default: ``True``.
    :type facet: string
    :param facet.mincount: the minimum counts for facet fields should be
        included in the results.
    :type facet.mincount: int
    :param facet.limit: the maximum number of values the facet fields return.
        A negative value means unlimited. This can be set instance-wide with
        the :ref:`search.facets.limit` config option. Default is 50.
    :type facet.limit: int
    :param facet.field: the fields to facet upon.  Default empty.  If empty,
        then the returned facet information is empty.
    :type facet.field: list of strings
    :param include_drafts: if ``True``, draft datasets will be included in the
        results. A user will only be returned their own draft datasets, and a
        sysadmin will be returned all draft datasets. Optional, the default is
        ``False``.
    :type include_drafts: boolean
    :param include_private: if ``True``, private datasets will be included in
        the results. Only private datasets from the user's organizations will
        be returned and sysadmins will be returned all private datasets.
        Optional, the default is ``False``.
    :param use_default_schema: use default package schema instead of
        a custom schema defined with an IDatasetForm plugin (default: False)
    :type use_default_schema: bool


    The following advanced Solr parameters are supported as well. Note that
    some of these are only available on particular Solr versions. See Solr's
    `dismax`_ and `edismax`_ documentation for further details on them:

    ``qf``, ``wt``, ``bf``, ``boost``, ``tie``, ``defType``, ``mm``


    .. _dismax: http://wiki.apache.org/solr/DisMaxQParserPlugin
    .. _edismax: http://wiki.apache.org/solr/ExtendedDisMax


    **Examples:**

    ``q=flood`` datasets containing the word `flood`, `floods` or `flooding`
    ``fq=tags:economy`` datasets with the tag `economy`
    ``facet.field=["tags"] facet.limit=10 rows=0`` top 10 tags

    **Results:**

    The result of this action is a dict with the following keys:

    :rtype: A dictionary with the following keys
    :param count: the number of results found.  Note, this is the total number
        of results found, not the total number of results returned (which is
        affected by limit and row parameters used in the input).
    :type count: int
    :param results: ordered list of datasets matching the query, where the
        ordering defined by the sort parameter used in the query.
    :type results: list of dictized datasets.
    :param facets: DEPRECATED.  Aggregated information about facet counts.
    :type facets: DEPRECATED dict
    :param search_facets: aggregated information about facet counts.  The outer
        dict is keyed by the facet field name (as used in the search query).
        Each entry of the outer dict is itself a dict, with a "title" key, and
        an "items" key.  The "items" key's value is a list of dicts, each with
        "count", "display_name" and "name" entries.  The display_name is a
        form of the name that can be used in titles.
    :type search_facets: nested dict of dicts.

    An example result: ::

     {'count': 2,
      'results': [ { <snip> }, { <snip> }],
      'search_facets': {u'tags': {'items': [{'count': 1,
                                             'display_name': u'tolstoy',
                                             'name': u'tolstoy'},
                                            {'count': 2,
                                             'display_name': u'russian',
                                             'name': u'russian'}
                                           ]
                                 }
                       }
     }

    **Limitations:**

    The full solr query language is not exposed, including.

    fl
        The parameter that controls which fields are returned in the solr
        query.
        fl can be  None or a list of result fields, such as ['id', 'extras_custom_field'].
        if fl = None, datasets are returned as a list of full dictionary.
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
    user = context.get('user')

    _check_access('package_search', context, data_dict)

    # Move ext_ params to extras and remove them from the root of the search
    # params, so they don't cause and error
    data_dict['extras'] = data_dict.get('extras', {})
    for key in [key for key in data_dict.keys() if key.startswith('ext_')]:
        data_dict['extras'][key] = data_dict.pop(key)

    # check if some extension needs to modify the search params
    try:
        for item in plugins.PluginImplementations(plugins.IPackageController):
            data_dict = item.before_search(data_dict)
    except NotFound, e:
        base_abort(404, 'Wrong parameter value in url')

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = 'score desc, ' + DEFAULT_SORTING

    results = []
    if not abort:
        if asbool(data_dict.get('use_default_schema')):
            data_source = 'data_dict'
        else:
            data_source = 'validated_data_dict'
        data_dict.pop('use_default_schema', None)

        result_fl = data_dict.get('fl')
        if not result_fl:
            data_dict['fl'] = 'id {0}'.format(data_source)
        else:
            data_dict['fl'] = ' '.join(result_fl)

        # Remove before these hit solr FIXME: whitelist instead
        include_private = asbool(data_dict.pop('include_private', False))
        include_drafts = asbool(data_dict.pop('include_drafts', False))
        data_dict.setdefault('fq', '')
        if not include_private:
            data_dict['fq'] = '+capacity:public ' + data_dict['fq']
        if include_drafts:
            data_dict['fq'] += ' +state:(active OR draft)'

        # Pop these ones as Solr does not need them
        extras = data_dict.pop('extras', None)

        # enforce permission filter based on user
        if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
            labels = None
        else:
            labels = lib_plugins.get_permission_labels(
                ).get_user_dataset_labels(context['auth_user_obj'])

        # ADDED BY HDX - setting default query params
        _set_default_value_if_needed('qf', data_dict)
        _set_default_value_if_needed('tie', data_dict)
        _set_default_value_if_needed('bf', data_dict)
        # END ADDED BY HDX

        query = search.query_for(model.Package)
        query.run(data_dict, permission_labels=labels)

        # Add them back so extensions can use them on after_search
        data_dict['extras'] = extras

        if result_fl:
            for package in query.results:
                if package.get('extras'):
                    package.update(package['extras'] )
                    package.pop('extras')
                results.append(package)
        else:
            for package in query.results:
                # get the package object
                package_dict = package.get(data_source)
                ## use data in search index if there
                if package_dict:
                    # the package_dict still needs translating when being viewed
                    package_dict = json.loads(package_dict)
                    if context.get('for_view'):
                        for item in plugins.PluginImplementations(
                                plugins.IPackageController):
                            package_dict = item.before_view(package_dict)
                    results.append(package_dict)
                else:
                    log.error('No package_dict is coming from solr for package '
                              'id %s', package['id'])

        count = query.count
        facets = query.facets
        facet_ranges = query.raw_response.get('facet_counts', {}).get('facet_ranges', {})
        facet_pivot = query.raw_response.get('facet_counts', {}).get('facet_pivot', {})
        facet_queries = query.raw_response.get('facet_counts', {}).get('facet_queries', {})
        expanded = query.raw_response.get('expanded', {})

    else:
        count = 0
        facets = {}
        facet_ranges = {}
        facet_pivot = {}
        facet_queries = {}
        results = []
        expanded = {}

    search_results = {
        'count': count,
        'facets': facets,
        'expanded': expanded,
        'results': results,
        'sort': data_dict['sort']
    }

    # create a lookup table of group name to title for all the groups and
    # organizations in the current search's facets.
    group_names = []
    for field_name in ('groups', 'organization'):
        group_names.extend(facets.get(field_name, {}).keys())

    groups = (session.query(model.Group.name, model.Group.title)
                    .filter(model.Group.name.in_(group_names))
                    .all()
              if group_names else [])
    group_titles_by_name = dict(groups)

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
                display_name = group_titles_by_name.get(key_, key_)
                display_name = display_name if display_name and display_name.strip() else key_
                new_facet_dict['display_name'] = display_name
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
    for item in plugins.PluginImplementations(plugins.IPackageController):
        search_results = item.after_search(search_results, data_dict)

    # After extensions have had a chance to modify the facets, sort them by
    # display name.
    for facet in search_results['search_facets']:
        search_results['search_facets'][facet]['items'] = sorted(
            search_results['search_facets'][facet]['items'],
            key=lambda facet: facet['display_name'], reverse=True)

    # ranges and pivot facets shouldn't be sorted so we process them after the sorting was done
    _process_facet_ranges(restructured_facets, facet_ranges)
    pivot_dict = {}
    _process_pivot_facets(restructured_facets, pivot_dict, facet_pivot)
    search_results['facet_pivot'] = pivot_dict
    _process_facet_queries(restructured_facets, facet_queries)
    search_results['facet_queries'] = facet_queries

    _remove_unwanted_dataset_properties(search_results.get('results'))

    return search_results


def _set_default_value_if_needed(query_param, data_dict):
    if not data_dict.get(query_param):
        default_value = config.get('hdx.solr.query.{}'.format(query_param))
        if default_value:
            data_dict[query_param] = default_value


def _process_facet_ranges(restructured_facets, facet_ranges):
    for facet_name, facet_dict in facet_ranges.items():
        restructured_facets[facet_name] = {
            'title': facet_name,
            'type': 'range',
            'items': []
        }
        new_facet_dict = None
        for i, item in enumerate(facet_dict.get('counts', [])):
            if i % 2 == 0:
                new_facet_dict = {'name': item, 'display_name': item}
            else:
                new_facet_dict['count'] = item
                restructured_facets[facet_name]['items'].append(new_facet_dict)


def _process_pivot_facets(restructured_facets, pivot_dict, facet_pivot):
    restructured_facets['pivot'] = {}
    for facet_name, first_level_list in facet_pivot.items():
        restructured_facets['pivot'][facet_name] = {
            'title': facet_name,
            'type': 'pivot',
            'items': []
        }
        pivot_dict[facet_name] = {}
        facet_category = restructured_facets['pivot'][facet_name]
        for f in first_level_list:
            item = _create_facet_item(f)
            facet_category['items'].append(item)

            pivot_dict[facet_name][item['name']] = {
                'count': f.get('count'),
            }
            if f.get('pivot'):
                item['items'] = []
                for f2 in f.get('pivot'):
                    item2 = _create_facet_item(f2)
                    item['items'].append(item2)
                    pivot_dict[facet_name][item['name']][item2['name']] = {
                        'count': f2.get('count')
                    }

            elif f.get('queries'):
                item['items'] = _generate_facet_queries_list(f.get('queries'))
                for key, value in f.get('queries').items():
                    pivot_dict[facet_name][item['name']][key] = {
                        'count': value
                    }


def _create_facet_item(solr_item):
    value = solr_item.get('value')
    item = {
        'count': solr_item.get('count'),
        'name': value,
        'display_name': value
    }
    return item


def _process_facet_queries(restructured_facets, facet_queries):
    restructured_facets['queries'] = _generate_facet_queries_list(facet_queries)


def _generate_facet_queries_list(query_dict):
    return [
        {
            'count': value,
            'name': key,
            'display_name': key
        }
    for key, value in query_dict.items()]


def _remove_unwanted_dataset_properties(dataset_list):
    if dataset_list:
        for dataset_dict in dataset_list:
            dataset_dict.pop('maintainer_email', None)


@logic.side_effect_free
def resource_show(context, data_dict):
    '''
    Wraps the default resource_show and adds additional information like:
    resource size (for uploaded files) and resource revision timestamp
    '''
    resource_dict = logic_get.resource_show(context, data_dict)

    # TODO: check if needed. Apparently the default resource_show() action anyway calls package_show
    _additional_hdx_resource_show_processing(context, resource_dict)

    return resource_dict


def _additional_hdx_resource_show_processing(context, resource_dict):
    # if _should_manually_load_property_value(context, resource_dict, 'size'):
    #     resource_dict['size'] = _get_resource_filesize(resource_dict)
    # if _should_manually_load_property_value(context, resource_dict, 'revision_last_updated'):
    #     resource_dict['revision_last_updated'] = _get_resource_revison_timestamp(resource_dict)
    if _should_manually_load_property_value(context, resource_dict, 'hdx_rel_url'):
        resource_dict['hdx_rel_url'] = _get_resource_hdx_relative_url(resource_dict)

    if not resource_dict.get('last_modified'):
        resource_dict['last_modified'] = resource_dict['metadata_modified']

    if config.get('hdx.apihighways.enabled') == 'true':
        resource_dict['apihighways_id'] = _get_resource_id_apihighways(resource_dict.get('id'))
        if resource_dict['apihighways_id']:
            resource_dict['apihighways_url'] = config.get('hdx.apihighways.baseurl') + resource_dict.get('apihighways_id')
    else:
        if 'apihighways_id' in resource_dict:
            del resource_dict['apihighways_id']
        if 'apihighways_url' in resource_dict:
            del resource_dict['apihighways_url']
    if resource_dict.get('url'):
        resource_dict['download_url'] = resource_dict.get('url')

@logic.side_effect_free
def package_show(context, data_dict):
    '''
    Wraps the default package_show and adds additional information to the resources:
    resource size (for uploaded files) and resource revision timestamp
    '''
    # data_dict['include_tracking'] = True
    package_dict = logic_get.package_show(context, data_dict)

    _additional_hdx_package_show_processing(context, package_dict)

    return package_dict


def _additional_hdx_package_show_processing(context, package_dict, just_for_reindexing=False):
    # added because showcase schema validation is generating "ckan.lib.navl.dictization_functions.Missing"
    if 'tracking_summary' in package_dict and not package_dict.get('tracking_summary'):
        del package_dict['tracking_summary']
    # this shouldn't be executed from showcases
    if package_dict.get('type') == 'dataset' and not context.get('no_compute_extra_hdx_show_properties'):

        for resource_dict in package_dict.get('resources', []):
            _additional_hdx_resource_show_processing(context, resource_dict)

        # downloads_list = (res['tracking_summary']['total'] for res in package_dict.get('resources', []) if
        #                   res.get('tracking_summary', {}).get('total'))
        # package_dict['total_res_downloads'] = sum(downloads_list)

        if _should_manually_load_property_value(context, package_dict, 'total_res_downloads'):
            total_res_downloads = jql.downloads_per_dataset_all_cached().get(package_dict['id'], 0)
            log.debug('Dataset {} has {} downloads'.format(package_dict['id'], total_res_downloads))
            package_dict['total_res_downloads'] = total_res_downloads

        if _should_manually_load_property_value(context, package_dict, 'pageviews_last_14_days'):
            pageviews_last_14_days = jql.pageviews_per_dataset_last_14_days_cached().get(package_dict['id'], 0)
            log.debug(
                'Dataset {} has {} page views in the last 14 days'.format(package_dict['id'], pageviews_last_14_days))
            package_dict['pageviews_last_14_days'] = pageviews_last_14_days

        if _should_manually_load_property_value(context, package_dict, 'has_quickcharts'):
            package_dict['has_quickcharts'] = False
            for resource_dict in package_dict.get('resources', []):
                resource_views = get_action('resource_view_list')(context, {'id': resource_dict['id']}) or []
                for view in resource_views:
                    if view.get("view_type") == 'hdx_hxl_preview':
                        package_dict['has_quickcharts'] = True
                        break

        if _should_manually_load_property_value(context, package_dict, 'has_geodata'):
            package_dict['has_geodata'] = False
            for resource_dict in package_dict.get('resources', []):
                if resource_dict.get('format') in GEODATA_FORMATS:
                    package_dict['has_geodata'] = True
                    break

        if _should_manually_load_property_value(context, package_dict, 'has_showcases'):
            package_dict['has_showcases'] = False
            package_dict['num_of_showcases'] = 0
            num_of_showcases = len(hdx_get_package_showcase_id_list(context, {'package_id': package_dict['id']}))
            if num_of_showcases > 0:
                package_dict['has_showcases'] = True
                package_dict['num_of_showcases'] = num_of_showcases

        if _should_manually_load_property_value(context, package_dict, 'extras_qa_completed'):
            qa_completed = tk.get_converter('hdx_assume_missing_is_true')(package_dict.get('extras_qa_completed'), {})
            qa_completed = tk.get_converter('boolean_validator')(qa_completed, {})
            package_dict['extras_qa_completed'] = qa_completed

        if _should_manually_load_property_value(context, package_dict, 'last_modified'):
            if get_extra_from_dataset('is_requestdata_type', package_dict):
                package_dict['last_modified'] = package_dict.get('metadata_modified')
            else:
                package_dict['last_modified'] = None
                all_dates = [dateutil.parser.parse(r.get('last_modified'))
                             for r in package_dict.get('resources', [])
                             if r.get('last_modified')]
                if all_dates:
                    package_dict['last_modified'] = max(all_dates).isoformat()

        freshness_calculator = freshness.get_calculator_instance(package_dict, None)
        if _should_manually_load_property_value(context, package_dict, 'due_date'):
            package_dict.pop('due_date', None)
            package_dict.pop('overdue_date', None)
            package_dict.pop('delinquent_date', None)
            freshness_calculator.populate_with_date_ranges()

        if not just_for_reindexing:
            member_list = get_action('hdx_member_list')(context, {'org_id': package_dict.get('owner_org')})
            if member_list and not member_list.get('is_member'):
                del package_dict['maintainer_email']

            # Freshness should be computed after the last_modified field
            freshness_calculator.populate_with_freshness()

            __compute_resource_grouping(context, package_dict)


def __compute_resource_grouping(context, package_dict):
    if context.get('use_cache', True):
        ResourceGrouping(package_dict).populate_computed_groupings()


@logic.side_effect_free
def shape_info_show(context, data_dict):
    dataset_dict = get_action('package_show')(context, data_dict)

    shape_infos = [{r.get('name'): json.loads(r.get('shape_info'))} for r in dataset_dict.get('resources', []) if r.get('shape_info')]

    return shape_infos


# def _check_dataset_preview_selected_value(context, data_dict, property_name):
#     use_cache = context.get('use_cache', True)
#     current_value = data_dict.get(property_name) not in (True, False)
#
#     return use_cache is False and current_value

def _should_manually_load_property_value(context, data_dict, property_name):
    '''
    IF use_cache is false OR if the property doesn't exist in the dict we need to load it manually
    :param context:
    :type context: dict
    :param data_dict: the resource_dict for example ( could be the dataset_dict for other properties in the future )
    :type data_dict: dict
    :param property_name: the property for which we need to decide if we need to manually load
    :type property_name: str
    :return: True if we need to load manually, otherwise False
    :rtype: bool
    '''
    use_cache = context.get('use_cache', True)
    current_value = data_dict.get(property_name)

    return not (use_cache and current_value is not None)


@logic.side_effect_free
def package_show_edit(context, data_dict):
    '''A package_show action for editing a package and resources.'''

    # Requires use_cache and for_edit in the context so resource urls for file
    # uploads don't include the full qualified url path.
    context['use_cache'] = False
    context['for_edit'] = True

    return package_show(context, data_dict)


@logic.side_effect_free
def package_qa_checklist_show(context, data_dict):
    dataset_dict = get_action('package_show')(context, data_dict)

    dataset_qa_checklist = get_obj_from_json_in_dict(dataset_dict, 'qa_checklist') or {}

    qa_checklist_completed = dataset_dict.get('qa_checklist_completed')
    if qa_checklist_completed:
        dataset_qa_checklist['checklist_complete'] = True
        dataset_qa_checklist.pop('metadata', None)
        dataset_qa_checklist.pop('dataProtection', None)
        dataset_qa_checklist.pop('resources', None)
    else:
        for r in dataset_dict.get('resources', []):
            r_qa_checklist = get_obj_from_json_in_dict(r, 'qa_checklist')
            if r_qa_checklist:
                qa_res_list = dataset_qa_checklist.get('resources', [])
                r_qa_checklist['id'] = r['id']
                qa_res_list.append(r_qa_checklist)
                dataset_qa_checklist['resources'] = qa_res_list

    return dataset_qa_checklist


def _get_resource_filesize(resource_dict):
    if resource_dict.get('url_type') == 'upload':
        value = None
        try:
            upload = uploader.ResourceUpload(resource_dict)
            value = os.path.getsize(upload.get_path(resource_dict['id']))
        except Exception as e:
            log.debug(u'Error occurred trying to get the size for resource {}: {}'.format(resource_dict.get('name', ''),
                                                                                         str(e)))
        return value
    return None


def _get_resource_revison_timestamp(resource_dict):
    '''
    :param resource_dict: the dictized resource information
    :type resource_dict: dict
    :return: timestamp of the revision of the resource
    :rtype: str
    '''
    revision_id = resource_dict.get('revision_id')
    if revision_id:
        # context = {'model': model, 'session': model.Session}
        timestamp = model.Session.query(model.Revision.timestamp).filter(model.Revision.id == revision_id).first()
        if timestamp:
            return timestamp[0].isoformat()
        # revision_dict = logic.get_action('revision_show')(context, {'id': revision_id})
        # return revision_dict.get('timestamp')
    return None


def _get_resource_hdx_relative_url(resource_dict):
    if helpers.is_ckan_domain(resource_dict.get('url', '')):
        return helpers.make_url_relative(resource_dict.get('url', ''))

    return resource_dict.get('url', '')


def _get_resource_id_apihighways(resource_id):
    ah_dict = pkg_caching.cached_resource_id_apihighways()
    if ah_dict:
        for res in ah_dict.get('data'):
            _id = res.get('attributes', {}).get('metadata', {})[0].get('attributes', {}).get('info', {}).get('resourceId', None)
            if _id and resource_id == _id:
                return res.get('id')
    return None

@logic.side_effect_free
def package_validate(context, data_dict):
    model = context['model']
    id = data_dict.get("id")

    pkg = model.Package.get(id) if id else None

    if pkg is None:
        action = 'package_create'
        type = data_dict.get('type', 'dataset')
    else:
        action = 'package_update'
        type = pkg.type
        context["package"] = pkg
        data_dict["id"] = pkg.id

    logic.check_access(action, context, data_dict)
    package_plugin = lib_plugins.lookup_package_plugin(type)

    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.create_package_schema() if action == 'package_create' \
            else package_plugin.update_package_schema()

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, action)

    if errors:
        raise ValidationError(errors)

    if 'groups_list' in data:
        del data['groups_list']
    return data


@logic.side_effect_free
def hdx_member_list(context, data_dict):
    result = {}
    try:
        org_members = get_action('member_list')(context, {'id': data_dict.get('org_id'), 'object_type': 'user'})
    except Exception, e:
        return None

    admins = []
    editors = []
    members = []
    user_obj = context.get('auth_user_obj')
    is_member = user_obj and user_obj.sysadmin

    for m in org_members:
        if m[2] == 'Admin':
            admins.append(m[0])
        if m[2] == 'Editor':
            editors.append(m[0])
        if m[2] == 'Member':
            members.append(m[0])
        if not is_member and user_obj:
            if m[0] == user_obj.id:
                is_member = True
    result['is_member'] = is_member
    result['admins_counter'] = len(admins)
    result['members_counter'] = len(members)
    result['editors_counter'] = len(editors)
    result['total_counter'] = len(org_members)
    result['admins'] = admins
    result['editors'] = editors
    result['members'] = members
    result['all'] = admins + editors + members

    return result


def hdx_send_mail_contributor(context, data_dict):
    _check_access('hdx_send_mail_contributor', context, data_dict)

    subject = u'[HDX] {fullname} {topic} for \"[Dataset] {pkg_title}\"'.format(
        fullname=data_dict.get('fullname'), topic=data_dict.get('topic'), pkg_title=data_dict.get('pkg_title'))
    requester_body_html = __create_body_for_contributor(data_dict, False)

    admins_body_html = __create_body_for_contributor(data_dict, True)

    recipients_list = []
    org_members = get_action("hdx_member_list")(context, {'org_id': data_dict.get('pkg_owner_org')})
    if org_members:
        admins = org_members.get('admins')
        for admin in admins:
            context['keep_email'] = True
            user = get_action("user_show")(context, {'id': admin})
            if user.get('email'):
                recipients_list.append({'email': user.get('email'), 'display_name': user.get('display_name')})

    pkg_dict = get_action("package_show")(context, {'id': data_dict.get('pkg_id')})
    maintainer = pkg_dict.get("maintainer")
    if maintainer:
        m_user = get_action("user_show")(context, {'id': maintainer})
        if not any(r['email'] == m_user.get('email') for r in recipients_list):
            recipients_list.append({'email': m_user.get('email'), 'display_name': m_user.get('display_name')})

    org_dict = get_action('hdx_light_group_show')(context, {'id': data_dict.get('pkg_owner_org')})
    subject = u'HDX dataset inquiry'
    email_data = {
        'org_name': org_dict.get('title'),
        'user_fullname': data_dict.get('fullname'),
        'user_email': data_dict.get('email'),
        'pkg_url': data_dict.get('pkg_url'),
        'pkg_title': data_dict.get('pkg_title'),
        'topic': data_dict.get('topic'),
        'msg': data_dict.get('msg'),
    }
    cc_recipients_list = [{'email': data_dict.get('hdx_email'), 'display_name': 'HDX'}]
    hdx_mailer.mail_recipient(recipients_list, subject, email_data, sender_name=data_dict.get('fullname'),
                              sender_email=data_dict.get('email'), cc_recipients_list=cc_recipients_list,
                              footer='hdx@un.org',
                              snippet='email/content/contact_contributor_request.html')

    subject = u'HDX dataset inquiry'
    email_data = {
        'user_fullname': data_dict.get('fullname'),
        'pkg_url': data_dict.get('pkg_url'),
        'pkg_title': data_dict.get('pkg_title'),
        'topic': data_dict.get('topic'),
        'msg': data_dict.get('msg'),
    }
    recipients_list = [{'email': data_dict.get('email'), 'display_name': data_dict.get('fullname')}]
    hdx_mailer.mail_recipient(recipients_list, subject, email_data, footer=data_dict.get('email'),
                              snippet='email/content/contact_contributor_request_confirmation_to_user.html')

    return None


def __create_body_for_contributor(data_dict, for_admins):
    '''
    :param data_dict:
    :type data_dict: dict
    :param for_admins: True for the email that should go to org admins. Some additional info is added in this case.
    :type for_admins: boolean
    :return: the html body for the email
    :rtype: str
    '''

    fullname = data_dict.get('fullname') if for_admins else 'You'

    html = u"""\
            <p>{fullname} sent the following message: </p>
            <br />
            <p><em>{msg}</em></p>
            <br />
            <p>Dataset: <a href=\"{pkg_url}\">{pkg_title}</a></p>
        """.format(fullname=fullname, msg=data_dict.get('msg'), pkg_url=data_dict.get('pkg_url'),
                   pkg_title=data_dict.get('pkg_title'))

    if for_admins:
        org_members_url = h.url_for(controller='organization', action='members', id=data_dict.get('pkg_owner_org'),
                                    qualified=True)
        org_members_url = org_members_url.replace('http://', 'https://')
        html += '<br />' \
                '<p>Please use your email\'s REPLY ALL function so that other administrators of your ' \
                '<a href="{org_members_url}" target="_blank">HDX organization</a> ' \
                'are aware that you are responding.</p>'.format(org_members_url=org_members_url)

    return html


def hdx_send_mail_members(context, data_dict):
    recipients_list = []
    org_members = get_action("hdx_member_list")(context, {'org_id': data_dict.get('pkg_owner_org_id')})
    if org_members:
        users_list = org_members.get(data_dict.get('topic_key'))
        for _user in users_list:
            # user = get_action("user_show")(context, {'id': admin})
            user_obj = model.User.get(_user)
            if user_obj and user_obj.email:
                recipients_list.append({'email': user_obj.email, 'display_name': user_obj.fullname})
    # recipients_list.append({'email': data_dict.get('email'), 'display_name': data_dict.get('fullname')})
    users_role = ''
    if data_dict.get('topic_key') == 'all':
        users_role = 'administrator(s), editor(s), and member(s)'
    elif data_dict.get('topic_key') == 'admins':
        users_role = 'administrator(s)]'
    elif data_dict.get('topic_key') == 'editors':
        users_role = 'editor(s)]'
    elif data_dict.get('topic_key') == 'members':
        users_role = 'member(s)]'
    subject = u'HDX group message from ' + data_dict.get('pkg_owner_org')
    email_data = {
        'org_name': data_dict.get('pkg_owner_org'),
        'user_fullname': data_dict.get('fullname'),
        'user_email': data_dict.get('email'),
        'msg': data_dict.get('msg'),
        'users_role': users_role
    }
    hdx_mailer.mail_recipient(recipients_list, subject, email_data, sender_name=data_dict.get('fullname'),
                              sender_email=data_dict.get('email'), footer='hdx@un.org',
                              snippet='email/content/group_message.html')
    return None

@logic.validate(logic.schema.default_pagination_schema)
@logic.side_effect_free
def recently_changed_packages_activity_list(context, data_dict):
    result = logic_get.recently_changed_packages_activity_list(context,data_dict)
    user_obj = context.get('auth_user_obj')
    is_sysadmin = user_obj and user_obj.sysadmin
    if is_sysadmin:
        return result

    for item in result:
        if 'data' in item:
            _data = item.get('data')
            if 'package' in _data:
                _package_dict = _data.get('package')
                member_list = get_action('hdx_member_list')(context, {'org_id': _package_dict.get('owner_org')})
                if (member_list and not member_list.get('is_member')) or member_list is None:
                    del _package_dict['maintainer_email']

    return result


@logic.side_effect_free
def hdx_recommend_tags(context, data_dict):
    tag_recommender = TagRecommender(data_dict.get('title'), data_dict.get('organization'))
    return tag_recommender.find_recommended_tags()


@logic.side_effect_free
def hdx_test_recommend_tags(context, data_dict):
    tag_recommender = TagRecommenderTest(**data_dict)
    return tag_recommender.run_test()


@logic.side_effect_free
def hdx_get_s3_link_for_resource(context, data_dict):
    resource_id = get_or_bust(data_dict, 'id')
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}

    # this does check_access('resource_show') so we don't need to do the check
    res_dict = get_action('resource_show')(context, {'id': resource_id})

    _check_access('hdx_resource_download', context, res_dict)

    if res_dict.get('url_type') == 'upload':
        upload = uploader.get_resource_uploader(res_dict)
        bucket_name = config.get('ckanext.s3filestore.aws_bucket_name')
        host_name = config.get('ckanext.s3filestore.host_name')
        bucket = upload.get_s3_bucket(bucket_name)

        filename = os.path.basename(res_dict['url'])
        key_path = upload.get_path(res_dict['id'], filename)

        try:
            s3 = upload.get_s3_session()
            client = s3.client(service_name='s3', endpoint_url=host_name)
            # url = client.generate_presigned_url(ClientMethod='get_object',
            #                                     Params={'Bucket': bucket.name,
            #                                             'Key': key_path},
            #                                     ExpiresIn=60)
            url = generate_temporary_link(client, bucket.name, key_path)
            return {'s3_url': url}

        except ClientError as ex:
            log.error(unicode(ex))
            base_abort(404, _('Resource data not found'))

    else:
        return {'s3_url': res_dict.get('url')}


@logic.side_effect_free
def hdx_format_autocomplete(context, data_dict):

    q = data_dict['q']
    if not q:
        return []

    return resource_format_autocomplete(q, 5)


@logic.side_effect_free
def hdx_guess_format_from_extension(context, data_dict):

    q = data_dict['q']
    if not q:
        return None

    return guess_format_from_extension(q)
