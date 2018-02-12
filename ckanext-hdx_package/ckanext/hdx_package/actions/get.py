'''
Created on Sep 02, 2015

@author: alexandru-m-g
'''

import os

import ckan.logic as logic
import ckan.model as model
import ckan.plugins as plugins
import ckan.lib.navl.dictization_functions
import ckan.lib.search as search
import ckan.logic.action.get as logic_get
import ckan.lib.plugins as lib_plugins
import ckan.authz as authz

import sqlalchemy
import logging
import json

from ckan.lib import uploader

import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_theme.util.jql as jql
from ckanext.hdx_package.helpers import helpers
from paste.deploy.converters import asbool


from ckanext.hdx_package.helpers.geopreview import GIS_FORMATS
from ckanext.hdx_search.actions.actions import hdx_get_package_showcase_id_list


_validate = ckan.lib.navl.dictization_functions.validate
ValidationError = logic.ValidationError
_check_access = logic.check_access
log = logging.getLogger(__name__)
get_action = logic.get_action

_FOOTER_CONTACT_CONTRIBUTOR = hdx_mailer.FOOTER + '<small><p>Note: <a href="mailto:hdx.feedback@gmail.com">hdx.feedback@gmail.com</a> is blind copied on this message so that we are aware of the initial correspondence related to datasets on the HDX site. Please contact us directly should you need further support.</p></small>'
_FOOTER_GROUP_MESSAGE = hdx_mailer.FOOTER

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

    THIS IS A COPY OF THE package_search() ACTION FROM CORE CKAN
    IT'S CHANGED TO RETURN MORE DATA FROM THE SOLR QUERY (collapse/expand)

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
        query cannot be changed.  CKAN always returns the matched datasets as
        dictionary objects.
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
    for item in plugins.PluginImplementations(plugins.IPackageController):
        data_dict = item.before_search(data_dict)

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = 'score desc, metadata_modified desc'

    results = []
    if not abort:
        if asbool(data_dict.get('use_default_schema')):
            data_source = 'data_dict'
        else:
            data_source = 'validated_data_dict'
        data_dict.pop('use_default_schema', None)
        # return a list of package ids
        data_dict['fl'] = 'id {0}'.format(data_source)

        # we should remove any mention of capacity from the fq and
        # instead set it to only retrieve public datasets
        fq = data_dict.get('fq', '')

        # Remove before these hit solr FIXME: whitelist instead
        include_private = asbool(data_dict.pop('include_private', False))
        include_drafts = asbool(data_dict.pop('include_drafts', False))

        capacity_fq = 'capacity:"public"'
        if include_private and authz.is_sysadmin(user):
            capacity_fq = None
        elif include_private and user:
            orgs = logic.get_action('organization_list_for_user')(
                {'user': user}, {'permission': 'read'})
            if orgs:
                capacity_fq = '({0} OR owner_org:({1}))'.format(
                    capacity_fq,
                    ' OR '.join(org['id'] for org in orgs))
            if include_drafts:
                capacity_fq = '({0} OR creator_user_id:({1}))'.format(
                    capacity_fq,
                    authz.get_user_id_for_username(user))

        if capacity_fq:
            fq = ' '.join(p for p in fq.split() if 'capacity:' not in p)
            data_dict['fq'] = capacity_fq + ' ' + fq

        fq = data_dict.get('fq', '')
        if include_drafts:
            user_id = authz.get_user_id_for_username(user, allow_none=True)
            if authz.is_sysadmin(user):
                data_dict['fq'] = '+state:(active OR draft) ' + fq
            elif user_id:
                # Query to return all active datasets, and all draft datasets
                # for this user.
                u_fq = ' ((creator_user_id:{0} AND +state:(draft OR active))' \
                       ' OR state:active) '.format(user_id)
                data_dict['fq'] = u_fq + ' ' + fq
        elif not authz.is_sysadmin(user):
            data_dict['fq'] = '+state:active ' + fq

        # Pop these ones as Solr does not need them
        extras = data_dict.pop('extras', None)

        query = search.query_for(model.Package)
        query.run(data_dict)

        # Add them back so extensions can use them on after_search
        data_dict['extras'] = extras

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
        expanded = query.raw_response.get('expanded', {})
    else:
        count = 0
        facets = {}
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

    return search_results


@logic.side_effect_free
def resource_show(context, data_dict):
    '''
    Wraps the default resource_show and adds additional information like:
    resource size (for uploaded files) and resource revision timestamp
    '''
    resource_dict = logic_get.resource_show(context, data_dict)

    # TODO: check if needed. Apparently the default resource_show() action anyway calls package_show
    if _should_manually_load_property_value(context, resource_dict, 'size'):
        resource_dict['size'] = _get_resource_filesize(resource_dict)

    if _should_manually_load_property_value(context, resource_dict, 'revision_last_updated'):
        resource_dict['revision_last_updated'] = _get_resource_revison_timestamp(resource_dict)

    if _should_manually_load_property_value(context, resource_dict, 'hdx_rel_url'):
        resource_dict['hdx_rel_url'] = _get_resource_hdx_relative_url(resource_dict)

    return resource_dict


