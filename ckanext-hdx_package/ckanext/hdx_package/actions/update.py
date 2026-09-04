'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

import datetime
import logging
import re

from six import text_type
from flask import request
from sqlalchemy import or_
from typing import Any, Dict

import ckan.lib.dictization.model_save as model_save
import ckan.lib.helpers as h
import ckan.lib.munge as munge
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
import ckan.logic.action.update as core_update
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckanext.hdx_package.helpers.resource_triggers.common
import ckanext.hdx_package.helpers.resource_triggers.geopreview as geopreview
import ckanext.hdx_package.helpers.helpers as helpers
from ckan.types.logic import ActionResult
from ckan.types import Context, DataDict
from ckan.common import _
from ckanext.hdx_org_group.helpers.org_batch import get_batch_or_generate
from ckanext.hdx_package.helpers.analytics import QACompletedAnalyticsSender
from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED, \
    BATCH_MODE, BATCH_MODE_DONT_GROUP, BATCH_MODE_KEEP_OLD
from ckanext.hdx_package.helpers.resource_processors.csrf_field_remover import remove_unwanted_csrf_field
from ckanext.hdx_package.helpers.resource_triggers import \
    BEFORE_PACKAGE_UPDATE_LISTENERS, AFTER_PACKAGE_UPDATE_LISTENERS, VERSION_CHANGE_ACTIONS
from ckanext.hdx_package.helpers.file_removal import file_remove, find_filename_in_url


_check_access = tk.check_access
_get_action = tk.get_action
_get_or_bust = tk.get_or_bust

get_or_bust = tk.get_or_bust

NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

log = logging.getLogger(__name__)

SKIP_VALIDATION = 'skip_validation'


# @fs_check.fs_check_4_resources
@geopreview.geopreview_4_resources
def resource_update(context, data_dict):
    '''
    This runs the 'resource_update' action from core ckan's update.py
    It allows us to do some minor changes and wrap it.
    '''

    id = _get_or_bust(data_dict, "id")
    model = context['model']
    resource_obj = model.Resource.get(id)
    if not resource_obj:
        log.debug('Could not find resource %s', id)
        raise NotFound(_('Resource was not found.'))

    old_resource_format = resource_obj.format

    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)

    # make the update faster (less computation in the custom package_show)
    context['no_compute_extra_hdx_show_properties'] = True

    # prev_resource_dict = _fetch_prev_resource_info(context['model'], id)
    # new_file_uploaded = bool(data_dict.get('upload'))

    if data_dict.get('resource_type', '') != 'file.upload':
        # If this isn't an upload, it is a link so make sure we update
        # the url_type otherwise solr will screw everything up
        data_dict['url_type'] = 'api'

        # we need to overwrite size field (not just setting it to None or pop) otherwise
        # ckan.lib.dictization.model_save.resource_dict_save() keeps the old value
        data_dict['size'] = 0
    else:
        try:
            if len(request.files) > 0:
                data_dict['size'] = request.content_length
                data_dict['mimetype'] = request.files['upload'].mimetype
        except RuntimeError as re:
            log.debug('This usually happens for tests when there is no HTTP request: ' + text_type(re))

    if data_dict.get('datastore_active', 'false') in ('false', 'False'):
        data_dict['datastore_active'] = False
    else:
        if data_dict.get('datastore_active', 'true') in ('true', 'True'):
            data_dict['datastore_active'] = True

    # result_dict = run_action_without_geo_preview(core_update.resource_update, context, data_dict)
    # return result_dict
    ## if new_file_uploaded:
    ##     _delete_old_file_if_necessary(prev_resource_dict, result_dict)


    # pkg_id_or_username = _get_or_bust(data_dict, 'package_id')
    # pkg = model.Package.get(pkg_id_or_username)


    pkg_id = resource_obj.package.id

    data_revise_dict = {
        "match": {"id": pkg_id},
        "filter": [
            "+resources__" + id + "__id",
            "-resources__" + id + "__*"
        ],
        "update__resources__" + id: data_dict
    }
    revise_response = run_action_without_geo_preview(core_update.package_revise, context, data_revise_dict)
    package = revise_response.get('package', {})
    if isinstance(package, str):
        package = _get_action('package_show')(context, {'id': pkg_id})

    res_list = [res for res in package.get('resources', []) if res.get('id') == id]
    resource = res_list[-1]

    if old_resource_format != resource['format']:
        _get_action('resource_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': package,
             'resource': resource})

    return resource


