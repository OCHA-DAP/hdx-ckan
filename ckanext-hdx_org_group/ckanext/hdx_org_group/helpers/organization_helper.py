'''
Created on Jan 14, 2015

@author: alexandru-m-g
'''

import logging
import json
import os

import pylons.config as config

import ckan.logic as logic
import ckan.plugins as plugins
import ckan.lib.dictization as dictization
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization.model_save as model_save
import ckan.lib.navl.dictization_functions
import ckanext.hdx_crisis.dao.data_access as data_access
import ckan.model as model
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
import paste.deploy.converters as converters
import ckanext.hdx_theme.helpers.less as less
import ckanext.hdx_theme.helpers.helpers as h
import ckan.lib.helpers as helpers
import ckan.logic.action as core
import ckanext.hdx_search.command as lunr
import shlex
import subprocess
import random
from datetime import datetime, timedelta
from ckan.common import _

BUCKET = str(uploader.get_storage_path()) + '/storage/uploads/group/'

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
        elif sort_by == 'datasets desc':
            return sorted(results, key=lambda x: x.get('packages', 0), reverse=True)
        elif sort_by == 'datasets asc':
            return sorted(results, key=lambda x: x.get('packages', 0))
        elif sort_by == 'popularity':
            pass
    return results


def hdx_get_featured_orgs(context, data_dict):
    orgs = list()
    # Pull resource with data on our featured orgs
    resource_id = config.get('hdx.featured_org_config')  # Move this to common_config once data team has set things up
    user = context.get('user')
    userobj = context.get('auth_user_obj')
    reset_thumbnails = data_dict.get('reset_thumbnails', 'false')
    featured_config = get_featured_orgs_config(user, userobj, resource_id)

    for cfg in featured_config:
        # getting the first 3 rows/organizations
        if len(orgs) < 3:
            # Check for screencap
            file_path = BUCKET + cfg.get('org_name') + '_thumbnail.png'
            exists = os.path.isfile(file_path)
            expired = False
            if exists:
                timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
                expire = timestamp + timedelta(days=7)
                expired = datetime.utcnow() > expire
            reset = not exists or expired
            if reset or reset_thumbnails == 'true':
                # Build new screencap
                context['reset'] = reset
                context['file_path'] = file_path
                context['cfg'] = cfg
                log.info("Triggering screenshot for " + cfg.get('org_name'))
                get_action('hdx_trigger_screencap')(context, data_dict)
                # trigger_screencap(file_path, cfg)
                # check again if file exists

            # context = {'model': model, 'session': model.Session,
            #            'user': user, 'for_view': True,
            #            'auth_user_obj': userobj}
            org_dict = get_action('organization_show')(context, {'id': cfg.get('org_name')})

            # Build highlight data
            org_dict['highlight'] = get_featured_org_highlight(context, org_dict, cfg)

            # checking again here if the file was generated
            exists = os.path.isfile(file_path)
            if exists:
                org_dict['featured_org_thumbnail'] = "/image/" + cfg['org_name'] + '_thumbnail.png'
            else:
                org_dict['featured_org_thumbnail'] = "/images/featured_orgs_placeholder" + str(len(orgs)) + ".png"
            orgs.append(org_dict)
    return orgs


# def trigger_screencap(file_path, cfg):
#     if not cfg['screen_cap_asset_selector']:  # If there's no selector set just don't bother
#         return False
#     try:
#         command = 'capturejs -l --uri "' + config['ckan.site_url'] + helpers.url_for('organization_read', id=cfg[
#             'org_name']) + '" --output ' + file_path + ' --selector "' + cfg['screen_cap_asset_selector'] + '"' + ' --timeout 10000'
#         args = shlex.split(command)
#         subprocess.Popen(args)
#         return True
#     except:
#         return False


def get_viz_title_from_extras(org_dict):
    try:
        for item in org_dict.get('extras'):
            if item.get('key') == 'visualization_config':
                return json.loads(item.get('value')).get('viz-title')
    except:
        return None
    return None


