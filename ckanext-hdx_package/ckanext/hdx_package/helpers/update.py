'''
Created on Apr 30, 2014

@author: alexandru-m-g
'''

import logging
import datetime
import json

import ckan.plugins as plugins
import ckan.logic as logic
import ckan.logic.schema as schema_
import ckan.lib.dictization as dictization
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization.model_save as model_save
import ckan.lib.navl.dictization_functions
import ckan.lib.navl.validators as validators
import ckan.lib.plugins as lib_plugins
import ckan.model as model
from ckanext.hdx_package.helpers import helpers

from ckan.common import _

log = logging.getLogger(__name__)

_check_access = logic.check_access
_get_action = logic.get_action
_validate = ckan.lib.navl.dictization_functions.validate
ValidationError = logic.ValidationError


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

def package_update(context, data_dict):
    '''Update a dataset (package).

    You must be authorized to edit the dataset and the groups that it belongs
    to.

    Plugins may change the parameters of this function depending on the value
    of the dataset's ``type`` attribute, see the ``IDatasetForm`` plugin
    interface.

    For further parameters see ``package_create()``.

    :param id: the name or id of the dataset to update
    :type id: string

    :returns: the updated dataset (if 'return_package_dict' is True in the
              context, which is the default. Otherwise returns just the
              dataset id)
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']
    name_or_id = data_dict.get("id") or data_dict['name']

    pkg = model.Package.get(name_or_id)
    if pkg is None:
        raise NotFound(_('Package was not found.'))
    context["package"] = pkg
    data_dict["id"] = pkg.id
    if 'groups' in data_dict:
        data_dict['solr_additions'] = build_additions(data_dict['groups'])

    _check_access('package_update', context, data_dict)

    # get the schema
    package_plugin = lib_plugins.lookup_package_plugin(pkg.type)
    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.update_package_schema()

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                package_plugin.check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work.
                package_plugin.check_data_dict(data_dict)

    data, errors = _validate(data_dict, schema, context)
    log.debug('package_update validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              context.get('package').name if context.get('package') else '',
              data)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Update object %s') % data.get("name")

    # avoid revisioning by updating directly
    model.Session.query(model.Package).filter_by(id=pkg.id).update(
        {"metadata_modified": datetime.datetime.utcnow()})
    model.Session.refresh(pkg)

    if 'tags' in data:
        data['tags'] = helpers.get_tag_vocabulary(data['tags'])

    pkg = modified_save(context, pkg, data)

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    org_dict = {'id': pkg.id}
    if 'owner_org' in data:
        org_dict['organization_id'] = pkg.owner_org
    _get_action('package_owner_org_update')(context_org_update,
                                            org_dict)

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.edit(pkg)

        item.after_update(context, data)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug('Updated object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    # Make sure that a user provided schema is not used on package_show
    context.pop('schema', None)

    # we could update the dataset so we should still be able to read it.
    context['ignore_auth'] = True
    output = data_dict['id'] if return_id_only \
        else _get_action('package_show')(context, {'id': data_dict['id']})

    return output


def modified_save(context, pkg, data):
    groups_key = 'groups'
    if groups_key in data:
        temp_groups = data[groups_key]
        data[groups_key] = None
        pkg = model_save.package_dict_save(data, context)
        data[groups_key] = temp_groups
    else:
        pkg = model_save.package_dict_save(data, context)
    package_membership_list_save(data.get("groups"), pkg, context)
    return pkg


def package_membership_list_save(group_dicts, package, context):

    allow_partial_update = context.get("allow_partial_update", False)
    if group_dicts is None and allow_partial_update:
        return

    capacity = 'public'
    model = context["model"]
    session = context["session"]
    pending = context.get('pending')
    user = context.get('user')

    members = session.query(model.Member) \
        .filter(model.Member.table_id == package.id) \
        .filter(model.Member.capacity != 'organization')

    group_member = dict((member.group, member)
                        for member in
                        members)
    groups = set()
    for group_dict in group_dicts or []:
        id = group_dict.get("id")
        name = group_dict.get("name")
        capacity = group_dict.get("capacity", "public")
        if capacity == 'organization':
            continue
        if id:
            group = session.query(model.Group).get(id)
        else:
            group = session.query(model.Group).filter_by(name=name).first()
        if group:
            groups.add(group)

    # need to flush so we can get out the package id
    model.Session.flush()

    # Remove any groups we are no longer in
    for group in set(group_member.keys()) - groups:
        member_obj = group_member[group]
        if member_obj and member_obj.state == 'deleted':
            continue

        member_obj.capacity = capacity
        member_obj.state = 'deleted'
        session.add(member_obj)

    # Add any new groups
    for group in groups:
        member_obj = group_member.get(group)
        if member_obj and member_obj.state == 'active':
            continue
        member_obj = group_member.get(group)
        if member_obj:
            member_obj.capacity = capacity
            member_obj.state = 'active'
        else:
            member_obj = model.Member(table_id=package.id,
                                      table_name='package',
                                      group=group,
                                      capacity=capacity,
                                      group_id=group.id,
                                      state='active')
        session.add(member_obj)


def hdx_package_update_metadata(context, data_dict):
    '''
    With the default package_update action from core ckan you need to supply the entire package 
    as a parameter, you can't supply just the modified field (or if you do, alot of fields get deleted).
    As specified in the documentation one should first load the package via package_show() and this 
    is what this function does.
    '''

    # allowed_fields = ['indicator', 'package_creator', 'methodology',
    #                   'dataset_source', 'dataset_date', 'license_other',
    #                   'license_title', 'caveats', 'name', 'title',
    #                   'last_metadata_update_date', 'dataset_source_code', 'dataset_source',
    #                   'indicator_type', 'indicator_type_code', 'dataset_summary',
    #                   'methodology', 'more_info', 'terms_of_use',
    #                   'validation_notes_and_comments', 'last_data_update_date',
    #                   'groups']

    allowed_fields = ['indicator', 'package_creator',
                      'dataset_date',
                      'last_metadata_update_date',
                      'indicator_type', 'indicator_type_code',
                      'more_info',
                      'last_data_update_date',
                      'groups']

    package = _get_action('package_show')(context, data_dict)
    requested_groups = [el.get('id', el.get('name', '')) for el in data_dict.get('groups',[])]
    for key, value in data_dict.iteritems():
        if key in allowed_fields:
            package[key] = value
    if not package['notes']:
        package['notes'] = ' '
    package = _get_action('package_update')(context, package)
    db_groups = [el.get('name','') for el in package.get('groups',[]) ]

    if len(requested_groups) != len(db_groups):
        not_saved_groups = set(requested_groups) - set(db_groups)
        log.warn('Indicator: {} - num of groups in request is {} but only {} are in the db. Difference: {}'.
                 format(package.get('name','unknown'),len(requested_groups), len(db_groups), ", ".join(not_saved_groups)))


    return package


def hdx_resource_update_metadata(context, data_dict):
    '''
    With the default resource_update action from core ckan you need to supply the entire resource dict 
    as a parameter and you can't supply just a modified field .
    This function first loads the resource via resource_show() and then modifies the respective dict. 
    '''
    allowed_fields = ['last_data_update_date']

    resource = _get_action('resource_show')(context, data_dict)
    for key, value in data_dict.iteritems():
        if key in allowed_fields:
            resource[key] = value
    resource = _get_action('resource_update')(context, resource)

    return resource
