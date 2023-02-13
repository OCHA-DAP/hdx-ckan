'''
Created on Jan 14, 2015

@author: alexandru-m-g
'''

import json
import logging
import os
import six

import ckanext.hdx_search.cli.click_feature_search_command as lunr
import ckanext.hdx_theme.helpers.helpers as h
import ckanext.hdx_users.helpers.mailer as hdx_mailer
from sqlalchemy import func
import ckanext.hdx_org_group.helpers.static_lists as static_lists

import ckan.lib.dictization as dictization
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization.model_save as model_save
import ckan.lib.helpers as helpers
import ckan.lib.navl.dictization_functions
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
import ckan.logic as logic
import ckan.logic.action as core
import ckan.model as model
import ckan.plugins as plugins
from ckan.common import _, c, config
import ckan.plugins.toolkit as toolkit
import ckan.lib.base as base

BUCKET = str(uploader.get_storage_path()) + '/storage/uploads/group/'
abort = base.abort

log = logging.getLogger(__name__)
chained_action = toolkit.chained_action
get_action = logic.get_action
check_access = logic.check_access
_get_or_bust = logic.get_or_bust
_validate = ckan.lib.navl.dictization_functions.validate

NotFound = logic.NotFound
ValidationError = logic.ValidationError


def filter_and_sort_results_case_insensitive(results, sort_by, q=None, has_datasets=False):
    '''
    :param results: list of organizations to filter/sort
    :type results: list[dict]
    :param sort_by:
    :type sort_by: str
    :param q:
    :type q: str
    :param has_datasets: True if it should filter out orgs without at least one datasets
    :type has_datasets: bool
    :return: sorted/filtered list
    :rtype: list[dict]
    '''

    filtered_results = results
    if q:
        q = q.lower()
        filtered_results = [org for org in filtered_results
                            if q in org.get('title', '').lower() or q in org.get('name', '')
                            or q in org.get('description', '').lower()]
    if has_datasets:
        filtered_results = [org for org in filtered_results if 'package_count' in org and org['package_count']]

    if filtered_results:
        if sort_by == 'title asc':
            return sorted(filtered_results, key=lambda x: x.get('title', '').lower())
        elif sort_by == 'title desc':
            return sorted(filtered_results, key=lambda x: x.get('title', '').lower(), reverse=True)
        elif sort_by == 'datasets desc':
            return sorted(filtered_results, key=lambda x: x.get('package_count', 0), reverse=True)
        elif sort_by == 'datasets asc':
            return sorted(filtered_results, key=lambda x: x.get('package_count', 0))
        elif sort_by == 'popularity':
            pass
    return filtered_results


# def hdx_get_featured_orgs(context, data_dict):
#     orgs = list()
#     # Pull resource with data on our featured orgs
#     resource_id = config.get('hdx.featured_org_config')  # Move this to common_config once data team has set things up
#     user = context.get('user')
#     userobj = context.get('auth_user_obj')
#     reset_thumbnails = data_dict.get('reset_thumbnails', 'false')
#     featured_config = get_featured_orgs_config(user, userobj, resource_id)
#
#     for cfg in featured_config:
#         # getting the first 3 rows/organizations
#         if len(orgs) < 3:
#             # Check for screencap
#             file_path = BUCKET + cfg.get('org_name') + '_thumbnail.png'
#             exists = os.path.isfile(file_path)
#             expired = False
#             if exists:
#                 timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
#                 expire = timestamp + timedelta(days=7)
#                 expired = datetime.utcnow() > expire
#             reset = not exists or expired
#             if reset or reset_thumbnails == 'true':
#                 # Build new screencap
#                 context['reset'] = reset
#                 context['file_path'] = file_path
#                 context['cfg'] = cfg
#                 log.info("Triggering screenshot for " + cfg.get('org_name'))
#                 get_action('hdx_trigger_screencap')(context, data_dict)
#
#             org_dict = get_action('organization_show')(context, {'id': cfg.get('org_name')})
#
#             # Build highlight data
#             org_dict['highlight'] = get_featured_org_highlight(context, org_dict, cfg)
#
#             # checking again here if the file was generated
#             exists = os.path.isfile(file_path)
#             if exists:
#                 org_dict['featured_org_thumbnail'] = "/image/" + cfg['org_name'] + '_thumbnail.png'
#             else:
#                 org_dict['featured_org_thumbnail'] = "/images/featured_orgs_placeholder" + str(len(orgs)) + ".png"
#             orgs.append(org_dict)
#     return orgs


