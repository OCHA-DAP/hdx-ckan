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
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.logic.action.get as logic_get
import ckan.lib.plugins as lib_plugins

import sqlalchemy
import logging
import json

from ckan.lib import uploader
import ckanext.hdx_users.controllers.mailer as hdx_mailer
from ckan.common import _

_validate = ckan.lib.navl.dictization_functions.validate
ValidationError = logic.ValidationError
_check_access = logic.check_access
log = logging.getLogger(__name__)
get_action = logic.get_action

_footer = '<br><small><p><a href="https://data.humdata.org">Humanitarian Data Exchange</a></p>' + '<p>Sign up for <a href="http://eepurl.com/PlJgH">Blogs</a> | <a href="https://twitter.com/humdata">Follow us on Twitter</a> | <a href="mailto:hdx@un.org" target="_top">Contact us</a></p><p>Your message may be monitored by the HDX team for internal use such as improving your user experience and the overall quality of our services.</p></small>'


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
    IT USES ONLY ONE SQLALCHEMY QUERY TO GET ORG AND GROUP DISPLAY_NAMES

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
    :param rows: the number of matching rows to return.
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


    The following advanced Solr parameters are supported as well. Note that
    some of these are only available on particular Solr versions. See Solr's
    `dismax`_ and `edismax`_ documentation for further details on them:

    ``qf``, ``wt``, ``bf``, ``boost``, ``tie``, ``defType``, ``mm``


    .. _dismax: http://wiki.apache.org/solr/DisMaxQParserPlugin
    .. _edismax: http://wiki.apache.org/solr/ExtendedDisMax


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
    :param use_default_schema: use default package schema instead of
        a custom schema defined with an IDatasetForm plugin (default: False)
    :type use_default_schema: bool

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
        data_source = 'data_dict' if data_dict.get('use_default_schema') else 'validated_data_dict'
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
            # COMMENTING BELOW CODE FRAGMENT OUT ACCORDING TO A CHANGE DONE IN
            # CKAN CORE https://github.com/ckan/ckan/commit/463bc3e3422ad60a5a00148167115485d93c1bbb#diff-4494aaf212251212949348df94158668
            # pkg_query = session.query(model.Package)\
            #     .filter(model.Package.id == package)\
            #     .filter(model.Package.state == u'active')
            # pkg = pkg_query.first()
            #
            # ## if the index has got a package that is not in ckan then
            # ## ignore it.
            # if not pkg:
            #     log.warning('package %s in index but not in database'
            #                 % package)
            #     continue
            ## use data in search index if there
            if package_dict:
                ## the package_dict still needs translating when being viewed
                package_dict = json.loads(package_dict)
                if context.get('for_view'):
                    for item in plugins.PluginImplementations(
                            plugins.IPackageController):
                        package_dict = item.before_view(package_dict)
                results.append(package_dict)
                # else:
                #     results.append(model_dictize.package_dictize(pkg, context))

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

    org_group_keys = []
    for key, value in facets.items():
        if key in ('groups', 'organization'):
            org_group_keys.extend(value.keys())

    groups = session.query(model.Group.name, model.Group.title).filter(model.Group.name.in_(org_group_keys)).all()
    group_display_names = {g.name: g.title for g in groups}

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
                new_facet_dict['display_name'] = group_display_names.get(key_, key_)
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
    resource_dict = logic_get.resource_show(context, data_dict)

    if not resource_dict.get('size'):
        resource_dict['size'] = __get_resource_filesize(resource_dict)

    return resource_dict


@logic.side_effect_free
def package_show(context, data_dict):
    package_dict = logic_get.package_show(context, data_dict)

    for resource_dict in package_dict.get('resources', []):
        if not resource_dict.get('size'):
            resource_dict['size'] = __get_resource_filesize(resource_dict)

    downloads_list = (res['tracking_summary']['total'] for res in package_dict.get('resources', []) if
                      res.get('tracking_summary', {}).get('total'))
    package_dict['total_res_downloads'] = sum(downloads_list)

    return package_dict


@logic.side_effect_free
def package_show_edit(context, data_dict):
    '''A package_show action for editing a package and resources.'''

    # Requires use_cache and for_edit in the context so resource urls for file
    # uploads don't include the full qualified url path.
    context['use_cache'] = False
    context['for_edit'] = True

    return package_show(context, data_dict)


def __get_resource_filesize(resource_dict):
    if resource_dict.get('url_type') == 'upload':
        value = None
        try:
            upload = uploader.ResourceUpload(resource_dict)
            value = os.path.getsize(upload.get_path(resource_dict['id']))
        except Exception as e:
            log.warn(u'Error occurred trying to get the size for resource {}: {}'.format(resource_dict.get('name', ''),
                                                                                         str(e)))
        return value
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
    subject = '[HDX] {fullname} {topic} for \"[Dataset] {pkg_title}\"'.format(
        fullname=data_dict.get('fullname'), topic=data_dict.get('topic'), pkg_title=data_dict.get('pkg_title'))
    html = """\
            <p>{fullname} mentioned: </p>
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
                recipients_list.append({'email': user.get('email'), 'name': user.get('display_name')})
    recipients_list.append({'email': data_dict.get('email'), 'name': data_dict.get('fullname')})
    recipients_list.append({'email': data_dict.get('hdx_email'), 'name': 'HDX'})
    hdx_mailer.mail_recipient(recipient_name=None, recipient_email=None, subject=subject, body=html,
                              recipients_list=recipients_list, footer=_footer, sender_name=data_dict.get('fullname'),
                              sender_email=data_dict.get('email'))

    return None


def hdx_send_mail_members(context, data_dict):
    subject = '[HDX] {fullname} sent a group message regarding \"[Dataset] {pkg_title}\"'.format(
        fullname=data_dict.get('fullname'), topic=data_dict.get('topic'), pkg_title=data_dict.get('pkg_title'))
    html = """\
            <p>This message was sent to {topic} of {pkg_owner_org} </p>
            <p>{fullname} mentioned: </p>
            <p>{msg}</p>
            <p>Dataset: <a href=\"{pkg_url}\">{pkg_title}</a>
        """.format(topic=data_dict.get('topic').lower(), pkg_owner_org=data_dict.get('pkg_owner_org'),
                   fullname=data_dict.get('fullname'), msg=data_dict.get('msg'),
                   pkg_url=data_dict.get('pkg_url'), pkg_title=data_dict.get('pkg_title'))

    recipients_list = []
    org_members = get_action("hdx_member_list")(context, {'org_id': data_dict.get('pkg_owner_org_id')})
    if org_members:
        admins = org_members.get(data_dict.get('topic_key'))
        for admin in admins:
            user = get_action("user_show")(context, {'id': admin})
            if user.get('email'):
                recipients_list.append({'email': user.get('email'), 'name': user.get('display_name')})
    recipients_list.append({'email': data_dict.get('email'), 'name': data_dict.get('fullname')})
    recipients_list.append({'email': data_dict.get('hdx_email'), 'name': 'HDX'})
    hdx_mailer.mail_recipient(recipient_name=None, recipient_email=None, subject=subject, body=html,
                              recipients_list=recipients_list, footer=_footer, sender_name=data_dict.get('fullname'),
                              sender_email=data_dict.get('email'))

    return None
