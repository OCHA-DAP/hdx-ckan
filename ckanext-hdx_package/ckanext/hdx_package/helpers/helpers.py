import re
import urlparse
import uuid

import json
import logging

import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic

import ckan.plugins.toolkit as tk
import ckan.new_authz as new_authz
import ckan.lib.activity_streams as activity_streams
import ckan.model.package as package
import ckan.model.misc as misc

from pylons import config


from ckan.common import _, c, request
from ckanext.hdx_package.exceptions import NoOrganization


get_action = logic.get_action
log = logging.getLogger(__name__)
_check_access = logic.check_access
_get_or_bust = logic.get_or_bust
NotFound = logic.NotFound
ValidationError = logic.ValidationError
_get_action = logic.get_action


group_codes = {"yem": "Yemen", "rom": "Romania", "bvt": "Bouvet Island", "mnp": "Northern Mariana Islands", "lso": "Lesotho", "tkl": "Tokelau", "tkm": "Turkmenistan", "alb": "Albania", "ita": "Italy", "tto": "Trinidad And Tobago", "nld": "Netherlands", "world": "World", "tcd": "Chad", "reu": "Reunion", "mne": "Montenegro", "mng": "Mongolia", "bfa": "Burkina Faso", "nga": "Nigeria", "zmb": "Zambia", "gmb": "Gambia", "hrv": "Croatia (Local Name: Hrvatska)", "gtm": "Guatemala", "lka": "Sri Lanka", "aus": "Australia", "jam": "Jamaica", "pcn": "Pitcairn", "aut": "Austria", "sgp": "Singapore", "dji": "Djibouti", "vct": "Saint Vincent And The Grenadines", "mwi": "Malawi", "fin": "Finland", "uga": "Uganda", "moz": "Mozambique", "bih": "Bosnia And Herzegowina", "tjk": "Tajikistan", "pse": "State of Palestine", "lca": "Saint Lucia", "svn": "Slovenia", "ssd": "South Sudan", "geo": "Georgia", "nor": "Norway", "mhl": "Marshall Islands", "pak": "Pakistan", "png": "Papua New Guinea", "guf": "French Guiana", "umi": "U.S. Minor Islands", "nfk": "Norfolk Island", "zwe": "Zimbabwe", "gum": "Guam", "gbr": "United Kingdom", "guy": "Guyana", "cri": "Costa Rica", "cmr": "Cameroon", "shn": "St. Helena", "kwt": "Kuwait", "mtq": "Martinique", "wsm": "Samoa", "mda": "Moldova, Republic Of", "mdg": "Madagascar", "hti": "Haiti", "aze": "Azerbajan", "qat": "Qatar", "mar": "Morocco", "are": "United Arab Emirates", "arg": "Argentina", "sen": "Senegal", "btn": "Bhutan", "mdv": "Maldives", "arm": "Armenia", "tmp": "East Timor", "est": "Estonia", "mus": "Mauritius", "esp": "Spain", "lux": "Luxemburg", "irq": "Iraq", "bdi": "Burundi", "smr": "San Marino", "per": "Peru", "blr": "Belarus", "irl": "Ireland", "sur": "Suriname", "irn": "Iran (Islamic Republic Of)", "abw": "Aruba", "stp": "Sao Tome And Principe", "tca": "Turks And Caicos Islands", "ner": "Niger", "esh": "Western Sahara", "plw": "Palau", "ken": "Kenya", "jor": "Jordan", "spm": "St. Pierre And Miquelon", "tur": "Turkey", "omn": "Oman", "tuv": "Tuvalu", "mmr": "Myanmar", "bwa": "Botswana", "ecu": "Ecuador", "tun": "Tunisia", "swe": "Sweden", "rus": "Russia", "hkg": "Hong Kong", "asm": "American Samoa", "dza": "Algeria", "atg": "Antigua And Barbuda", "bgd": "Bangladesh", "ltu": "Lithuania", "ata": "Antartica", "isr": "Israel", "caf": "Central African Republic", "idn": "Indonesia", "bgr": "Bulgaria", "bol": "Bolivia (Plurinational State of)", "cod": "Democratic Republic of the Congo", "cog": "Congo", "isl": "Iceland", "glp": "Guadeloupe", "tha": "Thailand", "eth": "Ethiopia", "com": "Comoros", "col": "Colombia", "wlf": "Wallis And Futuna Islands", "sjm": "Svalbard And Jan Mayen Islands", "cxr": "Christmas Island", "can": "Canada", "zaf": "South Africa", "fro": "Faroe Islands", "sgs": "South Georgia And South S.S.", "som": "Somalia", "uzb": "Uzbekistan", "ukr": "Ukraine", "vir": "Virgin Islands (U.S.)", "brn": "Brunei Darussalam", "pol": "Poland", "tgo": "Togo", "dnk": "Denmark", "brb": "Barbados", "bra": "Brazil", "fra": "France", "mkd": "Macedonia", "che": "Switzerland", "usa": "United States", "chl": "Chile", "msr": "Montserrat", "chn": "China", "mex": "Mexico", "swz": "Swaziland", "ton": "Tonga", "gib": "Gibraltar", "rwa": "Rwanda", "gin": "Guinea", "kor": "Korea, Republic Of", "vat": "Holy See (Vatican City State)", "cub": "Cuba", "mco": "Monaco", "atf": "French Southern Territories", "cyp": "Cyprus", "hun": "Hungary", "kgz": "Kyrgyzstan", "fji": "Fiji", "ven": "Venezuela", "ncl": "New Caledonia", "bmu": "Bermuda", "hmd": "Heard And Mc Donald Islands", "sdn": "Sudan", "gab": "Gabon", "cym": "Cayman Islands", "svk": "Slovakia (Slovak Republic)", "dma": "Dominica", "gnq": "Equatorial Guinea", "ben": "Benin", "bel": "Belgium", "slv": "El Salvador", "mli": "Mali", "deu": "Germany", "gnb": "Guinea-Bissau", "flk": "Falkland Islands (Malvinas)", "lva": "Latvia", "civ": "C\u00f4te d'Ivoire", "mlt": "Malta", "sle": "Sierra Leone", "aia": "Anguilla", "eri": "Eritrea", "slb": "Solomon Islands", "nzl": "New Zealand", "and": "Andorra", "lbr": "Liberia", "jpn": "Japan", "lby": "Libya", "mys": "Malaysia", "pri": "Puerto Rico", "myt": "Mayotte", "prk": "Democratic People's Republic of Korea", "ant": "Netherlands Antilles", "prt": "Portugal", "khm": "Cambodia", "ind": "India", "bhs": "Bahamas", "bhr": "Bahrain", "pry": "Paraguay", "sau": "Saudi Arabia", "cze": "Czech Republic", "lie": "Liechtenstein", "fxx": "France, Metropolitan", "afg": "Afghanistan", "vut": "Vanuatu", "vgb": "Virgin Islands (British)", "nam": "Namibia", "grd": "Grenada", "nru": "Nauru", "grc": "Greece", "twn": "Taiwan, Province Of China", "grl": "Greenland", "lbn": "Lebanon", "srb": "Serbia", "pan": "Panama", "syc": "Seychelles", "npl": "Nepal", "lao": "Lao People\'s Democratic Republic", "phl": "Philippines", "kir": "Kiribati", "vnm": "Viet Nam", "iot": "British Indian Ocean Territory", "syr": "Syrian Arab Republic", "mac": "Macau", "kaz": "Kazakhstan", "cok": "Cook Islands", "pyf": "French Polynesia", "niu": "Niue", "ago": "Angola", "egy": "Egypt", "hnd": "Honduras", "dom": "Dominican Republic", "mrt": "Mauritania", "blz": "Belize", "nic": "Nicaragua", "fsm": "Micronesia, Federated States Of", "kna": "Saint Kitts And Nevis", "gha": "Ghana", "cck": "Cocos (Keeling) Islands", "ury": "Uruguay", "cpv": "Cape Verde", "tza": "United Republic of Tanzania"}