@logic.side_effect_free
def package_show(context, data_dict):
    '''
    Wraps the default package_show and adds additional information to the resources:
    resource size (for uploaded files) and resource revision timestamp
    '''
    # data_dict['include_tracking'] = True
    package_dict = logic_get.package_show(context, data_dict)

    # added because showcase schema validation is generating "ckan.lib.navl.dictization_functions.Missing"
    if 'tracking_summary' in package_dict and not package_dict.get('tracking_summary'):
        del package_dict['tracking_summary']

    # this shouldn't be executed from showcases
    if package_dict.get('type') == 'dataset' and not context.get('no_compute_extra_hdx_show_properties'):
        for resource_dict in package_dict.get('resources', []):
            if _should_manually_load_property_value(context, resource_dict, 'size'):
                resource_dict['size'] = _get_resource_filesize(resource_dict)

            if _should_manually_load_property_value(context, resource_dict, 'revision_last_updated'):
                resource_dict['revision_last_updated'] = _get_resource_revison_timestamp(resource_dict)

            if _should_manually_load_property_value(context, resource_dict, 'hdx_rel_url'):
                resource_dict['hdx_rel_url'] = _get_resource_hdx_relative_url(resource_dict)

        # downloads_list = (res['tracking_summary']['total'] for res in package_dict.get('resources', []) if
        #                   res.get('tracking_summary', {}).get('total'))
        # package_dict['total_res_downloads'] = sum(downloads_list)

        if _should_manually_load_property_value(context, package_dict, 'total_res_downloads'):
            total_res_downloads = jql.downloads_per_dataset_all_cached().get(package_dict['id'], 0)
            log.debug('Dataset {} has {} downloads'.format(package_dict['id'], total_res_downloads))
            package_dict['total_res_downloads'] = total_res_downloads

        if _should_manually_load_property_value(context, package_dict, 'pageviews_last_14_days'):
            pageviews_last_14_days = jql.pageviews_per_dataset_last_14_days_cached().get(package_dict['id'], 0)
            log.debug('Dataset {} has {} page views in the last 14 days'.format(package_dict['id'], pageviews_last_14_days))
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

    return package_dict


@logic.side_effect_free
def shape_info_show(context, data_dict):
    dataset_dict = get_action('package_show')(context, data_dict)

    shape_infos = [{r.get('name'): json.loads(r.get('shape_info'))} for r in dataset_dict.get('resources', []) if r.get('shape_info')]

    return shape_infos



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

    return not (use_cache and current_value)


@logic.side_effect_free
def package_show_edit(context, data_dict):
    '''A package_show action for editing a package and resources.'''

    # Requires use_cache and for_edit in the context so resource urls for file
    # uploads don't include the full qualified url path.
    context['use_cache'] = False
    context['for_edit'] = True

    return package_show(context, data_dict)


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
    subject = u'[HDX] {fullname} {topic} for \"[Dataset] {pkg_title}\"'.format(
        fullname=data_dict.get('fullname'), topic=data_dict.get('topic'), pkg_title=data_dict.get('pkg_title'))
    html = u"""\
            <p>{fullname} sent the following message: </p>
            <p>{msg}</p>
            <p>Dataset: <a href=\"{pkg_url}\">{pkg_title}</a>
        """.format(fullname=data_dict.get('fullname'), msg=data_dict.get('msg'), pkg_url=data_dict.get('pkg_url'),
                   pkg_title=data_dict.get('pkg_title'))

    recipients_list = []
    org_members = get_action("hdx_member_list")(context, {'org_id': data_dict.get('pkg_owner_org')})
    if org_members:
        admins = org_members.get('admins')
        for admin in admins:
            user = get_action("user_show")(context, {'id': admin})
            if user.get('email'):
                recipients_list.append({'email': user.get('email'), 'display_name': user.get('display_name')})
    recipients_list.append({'email': data_dict.get('email'), 'display_name': data_dict.get('fullname')})

    bcc_recipients_list = [{'email': data_dict.get('hdx_email'), 'display_name': 'HDX'}]

    hdx_mailer.mail_recipient(recipients_list=recipients_list, subject=subject, body=html,
                              sender_name=data_dict.get('fullname'), sender_email=data_dict.get('email'),
                              bcc_recipients_list=bcc_recipients_list, footer=_FOOTER_CONTACT_CONTRIBUTOR)

    return None


def hdx_send_mail_members(context, data_dict):
    subject = u'[HDX] {fullname} sent a group message regarding \"[Dataset] {pkg_title}\"'.format(
        fullname=data_dict.get('fullname'), topic=data_dict.get('topic'), pkg_title=data_dict.get('pkg_title'))
    html = u"""\
            <p>{fullname} sent the following message to {topic} of {pkg_owner_org}: </p>
            <p>{msg}</p>
        """.format(fullname=data_dict.get('fullname'), topic=data_dict.get('topic').lower(),
                   pkg_owner_org=data_dict.get('pkg_owner_org'), msg=data_dict.get('msg'))

    if data_dict.get('source_type') == 'dataset':
        html += u'<p>Dataset: <a href=\"{pkg_url}\">{pkg_title}</a>'.format(pkg_url=data_dict.get('pkg_url'),
                                                                            pkg_title=data_dict.get('pkg_title'))

    recipients_list = []
    org_members = get_action("hdx_member_list")(context, {'org_id': data_dict.get('pkg_owner_org_id')})
    if org_members:
        admins = org_members.get(data_dict.get('topic_key'))
        for admin in admins:
            user = get_action("user_show")(context, {'id': admin})
            if user.get('email'):
                recipients_list.append({'email': user.get('email'), '_display_name': user.get('display_name')})
    recipients_list.append({'email': data_dict.get('email'), 'display_name': data_dict.get('fullname')})

    hdx_mailer.mail_recipient(recipients_list=recipients_list, subject=subject, body=html,
                              sender_name=data_dict.get('fullname'), sender_email=data_dict.get('email'),
                              footer=_FOOTER_GROUP_MESSAGE)

    return None
