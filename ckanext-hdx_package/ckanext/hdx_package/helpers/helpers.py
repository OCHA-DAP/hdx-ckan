import json
import logging
import re
import urlparse

import ckanext.hdx_package.helpers.custom_validator as vd
from ckanext.hdx_package.exceptions import NoOrganization
from ckanext.hdx_package.helpers.caching import cached_group_iso_to_title
from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator
from pylons import config

import ckan.authz as new_authz
import ckan.lib.activity_streams as activity_streams
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
import ckan.model.misc as misc
import ckan.model.package as package
import ckan.plugins.toolkit as tk
from ckan.common import _, c, request

get_action = logic.get_action
log = logging.getLogger(__name__)
_check_access = logic.check_access
_get_or_bust = logic.get_or_bust
NotFound = logic.NotFound
ValidationError = logic.ValidationError
_get_action = logic.get_action


def build_additions(groups):
    """
    Builds additions for solr searches
    """
    countries = []
    for g in groups:
        try:
            if 'name' in g:
                # grp_list = cached_group_iso_to_title()
                # country = grp_list[g.get('name')] if g.get('name') in grp_list else g.get('name')
                countries.append(cached_group_iso_to_title()[g.get('name')])
        except Exception, e:
            ex_msg = e.message if hasattr(e, 'message') else str(e)
            log.error(ex_msg)
    return json.dumps({'countries':countries})


def hdx_user_org_num(user_id):
    """
    Get number of orgs for a specific user
    """
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    try:
        user = tk.get_action('organization_list_for_user')(
            context, {'id': user_id, 'permission': 'create_dataset'})
    except logic.NotAuthorized:
        base.abort(403, _('Unauthorized to see organization member list'))

    return user


# def hdx_organizations_available_with_roles():
#     """
#     Gets roles of organizations the current user belongs to
#     """
#     organizations_available = h.organizations_available('read')
#     if organizations_available and len(organizations_available) > 0:
#         orgs_where_editor = []
#         orgs_where_admin = []
#     am_sysadmin = new_authz.is_sysadmin(c.user)
#     if not am_sysadmin:
#         orgs_where_editor = set(
#             [org['id'] for org in h.organizations_available('create_dataset')])
#         orgs_where_admin = set([org['id']
#                                 for org in h.organizations_available('admin')])
#
#     for org in organizations_available:
#         org['has_add_dataset_rights'] = True
#         if am_sysadmin:
#             org['role'] = 'sysadmin'
#         elif org['id'] in orgs_where_admin:
#             org['role'] = 'admin'
#         elif org['id'] in orgs_where_editor:
#             org['role'] = 'editor'
#         else:
#             org['role'] = 'member'
#             org['has_add_dataset_rights'] = False
#
#     organizations_available.sort(key=lambda y:
#                                  y['display_name'].lower())
#     return organizations_available


def hdx_get_activity_list(context, data_dict):
    """
    Get activity list for a given package

    """
    try:
        activity_stream = get_action('package_activity_list')(context, data_dict)
    except Exception, ex:
        log.exception(ex)
        activity_stream = []
    #activity_stream = package_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'package',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }
    return _activity_list(context, activity_stream, extra_vars)


def hdx_find_license_name(license_id, license_name):
    """
    Look up license name by id
    """
    if license_name == None or len(license_name) == 0 or license_name == license_id:
        original_license_list = (
            l.as_dict() for l in package.Package._license_register.licenses)
        license_dict = {l['id']: l['title']
                        for l in original_license_list}
        if license_id in license_dict:
            return license_dict[license_id]
    return license_name


# code copied from activity_streams.activity_list_to_html and modified to
# return only the activity list
def _activity_list(context, activity_stream, extra_vars):
    '''Return the given activity stream

    :param activity_stream: the activity stream to render
    :type activity_stream: list of activity dictionaries
    :param extra_vars: extra variables to pass to the activity stream items
        template when rendering it
    :type extra_vars: dictionary


    '''
    activity_list = []  # These are the activity stream messages.
    for activity in activity_stream:
        detail = None
        activity_type = activity['activity_type']
        # Some activity types may have details.
        if activity_type in activity_streams.activity_stream_actions_with_detail:
            details = logic.get_action('activity_detail_list')(context=context,
                                                               data_dict={'id': activity['id']})
            # If an activity has just one activity detail then render the
            # detail instead of the activity.
            if len(details) == 1:
                detail = details[0]
                object_type = detail['object_type']

                if object_type == 'PackageExtra':
                    object_type = 'package_extra'

                new_activity_type = '%s %s' % (detail['activity_type'],
                                               object_type.lower())
                if new_activity_type in activity_streams.activity_stream_string_functions:
                    activity_type = new_activity_type

        if not activity_type in activity_streams.activity_stream_string_functions:
            raise NotImplementedError("No activity renderer for activity "
                                      "type '%s'" % activity_type)

        if activity_type in activity_streams.activity_stream_string_icons:
            activity_icon = activity_streams.activity_stream_string_icons[
                activity_type]
        else:
            activity_icon = activity_streams.activity_stream_string_icons[
                'undefined']

        activity_msg = activity_streams.activity_stream_string_functions[activity_type](context,
                                                                                        activity)

        # Get the data needed to render the message.
        matches = re.findall('\{([^}]*)\}', activity_msg)
        data = {}
        for match in matches:
            snippet = activity_streams.activity_snippet_functions[
                match](activity, detail)
            data[str(match)] = snippet

        activity_list.append({'msg': activity_msg,
                              'type': activity_type.replace(' ', '-').lower(),
                              'icon': activity_icon,
                              'data': data,
                              'timestamp': activity['timestamp'],
                              'is_new': activity.get('is_new', False)})
    extra_vars['activities'] = activity_list
    return extra_vars


