import logging
import json

import sqlalchemy

import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.search as search
import ckan.authz as new_authz
import ckan.model as model
import ckan.logic.action.get as ckan_get

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_theme.helpers.counting_actions as counting
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_theme.hxl.transformers.transformers as transformers
import ckan.authz as authz

from ckanext.hdx_theme.helpers.hdx_stats import HDXStatsHelper
from ckanext.hdx_theme.hxl.proxy import do_hxl_transformation, transform_response_to_dict_list

from ckanext.hdx_theme.util.analytics_stats import HDXStats, HDXStatsAnalyticsSender

_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
config = tk.config
g = tk.g
_ = tk._
NotFound = logic.NotFound

log = logging.getLogger(__name__)


def member_list(context, data_dict=None):
    '''Return the members of a group.

    Modified copy of the original ckan member_list action to also return
    the non-translated capacity (role)

    :rtype: list of (id, type, translated capacity, capacity ) tuples

    '''
    model = context['model']

    group = model.Group.get(_get_or_bust(data_dict, 'id'))
    if not group:
        raise logic.NotFound
    # user = context.get('user')
    if group.state == 'deleted' and (not g.userobj or not g.userobj.sysadmin):
        raise logic.NotFound

    obj_type = data_dict.get('object_type', None)
    capacity = data_dict.get('capacity', None)
    show_user_info = data_dict.get('user_info', False)
    show_sysadmin_info = data_dict.get('sysadmin_info', False)
    q_term = data_dict.get('q', None)

    # User must be able to update the group to remove a member from it
    _check_access('group_show', context, data_dict)

    q = model.Session.query(model.Member, model.User). \
        filter(model.Member.table_id == model.User.id). \
        filter(model.Member.group_id == group.id). \
        filter(model.Member.state == "active")

    if q_term and q_term != '':
        q = q.filter(sqlalchemy.or_(
            model.User.fullname.ilike('%' + q_term + '%'),
            model.User.name.ilike('%' + q_term + '%')
        )
        )

    if obj_type:
        q = q.filter(model.Member.table_name == obj_type)
    if capacity:
        q = q.filter(model.Member.capacity == capacity)

    trans = new_authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return trans[capacity]
        except KeyError:
            return capacity

    if show_user_info:
        if show_sysadmin_info:
            return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity,
                     u.fullname if u.fullname else u.name, u.sysadmin)
                    for m, u in q.all()]
        else:
            return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity,
                     u.fullname if u.fullname else u.name)
                    for m, u in q.all()]
    else:
        return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity)
                for m, u in q.all()]

@logic.side_effect_free
def cached_group_list(context, data_dict):
    # to make things simpler for caching there's no argument passed
    groups = caching.cached_group_list()
    return groups


def invalidate_cache_for_groups(context, data_dict):
    _check_access('invalidate_cache_for_groups', context, data_dict)
    caching.invalidate_group_caches()


@logic.side_effect_free
def cached_organization_list(context, data_dict):
    orgs = caching.cached_organization_list()

    _refresh_pkg_count_on_org_list(orgs)

    return orgs


def _refresh_pkg_count_on_org_list(orgs):
    query_params = {
        'start': 0,
        'rows': 1,
        'fq': 'private: false',
        'fl': 'id name',
        'facet': 'true',
        'facet.pivot': ['organization,archived'],
        'facet.limit': 2000,
    }
    # search_result = tk.get_action('package_search')({}, query_params)
    query = search.query_for(model.Package)
    query.run(query_params)
    org_name_to_pkg_count = query.raw_response.get('facet_counts', {}).get('facet_pivot', {}).get(
        'organization,archived', {})
    org_name_to_pkg_count_dict = {}
    for org in org_name_to_pkg_count:
        org_name_to_pkg_count_dict[org.get('value')] = org

    try:
        for org in orgs:
            _org = org_name_to_pkg_count_dict.get(org['name'])
            if _org and 'pivot' in _org:
                for item in _org.get('pivot'):
                    if item.get('field') == u'archived' and item.get('value') == 'false':
                        org['package_count'] = item.get('count', 0)
                    elif item.get('field') == u'archived' and item.get('value') == 'true':
                        org['archived_package_count'] = item.get('count', 0)
            else:
                org['package_count'] = 0
                org['archived_package_count'] = 0
    except Exception as ex:
        log.info(ex)