def run_action_without_geo_preview(action, context, data_dict):
    do_geo_preview_in_context = 'do_geo_preview' in context
    if not do_geo_preview_in_context:
        context['do_geo_preview'] = False
        result_dict = action(context, data_dict)
        context.pop('do_geo_preview', None)
    else:
        result_dict = action(context, data_dict)

    return result_dict


def _delete_old_file_if_necessary(prev_resource_dict, resource_dict):
    prev_resource_is_upload = prev_resource_dict.get('url_type') == 'upload'
    new_resource_is_api = resource_dict.get('url_type') == 'api'
    filename = find_filename_in_url(resource_dict.get('url', ''))
    munged_current_filename = munge.munge_filename(filename)
    munged_prev_filename = munge.munge_filename(prev_resource_dict['url'])
    new_file_has_same_name = munged_current_filename == munged_prev_filename
    if prev_resource_is_upload and (new_resource_is_api or not new_file_has_same_name):
        log.info(u'Deleting resource {}/{}'.format(prev_resource_dict['id'], prev_resource_dict['name']))
        file_remove(prev_resource_dict['id'], prev_resource_dict['url'], prev_resource_dict['url_type'])
    else:
        log.info(u'Not deleting resource: prev_resource_is_upload {} '
                 u'/ new_file_has_same_name {} / new_resource_is_api {}'
                 .format(prev_resource_is_upload, new_file_has_same_name, new_resource_is_api))


# def _fetch_prev_resource_info(model, resource_id):
#     id_to_resource_map = _fetch_prev_resources_info(model, [resource_id])
#     return id_to_resource_map.get(resource_id)


def _fetch_prev_resources_info(model, resource_ids):
    q = model.Session.query(model.Resource).filter(
        or_(
            model.Resource.id.in_(resource_ids), model.Resource.name.in_(resource_ids)
        )
    )
    resources = q.all()
    id_to_resource_map = {}
    for res in resources:
        id_to_resource_map[res.id] = {
            'id': res.id,
            'name': res.name,
            'url_type': res.url_type,
            'url': res.url,
        }
    return id_to_resource_map


def _normalize_supported_formats(config_value: Any) -> set[str]:
    if not config_value:
        return set()
    if isinstance(config_value, str):
        return {f.strip().lower() for f in re.split(r'[\s,]+', config_value) if f.strip()}
    normalized = set()
    for value in config_value:
        if value is None:
            continue
        if isinstance(value, str):
            normalized.update(f.strip().lower() for f in re.split(r'[\s,]+', value) if f.strip())
        else:
            normalized.add(str(value).strip().lower())
    return normalized


def _normalize_resource_url_for_comparison(url: Any, url_type: Any) -> Any:
    """
    Normalizes a url for comparison against the existing stored value.

    For url_type == 'upload': mirrors resource_dict_save()'s exact operation
    (`url.rsplit('/')[-1]`, ckan/lib/dictization/model_save.py:41) - NOT
    find_filename_in_url(), which drops query strings/fragments and would
    mask a real change like '...?version=1' -> '...?version=2'.

    For other url_types: only strips whitespace; scheme handling is left to
    _urls_match_for_comparison() below.

    Runs before validation, so a non-string url (not yet coerced by the
    schema) is returned as-is rather than crashing on .strip().
    """
    if url is None:
        return None
    if not isinstance(url, str):
        return url
    normalized = url.strip()
    if url_type == 'upload':
        return normalized.rsplit('/', 1)[-1]
    return normalized


_URL_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.\-]*:')


def _urls_match_for_comparison(existing_url: Any, incoming_url: Any) -> bool:
    """
    Compares a raw, DB-stored existing url (deliberately NOT run through
    _normalize_resource_url_for_comparison() - see package_update() for why)
    against an incoming url that already has been, without masking a genuine
    scheme change (e.g. http -> https).

    model_dictize.resource_dictize() (ckan/lib/dictization/model_dictize.py:
    132-144) prepends 'http://' to a stored url with NO scheme at all when
    not for_edit - exactly the shape of a package_show() -> edit ->
    package_update() round trip. So an existing scheme-less url matches an
    incoming url that's identical after stripping a leading 'http://' (never
    'https://'). If the existing url already has a scheme, no special-casing
    applies - a real http -> https edit is correctly seen as a change.
    """
    if existing_url == incoming_url:
        return True
    if not isinstance(existing_url, str) or not isinstance(incoming_url, str):
        return False
    if _URL_SCHEME_RE.match(existing_url):
        # existing url already has an explicit scheme - no synthesized-scheme
        # special case applies; the plain comparison above is authoritative.
        return False
    return re.sub(r'^http://', '', incoming_url, flags=re.IGNORECASE) == existing_url.lstrip('/')