def build_additions(groups):
    """
    Builds additions for solr searches
    """
    countries = []
    for g in groups:
        try:
            if 'id' in g:
                countries.append(group_codes[g['id']])
            else:
                countries.append(group_codes[g['name']]) #API will hit this
        except:
            pass
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
        base.abort(401, _('Unauthorized to see organization member list'))

    return user


def hdx_organizations_available_with_roles():
    """
    Gets roles of organizations the current user belongs to
    """
    organizations_available = h.organizations_available('read')
    if organizations_available and len(organizations_available) > 0:
        orgs_where_editor = []
        orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set(
            [org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id']
                                for org in h.organizations_available('admin')])

    for org in organizations_available:
        org['has_add_dataset_rights'] = True
        if am_sysadmin:
            org['role'] = 'sysadmin'
        elif org['id'] in orgs_where_admin:
            org['role'] = 'admin'
        elif org['id'] in orgs_where_editor:
            org['role'] = 'editor'
        else:
            org['role'] = 'member'
            org['has_add_dataset_rights'] = False

    organizations_available.sort(key=lambda y:
                                 y['display_name'].lower())
    return organizations_available


def hdx_get_activity_list(context, data_dict):
    """
    Get activity list for a given package

    """
    activity_stream = get_action('package_activity_list')(context, data_dict)
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

    q = q.join('package_tags').filter(model.PackageTag.state == 'active')
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
        if c.userobj or c.user:
            data_dict['href'] = '/dashboard/organizations'
            data_dict['onclick'] = ''
            return data_dict
        data_dict['href'] = '/contribute'
        data_dict['onclick'] = ''
        return data_dict

    data_dict['href'] = '#'
    data_dict['onclick'] = 'contributeAddDetails()'

    return data_dict