# def get_featured_org_highlight(context, org_dict, config):
#     if config.get('highlight_asset_type') == 'dataset':
#         if config.get('highlight_asset_id'):
#             try:
#                 choice = get_action('package_show')(context, {'id': config['highlight_asset_id']})
#                 return {'link': helpers.url_for('dataset_read', id=choice['id']), 'description': 'Popular Dataset: ',
#                         'type': 'dataset', 'title': choice['title']}
#             except:
#                 return {'link': '', 'description': '', 'type': 'dataset', 'title': ''}
#         else:
#             # select a dataset at random (sort of)
#             if len(org_dict['packages']) > 0:
#                 choice = random.choice(org_dict['packages'])
#                 return {'link': helpers.url_for('dataset_read', id=choice['name']), 'description': 'Popular Dataset: ',
#                         'type': 'dataset', 'title': choice['title']}
#             else:
#                 return {'link': '', 'description': '', 'type': 'dataset', 'title': ''}
#     else:
#         topline_default = org_url = [el.get('value', None) for el in org_dict.get('extras', []) if
#                                      el.get('key', '') == 'topline_resource']
#         if config.get('highlight_asset_row_code'):
#             top_line_src_dict = {
#                 'top-line-numbers': {
#                     'resource_id': config['highlight_asset_id'] if config.get('highlight_asset_id') else topline_default
#                 }
#             }
#             datastore_access = data_access.DataAccess(top_line_src_dict)
#             datastore_access.fetch_data(context)
#             top_line_items = datastore_access.get_top_line_items()
#             if len(top_line_items) > 0:
#                 choice = top_line_items[config['highlight_asset_row_code']]
#                 return {'link': '', 'description': 'Key Figures: ', 'type': 'topline', 'title': choice['title']}
#             else:
#                 return {'link': '', 'description': '', 'type': 'topline', 'title': ''}
#
#         else:
#             # select a line at random
#             top_line_src_dict = {
#                 'top-line-numbers': {
#                     'resource_id': config['highlight_asset_id'] if config.get('highlight_asset_id') else topline_default
#                 }
#             }
#             datastore_access = data_access.DataAccess(top_line_src_dict)
#             datastore_access.fetch_data(context)
#             top_line_items = datastore_access.get_top_line_items()
#             if len(top_line_items) > 0:
#                 choice = random.choice(top_line_items)
#                 return {'link': '', 'description': 'Key Figures: ', 'type': 'topline', 'title': choice['title']}
#             else:
#                 return {'link': '', 'description': '', 'type': 'topline', 'title': ''}


def get_featured_org_highlight(context, org_dict, config):
    link = helpers.url_for('organization_read', id=org_dict.get('name'))
    title = ''
    description = ''
    if config.get('highlight_asset_type').strip().lower() == 'key figures':
        description = 'Key Figures'
        link += '#key-figures'
    if config.get('highlight_asset_type').strip().lower() == 'interactive data':
        description = 'Interactive Data: '
        link += '#interactive-data'
        title = get_viz_title_from_extras(org_dict)
    return {'link': link, 'description': description, 'type': config.get('highlight_asset_type'), 'title': title}


def get_featured_orgs_config(user, userobj, resource_id):
    context = {'model': model, 'session': model.Session,
               'user': user, 'for_view': True,
               'auth_user_obj': userobj}
    featured_org_dict = {
        'datastore_config': {
            'resource_id': resource_id
        }
    }
    datastore_access = data_access.DataAccess(featured_org_dict)
    datastore_access.fetch_data_generic(context)
    org_items = datastore_access.get_top_line_items()

    return org_items


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
                    base_color = variables.get('highlight_color', '#0088FF') or '#0088FF'
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
    test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    result = hdx_group_or_org_update(context, data_dict, is_org=True)
    if not test:
        lunr.buildIndex('ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search')
    compile_less(result)

    return result