def _normalize_last_modified_for_comparison(value: Any) -> Any:
    """
    Normalizes last_modified for comparison against the raw DB value.

    Mirrors isodate()'s own '' -> None conversion (ckan/logic/validators.py)
    before parsing everything else via h.date_str_to_datetime(), so
    equivalent-but-differently-formatted strings (e.g. with/without
    microseconds) compare equal, same as CKAN's own from_dict() would once
    parsed. An unparseable string is left as-is; validation further down is
    what rejects it.
    """
    if value == '':
        return None
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return h.date_str_to_datetime(value).isoformat()
        except (TypeError, ValueError):
            return value
    return value


def _last_modified_matches_for_comparison(
        existing_last_modified: Any, incoming_last_modified: Any, existing_metadata_modified: Any) -> bool:
    """
    Compares raw DB last_modified against an incoming value (both already
    normalized), matching what core's from_dict()/resource_dict_save() do
    once isodate() has parsed it - including blank -> None matching a null
    DB value.

    One deliberate addition: when the raw DB value is None, an incoming
    value equal to the resource's metadata_modified is ALSO treated as
    unchanged - tolerates get.py's read-time
    `last_modified = metadata_modified` synthesis (actions/get.py:541-542)
    surviving an untouched round trip without being seen as a new value.
    """
    if incoming_last_modified == existing_last_modified:
        return True
    if existing_last_modified is None and incoming_last_modified is not None:
        return incoming_last_modified == existing_metadata_modified
    return False


def _datastore_table_exists(resource_id: str) -> bool:
    try:
        _get_action('datastore_search')(
            {'ignore_auth': True},
            {'resource_id': resource_id, 'limit': 0, 'include_total': False}
        )
        return True
    except NotFound:
        return False


def _manage_datastore_for_uploads(context: Context, package_dict: Dict[str, Any]):
    uploaded_resource_ids = context.get(FILE_WAS_UPLOADED, set())
    if not uploaded_resource_ids:
        return

    supported_formats = _normalize_supported_formats(
        tk.config.get('ckan.datapusher.formats')
        or tk.config.get('ckanext.datapusher_plus.formats')
        or []
    )

    try:
        hdx_allowed = _get_action('hdx_is_package_allowed_for_datastore')(
            {'ignore_auth': True}, {'package_id': package_dict['id']}
        )
    except Exception:
        log.exception(
            'Could not determine datastore allowlist status for package %s — skipping datastore management',
            package_dict.get('id')
        )
        return

    for resource_id in uploaded_resource_ids:
        try:
            resource_dict = next(
                (r for r in package_dict.get('resources', []) if r.get('id') == resource_id), None
            )
            if not resource_dict:
                continue
            resource_format = (resource_dict.get('format') or '').lower()
            eligible = (
                resource_format in supported_formats
                and hdx_allowed
                and resource_dict.get('url_type') != 'datapusher'
            )
            if eligible:
                for item in plugins.PluginImplementations(plugins.IResourceController):
                    if item.name == 'datapusher_plus':
                        item._submit_to_datapusher(resource_dict)  # noqa
            elif _datastore_table_exists(resource_id):
                try:
                    _get_action('datastore_delete')(
                        {'ignore_auth': True}, {'resource_id': resource_id, 'force': True}
                    )
                    log.info('Deleted datastore for resource %s (format=%s, hdx_allowed=%s)',
                             resource_id, resource_format, hdx_allowed)
                except Exception:
                    log.exception('Failed to delete datastore for resource %s', resource_id)
        except Exception:
            # Fail open per-resource: a failure while submitting/looking up one resource's
            # datastore state must not prevent the remaining flagged resource ids in this
            # same package_update() call from being processed (see outer fail-open handling
            # in package_update()).
            log.exception('Failed to manage datastore for resource %s', resource_id)


