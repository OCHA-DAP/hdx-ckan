import re
import ckan.lib.helpers as h
from ckan.common import (
    c, request
)
import sqlalchemy
import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import datetime
import json
import logging
import ckan.plugins.toolkit as tk
import re
import ckan.new_authz as new_authz
import ckan.lib.activity_streams as activity_streams
import ckan.model.package as package
import ckan.model.misc as misc
import ckan.lib.plugins as lib_plugins
import ckanext.hdx_theme.helpers.counting_actions as counting
import ckan.lib.dictization.model_save as model_save
import ckan.plugins as plugins

from ckan.logic.action.create import _validate

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _, c, request, response
from ckan.model.tag import PackageTag, Tag

get_action = logic.get_action
log = logging.getLogger(__name__)
_check_access = logic.check_access
_get_or_bust = logic.get_or_bust
NotFound = logic.NotFound
ValidationError = logic.ValidationError
_get_action = logic.get_action


group_codes = {"yem": "Yemen", "rom": "Romania", "bvt": "Bouvet Island", "mnp": "Northern Mariana Islands", "lso": "Lesotho", "tkl": "Tokelau", "tkm": "Turkmenistan", "alb": "Albania", "ita": "Italy", "tto": "Trinidad And Tobago", "nld": "Netherlands", "world": "World", "tcd": "Chad", "reu": "Reunion", "mne": "Montenegro", "mng": "Mongolia", "bfa": "Burkina Faso", "nga": "Nigeria", "zmb": "Zambia", "gmb": "Gambia", "hrv": "Croatia (Local Name: Hrvatska)", "gtm": "Guatemala", "lka": "Sri Lanka", "aus": "Australia", "jam": "Jamaica", "pcn": "Pitcairn", "aut": "Austria", "sgp": "Singapore", "dji": "Djibouti", "vct": "Saint Vincent And The Grenadines", "mwi": "Malawi", "fin": "Finland", "uga": "Uganda", "moz": "Mozambique", "bih": "Bosnia And Herzegowina", "tjk": "Tajikistan", "pse": "State of Palestine", "lca": "Saint Lucia", "svn": "Slovenia", "ssd": "South Sudan", "geo": "Georgia", "nor": "Norway", "mhl": "Marshall Islands", "pak": "Pakistan", "png": "Papua New Guinea", "guf": "French Guiana", "umi": "U.S. Minor Islands", "nfk": "Norfolk Island", "zwe": "Zimbabwe", "gum": "Guam", "gbr": "United Kingdom", "guy": "Guyana", "cri": "Costa Rica", "cmr": "Cameroon", "shn": "St. Helena", "kwt": "Kuwait", "mtq": "Martinique", "wsm": "Samoa", "mda": "Moldova, Republic Of", "mdg": "Madagascar", "hti": "Haiti", "aze": "Azerbajan", "qat": "Qatar", "mar": "Morocco", "are": "United Arab Emirates", "arg": "Argentina", "sen": "Senegal", "btn": "Bhutan", "mdv": "Maldives", "arm": "Armenia", "tmp": "East Timor", "est": "Estonia", "mus": "Mauritius", "esp": "Spain", "lux": "Luxemburg", "irq": "Iraq", "bdi": "Burundi", "smr": "San Marino", "per": "Peru", "blr": "Belarus", "irl": "Ireland", "sur": "Suriname", "irn": "Iran (Islamic Republic Of)", "abw": "Aruba", "stp": "Sao Tome And Principe", "tca": "Turks And Caicos Islands", "ner": "Niger", "esh": "Western Sahara", "plw": "Palau", "ken": "Kenya", "jor": "Jordan", "spm": "St. Pierre And Miquelon", "tur": "Turkey", "omn": "Oman", "tuv": "Tuvalu", "mmr": "Myanmar", "bwa": "Botswana", "ecu": "Ecuador", "tun": "Tunisia", "swe": "Sweden", "rus": "Russia", "hkg": "Hong Kong", "asm": "American Samoa", "dza": "Algeria", "atg": "Antigua And Barbuda", "bgd": "Bangladesh", "ltu": "Lithuania", "ata": "Antartica", "isr": "Israel", "caf": "Central African Republic", "idn": "Indonesia", "bgr": "Bulgaria", "bol": "Bolivia (Plurinational State of)", "cod": "Democratic Republic of the Congo", "cog": "Congo", "isl": "Iceland", "glp": "Guadeloupe", "tha": "Thailand", "eth": "Ethiopia", "com": "Comoros", "col": "Colombia", "wlf": "Wallis And Futuna Islands", "sjm": "Svalbard And Jan Mayen Islands", "cxr": "Christmas Island", "can": "Canada", "zaf": "South Africa", "fro": "Faroe Islands", "sgs": "South Georgia And South S.S.", "som": "Somalia", "uzb": "Uzbekistan", "ukr": "Ukraine", "vir": "Virgin Islands (U.S.)", "brn": "Brunei Darussalam", "pol": "Poland", "tgo": "Togo", "dnk": "Denmark", "brb": "Barbados", "bra": "Brazil", "fra": "France", "mkd": "Macedonia", "che": "Switzerland", "usa": "United States", "chl": "Chile", "msr": "Montserrat", "chn": "China", "mex": "Mexico", "swz": "Swaziland", "ton": "Tonga", "gib": "Gibraltar", "rwa": "Rwanda", "gin": "Guinea", "kor": "Korea, Republic Of", "vat": "Holy See (Vatican City State)", "cub": "Cuba", "mco": "Monaco", "atf": "French Southern Territories", "cyp": "Cyprus", "hun": "Hungary", "kgz": "Kyrgyzstan", "fji": "Fiji", "ven": "Venezuela", "ncl": "New Caledonia", "bmu": "Bermuda", "hmd": "Heard And Mc Donald Islands", "sdn": "Sudan", "gab": "Gabon", "cym": "Cayman Islands", "svk": "Slovakia (Slovak Republic)", "dma": "Dominica", "gnq": "Equatorial Guinea", "ben": "Benin", "bel": "Belgium", "slv": "El Salvador", "mli": "Mali", "deu": "Germany", "gnb": "Guinea-Bissau", "flk": "Falkland Islands (Malvinas)", "lva": "Latvia", "civ": "C\u00f4te d'Ivoire", "mlt": "Malta", "sle": "Sierra Leone", "aia": "Anguilla", "eri": "Eritrea", "slb": "Solomon Islands", "nzl": "New Zealand", "and": "Andorra", "lbr": "Liberia", "jpn": "Japan", "lby": "Libya", "mys": "Malaysia", "pri": "Puerto Rico", "myt": "Mayotte", "prk": "Democratic People's Republic of Korea", "ant": "Netherlands Antilles", "prt": "Portugal", "khm": "Cambodia", "ind": "India", "bhs": "Bahamas", "bhr": "Bahrain", "pry": "Paraguay", "sau": "Saudi Arabia", "cze": "Czech Republic", "lie": "Liechtenstein", "fxx": "France, Metropolitan", "afg": "Afghanistan", "vut": "Vanuatu", "vgb": "Virgin Islands (British)", "nam": "Namibia", "grd": "Grenada", "nru": "Nauru", "grc": "Greece", "twn": "Taiwan, Province Of China", "grl": "Greenland", "lbn": "Lebanon", "srb": "Serbia", "pan": "Panama", "syc": "Seychelles", "npl": "Nepal", "lao": "Lao People\'s Democratic Republic", "phl": "Philippines", "kir": "Kiribati", "vnm": "Viet Nam", "iot": "British Indian Ocean Territory", "syr": "Syrian Arab Republic", "mac": "Macau", "kaz": "Kazakhstan", "cok": "Cook Islands", "pyf": "French Polynesia", "niu": "Niue", "ago": "Angola", "egy": "Egypt", "hnd": "Honduras", "dom": "Dominican Republic", "mrt": "Mauritania", "blz": "Belize", "nic": "Nicaragua", "fsm": "Micronesia, Federated States Of", "kna": "Saint Kitts And Nevis", "gha": "Ghana", "cck": "Cocos (Keeling) Islands", "ury": "Uruguay", "cpv": "Cape Verde", "tza": "United Republic of Tanzania"}