def invalidate_cache_for_organizations(context, data_dict):
    _check_access('invalidate_cache_for_organizations', context, data_dict)
    caching.invalidate_cached_organization_list()


def invalidate_cached_resource_id_apihighways(context, data_dict):
    _check_access('invalidate_cached_resource_id_apihighways', context, data_dict)
    caching.invalidate_cached_resource_id_apihighways()


def invalidate_region(context, data_dict):
    _check_access('invalidate_region', context, data_dict)

    from ckanext.hdx_theme.util.jql import dogpile_jql_region
    from ckanext.hdx_package.helpers.caching import dogpile_org_group_lists_region, dogpile_pkg_external_region
    from ckanext.hdx_org_group.helpers.caching import dogpile_country_region
    from ckanext.hdx_theme.helpers.caching import dogpile_requests_region

    region_map = {
        'jql': dogpile_jql_region,
        'org_group': dogpile_org_group_lists_region,
        'country': dogpile_country_region,
        'requests': dogpile_requests_region,
        'pkg_external': dogpile_pkg_external_region
    }

    region_name = data_dict.get('name', '')
    region = region_map.get(region_name)
    message = 'Couldn\'t invalidate cache for region ' + region_name
    if region:
        region.invalidate()
        message = 'Successfully invalidated cache for region ' + region_name

    return {
        'message': message
    }


def hdx_basic_user_info(context, data_dict):
    result = {}

    _check_access('hdx_basic_user_info', context, data_dict)

    model = context['model']
    id = data_dict.get('id', None)
    if id:
        user_obj = model.User.get(id)
        if user_obj is None:
            raise logic.NotFound
        else:
            ds_num = counting.count_user_datasets(id)
            org_num = counting.count_user_orgs(id)
            grp_num = counting.count_user_grps(id)
            result = _create_user_dict(user_obj, ds_num=ds_num, org_num=org_num, grp_num=grp_num)
    return result


def _create_user_dict(user_obj, **kw):
    result = {'display_name': user_obj.fullname or user_obj.name,
              'created': user_obj.created.isoformat(),
              'name': user_obj.name,
              'email': user_obj.email,
              'email_hash': user_obj.email_hash,
              'id': user_obj.id}
    result.update(kw)
    return result


# def hdx_get_sys_admins(context, data_dict):
#     # TODO: check access that user is logged in
#     q = model.Session.query(model.User).filter(model.User.sysadmin == True)
#     return [{'name': m.name, 'display_name': m.fullname or m.name, 'email': m.email} for m in q.all()]


def hdx_send_editor_request_for_org(context, data_dict):
    _check_access('hdx_send_editor_request_for_org', context, data_dict)

    body = _('New request editor/admin role\n' \
             'Full Name: {fn}\n' \
             'Username: {username}\n' \
             'Email: {mail}\n' \
             'Organisation: {org}\n' \
             'Message from user: {msg}\n' \
             '(This is an automated mail)' \
             '').format(fn=data_dict['display_name'], username=data_dict['name'], mail=data_dict['email'],
                        org=data_dict['organization'], msg=data_dict.get('message', ''))
    if config.get('hdx.onboarding.send_confirmation_email', 'false') == 'true':
        hdx_mail.send_mail(data_dict['admins'], _('New Request Membership'), body, one_email=True)


@logic.side_effect_free
def hdx_get_indicator_values(context, data_dict):
    '''
    Makes a call to the REST API that provides the indicator values
    Current param supported are:
    :param it: indicator types
    :type it: list
    :param l: locations
    :type l: list
    :param s: sources
    :type s: list
    :param minTime: the start year
    :type minTime: int
    :param maxTime: the end year
    :type maxTime: int
    :param periodType: filter the period by another criteria
    :type periodType: string
    :param pageNum: for pagination - page number
    :type pageNum: int
    :param pageSize: for pagination - max number of items in result
    :type pageSize: int
    :param lang: language
    :type lang: string
    '''

    transformer = transformers.FilterTransformer('#country+code', data_dict.get('l'))
    source_url = config.get('hdx.locations.toplines_url')
    if source_url:
        mapping = {
            '#country+code': 'countryCode',
            '#date': 'date',
            '#indicator+name': 'indicatorTypeName',
            '#indicator+unit': 'unitName',
            '#meta+source': 'sourceName',
            '#meta+url': 'datasetLink',
            '#value+amount': 'value',
        }
        result = transform_response_to_dict_list(do_hxl_transformation(source_url, transformer), mapping)

        for item in result:
            if 'value' in item:
                item['value'] = float(item['value'])

        return result

    return []