@ckanext.hdx_package.helpers.resource_triggers.common.trigger_4_resource_changes(
    BEFORE_PACKAGE_UPDATE_LISTENERS, AFTER_PACKAGE_UPDATE_LISTENERS, VERSION_CHANGE_ACTIONS
)
def package_update(
        context: Context, data_dict: DataDict) -> ActionResult.PackageUpdate:
    '''Update a dataset (package).

    You must be authorized to edit the dataset and the groups that it belongs
    to.

    .. note:: Update methods may delete parameters not explicitly provided in the
        data_dict. If you want to edit only a specific attribute use `package_patch`
        instead.

    It is recommended to call
    :py:func:`ckan.logic.action.get.package_show`, make the desired changes to
    the result, and then call ``package_update()`` with it.

    Plugins may change the parameters of this function depending on the value
    of the dataset's ``type`` attribute, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    For further parameters see
    :py:func:`~ckan.logic.action.create.package_create`.

    :param id: the name or id of the dataset to update
    :type id: string

    :returns: the updated dataset (if ``'return_id_only'`` is ``False`` in
              the context, which is the default. Otherwise returns just the
              dataset id)
    :rtype: dictionary

    '''

    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)
    remove_unwanted_csrf_field(data_dict)

    model = context['model']
    name_or_id = data_dict.get('id') or data_dict.get('name')
    if name_or_id is None:
        raise ValidationError({'id': _('Missing value')})

    pkg = model.Package.get(name_or_id)
    if pkg is None:
        raise NotFound(_('Package was not found.'))
    context["package"] = pkg
    prev_last_modified = pkg.metadata_modified

    # Ids of every resource already belonging to this package (ANY state, including
    # 'deleted') - used ONLY for core validation/comparison semantics (id-collision
    # checks, url/last_modified diffing), matching core's unfiltered
    # session.query(model.Resource).get(id) lookup. NOT used for datastore "newness" -
    # see active_resource_ids below for that separate concern.
    #
    # We use resources_all (not `resources`, which excludes 'deleted') so a resurrected
    # id is still seen as existing here, same as core.
    #
    # Core's lookup has no package filter at all, so an id from a DIFFERENT package
    # (e.g. reused from a deleted resource in package A) is also "existing" from core's
    # POV, reassigned via package_resource_list_save() (ckan/lib/dictization/
    # model_save.py:91-100). We extend this set below with a targeted lookup for just
    # the incoming ids not already found here, to mirror that cross-package case.
    existing_resource_ids = {r.id for r in pkg.resources_all}
    # SEPARATE from existing_resource_ids - scoped to this package's currently ACTIVE
    # resources only (excludes 'deleted') - used ONLY to determine datastore "newness"
    # (resource_was_new). HDX's patched package_resource_list_save() (ckan/lib/
    # dictization/model_save.py:110-121) drops a resource's datastore table the moment
    # it leaves the active list (soft-delete). So a resurrected id in the SAME package
    # must be treated as "new" for datastore purposes even though core's validation
    # sees it as existing - otherwise its already-dropped table is never resubmitted.
    active_resource_ids = {r.id for r in pkg.resources}
    existing_resource_urls = {r.id: r.url for r in pkg.resources_all}
    # Raw DB snapshot - NOT falling back to metadata_modified (see
    # existing_resource_metadata_modified / _last_modified_matches_for_comparison for
    # that round-trip tolerance instead), so a blank/None incoming value correctly
    # matches a null raw value.
    existing_resource_last_modified = {r.id: r.last_modified for r in pkg.resources_all}
    existing_resource_metadata_modified = {r.id: r.metadata_modified for r in pkg.resources_all}

    _incoming_resource_ids = [
        r.get('id') for r in data_dict.get('resources', [])
        if isinstance(r, dict) and isinstance(r.get('id'), str) and r.get('id')
    ]
    _unknown_incoming_resource_ids = [
        r_id for r_id in _incoming_resource_ids if r_id not in existing_resource_ids
    ]
    if _unknown_incoming_resource_ids:
        matching_existing_resources = model.Session.query(model.Resource).filter(
            model.Resource.id.in_(_unknown_incoming_resource_ids)
        ).all()
        existing_resource_ids |= {resource.id for resource in matching_existing_resources}
        existing_resource_urls.update(
            {r.id: r.url for r in matching_existing_resources}
        )
        existing_resource_last_modified.update(
            {r.id: r.last_modified for r in matching_existing_resources}
        )
        existing_resource_metadata_modified.update(
            {r.id: r.metadata_modified for r in matching_existing_resources}
        )

    # immutable fields
    data_dict["id"] = pkg.id
    data_dict['type'] = pkg.type
    if 'groups' in data_dict:
        data_dict['solr_additions'] = helpers.build_additions(data_dict['groups'])

    # if 'dataset_confirm_freshness' in data_dict and data_dict['dataset_confirm_freshness'] == 'on':
    #     data_dict['review_date'] = datetime.datetime.utcnow()

    _check_access('package_update', context, data_dict)

    user = context['user']
    # get the schema

    package_plugin = lib_plugins.lookup_package_plugin(pkg.type)
    schema = context.get('schema') or package_plugin.update_package_schema()

    # Inject the existing package_creator as it should not be modifiable
    if hasattr(pkg, 'extras'):
        data_dict['package_creator'] = pkg.extras.get('package_creator', data_dict.get('package_creator'))

    # Get previous version of QA COMPLETED
    prev_qa_completed = pkg.extras.get('qa_completed') == 'true'

    # Inject a code representing the batch within which this dataset was modified
    if pkg.type == 'dataset':
        if context.get(BATCH_MODE) == BATCH_MODE_KEEP_OLD:
            try:
                batch_extras = pkg._extras.get('batch')
                if batch_extras and batch_extras.state == 'active':
                    data_dict['batch'] = batch_extras.value
            except Exception as e:
                log.info(str(e))
        elif context.get(BATCH_MODE) != BATCH_MODE_DONT_GROUP:
            data_dict['batch'] = get_batch_or_generate(data_dict.get('owner_org'))

    # Sole owner/writer of context[FILE_WAS_UPLOADED] for this call. Reset here (not
    # just setdefault) so a caller reusing the same context across multiple
    # package_update() calls doesn't carry over a stale flag from a previous call.
    context[FILE_WAS_UPLOADED] = set()

    resource_upload_ids = []
    resource_uploads = []
    resource_had_real_upload = []
    resource_was_new = []
    for resource in data_dict.get('resources', []):
        # "New for datastore" is checked against active_resource_ids (excludes
        # 'deleted'), NOT `not bool(resource.get('id'))` - a caller-supplied id for a
        # not-yet-existing resource must still count as new (resource_dict_save() does),
        # or it never gets flagged for DataPusher+/datastore management.
        #
        # Runs BEFORE validation, so a caller-supplied id may be malformed/unhashable
        # (e.g. a list) - `in`/`.get()` lookups below would raise TypeError, so we treat
        # that as "not existing" here and let validation reject it properly instead.
        resource_id = resource.get('id')
        try:
            resource_id_is_existing = resource_id in existing_resource_ids
        except TypeError:
            resource_id_is_existing = False
        try:
            resource_was_new.append(resource_id not in active_resource_ids)
        except TypeError:
            resource_was_new.append(True)

        # An existing resource's url/last_modified changing with no upload/clear_upload
        # key (e.g. a direct url edit) isn't covered by the branch below, so it must be
        # flagged here - mirrors resource_dict_save() setting obj.url_changed = True
        # (replacing the now-no-op IResourceUrlChange hook).
        #
        # url: only the INCOMING side is normalized - the EXISTING (raw, stored) side is
        # compared as-is, since core only transforms the incoming dict, never the
        # persisted value. Re-normalizing the existing side with the incoming url_type
        # would mask a real change (e.g. a url-type resource's full url collapsing to a
        # bare filename just because url_type -> 'upload'). Compared via
        # _urls_match_for_comparison() (handles CKAN's scheme-less synthesis).
        #
        # last_modified: only compared when the key is actually present (an absent key
        # means "leave unchanged", matching from_dict()'s own gate). Compared via
        # _last_modified_matches_for_comparison() (handles blank input and the
        # metadata_modified round-trip case).
        #
        # Flagged pre-validation (stage 1), like a real upload replacement.
        resource_url_type = resource.get('url_type')
        resource_url = _normalize_resource_url_for_comparison(resource.get('url'), resource_url_type)
        resource_has_last_modified_key = 'last_modified' in resource
        resource_last_modified = _normalize_last_modified_for_comparison(resource.get('last_modified'))
        existing_url = None
        existing_last_modified = None
        existing_metadata_modified = None
        if resource_id_is_existing:
            existing_url = existing_resource_urls.get(resource_id)
            existing_last_modified = _normalize_last_modified_for_comparison(
                existing_resource_last_modified.get(resource_id))
            existing_metadata_modified = _normalize_last_modified_for_comparison(
                existing_resource_metadata_modified.get(resource_id))
        if resource_id_is_existing and (
                (resource_url is not None and not _urls_match_for_comparison(existing_url, resource_url))
                or (resource_has_last_modified_key and not _last_modified_matches_for_comparison(
                    existing_last_modified, resource_last_modified, existing_metadata_modified))):
            context.setdefault(FILE_WAS_UPLOADED, set()).add(resource_id)

        # I believe that unless a resource has either an upload field or is marked to be deleted
        # we don't need to create an uploader object which is expensive
        if 'clear_upload' in resource or resource.get('upload'):
            # Flagging happens in two stages, both writing into context[FILE_WAS_UPLOADED]:
            #  1. Here, for existing resources - must happen before plugin_validate() so
            #     validators like hdx_reset_on_file_upload can read the flag during validation.
            #  2. Below (after flush), for brand-new resources, once their real id is known -
            #     they have no previous version to reset, so stage 1 doesn't apply to them.
            #
            # was_real_upload (captured before creating the uploader) is the source of truth
            # for "a new file was actually uploaded" - `upload` itself is also truthy for the
            # clear_upload branch (no new data), so using it directly would wrongly flag a
            # cleared resource as a real upload.
            was_real_upload = bool(resource.get('upload'))
            resource_had_real_upload.append(was_real_upload)

            # Gated on resource_id_is_existing (not resource.get('id') truthiness), since a
            # brand-new resource can carry a caller-supplied id. Flagging it here would wrongly
            # expose it to hdx_reset_on_file_upload, which resets QA/sensitivity fields meant
            # only for real replacements - stage 2 below still flags new resources so
            # DataPusher+ submission isn't affected.
            if was_real_upload and resource_id_is_existing:
                context.setdefault(FILE_WAS_UPLOADED, set()).add(resource['id'])

            # file uploads/clearing
            upload = uploader.get_resource_uploader(resource)
            resource_upload_ids.append(resource.get('id') or resource.get('name'))

            if 'mimetype' not in resource:
                if hasattr(upload, 'mimetype'):
                    resource['mimetype'] = upload.mimetype

            resource['size'] = upload.filesize
        else:
            upload = None
            resource_had_real_upload.append(False)
        resource_uploads.append(upload)
    ids_to_prev_resource_dict = _fetch_prev_resources_info(model, resource_upload_ids)

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_update')
    log.debug('package_update validate_errs=%r user=%s package=%s data=%r',
              errors, user, context['package'].name, data)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    #avoid revisioning by updating directly
    model.Session.query(model.Package).filter_by(id=pkg.id).update(
        {"metadata_modified": datetime.datetime.utcnow()})
    model.Session.refresh(pkg)

    include_plugin_data = False
    user_obj = context.get('auth_user_obj')
    if user_obj:
        plugin_data = data.get('plugin_data', False)
        include_plugin_data = (
            user_obj.sysadmin  # type: ignore
            and plugin_data
        )

    if 'tags' in data:
        data['tags'] = helpers.get_tag_vocabulary(data['tags'])

    pkg = modified_save(context, data, include_plugin_data)
    # pkg = model_save.package_dict_save(data, context, include_plugin_data)

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    _get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    # Needed to let extensions know the new resources ids
    model.Session.flush()
    for index, (resource, upload, was_real_upload, was_new) in enumerate(
            zip(data.get('resources', []), resource_uploads, resource_had_real_upload, resource_was_new)):
        resource['id'] = pkg.resources[index].id

        # Second flagging stage: existing resources with a real upload were already
        # flagged above (harmless no-op re-add here); brand-new resources (upload or
        # URL-only) get their first flag here, now that their real id is known -
        # eligibility is still fully decided inside _manage_datastore_for_uploads().
        #
        # Gated on was_real_upload (not `upload`, also truthy for clear_upload) to avoid
        # wrongly submitting a cleared resource to DataPusher+. Doesn't reuse
        # flag_if_file_uploaded() - it gates on resource_dict.get('upload'), which may no
        # longer be present here.
        if was_real_upload or was_new:
            context.setdefault(FILE_WAS_UPLOADED, set()).add(resource['id'])

        if upload:
            log.info('There\'s a resource in package_update() which is marked for: {}'
                     .format('clear' if upload.clear else 'upload'))
            upload.upload(resource['id'], uploader.get_max_resource_size())


    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.edit(pkg)

        item.after_dataset_update(context, data)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug('Updated object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    # Make sure that a user provided schema is not used on package_show
    context.pop('schema', None)

    # we could update the dataset so we should still be able to read it.
    context['ignore_auth'] = True
    new_data_dict = _get_action('package_show')(context, {'id': data_dict['id'], "include_plugin_data": include_plugin_data})

    # Added by HDX - triggers DataPusher+ after commit (so DB state is consistent).
    # Skipped when defer_commit is set: the caller hasn't committed yet (and may roll
    # back), so it's the deferring caller's responsibility to trigger this themselves.
    if not context.get('defer_commit'):
        try:
            _manage_datastore_for_uploads(context, new_data_dict)
        except Exception:
            # Fail open: a transient DataPusher+/datastore failure must not fail an
            # already-committed package_update() call for the caller.
            log.exception('Failed to manage datastore for package %s', new_data_dict.get('id'))
    else:
        log.info('defer_commit set on context - skipping datastore management for package %s; '
                  'caller is responsible for triggering it after the deferred commit if needed',
                  new_data_dict.get('id'))

    # HDX - delete previous files if needed
    for resource_dict in new_data_dict.get('resources'):
        prev_resource_dict = ids_to_prev_resource_dict.get(resource_dict['id'])
        if prev_resource_dict:
            _delete_old_file_if_necessary(prev_resource_dict, resource_dict)

    new_qa_completed = new_data_dict.get('qa_completed')
    if new_qa_completed != prev_qa_completed and new_data_dict.get('type') == 'dataset':
        QACompletedAnalyticsSender(new_data_dict, prev_last_modified,
                                   mark_as_set=new_qa_completed).send_to_queue()
        log.debug('new QA COMPLETED value: {}'.format(new_qa_completed))

    return data_dict['id'] if return_id_only else new_data_dict


def package_resource_reorder(context, data_dict):
    '''
    This runs the 'package_resource_reorder' action from core ckan's update.py
    It allows us to do some minor changes and wrap it.
    '''

    process_batch_mode(context, data_dict)

    context['do_geo_preview'] = False
    result_dict = core_update.package_resource_reorder(context, data_dict)

    return result_dict


def process_batch_mode(context, data_dict):
    if BATCH_MODE in data_dict:
        context[BATCH_MODE] = data_dict[BATCH_MODE]
        del data_dict[BATCH_MODE]




def process_skip_validation(context: Context, data_dict: DataDict):
    if SKIP_VALIDATION in data_dict:
        context[SKIP_VALIDATION] = data_dict[SKIP_VALIDATION]
        del data_dict[SKIP_VALIDATION]

    # allow sysadmins to set the broken link field
    user_obj: model.User = context.get('auth_user_obj')
    broken_link_field_set = (data_dict.get('broken_link') is not None) or \
                            any('broken_link' in resource for resource in data_dict.get('resources', []))
    is_sysadmin = user_obj and not user_obj.is_anonymous and user_obj.sysadmin
    if is_sysadmin and broken_link_field_set:
        context['allow_broken_link_field'] = True


def modified_save(
        context: Context, data: DataDict,
        include_plugin_data: bool = False) -> 'model.Package':
    """
    Wrapper around lib.dictization.model_save.package_dict_save
    """
    groups_key = 'groups'
    if groups_key in data:
        temp_groups = data[groups_key]
        data[groups_key] = None
        pkg = model_save.package_dict_save(data, context, include_plugin_data)
        data[groups_key] = temp_groups
    else:
        pkg = model_save.package_dict_save(data, context, include_plugin_data)
    package_membership_list_save(data.get("groups"), pkg, context)
    return pkg


def package_membership_list_save(group_dicts, package, context):
    """
    Overrides lib.dictization.model_save.package_membership_list_save
    """

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

    allowed_fields = ['indicator',
                      'package_creator',
                      'dataset_date',
                      'last_metadata_update_date',
                      'dataset_source_short_name',
                      'source_code',
                      'indicator_type',
                      'indicator_type_code',
                      'more_info',
                      'last_data_update_date',
                      'groups', 'maintainer',
                      'maintainer_email',
                      'data_update_frequency']

    package = _get_action('package_show')(context, data_dict)
    requested_groups = [el.get('id', el.get('name', '')) for el in data_dict.get('groups', [])]
    for key, value in data_dict.items():
        if key in allowed_fields:
            package[key] = value
    if not package['notes']:
        package['notes'] = ' '
    package = _get_action('package_update')(context, package)
    db_groups = [el.get('name', '') for el in package.get('groups', [])]

    if len(requested_groups) != len(db_groups):
        not_saved_groups = set(requested_groups) - set(db_groups)
        log.warn('Indicator: {} - num of groups in request is {} but only {} are in the db. Difference: {}'.
                 format(package.get('name', 'unknown'), len(requested_groups), len(db_groups),
                        ", ".join(not_saved_groups)))

    return package


def hdx_resource_update_metadata(context, data_dict):
    '''
    With the default resource_update action from core ckan you need to supply the entire resource dict
    as a parameter and you can't supply just a modified field .
    This function first loads the resource via resource_show() and then modifies the respective dict.
    '''

    process_batch_mode(context, data_dict)
    process_skip_validation(context, data_dict)

    # Below params are needed in context so that the URL of the resource is not
    # transformed to a real URL for an uploaded file
    # ( for uploaded files the url field is the filename )
    context['use_cache'] = False
    context['for_edit'] = True

    allowed_fields = ['last_data_update_date', 'shape_info', 'test_field']

    resource_was_modified = False
    resource = _get_action('resource_show')(context, data_dict)

    if data_dict.get('shape_info'):
        data_dict['shape_info'] = geopreview.add_to_shape_info_list(data_dict.get('shape_info'), resource)

    update_resource_key = 'update__resources__' + resource['id']
    revise_data_dict = {
        'match': {
            'id': resource['package_id']
        },
        update_resource_key: {}
    }

    for key, value in data_dict.items():
        if key in allowed_fields:
            resource_was_modified = True
            revise_data_dict[update_resource_key][key] = value

    if resource_was_modified:
        # we don't want the resource update to generate another
        # geopreview transformation
        context['do_geo_preview'] = False
        revise_response = _get_action('package_revise')(context, revise_data_dict)
        resource_list = revise_response.get('package', {}).get('resources', [])
        response = next(
            (r for r in resource_list if r['id'] == resource['id']),
            {'error': 'Resource not found in response from package_revise'}
        )


    else:
        response = resource

    return response


def hdx_resource_delete_metadata(context, data_dict):
    '''
    Removes an entry from the resources extras.
    Nothing happens if the field to be removed doesn't exist in the resource.

    :param id: id of the resource that will be modified
    :type id: str
    :param field_list: list of field names that should be removed
    :type field_list: list
    '''

    # Below params are needed in context so that the URL of the resource is not
    # transformed to a real URL for an uploaded file
    # ( for uploaded files the url field is the filename )
    context['use_cache'] = False
    context['for_edit'] = True

    allowed_fields = ['shape', 'test_field']

    resource_was_modified = False
    field_list = data_dict.get('field_list', [])
    resource = None
    if field_list and len(field_list) > 0:
        resource = _get_action('resource_show')(context, data_dict)
        for field in field_list:
            if field in allowed_fields and field in resource:
                del resource[field]
                resource_was_modified = True

        if resource_was_modified:
            # we don't want the resource update to generate another
            # geopreview transformation
            context['do_geo_preview'] = False
            resource = _get_action('resource_update')(context, resource)

    return resource


def resource_view_update(context, data_dict):
    '''
    Theoretically the core ckan "resource_view_update" should only need the resource_view_id for the update.
    Unfortunately, the auth needs the resource_id as well. So if it's not already there this wrapper
    function injects it.
    '''
    if not data_dict.get('resource_id'):
        model = context['model']
        resource_view = model.ResourceView.get(data_dict.get('id'))
        data_dict['resource_id'] = resource_view.resource_id
    core_update.resource_view_update(context, data_dict)


def hdx_push_resource_to_datastore(context: Context, data_dict: DataDict) -> Dict[str, Any]:
    _check_access('hdx_push_resource_to_datastore', context, data_dict)
    resource_id = data_dict.get('resource_id')
    dataset_id = data_dict.get('dataset_id')
    if not resource_id and not dataset_id:
        raise ValidationError({'resource_id': [_('Missing value')], 'dataset_id': [_('Missing value')]})

    datapusher_plugin = next(
        (item for item in plugins.PluginImplementations(plugins.IResourceController) if item.name == 'datapusher_plus'),
        None
    )
    if not datapusher_plugin:
        return {'success': False, 'message': 'Datapusher Plus plugin not found'}

    if resource_id:
        resource_dict = _get_action('resource_show')(context, {'id': resource_id})
        datapusher_plugin._submit_to_datapusher(resource_dict)
        return {'success': True, 'message': 'Resource submitted to Datapusher Plus'}

    else:
        package_dict = _get_action('package_show')(context, {'id': dataset_id})
        csv_resources = [res for res in package_dict.get('resources', []) if res.get('format', '').lower() == 'csv']
        for resource_dict in csv_resources:
            datapusher_plugin._submit_to_datapusher(resource_dict)

        if not csv_resources:
            return {'success': False, 'message': 'No CSV resources found for dataset'}

        return {
            'success': True,
            'message': 'Submitted {} CSV resource(s) to Datapusher Plus'.format(len(csv_resources))
        }