def remove_image(filename):
    if not filename.startswith('http'):
        try:
            os.remove(uploader.get_storage_path() + '/storage/uploads/group/' + filename)
        except:
            return False
    return True


def hdx_group_create(context, data_dict):
    return _run_core_group_org_action(context, data_dict, core.create.group_create)


def hdx_group_update(context, data_dict):
    return _run_core_group_org_action(context, data_dict, core.update.group_update)


def hdx_group_delete(context, data_dict):
    return _run_core_group_org_action(context, data_dict, core.delete.group_delete)


def hdx_organization_create(context, data_dict):
    data_dict['type'] = 'organization'
    test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    result = hdx_group_or_org_create(context, data_dict, is_org=True)
    if not test:
        lunr.buildIndex('ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search')
    compile_less(result)
    return result


def hdx_organization_delete(context, data_dict):
    return _run_core_group_org_action(context, data_dict, core.delete.organization_delete)


def _run_core_group_org_action(context, data_dict, core_action):
    '''
    Runs core ckan action with lunr update
    '''
    test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    result = core_action(context, data_dict)
    if not test:
        lunr.buildIndex('ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search')
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

    if is_org:
        check_access('organization_update', context, data_dict)
    else:
        check_access('group_update', context, data_dict)

    # get the schema
    group_plugin = lib_plugins.lookup_group_plugin(group.type)
    try:
        schema = group_plugin.form_to_db_schema_options({'type': 'update',
                                                         'api': 'api_version' in context,
                                                         'context': context})
    except AttributeError:
        schema = group_plugin.form_to_db_schema()

    try:
        customization = json.loads(group.extras['customization'])
    except:
        customization = {'image_sq': '', 'image_rect': ''}

    try:
        data_dict['customization'] = json.loads(data_dict['customization'])
    except:
        data_dict['customization'] = {}


    # If we're removing the image
    if 'clear_image_sq' in data_dict and data_dict['clear_image_sq']:
        remove_image(customization['image_sq'])
        data_dict['customization']['image_sq'] = ''
        customization['image_rect'] = ''

    if 'clear_image_rect' in data_dict and data_dict['clear_image_rect']:
        remove_image(customization['image_rect'])
        data_dict['customization']['image_rect'] = ''
        customization['image_rect'] = ''

    if 'image_sq_upload' in data_dict and data_dict['image_sq_upload'] != '' and data_dict['image_sq_upload'] != None:
        # If old image was uploaded remove it
        if customization['image_sq']:
            remove_image(customization['image_sq'])

        upload1 = uploader.Upload('group', customization['image_sq'])
        upload1.update_data_dict(data_dict, 'image_sq',
                                 'image_sq_upload', 'clear_upload')

    if 'image_rect_upload' in data_dict and data_dict['image_rect_upload'] != '' and data_dict[
        'image_rect_upload'] != None:
        if customization['image_rect']:
            remove_image(customization['image_rect'])
        upload2 = uploader.Upload('group', customization['image_rect'])
        upload2.update_data_dict(data_dict, 'image_rect',
                                 'image_rect_upload', 'clear_upload')

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

    try:
        upload1.upload(uploader.get_max_image_size())
    except:
        pass

    try:
        upload2.upload(uploader.get_max_image_size())
    except:
        pass

    if not context.get('defer_commit'):
        model.repo.commit()

    return model_dictize.group_dictize(group, context)