# @logic.side_effect_free
# def hdx_get_indicator_available_periods(context, data_dict):
#     '''
#     Makes a call to the REST API that provides the indicator values
#     Current param supported are:
#     :param it: indicator types
#     :type it: list
#     :param l: locations
#     :type l: list
#     :param s: sources
#     :type s: list
#     :param minTime: the start year
#     :type minTime: int
#     :param maxTime: the end year
#     :type maxTime: int
#     '''
#
#     endpoint = config.get('hdx.rest.indicator.endpoint.facets') + "/available-periods" + '?'
#
#     filter_list = []
#
#     for param_name in ['it', 'l', 'ds', 's', 'minTime', 'maxTime']:
#         param_values = data_dict.get(param_name, None)
#         filter_list = _add_to_filter_list(param_values, param_name, filter_list)
#
#     filter_list.sort()
#     url = endpoint + "&".join(filter_list)
#
#     return _make_rest_api_request(url)


def _add_to_filter_list(src, param_name, filter_list):
    if src:
        if isinstance(src, list):
            temp_filters = [
                '{}={}'.format(param_name, elem) for elem in src]
            filter_list = filter_list + temp_filters
        else:
            filter_list.append('{}={}'.format(param_name, src))

    return filter_list


@logic.side_effect_free
def hdx_carousel_settings_show(context, data_dict):
    '''
    :returns: list of dictionaries representing the setting for each carousel item. Returns default if nothing is in db.
    :rtype: list of dict
    '''
    from ckanext.hdx_theme.helpers.initial_carousel_settings import INITIAL_CAROUSEL_DATA

    carousel_settings = []
    setting_value_json = model.get_system_info('hdx.carousel.config', config.get('hdx.carousel.config'))
    if setting_value_json:
        try:
            carousel_settings = json.loads(setting_value_json)
        except TypeError as e:
            log.warn('The "hdx.carousel.config" setting is not a proper json string')

    if not carousel_settings and not context.get('not_initial'):
        carousel_settings = INITIAL_CAROUSEL_DATA
        for i, item in enumerate(carousel_settings):
            item['order'] = i + 1

    return carousel_settings


@logic.side_effect_free
def hdx_quick_links_settings_show(context, data_dict):
    '''
    :returns: list of dictionaries representing the setting for each quick_links item. Returns default if nothing is in db.
    :rtype: list of dict
    '''

    quick_links_settings = []
    setting_value_json = model.get_system_info('hdx.quick_links.config', config.get('hdx.quick_links.config'))
    if setting_value_json:
        try:
            quick_links_settings = json.loads(setting_value_json)
        except TypeError as e:
            log.warn('The "hdx.quick_links.config" setting is not a proper json string')

    return quick_links_settings


@logic.side_effect_free
def package_links_settings_show(context, data_dict):
    '''
    :returns: list of dictionaries representing the setting for each package_links item. Returns default if nothing is in db.
    :rtype: list of dict
    '''

    package_links_settings = []
    setting_value_json = model.get_system_info('hdx.package_links.config', config.get('hdx.package_links.config'))
    if setting_value_json:
        try:
            package_links_settings = json.loads(setting_value_json)
        except TypeError as e:
            log.warn('The "hdx.package_links.config" setting is not a proper json string')

    return package_links_settings


def hdx_carousel_settings_update(context, data_dict):
    '''

    :param 'hdx.carousel.config': a list with the carousel settings
    :type 'hdx.carousel.config': list
    :return: The JSON string that is the value of the new 'hdx.carousel.config'
    :rtype: str
    '''

    logic.check_access('hdx_carousel_update', context, {})

    settings = data_dict.get('hdx.carousel.config')
    settings_json = json.dumps(settings)
    model.set_system_info('hdx.carousel.config', settings_json)
    return settings_json