def get_viz_title_from_extras(org_dict):
    try:
        for item in org_dict.get('extras'):
            if item.get('key') == 'visualization_config':
                result = json.loads(item.get('value')).get('vis-title') or json.loads(item.get('value')).get(
                    'viz-title')
                return result
    except:
        return None
    return None


def get_value_dict_from_extras(org_dict, key='visualization_config'):
    try:
        for item in org_dict.get('extras'):
            if item.get('key') == key:
                return json.loads(item.get('value'))
    except:
        return None
    return None


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


# def get_featured_orgs_config(user, userobj, resource_id):
#     context = {'model': model, 'session': model.Session,
#                'user': user, 'for_view': True,
#                'auth_user_obj': userobj}
#     featured_org_dict = {
#         'datastore_config': {
#             'resource_id': resource_id
#         }
#     }
#     datastore_access = data_access.DataAccess(featured_org_dict)
#     datastore_access.fetch_data_generic(context)
#     org_items = datastore_access.get_top_line_items()
#
#     return org_items


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


# def compile_less(result, translate_func=None):
#     return True
    # base_color = '#007CE0'  # default value
    # logo_use_org_color = "false"
    #
    # def get_value_from_result(key):
    #     value = result.get(key)
    #     if not value:
    #         extra = next((e for e in (result.get('extras') or []) if e['key'] == key), None)
    #         if extra:
    #             value = extra.get('value')
    #     return value
    #
    # less_code_list = get_value_from_result('less')
    # customization = get_value_from_result('customization')
    #
    # if customization:
    #     try:
    #         variables = json.loads(customization)
    #         base_color = variables.get('highlight_color', '#007CE0') or '#007CE0'
    #         logo_use_org_color = variables.get('use_org_color', 'false')
    #     except:
    #         base_color = '#007CE0'
    #
    # if less_code_list:
    #     less_code = less_code_list.strip()
    #     if less_code:
    #         less_code = _add_custom_less_code(base_color, logo_use_org_color) + less_code
    #         css_dest_dir = '/organization/' + result['name']
    #         compiler = less.LessCompiler(less_code, css_dest_dir, result['name'],
    #                                      h.hdx_get_extras_element(result, value_key="modified_at"),
    #                                      translate_func=translate_func)
    #         compilation_result = compiler.compile_less()
    #         result['less_compilation'] = compilation_result


# def _add_custom_less_code(base_color, logo_use_org_color):
#     # Add base color definition
#     less_code = '\n\r@wfpBlueColor: ' + base_color + ';\n\r'
#     if not 'true' == logo_use_org_color:
#         less_code += '@logoBackgroundColor: #FAFAFA; @logoBorderColor: #CCCCCC;'
#     return less_code


def hdx_organization_update(context, data_dict):
    test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    result = hdx_group_or_org_update(context, data_dict, is_org=True)
    if not test:
        lunr.build_index()

    # hdx_generate_embedded_preview(result)
    return result


# def hdx_generate_embedded_preview(result):
#     org_name = result.get('name') or result.get('id')
#     vis_config = get_value_dict_from_extras(result, 'visualization_config')
#     if vis_config and vis_config.get('visualization-select') == 'embedded-preview':
#         selector = vis_config.get('vis-preview-selector', None)
#         url = vis_config.get('vis-url')
#         file_path = BUCKET + org_name + '_embedded_preview.png'
#         hdx_capturejs(url, file_path, selector, renderdelay=15000)
#         return True
#     return False


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

def _check_user_is_maintainer(context, user_id, org_id):
    group = model.Group.get(org_id)
    result = logic.get_action('package_search')(context, {
        'q': '*:*',
        'fq': 'maintainer:{0}, organization:{1}'.format(user_id, group.name),
        'rows': 100,
    })

    if len(result['results']) > 0:
        return True
    return False