def hdx_group_or_org_create(context, data_dict, is_org=False):
    # Overriding default so that orgs can have multiple images
    
    model = context['model']
    user = context['user']
    session = context['session']
    data_dict['is_organization'] = is_org

    if is_org:
        check_access('organization_create', context, data_dict)
    else:
        check_access('group_create', context, data_dict)

    # get the schema
    group_type = data_dict.get('type')
    group_plugin = lib_plugins.lookup_group_plugin(group_type)
    try:
        schema = group_plugin.form_to_db_schema_options({
            'type': 'create', 'api': 'api_version' in context,
            'context': context})
    except AttributeError:
        schema = group_plugin.form_to_db_schema()

    try:
        customization = json.loads(group.extras['customization'])
    except:
        customization = {'image_sq': '', 'image_rect': ''}

    try:
        data_dict['customization'] = json.loads(data_dict['customization'])
    except:
        data_dict['customization'] = {}

    if 'image_sq_upload' in data_dict and data_dict['image_sq_upload'] != '' and data_dict['image_sq_upload'] != None:
        # If old image was uploaded remove it
        if customization['image_sq']:
            remove_image(customization['image_sq'])

        upload1 = uploader.Upload('group', customization['image_sq'])
        upload1.update_data_dict(data_dict, 'image_sq',
                                 'image_sq_upload', 'clear_upload')

    if 'image_rect_upload' in data_dict and data_dict['image_rect_upload'] != '' and data_dict[
        'image_rect_upload'] != None:
        if customization['image_rect']:
            remove_image(customization['image_rect'])
        upload2 = uploader.Upload('group', customization['image_rect'])
        upload2.update_data_dict(data_dict, 'image_rect',
                                 'image_rect_upload', 'clear_upload')

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

    if 'api_version' not in context:
        # old plugins do not support passing the schema so we need
        # to ensure they still work
        try:
            group_plugin.check_data_dict(data_dict, schema)
        except TypeError:
            group_plugin.check_data_dict(data_dict)

    data, errors = lib_plugins.plugin_validate(
        group_plugin, context, data_dict, schema,
        'organization_create' if is_org else 'group_create')
    log.debug('group_create validate_errs=%r user=%s group=%s data_dict=%r',
              errors, context.get('user'), data_dict.get('name'), data_dict)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user

    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Create object %s') % data.get("name")

    group = model_save.group_dict_save(data, context)

    if user:
        admins = [model.User.by_name(user.decode('utf8'))]
    else:
        admins = []
    model.setup_default_user_roles(group, admins)
    # Needed to let extensions know the group id
    session.flush()

    if is_org:
        plugin_type = plugins.IOrganizationController
    else:
        plugin_type = plugins.IGroupController

    for item in plugins.PluginImplementations(plugin_type):
        item.create(group)

    if is_org:
        activity_type = 'new organization'
    else:
        activity_type = 'new group'

    user_id = model.User.by_name(user.decode('utf8')).id

    activity_dict = {
        'user_id': user_id,
        'object_id': group.id,
        'activity_type': activity_type,
    }
    activity_dict['data'] = {
        'group': ckan.lib.dictization.table_dictize(group, context)
    }
    activity_create_context = {
        'model': model,
        'user': user,
        'defer_commit': True,
        'ignore_auth': True,
        'session': session
    }
    logic.get_action('activity_create')(activity_create_context, activity_dict)

    try:
        upload1.upload(uploader.get_max_image_size())
    except:
        pass

    try:
        upload2.upload(uploader.get_max_image_size())
    except:
        pass

    if not context.get('defer_commit'):
        model.repo.commit()
    context["group"] = group
    context["id"] = group.id

    # creator of group/org becomes an admin
    # this needs to be after the repo.commit or else revisions break
    member_dict = {
        'id': group.id,
        'object': user_id,
        'object_type': 'user',
        'capacity': 'admin',
    }
    member_create_context = {
        'model': model,
        'user': user,
        'ignore_auth': True,  # we are not a member of the group at this point
        'session': session
    }
    logic.get_action('member_create')(member_create_context, member_dict)

    log.debug('Created object %s' % group.name)
    return model_dictize.group_dictize(group, context)

def recompile_everything(context):
    orgs = get_action('organization_list')(context, {'all_fields': False})
    if orgs:
        for org_name in orgs:
            org = get_action('hdx_light_group_show')(context, {'id': org_name})
            compile_less(org, translate_func=lambda str: str)