def hdx_tag_autocomplete_list(context, data_dict):
    '''Return a list of tag names that contain a given string.

    By default only free tags (tags that don't belong to any vocabulary) are
    searched. If the ``vocabulary_id`` argument is given then only tags
    belonging to that vocabulary will be searched instead.

    :param query: the string to search for
    :type query: string
    :param vocabulary_id: the id or name of the tag vocabulary to search in
      (optional)
    :type vocabulary_id: string
    :param fields: deprecated
    :type fields: dictionary
    :param limit: the maximum number of tags to return
    :type limit: int
    :param offset: when ``limit`` is given, the offset to start returning tags
        from
    :type offset: int

    :rtype: list of strings

    '''
    _check_access('tag_autocomplete', context, data_dict)
    data_dict.update({
        'vocabulary_id': 'Topics',

    })
    matching_tags, count = _tag_search(context, data_dict)
    if matching_tags:
        return [tag.name for tag in matching_tags]
    else:
        return []

# code copied from get.py line 1748


def _tag_search(context, data_dict):
    """
    Searches tags for autocomplete, but makes sure only return active tags
    """
    model = context['model']

    terms = data_dict.get('query') or data_dict.get('q') or []
    if isinstance(terms, basestring):
        terms = [terms]
    terms = [t.strip() for t in terms if t.strip()]

    if 'fields' in data_dict:
        log.warning('"fields" parameter is deprecated.  '
                    'Use the "query" parameter instead')

    fields = data_dict.get('fields', {})
    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    # TODO: should we check for user authentication first?
    q = model.Session.query(model.Tag)

    if 'vocabulary_id' in data_dict:
        # Filter by vocabulary.
        vocab = model.Vocabulary.get(_get_or_bust(data_dict, 'vocabulary_id'))
        if not vocab:
            raise NotFound
        q = q.filter(model.Tag.vocabulary_id == vocab.id)

# CHANGES to initial version
#     else:
# If no vocabulary_name in data dict then show free tags only.
#         q = q.filter(model.Tag.vocabulary_id == None)
# If we're searching free tags, limit results to tags that are
# currently applied to a package.
#         q = q.distinct().join(model.Tag.package_tags)

    for field, value in fields.items():
        if field in ('tag', 'tags'):
            terms.append(value)

    if not len(terms):
        return [], 0

    for term in terms:
        escaped_term = misc.escape_sql_like_special_characters(
            term, escape='\\')
        q = q.filter(model.Tag.name.ilike('%' + escaped_term + '%'))

    # q = q.join('package_tags').filter(model.PackageTag.state == 'active')
    count = q.count()
    q = q.offset(offset)
    q = q.limit(limit)
    tags = q.all()
    return tags, count


def pkg_topics_list(data_dict):
    """
    Get a list of topics
    """
    pkg = model.Package.get(data_dict['id'])
    vocabulary = model.Vocabulary.get('Topics')
    topics = []
    if vocabulary:
        topics = pkg.get_tags(vocab=vocabulary)
    return topics


def get_tag_vocabulary(tags):
    """
    Get vocabulary for a given list of tags
    """
    for item in tags:
        tag_name = item['name'].lower()
        vocabulary = model.Vocabulary.get('Topics')
        if vocabulary:
            topic = model.Tag.by_name(name=tag_name, vocab=vocabulary)
            if topic:
                item['vocabulary_id'] = vocabulary.id
        item['name'] = tag_name
    return tags


def hdx_unified_resource_format(format):
    '''
    This function is based on the unified_resource_format() function from ckan.lib.helpers.
    As the one from core ckan it checks the resource formats configuration to translate the
    format string to a standard format.
    The difference is that in case nothing is found in 'resource_formats.json' then it's
    turned to lowercase.

    :param format: resource format as written by the user
    :type format: string
    :return:
    :rtype:
    '''
    formats = h.resource_formats()
    format_clean = format.lower()
    if format_clean in formats:
        format_new = formats[format_clean][1]
    else:
        format_new = format_clean
    return format_new