def build_additions(groups):
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
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    try:
        user = tk.get_action('organization_list_for_user')(
            context, {'id': user_id, 'permission': 'create_dataset'})
    except logic.NotAuthorized:
        base.abort(401, _('Unauthorized to see organization member list'))

    return user


def hdx_organizations_available_with_roles():
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

    count = q.count()
    q = q.offset(offset)
    q = q.limit(limit)
    tags = q.all()
    return tags, count


def package_create(context, data_dict):
    '''Create a new dataset (package).

    You must be authorized to create new datasets. If you specify any groups
    for the new dataset, you must also be authorized to edit these groups.

    Plugins may change the parameters of this function depending on the value
    of the ``type`` parameter, see the ``IDatasetForm`` plugin interface.

    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'``
    :type name: string
    :param title: the title of the dataset (optional, default: same as
        ``name``)
    :type title: string
    :param author: the name of the dataset's author (optional)
    :type author: string
    :param author_email: the email address of the dataset's author (optional)
    :type author_email: string
    :param maintainer: the name of the dataset's maintainer (optional)
    :type maintainer: string
    :param maintainer_email: the email address of the dataset's maintainer
        (optional)
    :type maintainer_email: string
    :param license_id: the id of the dataset's license, see ``license_list()``
        for available values (optional)
    :type license_id: license id string
    :param notes: a description of the dataset (optional)
    :type notes: string
    :param url: a URL for the dataset's source (optional)
    :type url: string
    :param version: (optional)
    :type version: string, no longer than 100 characters
    :param state: the current state of the dataset, e.g. ``'active'`` or
        ``'deleted'``, only active datasets show up in search results and
        other lists of datasets, this parameter will be ignored if you are not
        authorized to change the state of the dataset (optional, default:
        ``'active'``)
    :type state: string
    :param type: the type of the dataset (optional), ``IDatasetForm`` plugins
        associate themselves with different dataset types and provide custom
        dataset handling behaviour for these types
    :type type: string
    :param resources: the dataset's resources, see ``resource_create()``
        for the format of resource dictionaries (optional)
    :type resources: list of resource dictionaries
    :param tags: the dataset's tags, see ``tag_create()`` for the format
        of tag dictionaries (optional)
    :type tags: list of tag dictionaries
    :param extras: the dataset's extras (optional), extras are arbitrary
        (key: value) metadata items that can be added to datasets, each extra
        dictionary should have keys ``'key'`` (a string), ``'value'`` (a
        string)
    :type extras: list of dataset extra dictionaries
    :param relationships_as_object: see ``package_relationship_create()`` for
        the format of relationship dictionaries (optional)
    :type relationships_as_object: list of relationship dictionaries
    :param relationships_as_subject: see ``package_relationship_create()`` for
        the format of relationship dictionaries (optional)
    :type relationships_as_subject: list of relationship dictionaries
    :param groups: the groups to which the dataset belongs (optional), each
        group dictionary should have one or more of the following keys which
        identify an existing group:
        ``'id'`` (the id of the group, string), ``'name'`` (the name of the
        group, string), ``'title'`` (the title of the group, string), to see
        which groups exist call ``group_list()``
    :type groups: list of dictionaries
    :param owner_org: the id of the dataset's owning organization, see
        ``organization_list()`` or ``organization_list_for_user`` for
        available values (optional)
    :type owner_org: string

    :returns: the newly created dataset (unless 'return_id_only' is set to True
              in the context, in which case just the dataset id will be returned)
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']

    package_type = data_dict.get('type')
    package_plugin = lib_plugins.lookup_package_plugin(package_type)
    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.create_package_schema()

    _check_access('package_create', context, data_dict)

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work
                package_plugin.check_data_dict(data_dict)

    data, errors = _validate(data_dict, schema, context)
    if 'tags' in data:
        data['tags'] = get_tag_vocabulary(data['tags'])
    if 'groups' in data:
         data['extras'].append({'key':'solr_additions','value':build_additions(data['groups'])})

    log.debug('package_create validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              data.get('name'), data_dict)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Create object %s') % data.get("name")

    admins = []
    if user:
        user_obj = model.User.by_name(user.decode('utf8'))
        if user_obj:
            admins = [user_obj]
            data['creator_user_id'] = user_obj.id

    pkg = model_save.package_dict_save(data, context)
    model.setup_default_user_roles(pkg, admins)
    # Needed to let extensions know the package id
    model.Session.flush()
    data['id'] = pkg.id

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    _get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.create(pkg)

        item.after_create(context, data)

    if not context.get('defer_commit'):
        model.repo.commit()

    # need to let rest api create
    context["package"] = pkg
    # this is added so that the rest controller can make a new location
    context["id"] = pkg.id
    log.debug('Created object %s' % pkg.name)

    # Make sure that a user provided schema is not used on package_show
    context.pop('schema', None)

    return_id_only = context.get('return_id_only', False)

    output = context['id'] if return_id_only \
        else _get_action('package_show')(context, {'id': context['id']})

    return output


def pkg_topics_list(data_dict):
    pkg = model.Package.get(data_dict['id'])
    vocabulary = model.Vocabulary.get('Topics')
    topics = []
    if vocabulary:
        topics = pkg.get_tags(vocab=vocabulary)
    return topics


def get_tag_vocabulary(tags):
    for item in tags:
        tag_name = item['name'].lower()
        vocabulary = model.Vocabulary.get('Topics')
        if vocabulary:
            topic = model.Tag.by_name(name=tag_name, vocab=vocabulary)
            if topic:
                item['vocabulary_id'] = vocabulary.id
        item['name'] = tag_name
    return tags