@chained_action
def organization_member_delete(original_action, context, data_dict):
    user_id = data_dict.get('user_id') or data_dict.get('user')
    if not user_id:
        user_id = model.User.get(data_dict.get('username')).id

    if _check_user_is_maintainer(context, user_id, data_dict.get('id')):
        abort(403, _('User is set as maintainer for datasets belonging to this org. Can\t delete, please change maintainer first'))

    return original_action(context, data_dict)

@chained_action
def organization_member_create(original_action, context, data_dict):
    user_id = data_dict.get('user') or data_dict.get('user_id')
    if not user_id:
        user_id = model.User.get(data_dict.get('username')).id

    if data_dict.get('role') == 'member':
        if _check_user_is_maintainer(context, user_id, data_dict.get('id')):
            abort(403, _('User is set as maintainer for datasets belonging to this org. Can\'t change role to \'member\', please change maintainer first'))

    return original_action(context, data_dict)

def hdx_organization_create(context, data_dict):
    data_dict['type'] = 'organization'
    test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
    result = hdx_group_or_org_create(context, data_dict, is_org=True)
    if not test:
        lunr.build_index()

    # hdx_generate_embedded_preview(result)
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
        lunr.build_index()
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

    data_dict['type'] = group.type

    # get the schema
    group_plugin = lib_plugins.lookup_group_plugin(group.type)
    try:
        schema = group_plugin.form_to_db_schema_options({'type': 'update',
                                                         'api': 'api_version' in context,
                                                         'context': context})
    except AttributeError:
        schema = group_plugin.form_to_db_schema()

    if is_org:
        check_access('organization_update', context, data_dict)
    else:
        check_access('group_update', context, data_dict)


    try:
        customization = json.loads(group.extras['customization'])
    except:
        customization = {'image_sq': '', 'image_rect': ''}

    try:
        data_dict['customization'] = json.loads(data_dict['customization'])
    except:
        data_dict['customization'] = {}

    # If we're removing the image
    upload_sq = _manage_image_upload_for_org('image_sq', customization, data_dict)
    upload_rect = _manage_image_upload_for_org('image_rect', customization, data_dict)

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
        'organization_update' if is_org else 'group_update')
    log.debug('group_update validate_errs=%r user=%s group=%s data_dict=%r',
              errors, context.get('user'),
              context.get('group').name if context.get('group') else '',
              data_dict)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    contains_packages = 'packages' in data_dict

    group = model_save.group_dict_save(
        data, context,
        prevent_packages_update=is_org or not contains_packages
    )

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
            'user_id': model.User.by_name(six.ensure_text(user)).id,
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
            activity_dict['activity_type'] = \
                'deleted organization' if is_org else 'deleted group'
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

    if upload_sq:
        upload_sq.upload(uploader.get_max_image_size())

    if upload_rect:
        upload_rect.upload(uploader.get_max_image_size())

    if not context.get('defer_commit'):
        model.repo.commit()

    return model_dictize.group_dictize(group, context)