def filesize_format(size_in_bytes):
    try:
        d = 1024.0
        size = int(size_in_bytes)

        # value = formatters.localised_filesize(size_in_bytes)
        # return value

        for unit in ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if size < d:
                return "%3.1f%s" % (size, unit)
            size /= d
        return "%.1f%s" % (size, 'Yi')
    except Exception, e:
        log.warn('Error occured when formatting the numner {}. Error {}'.format(size_in_bytes, str(e)))
        return size_in_bytes


def hdx_get_proxified_resource_url(data_dict, proxy_schemes=['http','https']):
    '''
    This function replaces the one with the similar name from ckanext.resourceproxy.plugin .
    Changes:
    1) Don't look at the protocol when checking if it is the same domain
    2) Return a domain relative url (without schema, domain or port) for local resources.

    :param data_dict: contains a resource and package dict
    :type data_dict: dict
    :param proxy_schemes: list of url schemes to proxy for.
    :type data_dict: list
    '''

    same_domain = is_ckan_domain(data_dict['resource']['url'])
    parsed_url = urlparse.urlparse(data_dict['resource']['url'])
    scheme = parsed_url.scheme

    if not same_domain and scheme in proxy_schemes:
        url = h.url_for(
            action='proxy_resource',
            controller='ckanext.resourceproxy.controller:ProxyController',
            id=data_dict['package']['name'],
            resource_id=data_dict['resource']['id'])
        log.info('Proxified url is {0}'.format(url))
    else:
        url = urlparse.urlunparse((None, None) + parsed_url[2:])
    return url


def is_ckan_domain(url):
    '''
    :param url: url to check whether it's on the same domain as ckan
    :type url: str
    :return: True if it's the same domain. False otherwise
    :rtype: bool
    '''
    ckan_url = config.get('ckan.site_url', '//localhost:5000')
    parsed_url = urlparse.urlparse(url)
    ckan_parsed_url = urlparse.urlparse(ckan_url)
    same_domain = True if not parsed_url.hostname or parsed_url.hostname == ckan_parsed_url.hostname else False
    return same_domain

def make_url_relative(url):
    '''
    Transforms something like http://testdomain.com/test to /test
    :param url: url to check whether it's on the same domain as ckan
    :type url: str
    :return: the new url as a string
    :rtype: str
    '''
    parsed_url = urlparse.urlparse(url)
    return urlparse.urlunparse((None, None) + parsed_url[2:])

def generate_mandatory_fields():
    '''

    :return: dataset dict with mandatory fields filled
    :rtype: dict
    '''

    user = c.user or c.author

    # random_string = str(uuid.uuid4()).replace('-', '')[:8]
    # dataset_name = 'autogenerated-{}-{}'.format(user, random_string)

    selected_org = None
    orgs = h.organizations_available('create_dataset')
    if len(orgs) == 0:
        raise NoOrganization(_('The user needs to belong to at least 1 organisation'))
    else:
        selected_org = orgs[0]


    data_dict = {
        'private': True,
        # 'name': dataset_name,
        # 'title': dataset_name,
        'license_id': 'cc-by',
        'owner_org': selected_org.get('id'),
        'dataset_source': selected_org.get('title'),
        'maintainer': user,
        'subnational': 1,
        'data_update_frequency': config.get('hdx.default_frequency', '-999'),
        'dataset_preview_check': '1',
        'dataset_preview': vd._DATASET_PREVIEW_FIRST_RESOURCE,
        'dataset_preview_value': vd._DATASET_PREVIEW_FIRST_RESOURCE
    }
    return data_dict


def hdx_check_add_data():
    data_dict = {}

    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}
    dataset_dict = None
    try:
        logic.check_access("package_create", context, dataset_dict)
    except logic.NotAuthorized, e:
        data_dict['data_module'] = 'hdx_click_stopper'
        data_dict['data_module_link_type'] = 'header add data'
        if c.userobj or c.user:
            data_dict['href'] = '/dashboard/organizations'
            data_dict['onclick'] = ''
            return data_dict
        data_dict['href'] = '/contribute'
        data_dict['onclick'] = ''
        return data_dict

    data_dict['href'] = '#'
    data_dict['onclick'] = 'contributeAddDetails(null, \'header\')'

    return data_dict


def hdx_get_last_modification_date(dataset_dict):
    return FreshnessCalculator.dataset_last_change_date(dataset_dict)


def hdx_get_due_overdue_date(dataset_dict, type='overdue', format='%b %-d %Y'):
    due_date, overdue_date = FreshnessCalculator(dataset_dict).read_from_range_due_overdue_dates()
    if type == 'due':
        d = due_date
    else:
        d = overdue_date

    if d:
        return d.strftime(format)
    else:
        return None