def hdx_quick_links_settings_update(context, data_dict):
    '''

    :param 'hdx.quick_links.config': a list with the quick_links settings
    :type 'hdx.quick_links.config': list
    :return: The JSON string that is the value of the new 'hdx.quick_links.config'
    :rtype: str
    '''

    logic.check_access('hdx_quick_links_update', context, {})

    settings = data_dict.get('hdx.quick_links.config')
    settings_json = json.dumps(settings)
    model.set_system_info('hdx.quick_links.config', settings_json)
    return settings_json


def package_links_settings_update(context, data_dict):
    '''

    :param 'hdx.package_links.config': a list with the package_links settings
    :type 'hdx.package_links.config': list
    :return: The JSON string that is the value of the new 'hdx.package_links.config'
    :rtype: str
    '''

    logic.check_access('hdx_quick_links_update', context, {})

    settings = data_dict.get('hdx.package_links.config')
    settings_json = json.dumps(settings)
    model.set_system_info('hdx.package_links.config', settings_json)
    return settings_json


@logic.side_effect_free
def package_links_by_id_list(context, data_dict):
    '''
    :returns: list of dictionaries representing the settings for a package_id
    :rtype: list of dict
    '''

    package_links_settings = []
    if data_dict.get('id'):
        setting_value_json = model.get_system_info('hdx.package_links.config', config.get('hdx.package_links.config'))
        if setting_value_json:
            try:
                _all_pls = json.loads(setting_value_json)
                for item in _all_pls:
                    if item.get('package_list'):
                        pkg_list = item.get('package_list').split(',')
                        if pkg_list and data_dict.get('id') in pkg_list:
                            package_links_settings.append(item)
            except TypeError as e:
                log.warn('The "hdx.package_links.config" setting is not a proper json string')
    return package_links_settings


def hdx_organization_list_for_user(context, data_dict):
    '''Return the organizations that the user has a given permission for.

    By default this returns the list of organizations that the currently
    authorized user can edit, i.e. the list of organizations that the user is an
    admin of.

    Specifically it returns the list of organizations that the currently
    authorized user has a given permission (for example: "manage_group") against.

    When a user becomes a member of an organization in CKAN they're given a
    "capacity" (sometimes called a "role"), for example "member", "editor" or
    "admin".

    Each of these roles has certain permissions associated with it. For example
    the admin role has the "admin" permission (which means they have permission
    to do anything). The editor role has permissions like "create_dataset",
    "update_dataset" and "delete_dataset".  The member role has the "read"
    permission.

    This function returns the list of organizations that the authorized user
    has a given permission for. For example the list of organizations that the
    user is an admin of, or the list of organizations that the user can create
    datasets in. This takes account of when permissions cascade down an
    organization hierarchy.

    :param permission: the permission the user has against the
        returned organizations, for example ``"read"`` or ``"create_dataset"``
        (optional, default: ``"edit_group"``)
    :type permission: string

    :returns: list of organizations that the user has the given permission for
    :rtype: list of dicts

    '''
    model = context['model']
    # added by HDX (from latest ckan code)
    if data_dict.get('id'):
        user_obj = model.User.get(data_dict['id'])
        if not user_obj:
            raise NotFound
        user = user_obj.name
    else:
        user = context['user']

    _check_access('organization_list_for_user', context, data_dict)
    sysadmin = authz.is_sysadmin(user)

    orgs_q = model.Session.query(model.Group) \
        .filter(model.Group.is_organization == True) \
        .filter(model.Group.state == 'active')

    if not sysadmin:
        # for non-Sysadmins check they have the required permission

        # NB 'edit_group' doesn't exist so by default this action returns just
        # orgs with admin role
        permission = data_dict.get('permission', 'edit_group')

        roles = authz.get_roles_with_permission(permission)

        if not roles:
            return []
        user_id = authz.get_user_id_for_username(user, allow_none=True)
        if not user_id:
            return []

        q = model.Session.query(model.Member, model.Group) \
            .filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity.in_(roles)) \
            .filter(model.Member.table_id == user_id) \
            .filter(model.Member.state == 'active') \
            .join(model.Group)

        group_ids = set()
        roles_that_cascade = \
            authz.check_config_permission('roles_that_cascade_to_sub_groups')
        for member, group in q.all():
            if member.capacity in roles_that_cascade:
                group_ids |= set([
                    grp_tuple[0] for grp_tuple
                    in group.get_children_group_hierarchy(type='organization')
                ])
            group_ids.add(group.id)

        if not group_ids:
            return []

        orgs_q = orgs_q.filter(model.Group.id.in_(group_ids))

    orgs_list = model_dictize.group_list_dictize(orgs_q.all(), context)
    return orgs_list