def _manage_image_upload_for_org(image_field, customization, data_dict):
    clear_field = 'clear_{}'.format(image_field)
    if clear_field in data_dict and data_dict[clear_field]:
        remove_image(customization[image_field])
        data_dict['customization'][image_field] = ''
        # customization[image_field] = ''

    upload_field = '{}_upload'.format(image_field)
    if data_dict.get(upload_field):
        # If old image exists remove it
        if customization[image_field]:
            remove_image(customization[image_field])

        upload_obj = uploader.Upload('group', customization[image_field])
        upload_obj.update_data_dict(data_dict, image_field,
                                 upload_field, 'clear_upload')

        return upload_obj
    return None


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

    # try:
    #     customization = json.loads(group.extras['customization'])
    # except:
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
        except TypeError as e:
            group_plugin.check_data_dict(data_dict)

    data, errors = lib_plugins.plugin_validate(
        group_plugin, context, data_dict, schema,
        'organization_create' if is_org else 'group_create')
    log.debug('group_create validate_errs=%r user=%s group=%s data_dict=%r',
              errors, context.get('user'), data_dict.get('name'), data_dict)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    group = model_save.group_dict_save(data, context)

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

    user_id = model.User.by_name(six.ensure_text(user)).id

    activity_dict = {
        'user_id': user_id,
        'object_id': group.id,
        'activity_type': activity_type,
        'data': {
            'group': ckan.lib.dictization.table_dictize(group, context)
        }
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

    return_id_only = context.get('return_id_only', False)
    action = 'organization_show' if is_org else 'group_show'

    output = context['id'] if return_id_only \
        else get_action(action)(context, {'id': group.id})

    return output


# def recompile_everything(context):
#     orgs = get_action('organization_list')(context, {'all_fields': False})
#     if orgs:
#         for org_name in orgs:
#             org = get_action('hdx_light_group_show')(context, {'id': org_name})
#             compile_less(org, translate_func=lambda str: str)


# def hdx_capturejs(uri, output_file, selector, renderdelay=90000, waitcapturedelay=10000, viewportsize='1200x800'):
#     quoted_selector = '"{}"'.format(selector)
#     screenshot_creator = ScreenshotCreator(uri, output_file, quoted_selector,
#                                            renderdelay=renderdelay, waitcapturedelay=waitcapturedelay,
#                                            http_timeout=None,
#                                            viewportsize=viewportsize, mogrify=True, resize='40%')
#     return screenshot_creator.execute()

def notify_admins(data_dict):
    try:
        if data_dict.get('admins'):
            # for admin in data_dict.get('admins'):
            hdx_mailer.mail_recipient(data_dict.get('admins'), data_dict.get('subject'), data_dict.get('message'))
    except Exception as e:
        log.error("Email server error: can not send email to admin users" + e.message)
        return False
    log.info("admin users where notified by email")
    return True


def hdx_user_in_org_or_group(group_id, include_pending=False):
    '''
    Based on user_in_org_or_group() from ckan.lib.helpers.
    Added a flag that includes "pending" requests in the check.
    Useful for not showing the "request membership" option for a user that already has done the request.
    :param group_id:
    :type group_id: str
    :param include_pending: if it should include the "pending" state in the check ( not just the "active") (optional)
    :type include_pending: bool
    :return: True if the user belongs to the group or org. Otherwise False
    :rtype: bool
    '''

    # we need a user
    if not c.userobj:
        return False
    # sysadmins can do anything
    if c.userobj.sysadmin:
        return True

    checked_states = ['active']
    if include_pending:
        checked_states.append('pending')

    query = model.Session.query(func.count(model.Member.id)) \
        .filter(model.Member.state.in_(checked_states)) \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.group_id == group_id) \
        .filter(model.Member.table_id == c.userobj.id)
    length = query.all()[0][0]
    return length != 0


def hdx_organization_type_list(include_default_value=None):
    result = []
    if include_default_value:
        result.append({'value': '-1', 'text': _('-- Please select --')})
    result.extend([{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST])
    # return [{'value': '-1', 'text': _('-- Please select --')}] + \
    #        [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]
    return result


def _find_last_update_for_orgs(org_names):
    org_to_update_time = {}
    if org_names:
        context = {
            'model': model,
            'session': model.Session
        }
        filter = 'organization:({}) +dataset_type:dataset'.format(' OR '.join(org_names))

        data_dict = {
            'q': '',
            'fq': filter,
            'fq_list': ['{!collapse field=organization nullPolicy=expand sort="metadata_modified desc"} '],
            'rows': len(org_names),
            'start': 0,
            'sort': 'metadata_modified desc'
        }
        query = get_action('package_search')(context, data_dict)
        org_to_update_time = {d['organization']['name']: d.get('metadata_modified') for d in query['results']}
    return org_to_update_time


def org_add_last_updated_field(displayed_orgs):
    org_to_last_update = _find_last_update_for_orgs([o.get('name') for o in displayed_orgs])
    for o in displayed_orgs:
        o['dataset_last_updated'] = org_to_last_update.get(o['name'], o.get('created'))


def hdx_organization_type_get_value(org_type_key):
    return next((org_type[0] for org_type in static_lists.ORGANIZATION_TYPE_LIST if org_type[1] == org_type_key),
                org_type_key)
