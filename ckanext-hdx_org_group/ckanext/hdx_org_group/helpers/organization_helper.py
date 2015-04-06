'''
Created on Jan 14, 2015

@author: alexandru-m-g
'''

import logging
import pylons.config as config
import json

import ckan.logic as logic
import ckan.plugins as plugins
import ckan.lib.dictization as dictization
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization as d
import ckan.lib.navl.dictization_functions
import ckan.model as model
import ckan.logic.action.update as update
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
import paste.deploy.converters as converters

import ckanext.hdx_theme.helpers.less as less
import ckanext.hdx_theme.helpers.helpers as h

from ckan.common import _, request

log = logging.getLogger(__name__)

get_action = logic.get_action
check_access = logic.check_access
_get_or_bust = logic.get_or_bust
_validate = ckan.lib.navl.dictization_functions.validate

NotFound = logic.NotFound
ValidationError = logic.ValidationError


def sort_results_case_insensitive(results, sort_by):
    if results:
        if sort_by == 'title asc':
            return sorted(results, key=lambda x: x.get('title', '').lower())
        elif sort_by == 'title desc':
            return sorted(results, key=lambda x: x.get('title', '').lower(), reverse=True)
    return results


def hdx_get_group_activity_list(context, data_dict):
    from ckanext.hdx_package.helpers import helpers as hdx_package_helpers

    group_uuid = data_dict.get('group_uuid', None)
    if group_uuid:
        check_access('group_show', context, data_dict)

        model = context['model']
        offset = data_dict.get('offset', 0)
        limit = int(
            data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

        activity_objects = model.activity.group_activity_list(group_uuid,
                                                              limit=limit, offset=offset)
        activity_stream = model_dictize.activity_list_dictize(
            activity_objects, context)
    else:
        if 'group_type' in data_dict and data_dict['group_type'] == 'organization':
            activity_stream = get_action(
                'organization_activity_list')(context, data_dict)
        else:
            activity_stream = get_action(
                'group_activity_list')(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'group',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }
    return hdx_package_helpers._activity_list(context, activity_stream, extra_vars)

@logic.side_effect_free
def hdx_light_group_show(context, data_dict):
    id = _get_or_bust(data_dict, "id")
    group_dict = {}
    group = model.Group.get(id)
    if not group:
        raise NotFound
    #group_dict['group'] = group
    group_dict['id'] = group.id
    group_dict['name'] = group.name
    group_dict['image_url'] = group.image_url
    group_dict['display_name'] = group_dict['title'] = group.title
    group_dict['description'] = group.description
    group_dict['revision_id'] = group.revision_id

    result_list = []
    for name, extra in group._extras.iteritems():
        dictized = d.table_dictize(extra, context)
        if not extra.state == 'active':
            continue
        value = dictized["value"]
        result_list.append(dictized)

        #Keeping the above for backwards compatibility
        group_dict[name]= dictized["value"]

    group_dict['extras'] = sorted(result_list, key=lambda x: x["key"])
    return group_dict


def compile_less(result, translate_func=None):
    if 'extras' in result:
        base_color = '#0088FF'  # default value
        logo_use_org_color = "false"
        less_code_list = None
        for el in result['extras']:
            if el['key'] == 'less':
                less_code_list = el.get('value', None)
            elif el['key'] == 'customization':
                variables = el.get('value', None)
                try:
                    variables = json.loads(variables)
                    base_color = variables.get('highlight_color', '#0088FF')
                    logo_use_org_color = variables.get('use_org_color', 'false')
                except:
                    base_color = '#0088FF'
        if less_code_list:
            less_code = less_code_list.strip()
            if less_code:
                less_code = _add_custom_less_code(base_color, logo_use_org_color) + less_code
                css_dest_dir = '/organization/' + result['name']
                compiler = less.LessCompiler(less_code, css_dest_dir, result['name'],
                                             h.hdx_get_extras_element(result['extras'], value_key="modified_at"),
                                             translate_func=translate_func)
                compilation_result = compiler.compile_less()
                result['less_compilation'] = compilation_result

def _add_custom_less_code(base_color, logo_use_org_color):
    # Add base color definition
    less_code = '\n\r@wfpBlueColor: ' + base_color + ';\n\r'
    if not 'true' == logo_use_org_color:
        less_code += '@logoBackgroundColor: #FAFAFA; @logoBorderColor: #CCCCCC;'
    return less_code


def hdx_organization_update(context, data_dict):
    result = hdx_group_or_org_update(context, data_dict, is_org=True)

    compile_less(result)

    return result

def hdx_group_or_org_update(context, data_dict, is_org=False):
    # Overriding default so that orgs can have multiple images
    model = context['model']
    user = context['user']
    session = context['session']
    id = _get_or_bust(data_dict, 'id')

    group = model.Group.get(id)
    context["group"] = group
    if group is None:
        raise NotFound('Group was not found.')

    # get the schema
    group_plugin = lib_plugins.lookup_group_plugin(group.type)
    try:
        schema = group_plugin.form_to_db_schema_options({'type':'update',
                                               'api':'api_version' in context,
                                               'context': context})
    except AttributeError:
        schema = group_plugin.form_to_db_schema()

    try:
        customization = json.loads(group.extras['customization'])
    except:
        customization = {'image_sq':'','image_rect':''}

    if 'image_sq_upload' in data_dict and data_dict['image_sq_upload'] != '' and data_dict['image_sq_upload'] != None:
        upload1 = uploader.Upload('group', customization['image_sq'])
        upload1.update_data_dict(data_dict, 'image_sq',
                           'image_sq_upload', 'clear_upload')

    if 'image_sq_upload' in data_dict and data_dict['image_rect'] != '' and data_dict['image_rect'] != None:
        upload2 = uploader.Upload('group', customization['image_rect'])
        upload2.update_data_dict(data_dict, 'image_rect',
                           'image_rect_upload', 'clear_upload')

    try:
        data_dict['customization'] = json.loads(data_dict['customization'])
    except:
        data_dict['customization'] = {}

    storage_path = uploader.get_storage_path()
    ##Rearrange things the way we need them
    try:
        if data_dict['image_sq'] != '' and data_dict['image_sq'] != None:
            data_dict['customization']['image_sq'] = data_dict['image_sq']
        else:
            data_dict['customization']['image_sq'] = customization['image_sq']
    except KeyError:
        data_dict['customization']['image_sq'] = ''

    try:
        if data_dict['image_rect'] != '' and data_dict['image_rect'] != None:
            data_dict['customization']['image_rect'] = data_dict['image_rect']
        else:
            data_dict['customization']['image_rect'] = customization['image_rect']
    except KeyError:
        data_dict['customization']['image_rect'] = ''

    data_dict['customization'] = json.dumps(data_dict['customization'])

    if is_org:
        check_access('organization_update', context, data_dict)
    else:
        check_access('group_update', context, data_dict)

    if 'api_version' not in context:
        # old plugins do not support passing the schema so we need
        # to ensure they still work
        try:
            group_plugin.check_data_dict(data_dict, schema)
        except TypeError:
            group_plugin.check_data_dict(data_dict)

    data, errors = _validate(data_dict, schema, context)
    log.debug('group_update validate_errs=%r user=%s group=%s data_dict=%r',
              errors, context.get('user'),
              context.get('group').name if context.get('group') else '',
              data_dict)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user

    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Update object %s') % data.get("name")

    # when editing an org we do not want to update the packages if using the
    # new templates.
    if ((not is_org)
            and not converters.asbool(
                config.get('ckan.legacy_templates', False))
            and 'api_version' not in context):
        context['prevent_packages_update'] = True
    group = model_save.group_dict_save(data, context)

    if is_org:
        plugin_type = plugins.IOrganizationController
    else:
        plugin_type = plugins.IGroupController

    for item in plugins.PluginImplementations(plugin_type):
        item.edit(group)

    if is_org:
        activity_type = 'changed organization'
    else:
        activity_type = 'changed group'

    activity_dict = {
            'user_id': model.User.by_name(user.decode('utf8')).id,
            'object_id': group.id,
            'activity_type': activity_type,
            }
    # Handle 'deleted' groups.
    # When the user marks a group as deleted this comes through here as
    # a 'changed' group activity. We detect this and change it to a 'deleted'
    # activity.
    if group.state == u'deleted':
        if session.query(ckan.model.Activity).filter_by(
                object_id=group.id, activity_type='deleted').all():
            # A 'deleted group' activity for this group has already been
            # emitted.
            # FIXME: What if the group was deleted and then activated again?
            activity_dict = None
        else:
            # We will emit a 'deleted group' activity.
            activity_dict['activity_type'] = 'deleted group'
    if activity_dict is not None:
        activity_dict['data'] = {
                'group': dictization.table_dictize(group, context)
                }
        activity_create_context = {
            'model': model,
            'user': user,
            'defer_commit': True,
            'ignore_auth': True,
            'session': session
        }
        get_action('activity_create')(activity_create_context, activity_dict)
        # TODO: Also create an activity detail recording what exactly changed
        # in the group.

    if 'image_sq_upload' in data_dict and data_dict['image_sq']:
        upload1.upload(uploader.get_max_image_size())
    if 'image_sq_upload' in data_dict and data_dict['image_rect']:
        upload2.upload(uploader.get_max_image_size())
    if not context.get('defer_commit'):
        model.repo.commit()


    return model_dictize.group_dictize(group, context)


def recompile_everything(context):
    orgs = get_action('organization_list')(context, {'all_fields': False})
    if orgs:
        for org_name in orgs:
            org = get_action('hdx_light_group_show')(context, {'id': org_name})
            compile_less(org, translate_func=lambda str: str)