def hdx_push_general_stats(context, data_dict):

    _check_access('hdx_push_general_stats', context, {})
    stats_helper = HDXStatsHelper(context, compute_user_stats=False).fetch_data()

    analytics_sender = HDXStatsAnalyticsSender(stats_helper)
    analytics_sender.send_to_queue()

    if analytics_sender.pushed_successfully:
        return analytics_sender.stats_dict
    else:
        raise Exception('There was a problem pushing the stats to the server')


@logic.side_effect_free
def hdx_general_statistics(context, data_dict):

    stats_helper = HDXStatsHelper(context).fetch_data()

    results = {
        'datasets': {
            'total': stats_helper.datasets_total,
            'with_geodata': stats_helper.datasets_with_geodata,
            'with_showcases': stats_helper.datasets_with_showcases,
            'qa': {
                'in_quarantine': stats_helper.datasets_qa_in_quarantine,
                HDXStatsHelper.IN_QA: stats_helper.datasets_qa_in_qa,
                HDXStatsHelper.QA_COMPLETED: stats_helper.datasets_qa_qa_completed,
            }
        },
        'organizations': {
            'total': stats_helper.orgs_total,
            'with_datasets': stats_helper.orgs_with_datasets,
            'without_datasets': stats_helper.orgs_total - stats_helper.orgs_with_datasets,
            'active_last_year': stats_helper.orgs_updating_data_past_year,
            'not_active_last_year': stats_helper.orgs_total - stats_helper.orgs_updating_data_past_year,
        },
        'users': {
            'total': stats_helper.active_users_completed + stats_helper.active_users_not_completed,
            'completed_registration': stats_helper.active_users_completed,
            'not_completed_registration': stats_helper.active_users_not_completed
        }
    }

    return results


# def page_create(context, data_dict):
#     '''
#     Only sysadmins are allowed to call this action
#     '''
#     return {'success': False, 'msg': _('Only sysadmins can manage custom pages')}


@logic.side_effect_free
def hdx_user_statistics(context, data_dict):
    _check_access('hdx_user_statistics', context, data_dict)

    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)
    q = model.Session.query(model.User)
    q = q.filter(model.User.state == 'active')
    user_list = q.all()

    result = {}
    for user in user_list:
        no_activities = get_activities_by_user_by_date(user.id, start_date, end_date)
        result[user.id] = {
            'id': user.id,
            'name': user.name,
            'no_of_activities': no_activities
        }
    return result


def get_activities_by_user_by_date(user_id, start_date=None, end_date=None):
    result = None
    if user_id:
        q = model.Session.query(model.Activity)
        q = q.filter(model.Activity.user_id == user_id)
        if start_date:
            q = q.filter(model.Activity.timestamp >= start_date)
        if end_date:
            q = q.filter(model.Activity.timestamp <= end_date)
        result = q.count()
    return result


@logic.side_effect_free
def hdx_organization_statistics(context, data_dict):
    _check_access('hdx_user_statistics', context, data_dict)

    org_list = tk.get_action('organization_list')(context, {"all_fields": True})

    query = model.Session.query(model.Group.id)
    query = query.filter(model.Group.state != 'active')
    query = query.filter(model.Group.is_organization == True)
    query = query.filter(model.Group.type == 'organization')
    orgs = query.all()
    inactive_org_list = []
    for org in orgs:
        inactive_org_list.append(logic.get_action('organization_show')(context, {'id': org.id, 'include_extras': True}))

    return {
        'active_organizations': org_list,
        'inactive_organizations': inactive_org_list
    }


@logic.side_effect_free
def hdx_activity_detail_list(context, data_dict):
    result = ckan_get.activity_detail_list(context, data_dict)
    detail_data_list = (
        detail_data
        for detail in result or []
        for detail_data in detail.get('data', {}).values()
    )
    for detail_data_dict in detail_data_list:
        detail_data_dict.pop('maintainer_email', None)
        detail_data_dict.pop('author_email', None)

    return result
